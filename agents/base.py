import json
import logging
import os
from datetime import datetime
from string import Template

from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter # type: ignore

from config import (AGENT_MAX_TOKENS, AGENT_TEMPERATURE, CHUNK_OVERLAP, CHUNK_SIZE, EMBED_MODEL,
                    MAX_TOOL_STEPS, PROMPTS_DIR)
from llm_client import call
from memory import save_turn, session_store

logger = logging.getLogger("uvicorn.error")
TAG, END = "<tool_call>", "</tool_call>"
embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def load_prompt(name):
    with open(os.path.join(PROMPTS_DIR, f"{name}.txt"), encoding="utf-8") as f:
        return f.read().strip()


def msg(role, text):
    return {"role": role, "content": [{"type": "text", "text": text}]}


class Agent:
    name = description = handoff_tool = ""

    def __init__(self):
        self.prompt = load_prompt(self.name)
        self.tools = {n: getattr(self, n) for n in dir(self) if n.startswith("search_")}

    def _run_tool(self, session_id, tool_call):
        try:
            result = self.tools[tool_call["name"]](**tool_call["arguments"])
        except Exception as e:
            return {"error": str(e)}
        if tool_call["name"] == self.handoff_tool:
            session_store.save_handoff(session_id, self.name, tool_call["arguments"])
        return result

    def run(self, session_id, message, handoff):
        system = Template(self.prompt).safe_substitute(
            today=datetime.now().strftime("%A, %d %B %Y"), handoff=json.dumps(handoff) if handoff else "none")
        messages = session_store.get(self.name, session_id) + [msg("user", message)]
        for _ in range(MAX_TOOL_STEPS):
            text = call(system, messages, AGENT_MAX_TOKENS, temperature=AGENT_TEMPERATURE)
            if TAG not in text:
                reply = text.strip()
                session_store.append_turn(self.name, session_id, message, reply)
                save_turn(session_id, self.name, message, reply)
                return reply
            payload = text.split(TAG, 1)[1].split(END)[0]
            result = self._run_tool(session_id, json.loads(payload))
            logger.info("[%s] %s -> %s", self.name, payload, result)
            messages += [msg("assistant", TAG + payload + END),
                         msg("user", f"<tool_result>{json.dumps(result, ensure_ascii=False)}</tool_result>")]
        raise RuntimeError(f"{self.name} reached the tool step limit")