"""Step 5: wrap the agent in a web service so anything can call it.

Run:  uvicorn steps.step5_service:app --reload --port 8010
Then: curl localhost:8010/health
(Port 8010, not uvicorn's default 8000, which other local apps often hold.)
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so we can import agent.py
import agent

app = FastAPI(title="Northwind Cloud ticket triage agent")


class Ticket(BaseModel):
    id: str
    sender: str = Field(alias="from")
    subject: str
    body: str


@app.get("/health")
def health():
    return {"status": "ok", "model": agent.MODEL}


@app.post("/triage")
def triage(ticket: Ticket):
    return agent.triage(ticket.model_dump(by_alias=True))
