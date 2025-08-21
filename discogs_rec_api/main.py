import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from ml.recommender import initialize
from discogs_rec_api.routers import (
    admin,
    auth,
    recommender,
    users,
    releases,
    favorites,
    searches,
    recommendations,
    feedback,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager that handles startup and shutdown events.

    Initializes database tables and loads ML models on startup.

    Args:
        app: FastAPI application instance

    Yields:
        None: Application runs in this context
    """
    initialize()
    yield


app = FastAPI(
    title="Discogs Recommendation API",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(recommender.router)
app.include_router(users.router)
app.include_router(favorites.router)
app.include_router(searches.router)
app.include_router(recommendations.router)
app.include_router(releases.router)
app.include_router(feedback.router)

logger = logging.getLogger("uvicorn")


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint that returns a welcome message.

    Returns:
        dict: Welcome message
    """
    return {"message": "Welcome to Discogs Rec!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "discogs_rec_api.main:app",
        reload=True,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
