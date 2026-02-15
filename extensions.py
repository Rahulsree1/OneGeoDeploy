"""
Shared Flask extensions (e.g. SocketIO) so controllers can emit without circular imports.
"""

import os
from flask_socketio import SocketIO

IS_VERCEL = bool(os.environ.get("VERCEL"))

# On Vercel → use threading (serverless safe)
# Elsewhere → use eventlet (real WebSocket support)
async_mode = "threading" if IS_VERCEL else "eventlet"

socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode=async_mode,
    logger=not IS_VERCEL,
    engineio_logger=not IS_VERCEL,
    ping_timeout=60,
    ping_interval=25,
)
