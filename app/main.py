import os
import uuid
import json
import yaml
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from contextlib import asynccontextmanager

from helpers.common import build_tree, flatten_tree
from helpers.llm import call_llm
from helpers.logging import logger, set_run_logger, reset_run_logger

# -------------------- Load Config --------------------
CONFIG_PATH = Path("config.yaml")
if not CONFIG_PATH.exists():
    raise FileNotFoundError("Missing config.yaml in project root")

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

WORKSPACE_PATH = Path(config.get("workspace_path", "workspace"))
WORKSPACE_PATH.mkdir(exist_ok=True)

OPENROUTER_API_KEY = config.get("openrouter_api_key")
OPENROUTER_MODEL = config.get("openrouter_model", "openai/gpt-oss-20b:free")
LOG_LEVEL = config.get("log_level", "INFO").upper()
IGNORE_FILES = config.get("ignore_files", [".gitignore"])
APP_PORT = int(config.get("app_port", 8000))
APP_RELOAD = config.get("app_reload", False)

# -------------------- App --------------------
app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

SCAN_CACHE = {}  # run_id -> tree JSON / mapping
logger.info("App initialized with config.yaml")

# -------------------- Routes --------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    logger.info("Landing page accessed")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scan", response_class=HTMLResponse)
def scan(request: Request):
    run_id = str(uuid.uuid4())
    set_run_logger(run_id)
    logger.info(f"[{run_id}] Scanning workspace at {WORKSPACE_PATH}")
    tree = build_tree(WORKSPACE_PATH, run_id, IGNORE_FILES)
    SCAN_CACHE[run_id] = tree
    logger.info(f"[{run_id}] Scan complete")
    return RedirectResponse(url=f"/prompt?run_id={run_id}", status_code=303)

@app.get("/prompt", response_class=HTMLResponse)
def prompt(request: Request, run_id: str):
    logger.info(f"[{run_id}] Prompt page accessed")
    tree = SCAN_CACHE.get(run_id)
    if not tree:
        logger.warning(f"[{run_id}] run_id not found")
        return HTMLResponse("<p>Error: run_id not found. Please scan first.</p>")
    tree_json = json.dumps(tree)
    return templates.TemplateResponse(
        "prompt.html", {"request": request, "tree_json": tree_json, "run_id": run_id}
    )

@app.post("/preview", response_class=HTMLResponse)
async def preview(request: Request, run_id: str = Form(...), prompt: str = Form(...)):
    logger.info(f"[{run_id}] Preview requested")
    tree = SCAN_CACHE.get(run_id)
    if not tree:
        logger.warning(f"[{run_id}] Scanned tree not found")
        return HTMLResponse("<p>Error: scanned tree not found.</p>")

    flat_items = flatten_tree(tree)
    try:
        mapping = await call_llm(OPENROUTER_API_KEY, OPENROUTER_MODEL, flat_items, prompt, run_id)
        logger.info(f"[{run_id}] LLM mapping generated with {len(mapping)} items")
    except Exception as e:
        return HTMLResponse(f"<p>Error calling LLM API: {e}</p>")

    SCAN_CACHE[f"{run_id}_mapping"] = mapping
    return templates.TemplateResponse("preview.html", {"request": request, "mapping": mapping, "run_id": run_id})

@app.post("/apply", response_class=HTMLResponse)
def apply(request: Request, run_id: str = Form(...)):
    logger.info(f"[{run_id}] Apply rename requested")
    mapping = SCAN_CACHE.get(f"{run_id}_mapping")
    if not mapping:
        logger.warning(f"[{run_id}] Mapping not found")
        return HTMLResponse("<p>Error: mapping not found. Please run rename first.</p>")

    renamed_items = []
    sorted_mapping = sorted(mapping, key=lambda e: len(Path(e["original"]).parts), reverse=True)

    for entry in sorted_mapping:
        src = WORKSPACE_PATH.parent / entry["original"]
        dst = WORKSPACE_PATH.parent / entry["new"]
        try:
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                src.rename(dst)
                renamed_items.append({"original": entry["original"], "new": entry["new"]})
                logger.info(f"[{run_id}] Renamed: {entry['original']} -> {entry['new']}")
        except Exception as e:
            renamed_items.append({"original": entry["original"], "new": f"Failed: {entry['new']}"})
            logger.error(f"[{run_id}] Failed to rename {entry['original']} -> {entry['new']}: {e}")

    updated_tree = build_tree(WORKSPACE_PATH, run_id, IGNORE_FILES)
    tree_json = json.dumps(updated_tree)
    logger.info(f"[{run_id}] Rename operation complete")

    # Reset run logger after apply
    reset_run_logger()

    return templates.TemplateResponse(
        "apply.html",
        {"request": request, "tree_json": tree_json, "renamed_items": renamed_items}
    )


# -------------------- Startup Event --------------------    
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info(f"Rename Genie App running at http://localhost:{APP_PORT}")
    yield
    # Shutdown logic
    logger.info("Rename Genie App is shutting down.")

# -------------------- Entry Point --------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=APP_PORT, reload=APP_RELOAD)
    