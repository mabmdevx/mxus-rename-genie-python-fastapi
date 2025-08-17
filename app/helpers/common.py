import os
from pathlib import Path

from helpers.logging import logger

def build_tree(path: Path, run_id=None, ignore_files=None):
    if path.name in ignore_files:
        logger.debug(f"[{run_id}] Ignoring file: {path}")
        return None
    node = {"name": path.name, "is_dir": path.is_dir(), "children": []}
    if path.is_dir():
        children = []
        for child in sorted(path.iterdir()):
            child_node = build_tree(child, run_id, ignore_files)
            if child_node:
                children.append(child_node)
        node["children"] = children
    logger.debug(f"[{run_id}] Built node for: {path}")
    return node

def flatten_tree(node, parent_path=""):
    path = os.path.join(parent_path, node["name"])
    items = [{"original": path, "is_dir": node["is_dir"]}]
    for child in node.get("children", []):
        items.extend(flatten_tree(child, path))
    return items