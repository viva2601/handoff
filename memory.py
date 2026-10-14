import json

import psycopg # type: ignore
import redis # type: ignore

from config import DATABASE_URL, MAX_MEMORY_TURNS, REDIS_HOST, REDIS_PORT, SESSION_TTL_SECONDS

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def _key(agent_name, session_id):
    return f"session:{agent_name}:{session_id}"


class SessionStore:
    def get(self, agent_name, session_id):
        raw = redis_client.get(_key(agent_name, session_id))
        return json.loads(raw) if raw else []

    def append_turn(self, agent_name, session_id, user_text, answer):
        history = self.get(agent_name, session_id) + [
            {"role": "user", "content": [{"type": "text", "text": user_text}]},
            {"role": "assistant", "content": [{"type": "text", "text": answer}]},
        ]
        redis_client.set(_key(agent_name, session_id), json.dumps(history[-MAX_MEMORY_TURNS * 2:]),
                         ex=SESSION_TTL_SECONDS)

    def set_last_agent(self, session_id, agent_name):
        redis_client.set(f"last_agent:{session_id}", agent_name, ex=SESSION_TTL_SECONDS)

    def last_agent(self, session_id):
        return redis_client.get(f"last_agent:{session_id}") or "none"

    def save_handoff(self, session_id, agent_name, details):
        key = f"handoff:{session_id}"
        redis_client.hset(key, agent_name, json.dumps(details))
        redis_client.expire(key, SESSION_TTL_SECONDS)

    def handoff_for(self, session_id, agent_name):
        saved = redis_client.hgetall(f"handoff:{session_id}")
        return {k: v for a, raw in saved.items() if a != agent_name for k, v in json.loads(raw).items()}


def save_turn(session_id, agent, user_text, assistant_text):
    with psycopg.connect(DATABASE_URL) as conn:
        conn.execute("INSERT INTO chat_history (session_id, agent, user_text, assistant_text) VALUES (%s, %s, %s, %s)",
                     (session_id, agent, user_text, assistant_text))


def load_turns(session_id):
    with psycopg.connect(DATABASE_URL) as conn:
        rows = conn.execute("SELECT agent, user_text, assistant_text FROM chat_history WHERE session_id = %s ORDER BY id",
                            (session_id,)).fetchall()
    return [{"agent": a, "user": u, "assistant": t} for a, u, t in rows]


session_store = SessionStore()