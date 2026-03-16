import requests
import threading
import time
import logging
from typing import Optional

class SBC:
    def __init__(self, ip, port=80, timeout=5, reconnect_interval=5, heartbeat_interval=10, name="NA", verbose=False) -> None:
        self.name = name
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.reconnect_interval = reconnect_interval
        self.heartbeat_interval = heartbeat_interval
        self.verbose = verbose

        self._connected = False
        self._stop_event = threading.Event()
        self._heartbeat_thread = None

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] (%(name)s) %(message)s"
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @property
    def _base_url(self) -> str:
        return f"http://{self.ip}:{self.port}"

    def _get(self, path: str) -> Optional[dict]:
        try:
            res = requests.get(self._base_url + path, timeout=self.timeout)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            self.logger.error(f"GET {path} failed: {e}")
            self._handle_disconnect()
            return None

    def _post(self, path: str, payload: dict) -> Optional[dict]:
        try:
            res = requests.post(
                self._base_url + path,
                json=payload,
                timeout=self.timeout
            )
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            self.logger.error(f"POST {path} failed: {e}")
            self._handle_disconnect()
            return None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def connect(self) -> None:
        """Ping the device until it responds, then start the heartbeat."""
        while not self._stop_event.is_set():
            self.logger.info(f"Attempting connection to {self.name}: {self.ip}:{self.port}")
            data = self._get("/ping")
            if data and data.get("type") == "pong":
                self._connected = True
                self.logger.info(f"Connection to {self.name} successful")
                self._start_heartbeat()
                return
            self.logger.info(f"Connection to {self.name} failed, retrying in {self.reconnect_interval}s")
            time.sleep(self.reconnect_interval)

    def disconnect(self) -> None:
        self._stop_event.set()
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_values(self, keyvals: dict) -> Optional[dict]:
        """POST /set  — e.g. set_values({'led0': 128, 'led1': 255})"""
        if not self._connected:
            self.logger.error("Unable to send — not connected")
            return None
        reply = self._post("/set", keyvals)
        if reply and not reply.get("success"):
            self.logger.error(f"set_values error: {reply.get('error')}")
        return reply

    def get_values(self, keys: list) -> Optional[dict]:
        """POST /get  — e.g. get_values(['led0', 'wiper0'])"""
        if not self._connected:
            self.logger.error("Unable to send — not connected")
            return None
        reply = self._post("/get", keys)
        if reply and not reply.get("success"):
            self.logger.error(f"get_values error: {reply.get('error')}")
        return reply

    def send_command(self, cmd: str, params: dict = None) -> Optional[dict]:
        """POST /cmd  — e.g. send_command('lightOn')"""
        if not self._connected:
            self.logger.error("Unable to send — not connected")
            return None
        body = {"cmd": cmd}
        if params:
            body["params"] = params
        reply = self._post("/cmd", body)
        if reply and not reply.get("success"):
            self.logger.error(f"send_command error: {reply.get('error')}")
        return reply

    def status(self) -> Optional[dict]:
        """GET /status  — returns ip, ssid, rssi"""
        return self._get("/status")

    # -------------------------------------------------------------------------
    # Heartbeat
    # -------------------------------------------------------------------------
    def _start_heartbeat(self) -> None:
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        while self._connected and not self._stop_event.is_set():
            time.sleep(self.heartbeat_interval)
            data = self._get("/ping")
            if not data or data.get("type") != "pong":
                self.logger.warning("Heartbeat failed")
                self._handle_disconnect()
                return

    def _handle_disconnect(self) -> None:
        if self._connected:
            self.logger.error("Disconnected — reconnecting...")
        self._connected = False
        if not self._stop_event.is_set():
            self.connect()


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    ip = input("SBC IP address: ").strip()
    sbc = SBC(ip, port=80, verbose=True)
    try:
        print("Connecting...")
        sbc.connect()
        print("Connected. Commands:")
        print("  set <key> <value>   — e.g.  set led0 128")
        print("  get <key>           — e.g.  get led0")
        print("  cmd <command>       — e.g.  cmd lightOn")
        print("  status")
        print("  quit")

        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                break

            if not line:
                continue

            parts = line.split()
            action = parts[0].lower()

            if action in ("quit", "exit"):
                break
            elif action == "set" and len(parts) == 3:
                key, val = parts[1], parts[2]
                # Try to convert to int, fall back to string
                try:
                    val = int(val)
                except ValueError:
                    pass
                print(sbc.set_values({key: val}))
            elif action == "get" and len(parts) == 2:
                print(sbc.get_values([parts[1]]))
            elif action == "cmd" and len(parts) >= 2:
                print(sbc.send_command(parts[1]))
            elif action == "status":
                print(sbc.status())
            else:
                print("Unknown command or wrong number of arguments")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        sbc.disconnect()
