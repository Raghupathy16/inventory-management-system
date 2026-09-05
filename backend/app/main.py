"""
Application entrypoint.

Deliberately thin: this file only creates the FastAPI app, configures
CORS, and registers routers. All actual logic lives in api/, services/,
repositories/. This keeps main.py readable no matter how large the app
grows — a common review complaint in real codebases is a main.py that has
turned into a 2,000-line dumping ground.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import check_db_connection

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CONCEPT: CORS (Cross-Origin Resource Sharing)
# ------------------------------------------------
# What it is: a browser security mechanism that blocks a web page served
# from one origin (e.g. http://localhost:5173, our React dev server) from
# making requests to a different origin (e.g. http://localhost:8000, our
# API) unless the API explicitly allows it.
# Why we need it: our React frontend and FastAPI backend run on different
# ports/origins during development, so without this, every API call from
# the browser would be silently blocked.
# Where we use it: applied globally here as middleware.
# What problem it solves: lets the frontend talk to the backend at all,
# while still letting us restrict *which* origins are allowed (important
# for production security — we don't want to allow "*" origins once real
# user data is involved).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health_check():
    """
    Confirms the API process is up AND the database is reachable.

    A health check that only returns {"status": "ok"} without touching the
    DB is close to useless for this project — nearly everything we build
    depends on that connection, so we want failures surfaced immediately
    and loudly, not discovered later when a real feature breaks.
    """
    check_db_connection()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database": "connected",
    }


# Routers from app/api/ will be registered here starting Phase 3
# (app.include_router(auth.router), etc.)
