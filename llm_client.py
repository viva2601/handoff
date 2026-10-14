import json

import requests  # type: ignore
from config import WRAPPER_URL, WRAPPER_API_KEY, WRAPPER_MODEL_ID


def _payload(system_text, messages, max_tokens, temperature):
    return {
        "model_id": WRAPPER_MODEL_ID,
        "body": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_text,
            "messages": messages,
        },
    }


def call(system_text, messages, max_tokens, temperature):
    headers = {"api-key": WRAPPER_API_KEY, "Content-Type": "application/json"}
    payload = _payload(system_text, messages, max_tokens, temperature)
    chunks = []
    with requests.post(WRAPPER_URL, headers=headers, json=payload, timeout=45, stream=True) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data = line[len("data:"):].strip()
            if data and data != "[DONE]":
                chunks.append(json.loads(data).get("text") or "")
    return "".join(chunks)