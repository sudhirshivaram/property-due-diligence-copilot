"""Application shell; no due-diligence endpoint is implemented yet."""

from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Property Due-Diligence Copilot")
app.include_router(router)
