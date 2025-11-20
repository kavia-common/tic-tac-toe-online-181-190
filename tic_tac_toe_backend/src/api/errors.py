from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette import status


# PUBLIC_INTERFACE
def not_found(detail: str = "Resource not found") -> HTTPException:
    """Return an HTTPException for 404 Not Found."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# PUBLIC_INTERFACE
def bad_request(detail: str = "Bad request") -> HTTPException:
    """Return an HTTPException for 400 Bad Request."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# PUBLIC_INTERFACE
def conflict(detail: str = "Conflict") -> HTTPException:
    """Return an HTTPException for 409 Conflict."""
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


# PUBLIC_INTERFACE
async def value_error_exception_handler(_: Request, exc: ValueError) -> JSONResponse:
    """FastAPI exception handler to map ValueError to HTTP 400 response."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc) or "Invalid value"},
    )


# PUBLIC_INTERFACE
async def key_error_exception_handler(_: Request, exc: KeyError) -> JSONResponse:
    """FastAPI exception handler to map KeyError to HTTP 404 response."""
    msg = str(exc).strip("'") if str(exc) else "Not found"
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": msg},
    )
