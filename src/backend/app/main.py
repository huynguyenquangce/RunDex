from fastapi import FastAPI

app = FastAPI(title="RunDex API", version="0.1.0")


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
