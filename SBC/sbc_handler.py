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
        # _connected/explicit connect/disconnect are no longer required;
        # we use HTTP requests on demand and run a lightweight ping loop.
        self._last_ping_ok = False
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
            # mark last ping as failed; heartbeat loop will report
            self._last_ping_ok = False
            return {"success": False, "error": str(e)}

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
            # mark last ping as failed; heartbeat loop will report
            self._last_ping_ok = False
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Device key/command mapping helpers
    # -------------------------------------------------------------------------
    def _set_key_for(self, key: str) -> str:
        """Return the key name expected by device for POST /set.
        Accepts either 'light.1' / 'light.2' / 'light.3' or 'led0' / 'led1' / 'led2',
        and converts to the device's set-key format (ledN or wiper0).
        """
        if key.startswith("light."):
            # light.1 -> led0, light.2 -> led1, light.3 -> led2
            try:
                idx = int(key.split('.', 1)[1]) - 1
                return f"led{idx}"
            except Exception:
                return key
        if key == "wiper":
            return "wiper0"
        return key

    def _get_key_for(self, key: str) -> str:
        """Return the key name expected by device for POST /get.
        Accepts either 'led0' / 'led1' / 'led2' or 'light.1' etc and returns
        the get-key format (light.N or wiper).
        """
        if key.startswith("led"):
            try:
                idx = int(key[3:])
                return f"light.{idx+1}"
            except Exception:
                return key
        if key.startswith("wiper"):
            return "wiper"
        return key

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------
    def start_heartbeat(self) -> None:
        """Start a background thread that periodically GETs /ping.

        This replaces persistent connection/reconnect logic — we just
        poll the device and update `self._last_ping_ok`.
        """
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def disconnect(self) -> None:
        # Stop the heartbeat loop (keeps interface name for compatibility)
        self._stop_event.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1)
        self._last_ping_ok = False

    def is_connected(self) -> bool:
        return self._last_ping_ok

    def set_values(self, keyvals: dict) -> Optional[dict]:
        """POST /set — accepts keys like 'light.1' or 'led0'; converts to device format."""
        # No persistent connection required; try sending regardless
        payload = {}
        for k, v in keyvals.items():
            payload[self._set_key_for(k)] = v

        reply = self._post("/set", payload)
        if reply and not reply.get("success"):
            self.logger.error(f"set_values error: {reply.get('error')}")
        return reply

    def get_values(self, keys: list) -> Optional[dict]:
        """POST /get — accepts keys like 'led0' or 'light.1' and returns normalized data.

        Returns: {'success': True, 'data': {<requested_key>: value, ...}}
        """
        # No persistent connection required; try sending regardless

        # Map requested keys to device get-keys
        requested = list(keys)
        device_keys = [self._get_key_for(k) for k in requested]

        reply = self._post("/get", device_keys)
        if not reply:
            return None
        if not reply.get("success"):
            self.logger.error(f"get_values error: {reply.get('error')}")
            return reply

        data = reply.get("data", {})
        # Map device-returned keys back to the caller's requested keys
        mapped = {}
        for orig, dk in zip(requested, device_keys):
            if dk in data:
                mapped[orig] = data[dk]
            else:
                mapped[orig] = None

        return {"success": True, "data": mapped}

    def send_command(self, cmd: str, params: dict = None) -> Optional[dict]:
        """POST /cmd  — e.g. send_command('lightOn')"""
        # No persistent connection required; try sending regardless
        body = {"cmd": cmd}
        if params:
            body["params"] = params

        # Basic validation for known commands
        if cmd == "setAll":
            if not params or "value" not in params:
                self.logger.error("send_command error: setAll requires params {'value': <0-255>}" )
                return {"success": False, "error": "missing params: value"}

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
        # kept for compatibility; start via `start_heartbeat()` instead
        self.start_heartbeat()

    def _heartbeat_loop(self) -> None:
        while not self._stop_event.is_set():
            data = self._get("/ping")
            if data and data.get("type") == "pong":
                if not self._last_ping_ok:
                    self.logger.info("Ping successful")
                self._last_ping_ok = True
            else:
                if self._last_ping_ok:
                    self.logger.warning("Ping failed")
                self._last_ping_ok = False
            time.sleep(self.heartbeat_interval)

    def _handle_disconnect(self) -> None:
        # kept for compatibility with older callers; simply mark as not ok
        if self._last_ping_ok:
            self.logger.error("Disconnected")
        self._last_ping_ok = False


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    ip = input("SBC IP address: ").strip()
    sbc = SBC(ip, port=80, verbose=True)
    try:
        print("Starting heartbeat...")
        #sbc.start_heartbeat()
        print("Ready. Commands:")
        print("  set <key> <value>   — e.g.  set light.1 128  (or set led0 128)")
        print("  get <key>           — e.g.  get light.1  (or get led0)")
        print("  cmd <command> [arg] — e.g.  cmd lightOn  OR  cmd setAll 200")
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
                cmd_name = parts[1]
                # support: cmd setAll 200
                if cmd_name == "setAll" and len(parts) >= 3:
                    try:
                        v = int(parts[2])
                    except ValueError:
                        print("Invalid value for setAll; must be integer 0-255")
                        continue
                    print(sbc.send_command(cmd_name, {"value": v}))
                else:
                    print(sbc.send_command(cmd_name))
            elif action == "status":
                print(sbc.status())
            else:
                print("Unknown command or wrong number of arguments")

    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        sbc.disconnect()
