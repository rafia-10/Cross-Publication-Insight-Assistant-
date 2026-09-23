from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import router
from app.database.postgres import init_db
from app.core.logging import configure_logging, get_logger
from app.core.middleware import CorrelationIdMiddleware
from app.core.exceptions import InsightAssistantError

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up — initialising database")
    init_db()
    logger.info("Application ready")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title="Cross-Publication Insight Assistant",
    description="Multi-agent AI system for analyzing GitHub repos and publications",
    version="0.1.0",
    lifespan=lifespan,
)

# ---- Middleware (order matters: outermost = first to run) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationIdMiddleware)


# ---- Global exception handlers ----

@app.exception_handler(InsightAssistantError)
async def insight_error_handler(request: Request, exc: InsightAssistantError) -> JSONResponse:
    """Convert typed application errors into structured JSON responses."""
    logger.error(
        "Application error",
        extra={
            "error_type": type(exc).__name__,
            "error": exc.message,
            "context": exc.context,
            "path": request.url.path,
        },
        exc_info=exc.cause,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": type(exc).__name__,
            "message": exc.message,
        },
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for any unhandled exception — prevents stack traces leaking to clients."""
    logger.exception(
        "Unhandled exception",
        extra={"path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred.",
        },
    )


app.include_router(router)

