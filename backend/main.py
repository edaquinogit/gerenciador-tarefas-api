from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, notificacoes, ordens, painel, sessoes, tarefas, usuarios
from backend.core.config import Settings, get_settings
from backend.database.connection import build_engine


def create_app(settings: Settings | None = None, engine=None) -> FastAPI:
    settings = settings or get_settings()
    owned_engine = engine is None
    engine = engine if engine is not None else build_engine(settings.DATABASE_URL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if owned_engine:
            engine.dispose()

    app = FastAPI(title=settings.PROJECT_NAME, version="2.7.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    if settings.CORS_ORIGINS or settings.BROWSER_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(set(settings.CORS_ORIGINS + settings.BROWSER_ORIGINS)),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
            allow_headers=["Authorization", "Content-Type", "X-Session-Request"],
        )
    app.include_router(auth.router)
    app.include_router(sessoes.router)
    app.include_router(usuarios.router)
    app.include_router(tarefas.router)
    app.include_router(ordens.router)
    app.include_router(notificacoes.router)
    app.include_router(painel.router)

    @app.get("/health", tags=["Sistema"])
    def health():
        return {"status": "ok"}

    return app
