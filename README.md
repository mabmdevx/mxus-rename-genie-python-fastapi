# Rename Genie

## Description
- A simple but powerful way to bulk rename your files and directories using AI powered by LLM

## Tech Stack
- Tech Stack: Python FastAPI, Bootstrap, HTML, CSS, JS
- WebApp Architecture: Postback
- LLM Platform: OpenRouter

### Screenshots

Homepage ![Rename Genie - Home](./screenshots/rename_genie1.png)

Scanned Workspace ![Rename Genie - Scanned Workspace](./screenshots/rename_genie2.png)

Scanned Workspace and Prompt ![Rename Genie - Scanned Workspace and Prompt](./screenshots/rename_genie3.png)

Preview before Apply ![Rename Genie - Preview before Apply](./screenshots/rename_genie4.png)

After Apply Summary ![Rename Genie - After Apply Summary](./screenshots/rename_genie5.png)

## Environment Setup

### Create a virtual environment
```
# For Unix environment
python -m venv .venv
source .venv/bin/activate
```

```
# For Windows environment
python -m venv .venv
.venv\Scripts\activate
```

### Install dependencies
```
pip install -r requirements.txt
```

### Create the config file
```
cp config.yaml.example config.yaml
```
Set your OpenRouter API key and OpenRouter model in config.yaml

### Running the app
```
python app/main.py
```

Application will start by default on http://localhost:8000

### Setup the workspace directory
Drop the files and folders you want to rename in the `workspace` directory.

