import logging
from datetime import datetime
from string import Template

from agents import build_agents
from agents.base import load_prompt, msg
from config import GENERIC_ERROR
from llm_client import call
from memory import session_store

logger = logging.getLogger("uvicorn.error")


class Orchestrator:
    def __init__(self):
        self.agents = build_agents()
        self.prompt = load_prompt("router")

    def route(self, session_id, message, last):
        turns = session_store.get(last, session_id) if last in self.agents else []
        system = Template(self.prompt).safe_substitute(
            today=datetime.now().strftime("%A, %d %B %Y"),
            catalog="\n".join(f"- {a.name}: {a.description}" for a in self.agents.values()),
            last_agent=last,
            last_reply=turns[-1]["content"][0]["text"] if turns else "none",
        )
        reply = call(system, [msg("user", message)], max_tokens=30, temperature=0.0)
        logger.info("[ORCH] router said %r (last agent: %s)", reply, last)
        fallback = self.agents.get(last, self.agents["general_agent"])
        return next((a for n, a in self.agents.items() if n in reply), fallback)

    def handle(self, session_id, message):
        try:
            last = session_store.last_agent(session_id)
            agent = self.route(session_id, message, last)
            session_store.set_last_agent(session_id, agent.name)
            handoff = session_store.handoff_for(session_id, agent.name)
            logger.info("[ORCH] session=%s routed %s -> %s | handoff: %s", session_id, last, agent.name, handoff or "none")
            return agent.run(session_id, message, handoff)
        except Exception:
            logger.exception("request failed")
            return GENERIC_ERROR


orchestrator = Orchestrator()