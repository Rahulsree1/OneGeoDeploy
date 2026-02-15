"""
Flask application entry point.
Run with: python app.py (so SocketIO uses eventlet for WebSocket support).
Serves the built frontend from backend when frontend/dist exists.
On Vercel (serverless), eventlet is skipped to avoid errors.
"""

import os

IS_VERCEL = bool(os.environ.get("VERCEL"))

# Only patch eventlet when NOT on Vercel
if not IS_VERCEL:
    import eventlet
    eventlet.monkey_patch()

from flask import Flask, send_from_directory
from flask_cors import CORS

from config.config import config
from config.db_config import DB_URL
from extensions import socketio
from models import db
from routes import api
from utils.error_handler import register_error_handlers

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    # VERY IMPORTANT: prevent connection exhaustion
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 1,
        "max_overflow": 0,
    }

    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:1729",
        "http://127.0.0.1:1729",
    ]

    CORS(app, origins=origins)

    db.init_app(app)
    socketio.init_app(app)

    # ❌ DO NOT run create_all on Vercel
    if not IS_VERCEL:
        with app.app_context():
            db.create_all()

    app.register_blueprint(api)
    register_error_handlers(app)

    # Serve frontend
    if os.path.isdir(FRONTEND_DIST):
        _dist_real = os.path.realpath(FRONTEND_DIST)

        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_spa(path):
            if path and not path.startswith("api/"):
                safe_path = path.replace("\\", "/").strip("/")
                if ".." in safe_path:
                    safe_path = ""
                if safe_path:
                    full = os.path.join(FRONTEND_DIST, safe_path)
                    if os.path.isfile(full):
                        canon = os.path.realpath(full)
                        if canon.lower().startswith(_dist_real.lower()):
                            return send_from_directory(FRONTEND_DIST, safe_path)

            return send_from_directory(FRONTEND_DIST, "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=1729,
        debug=config.DEBUG,
    )
