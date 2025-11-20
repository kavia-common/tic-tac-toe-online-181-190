from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from src.api.errors import (
    value_error_exception_handler,
    key_error_exception_handler,
)
from src.api.routers.games import router as games_router

openapi_tags = [
    {"name": "Health", "description": "Service health and diagnostics."},
    {"name": "Games", "description": "Create and manage Tic Tac Toe games."},
]

app = FastAPI(
    title="Tic Tac Toe Backend",
    description="REST API for playing Tic Tac Toe against players or the computer.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(ValueError, value_error_exception_handler)
app.add_exception_handler(KeyError, key_error_exception_handler)


@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    description="Lightweight endpoint to check service status.",
    status_code=status.HTTP_200_OK,
)
def health_check():
    """Health check endpoint returning a simple confirmation payload."""
    return {"message": "Healthy"}


# Include routers
app.include_router(games_router)
