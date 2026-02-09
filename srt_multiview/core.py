import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from screeninfo import get_monitors

from .paths import CONFIG_PATH, FFMPEG_PATH, FFPLAY_PATH


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        config = {
            "streams": [
                {"id": "stream-1", "name": "Flux 1", "port": 9001, "latency": 120},
                {"id": "stream-2", "name": "Flux 2", "port": 9002, "latency": 120},
                {"id": "stream-3", "name": "Flux 3", "port": 9003, "latency": 120},
            ],
            "mapping": {},
            "excludePrimaryDisplay": True,
        }
        return normalize_config(config)

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return normalize_config(config)
    except (json.JSONDecodeError, ValueError):
        return normalize_config(
            {
                "streams": [
                    {"id": "stream-1", "name": "Flux 1", "port": 9001, "latency": 120},
                ],
                "mapping": {},
                "excludePrimaryDisplay": True,
            }
        )


def normalize_config(config: dict) -> dict:
    config = dict(config or {})

    config.setdefault("streams", [])
    config.setdefault("mapping", {})
    config["excludePrimaryDisplay"] = bool(config.get("excludePrimaryDisplay", True))

    sender = dict(config.get("sender") or {})
    sender.setdefault("displayId", "")
    sender.setdefault("host", "127.0.0.1")
    sender.setdefault("port", 10000)
    sender.setdefault("latency", 120)
    sender.setdefault("fps", 30)
    sender.setdefault("bitrateK", 4000)
    sender["displayId"] = str(sender.get("displayId") or "")
    sender["host"] = str(sender.get("host") or "127.0.0.1")
    try:
        sender["port"] = int(sender.get("port") or 10000)
    except (TypeError, ValueError):
        sender["port"] = 10000
    try:
        sender["latency"] = int(sender.get("latency") or 120)
    except (TypeError, ValueError):
        sender["latency"] = 120
    try:
        sender["fps"] = int(sender.get("fps") or 30)
    except (TypeError, ValueError):
        sender["fps"] = 30
    try:
        sender["bitrateK"] = int(sender.get("bitrateK") or 4000)
    except (TypeError, ValueError):
        sender["bitrateK"] = 4000
    config["sender"] = sender

    mapping = config.get("mapping") or {}
    config["mapping"] = {str(k): str(v) for k, v in mapping.items() if v is not None}

    streams = config.get("streams") or []
    normalized_streams = []
    for i, s in enumerate(streams):
        if not isinstance(s, dict):
            continue
        stream = dict(s)
        stream.setdefault("id", f"stream-{i + 1}")
        stream.setdefault("name", stream["id"])
        stream.setdefault("port", 9000 + i + 1)
        stream.setdefault("latency", 120)
        normalized_streams.append(stream)

    config["streams"] = normalized_streams
    return config


def save_config(config: dict) -> None:
    config = normalize_config(config)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_displays(exclude_primary: bool = False) -> list[dict]:
    monitors = get_monitors()
    displays = []
    for i, m in enumerate(monitors):
        is_primary = bool(getattr(m, "is_primary", False))
        if exclude_primary and is_primary:
            continue

        name = getattr(m, "name", None)
        displays.append(
            {
                "id": str(name) if name is not None else f"monitor-{i}",
                "index": i,
                "name": str(name) if name else f"Écran {i + 1}",
                "width": m.width,
                "height": m.height,
                "x": m.x,
                "y": m.y,
                "isPrimary": is_primary,
            }
        )
    return displays


@dataclass
class PlayerLaunchResult:
    ok: bool
    reason: str | None = None


