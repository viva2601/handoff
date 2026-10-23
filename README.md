# Booking Orchestrator: Multi-Agent Travel Assistant

A multi-agent LLM system served through FastAPI. An LLM-based **orchestrator** routes each customer message to a specialist **flight**, **hotel**, or **general** agent. The agents call tools, answer policy questions with **RAG** over FAQ documents, and **hand off trip details** to each other, so a customer who searches for flights does not have to repeat the destination and dates when they ask about hotels.

## Features

- **LLM router:** picks one agent per message. It prefers the last active agent for short follow-ups ("2", "yes", a city name) and only switches when the topic clearly changes.
- **Specialist agents:**
  - `flight_agent`: searches flights and answers airline policy questions (baggage, cancellations, delays, documents)
  - `hotel_agent`: searches hotels, answers hotel policy questions, and reports live weather and forecasts for any city
  - `general_agent`: greetings, thanks, "what can you do", and anything unrelated to travel
- **Tool-calling loop:** agents emit `<tool_call>` JSON, the code runs the tool and returns a `<tool_result>`, and the loop is capped at 4 steps.
- **RAG FAQ search:** FAQ text is split into chunks, embedded with `sentence-transformers/all-MiniLM-L6-v2`, and stored in a persistent Chroma collection per agent (top 3 results per question).
- **Cross-agent handoff:** details saved from a flight search (destination, depart date, passengers) are carried into a hotel search (location, check-in, guests), and the other way round.
- **Live weather:** Open-Meteo geocoding and forecast APIs (current conditions or a date-range forecast).
- **Input validation through prompts:** passengers 1 to 9, hotel guests 1 to 10, dates within the next 12 months, stays of at most 30 nights, and no inventing of missing values.
- **Safety rules in prompts:** agents cannot book, confirm, or take payment. They treat customer messages and tool results as data, not instructions.
- **Memory:** short-term conversation memory in Redis (last 10 turns, 30-minute TTL) and a permanent chat log in PostgreSQL, grouped by session and trace ID.

## Architecture

```
Client --> FastAPI (/query)
              |
          Orchestrator  --(LLM router prompt)--> picks an agent
              |
   +----------+-----------+
   |          |           |
 Flight     Hotel      General
 agent      agent      agent
   |          |
 Tools: search_flights / search_hotels / search_weather / search_faq (Chroma)
              |
   Redis (session memory, last agent, handoff)   PostgreSQL (chat_history)
```

## API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/query` | Body: `{"session_id": "...", "query": "..."}`. Returns the assistant reply as plain text |
| GET | `/history/{session_id}` | Returns the stored turns for a session |

## Project structure

```
.
├── main.py              # Starts uvicorn
├── api.py               # FastAPI app and endpoints
├── config.py            # Settings and environment variables
├── llm_client.py        # LLM HTTP client (streaming responses)
├── memory.py            # Redis session store and PostgreSQL chat history
├── orchestrator.py      # Router and request handling
├── agents/
│   ├── __init__.py      # Agent registry
│   ├── base.py          # Agent base class: prompt, tool loop, memory
│   ├── flight_agent.py
│   ├── hotel_agent.py
│   └── general_agent.py
├── prompts/             # router.txt, flight_agent.txt, hotel_agent.txt, general_agent.txt
└── faq/                 # flight_agent.txt, hotel_agent.txt (FAQ entries separated by blank lines)
```

## Setup

**Requirements:** Python 3.10+, a running Redis server (default `localhost:6379`), and a PostgreSQL database.

1. Install the dependencies:
   ```bash
   pip install fastapi uvicorn pydantic python-dotenv requests "psycopg[binary]" redis \
       langchain-huggingface langchain-text-splitters langchain-chroma sentence-transformers
   ```
2. Create a `.env` file in the project root:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   WRAPPER_API_KEY=your-llm-api-key
   ```
3. Create the chat log table (schema inferred from the queries in `memory.py`; adjust it to your needs):
   ```sql
   CREATE TABLE IF NOT EXISTS chat_history (
       id SERIAL PRIMARY KEY,
       session_id TEXT NOT NULL,
       trace_id UUID,
       agent TEXT NOT NULL,
       user_text TEXT NOT NULL,
       assistant_text TEXT NOT NULL
   );
   ```
4. Start the server (it listens on port 8010):
   ```bash
   python main.py
   ```
   The first start downloads the embedding model and builds the Chroma FAQ index.

**Try it:**
```bash
curl -X POST http://localhost:8010/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "query": "Find flights from Mumbai to Delhi for 2 passengers next Friday"}'
```

## Notes and limitations

- `search_flights` and `search_hotels` return **sample data**. Replace them with a real flight or hotel provider API.
- The assistant only shows options. It cannot book, change, or cancel anything.
- The LLM is called through an HTTP wrapper that streams responses (`llm_client.py`, configured with `WRAPPER_URL` and `WRAPPER_MODEL_ID` in `config.py`). To use a different provider, only `llm_client.py` needs to change.
- There is no authentication on the API, and Redis is expected on localhost.

## Tech stack

Python, FastAPI, LangChain, ChromaDB, Hugging Face sentence-transformers, Redis, PostgreSQL (psycopg), Open-Meteo API, Anthropic Claude Haiku 4.5 (via AWS Bedrock)

## Author

**Vivaswan Tiwari**
[LinkedIn](https://www.linkedin.com/in/vivaswan-tiwari39853b140) · [GitHub](https://github.com/viva2601)
