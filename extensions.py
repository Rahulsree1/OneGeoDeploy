"""Shared Flask extensions (e.g. SocketIO) so controllers can emit without circular imports."""
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
