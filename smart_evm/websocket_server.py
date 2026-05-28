"""
websocket_server.py — Async WebSocket server.

The ESP8266 connects to this server and sends JSON vote / error packets.
All vote logic lives here on the PC side; we simply trust the ESP's packets.
"""

import asyncio
import json
import threading
from typing import Optional

import websockets
from PyQt6.QtCore import QObject, pyqtSignal

from config import WS_HOST, WS_PORT
from logger import get_logger

log = get_logger("smart_evm.ws")


class WebSocketServer(QObject):
    """
    Runs an asyncio WebSocket server on a background thread.
    Emits Qt signals so the UI can react without threading complexity.
    """

    vote_received   = pyqtSignal(int)          # candidate_id
    error_received  = pyqtSignal(str)          # reason string
    client_connected    = pyqtSignal(str)      # remote address
    client_disconnected = pyqtSignal(str)      # remote address
    server_started  = pyqtSignal(int)          # port number
    server_stopped  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ws-server")
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    # ------------------------------------------------------------------ #
    #  Internal                                                            #
    # ------------------------------------------------------------------ #

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as exc:
            log.error("WebSocket server error: %s", exc)
        finally:
            self._loop.close()
            self.server_stopped.emit()

    async def _serve(self) -> None:
        log.info("Starting WebSocket server on %s:%s", WS_HOST, WS_PORT)
        async with websockets.serve(self._handler, WS_HOST, WS_PORT):
            self.server_started.emit(WS_PORT)
            await asyncio.Future()   # run forever

    async def _handler(self, websocket) -> None:
        addr = websocket.remote_address
        remote = f"{addr[0]}:{addr[1]}" if addr else "unknown"
        log.info("ESP connected from %s", remote)
        self.client_connected.emit(remote)
        try:
            async for raw in websocket:
                self._process(raw)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            log.info("ESP disconnected: %s", remote)
            self.client_disconnected.emit(remote)

    def _process(self, raw: str) -> None:
        try:
            pkt = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Malformed packet: %s", raw)
            return

        pkt_type = pkt.get("type")

        if pkt_type == "vote":
            cid = pkt.get("candidate_id")
            if isinstance(cid, int) and 1 <= cid <= 5:
                log.info("Vote received → candidate %d", cid)
                self.vote_received.emit(cid)
            else:
                log.warning("Invalid candidate_id in vote packet: %s", pkt)

        elif pkt_type == "error":
            reason = pkt.get("reason", "unknown")
            log.warning("ESP error → %s", reason)
            self.error_received.emit(reason)

        else:
            log.warning("Unknown packet type: %s", pkt_type)
