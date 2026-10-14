import logging

from fastapi import FastAPI, Request # type: ignore
from fastapi.exceptions import RequestValidationError # type: ignore
from fastapi.responses import PlainTextResponse # type: ignore
from pydantic import BaseModel, Field # type: ignore

from config import GENERIC_ERROR
from memory import load_turns
from orchestrator import orchestrator

logger = logging.getLogger("uvicorn.error")
app = FastAPI(title="Booking Orchestrator")


class QueryRequest(BaseModel):
    session_id: str = "default"
    query: str = Field(min_length=1)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    logger.warning("Invalid request: %s", exc.errors())
    return PlainTextResponse(GENERIC_ERROR, status_code=400)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def query(req: QueryRequest):
    return PlainTextResponse(orchestrator.handle(req.session_id, req.query))


@app.get("/history/{session_id}")
def history(session_id: str):
    return {"session_id": session_id, "turns": load_turns(session_id)}