class PlayerManager:
    def __init__(self, ffplay_path: Path):
        self.ffplay_path = ffplay_path
        self.players: dict[str, subprocess.Popen] = {}

    def stop_player(self, stream_id: str) -> None:
        proc = self.players.get(stream_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.players.pop(stream_id, None)

    def stop_all(self) -> None:
        for stream_id in list(self.players.keys()):
            self.stop_player(stream_id)

    def start_player(self, stream: dict, display: dict) -> PlayerLaunchResult:
        if not self.ffplay_path.exists():
            return PlayerLaunchResult(ok=False, reason=f"ffplay introuvable: {self.ffplay_path}")

        stream_id = str(stream.get("id"))
        self.stop_player(stream_id)

        latency_ms = int(stream.get("latency", 120))
        port = int(stream.get("port"))
        srt_url = f"srt://0.0.0.0:{port}?mode=listener&latency={latency_ms * 1000}"

        args = [
            str(self.ffplay_path),
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "32",
            "-analyzeduration",
            "0",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-left",
            str(display["x"]),
            "-top",
            str(display["y"]),
            "-x",
            str(display["width"]),
            "-y",
            str(display["height"]),
            "-fs",
            "-i",
            srt_url,
        ]

        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self.players[stream_id] = proc
            return PlayerLaunchResult(ok=True)
        except Exception as e:
            return PlayerLaunchResult(ok=False, reason=str(e))

    def status(self) -> dict[str, bool]:
        return {stream_id: (proc.poll() is None) for stream_id, proc in self.players.items()}


player_manager = PlayerManager(FFPLAY_PATH)


@dataclass
class SenderLaunchResult:
    ok: bool
    reason: str | None = None


class SenderManager:
    def __init__(self, ffmpeg_path: Path):
        self.ffmpeg_path = ffmpeg_path
        self.proc: subprocess.Popen | None = None
        self.last_error: str | None = None

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def status(self) -> bool:
        return bool(self.proc and self.proc.poll() is None)

    def _virtual_desktop_origin(self, displays: list[dict]) -> tuple[int, int]:
        if not displays:
            return (0, 0)
        min_x = min(int(d.get("x", 0)) for d in displays)
        min_y = min(int(d.get("y", 0)) for d in displays)
        return (min_x, min_y)

    def start(
        self,
        display: dict,
        host: str,
        port: int,
        *,
        latency_ms: int = 120,
        fps: int = 30,
        bitrate_k: int = 4000,
    ) -> SenderLaunchResult:
        if not self.ffmpeg_path.exists():
            return SenderLaunchResult(ok=False, reason=f"ffmpeg introuvable: {self.ffmpeg_path}")

        self.stop()

        displays = get_displays(exclude_primary=False)
        origin_x, origin_y = self._virtual_desktop_origin(displays)
        crop_x = int(display["x"]) - origin_x
        crop_y = int(display["y"]) - origin_y
        width = int(display["width"])
        height = int(display["height"])

        latency_us = max(0, int(latency_ms)) * 1000
        fps = max(1, int(fps))
        bitrate_k = max(100, int(bitrate_k))
        host = (host or "127.0.0.1").strip()
        port = int(port)

        vf = f"crop={width}:{height}:{crop_x}:{crop_y}"
        out_url = (
            f"srt://{host}:{port}?mode=caller&latency={latency_us}"
            f"&transtype=live&pkt_size=1316"
        )

        args = [
            str(self.ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "warning",
            "-f",
            "gdigrab",
            "-framerate",
            str(fps),
            "-draw_mouse",
            "1",
            "-i",
            "desktop",
            "-vf",
            vf,
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-g",
            str(fps * 2),
            "-keyint_min",
            str(fps * 2),
            "-b:v",
            f"{bitrate_k}k",
            "-maxrate",
            f"{bitrate_k}k",
            "-bufsize",
            f"{bitrate_k * 2}k",
            "-f",
            "mpegts",
            out_url,
        ]

        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            self.proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self.last_error = None
            return SenderLaunchResult(ok=True)
        except Exception as e:
            self.proc = None
            self.last_error = str(e)
            return SenderLaunchResult(ok=False, reason=str(e))


sender_manager = SenderManager(FFMPEG_PATH)


def apply_mapping(config: dict) -> dict[str, bool]:
    config = normalize_config(config)

    results: dict[str, bool] = {}
    displays = get_displays(exclude_primary=False)
    display_map = {str(d["id"]): d for d in displays}

    for stream in config["streams"]:
        stream_id = str(stream["id"])
        display_id = config.get("mapping", {}).get(stream_id)

        if not display_id or str(display_id) not in display_map:
            player_manager.stop_player(stream_id)
            results[stream_id] = False
            continue

        display = display_map[str(display_id)]
        results[stream_id] = player_manager.start_player(stream, display).ok

    return results
