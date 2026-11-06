from fastapi import FastAPI

from app.api import events

app = FastAPI(
    title="RunDex API",
    version="0.1.0",
    description="Running events in Vietnam: list, search, filter and event details.",
)
app.include_router(events.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
