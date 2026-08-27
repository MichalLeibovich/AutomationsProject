"""Flask application factory.

A factory rather than a module-level application object: a test can build an
isolated instance with its own configuration, and nothing runs at import time.
"""

from __future__ import annotations

from typing import Final

from flask import Flask, Response, jsonify
from flask_cors import CORS

from api.middleware import register_middleware
from api.routes import ALL_BLUEPRINTS
from config.config import get_config
from config.logging_config import configure_logging
from database.connection import close_pool, init_pool
from utils.logger import get_logger

logger = get_logger(__name__)

API_PREFIX: Final = "/api"
"""Mount point for every resource blueprint."""

_DEFAULT_DEV_ORIGIN: Final = "http://localhost:5173"
"""Origin allowed when no explicit CORS origins are configured."""


def create_app() -> Flask:
    """Build and configure the application.

    Configures JSON output, CORS, middleware and blueprints, then opens the
    database pool eagerly so a bad DSN stops the process at boot rather than on
    the first request with a user waiting.

    Health probes stay at the root, where orchestrators expect them; everything
    else mounts under :data:`API_PREFIX`.

    Returns:
        The configured application.

    Raises:
        RuntimeError: If a mandatory configuration variable is unset.
        ServiceUnavailableError: If the database pool cannot be opened.
    """
    configure_logging()
    config = get_config()

    app = Flask(__name__)
    # Hebrew must reach the client as-is rather than as \\uXXXX escapes.
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False
    # Trailing-slash redirects break API clients that do not follow 308s.
    app.url_map.strict_slashes = False

    CORS(
        app,
        resources={r"/api/*": {"origins": config.cors_origins or [_DEFAULT_DEV_ORIGIN]}},
        expose_headers=["X-Correlation-Id"],
        allow_headers=["Content-Type", "X-Correlation-Id"],
    )

    register_middleware(app)

    for blueprint in ALL_BLUEPRINTS:
        if blueprint.name == "health":
            app.register_blueprint(blueprint)
        else:
            app.register_blueprint(blueprint, url_prefix=API_PREFIX)

    @app.get("/api")
    def api_root() -> Response:
        """Report the service identity and version.

        Returns:
            HTTP 200 with the service name, version and environment.
        """
        return jsonify(
            {
                "service": config.logging.service_name,
                "version": "2.0.0",
                "environment": config.env,
            }
        )

    init_pool()

    logger.info(
        "application ready",
        extra={"env": config.env, "prefix": API_PREFIX, "debug": config.debug},
    )
    return app


def main() -> None:
    """Run the development server.

    Production uses gunicorn against :mod:`wsgi` instead. The pool is closed on
    exit so PostgreSQL backends are released promptly.
    """
    config = get_config()
    app = create_app()

    try:
        app.run(host=config.host, port=config.port, debug=config.debug, threaded=True)
    finally:
        close_pool()


if __name__ == "__main__":
    main()
