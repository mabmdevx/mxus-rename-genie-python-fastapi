import json
import httpx

from helpers.logging import logger

async def call_llm(openrouter_api_key, openrouter_model, file_list, user_prompt, run_id):
    logger.info(f"[{run_id}] Calling LLM API with {len(file_list)} items")
    system_prompt = (
        "You are an assistant strictly limited to renaming files and directories. "
        "Return ONLY a JSON array with each entry containing 'original' and 'new'. "
        "Do not include explanations or anything else."
    )
    payload = {
        "model": openrouter_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps({"prompt": user_prompt, "files": file_list})},
        ],
    }
    headers = {"Authorization": f"Bearer {openrouter_api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"[{run_id}] Received LLM response")
            return json.loads(content)
        except Exception as e:
            logger.error(f"[{run_id}] LLM API call failed: {e}")
            raise