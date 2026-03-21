import os
import platform

import structlog

from app.containers.enums import Environment
from app.logger import setup_logging
from app.settings import Settings

logger = structlog.get_logger(__name__)


def build_startup_config(settings: Settings) -> dict:
    return {
        "env": settings.app.env,
        "log_level": settings.app.log_level,
        "version": settings.app.version,
        "name": settings.app.name,
        "python_version": platform.python_version(),
        "process_id": os.getpid(),
        "database": {
            "host": settings.db.host,
            "port": settings.db.port,
            "name": settings.db.name,
            "pool_size": settings.db.connection_pool_size,
            "max_overflow": settings.db.connection_max_overflow,
            "driver": "asyncpg",
        },
        "redis": {
            "host": settings.redis.host,
            "port": settings.redis.port,
        },
        "security": {
            "jwt_algorithm": settings.token.jwt_algorithm,
            "bcrypt_cost": settings.app.bcrypt_cost,
        },
        "token_ttl_seconds": {
            "access": int(settings.token.access_ttl.total_seconds()),
            "refresh": int(settings.token.refresh_ttl.total_seconds()),
            "reset": int(settings.token.reset_ttl.total_seconds()),
            "mfa_setup": int(settings.token.mfa_setup_ttl.total_seconds()),
            "mfa_challenge": int(settings.token.mfa_challenge_ttl.total_seconds()),
        },
    }


def log_startup_config(settings: Settings):
    startup_config = build_startup_config(settings)
    logger.info(
        "Application startup config",
        **startup_config,
    )


def bootstrap_app(settings: Settings):
    setup_logging(
        log_level=settings.app.log_level,
        is_json_logging=settings.app.env == Environment.PROD,
    )
    log_startup_config(settings)

    logger.info("Bootstrap completed", env=settings.app.env)
