import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("community.request")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Community platform backend: user authentication, conversation "
            "management and investor request management."
        ),
        openapi_tags=[
            {"name": "Auth", "description": "Registration, login and profile"},
            {"name": "Users", "description": "User administration"},
            {
                "name": "Conversations",
                "description": "Public listing of published conversations",
            },
            {
                "name": "Admin - Conversations",
                "description": "Create, edit, schedule, publish and cancel conversations",
            },
            {
                "name": "Investor Requests",
                "description": "Submit and track funding requests",
            },
            {
                "name": "Admin - Investor Requests",
                "description": "Review and update funding requests",
            },
        ],
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        # Never log request bodies, headers or query strings: they may carry
        # passwords, tokens or personal data.
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
