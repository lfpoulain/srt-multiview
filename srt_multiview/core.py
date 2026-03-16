import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from screeninfo import get_monitors

from .paths import CONFIG_PATH, FFMPEG_PATH, FFPLAY_PATH


def _win_creationflags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _terminate_proc(proc: subprocess.Popen | None) -> None:
    if not proc or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()


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
    config.setdefault("displayNames", {})
    config.setdefault("routes", [])
    config["excludePrimaryDisplay"] = bool(config.get("excludePrimaryDisplay", True))
    config["autoStartReceiver"] = bool(config.get("autoStartReceiver", False))
    config["autoStartSender"] = bool(config.get("autoStartSender", False))

    display_names = config.get("displayNames") or {}
    if isinstance(display_names, dict):
        config["displayNames"] = {str(k): str(v) for k, v in display_names.items() if v is not None}
    else:
        config["displayNames"] = {}

    routes = config.get("routes") or []
    normalized_routes = []
    if isinstance(routes, list):
        for i, r in enumerate(routes):
            if not isinstance(r, dict):
                continue
            route = dict(r)
            route.setdefault("id", f"route-{i + 1}")
            route.setdefault("name", route["id"])
            route.setdefault("inputPort", 9001)
            route.setdefault("inputLatency", 120)
            route.setdefault("multicastAddr", "239.10.10.10")
            route.setdefault("multicastPort", 1234)
            route.setdefault("pktSize", 1316)
            route.setdefault("ttl", 1)

            route["id"] = str(route.get("id") or f"route-{i + 1}")
            route["name"] = str(route.get("name") or route["id"])
            try:
                route["inputPort"] = int(route.get("inputPort") or 9001)
            except (TypeError, ValueError):
                route["inputPort"] = 9001
            try:
                route["inputLatency"] = int(route.get("inputLatency") or 120)
            except (TypeError, ValueError):
                route["inputLatency"] = 120
            route["multicastAddr"] = str(route.get("multicastAddr") or "239.10.10.10").strip()
            try:
                route["multicastPort"] = int(route.get("multicastPort") or 1234)
            except (TypeError, ValueError):
                route["multicastPort"] = 1234
            try:
                route["pktSize"] = int(route.get("pktSize") or 1316)
            except (TypeError, ValueError):
                route["pktSize"] = 1316
            try:
                route["ttl"] = int(route.get("ttl") or 1)
            except (TypeError, ValueError):
                route["ttl"] = 1

            normalized_routes.append(route)

    config["routes"] = normalized_routes

    sender = dict(config.get("sender") or {})
    sender.setdefault("displayId", "")
    sender.setdefault("host", "127.0.0.1")
    sender.setdefault("port", 10000)
    sender.setdefault("latency", 120)
    sender.setdefault("fps", 30)
    sender.setdefault("bitrateK", 4000)
    sender.setdefault("includeSystemAudio", False)
    sender["displayId"] = str(sender.get("displayId") or "")
    sender["host"] = str(sender.get("host") or "127.0.0.1")
    sender["includeSystemAudio"] = bool(sender.get("includeSystemAudio", False))
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
        stream.setdefault("muteAudio", False)
        stream.setdefault("displayMode", "fit")
        stream.setdefault("rotate", 0)
        stream.setdefault("source", "srt")
        stream.setdefault("sourceRouteId", "")
        stream.setdefault("udpAddr", "")
        stream.setdefault("udpPort", 0)
        stream["id"] = str(stream.get("id") or f"stream-{i + 1}")
        stream["name"] = str(stream.get("name") or stream["id"])
        try:
            stream["port"] = int(stream.get("port") or (9000 + i + 1))
        except (TypeError, ValueError):
            stream["port"] = 9000 + i + 1
        try:
            stream["latency"] = int(stream.get("latency") or 120)
        except (TypeError, ValueError):
            stream["latency"] = 120
        stream["muteAudio"] = bool(stream.get("muteAudio", False))
        mode = str(stream.get("displayMode") or "fit").strip().lower()
        if mode not in {"fit", "fill", "stretch"}:
            mode = "fit"
        stream["displayMode"] = mode
        try:
            rotate = int(stream.get("rotate") or 0)
        except (TypeError, ValueError):
            rotate = 0
        if rotate not in {0, 90, 180, 270}:
            rotate = 0
        stream["rotate"] = rotate
        source = str(stream.get("source") or "srt").strip().lower()
        if source not in {"srt", "route", "udp"}:
            source = "srt"
        stream["source"] = source
        stream["sourceRouteId"] = str(stream.get("sourceRouteId") or "")
        stream["udpAddr"] = str(stream.get("udpAddr") or "").strip()
        try:
            stream["udpPort"] = int(stream.get("udpPort") or 0)
        except (TypeError, ValueError):
            stream["udpPort"] = 0
        normalized_streams.append(stream)

    config["streams"] = normalized_streams
    return config


def save_config(config: dict) -> None:
    config = normalize_config(config)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_displays(exclude_primary: bool = False, *, name_overrides: dict[str, str] | None = None) -> list[dict]:
    monitors = get_monitors()
    displays = []
    overrides = name_overrides or {}

    pending: list[tuple[str, int, object]] = []
    for i, m in enumerate(monitors):
        is_primary = bool(getattr(m, "is_primary", False))
        if exclude_primary and is_primary:
            continue

        name = getattr(m, "name", None)
        name_str = str(name).strip() if name is not None else ""
        base_id = name_str if name_str else f"geom-{m.x}-{m.y}-{m.width}x{m.height}"
        pending.append((base_id, i, m))

    counts: dict[str, int] = {}
    for base_id, _i, _m in pending:
        counts[base_id] = counts.get(base_id, 0) + 1

    occurrence: dict[str, int] = {}
    for base_id, i, m in pending:
        if counts.get(base_id, 0) > 1:
            idx = occurrence.get(base_id, 0) + 1
            occurrence[base_id] = idx
            display_id = f"{base_id}-{idx}"
        else:
            display_id = base_id

        display_name = base_id if not base_id.startswith("geom-") else f"Écran {i + 1}"
        if str(display_id) in overrides and overrides[str(display_id)]:
            display_name = str(overrides[str(display_id)])
        elif str(base_id) in overrides and overrides[str(base_id)]:
            display_name = str(overrides[str(base_id)])

        displays.append(
            {
                "id": display_id,
                "index": i,
                "name": display_name,
                "width": m.width,
                "height": m.height,
                "x": m.x,
                "y": m.y,
                "isPrimary": bool(getattr(m, "is_primary", False)),
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
        _terminate_proc(proc)
        self.players.pop(stream_id, None)

    def stop_all(self) -> None:
        for stream_id in list(self.players.keys()):
            self.stop_player(stream_id)

    def _input_url(self, stream: dict) -> tuple[str, str | None]:
        source = str(stream.get("source") or "srt").strip().lower()
        if source not in {"srt", "udp"}:
            source = "srt"

        if source == "udp":
            addr = str(stream.get("udpAddr") or "").strip()
            udp_port = int(stream.get("udpPort") or 0)
            if not addr or udp_port <= 0:
                return ("", "Source UDP invalide")
            return (f"udp://@{addr}:{udp_port}", None)

        latency_ms = int(stream.get("latency", 120))
        port = int(stream.get("port"))
        return (f"srt://0.0.0.0:{port}?mode=listener&latency={latency_ms * 1000}", None)

    def _vf(self, stream: dict, display: dict) -> str:
        display_w = int(display["width"])
        display_h = int(display["height"])
        mode = str(stream.get("displayMode") or "fit").strip().lower()
        if mode not in {"fit", "fill", "stretch"}:
            mode = "fit"

        try:
            rotate = int(stream.get("rotate") or 0)
        except Exception:
            rotate = 0
        if rotate not in {0, 90, 180, 270}:
            rotate = 0

        if mode == "stretch":
            vf = f"scale={display_w}:{display_h}"
        elif mode == "fill":
            vf = (
                f"scale={display_w}:{display_h}:force_original_aspect_ratio=increase,"
                f"crop={display_w}:{display_h}"
            )
        else:
            vf = (
                f"scale={display_w}:{display_h}:force_original_aspect_ratio=decrease,"
                f"pad={display_w}:{display_h}:(ow-iw)/2:(oh-ih)/2"
            )

        if rotate == 90:
            return f"transpose=1,{vf}"
        if rotate == 270:
            return f"transpose=2,{vf}"
        if rotate == 180:
            return f"transpose=1,transpose=1,{vf}"
        return vf

    def start_player(self, stream: dict, display: dict) -> PlayerLaunchResult:
        if not self.ffplay_path.exists():
            return PlayerLaunchResult(ok=False, reason=f"ffplay introuvable: {self.ffplay_path}")

        stream_id = str(stream.get("id"))
        self.stop_player(stream_id)

        input_url, input_err = self._input_url(stream)
        if input_err:
            return PlayerLaunchResult(ok=False, reason=input_err)

        vf = self._vf(stream, display)

        source = str(stream.get("source") or "srt").strip().lower()
        if source not in {"srt", "udp"}:
            source = "srt"

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
            "-vf",
            vf,
            "-fs",
        ]

        if source == "udp":
            args.extend([
                "-framedrop",
                "-sync",
                "ext",
            ])

        if bool(stream.get("muteAudio")):
            args.append("-an")

        args.extend([
            "-i",
            input_url,
        ])

        creationflags = _win_creationflags()

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
        status: dict[str, bool] = {}
        for stream_id, proc in list(self.players.items()):
            alive = proc.poll() is None
            status[stream_id] = alive
            if not alive:
                self.players.pop(stream_id, None)
        return status


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
        _terminate_proc(self.proc)
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
        include_system_audio: bool = False,
    ) -> SenderLaunchResult:
        if not self.ffmpeg_path.exists():
            self.last_error = f"ffmpeg introuvable: {self.ffmpeg_path}"
            return SenderLaunchResult(ok=False, reason=self.last_error)

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
        ]

        if include_system_audio:
            args.extend(
                [
                    "-f",
                    "wasapi",
                    "-i",
                    "default",
                ]
            )

        args.extend([
            "-vf",
            vf,
        ])

        if include_system_audio:
            args.extend(["-map", "0:v:0", "-map", "1:a:0"])
        else:
            args.append("-an")

        args.extend([
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
        ])

        if include_system_audio:
            args.extend(
                [
                    "-c:a",
                    "aac",
                    "-b:a",
                    "128k",
                    "-ac",
                    "2",
                    "-ar",
                    "48000",
                ]
            )

        args.extend([
            "-f",
            "mpegts",
            out_url,
        ])

        creationflags = _win_creationflags()

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


@dataclass
class RouteLaunchResult:
    ok: bool
    reason: str | None = None


class RouteManager:
    def __init__(self, ffmpeg_path: Path):
        self.ffmpeg_path = ffmpeg_path
        self.procs: dict[str, subprocess.Popen] = {}
        self.last_error: dict[str, str] = {}

    def stop_route(self, route_id: str) -> None:
        proc = self.procs.get(route_id)
        _terminate_proc(proc)
        self.procs.pop(route_id, None)

    def stop_all(self) -> None:
        for route_id in list(self.procs.keys()):
            self.stop_route(route_id)

    def status(self) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for route_id, proc in list(self.procs.items()):
            alive = proc.poll() is None
            status[route_id] = alive
            if not alive:
                self.procs.pop(route_id, None)
        return status

    def start_route(self, route: dict) -> RouteLaunchResult:
        if not self.ffmpeg_path.exists():
            return RouteLaunchResult(ok=False, reason=f"ffmpeg introuvable: {self.ffmpeg_path}")

        route_id = str(route.get("id") or "")
        if not route_id:
            return RouteLaunchResult(ok=False, reason="Route invalide")

        self.stop_route(route_id)

        in_port = int(route.get("inputPort") or 0)
        in_latency_ms = int(route.get("inputLatency") or 120)
        maddr = str(route.get("multicastAddr") or "").strip()
        mport = int(route.get("multicastPort") or 0)
        pkt_size = int(route.get("pktSize") or 1316)
        ttl = int(route.get("ttl") or 1)

        if in_port <= 0 or not maddr or mport <= 0:
            return RouteLaunchResult(ok=False, reason="Paramètres de route incomplets")

        in_url = f"srt://0.0.0.0:{in_port}?mode=listener&latency={max(0, in_latency_ms) * 1000}"
        out_url = f"udp://{maddr}:{mport}?pkt_size={pkt_size}&ttl={ttl}"

        args = [
            str(self.ffmpeg_path),
            "-hide_banner",
            "-loglevel",
            "warning",
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-i",
            in_url,
            "-c",
            "copy",
            "-flush_packets",
            "1",
            "-mpegts_flags",
            "+resend_headers",
            "-f",
            "mpegts",
            out_url,
        ]

        creationflags = _win_creationflags()

        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self.procs[route_id] = proc
            self.last_error.pop(route_id, None)
            return RouteLaunchResult(ok=True)
        except Exception as e:
            self.last_error[route_id] = str(e)
            return RouteLaunchResult(ok=False, reason=str(e))


route_manager = RouteManager(FFMPEG_PATH)


def apply_mapping(config: dict) -> dict[str, PlayerLaunchResult]:
    config = normalize_config(config)

    results: dict[str, PlayerLaunchResult] = {}
    displays = get_displays(exclude_primary=False, name_overrides=config.get("displayNames") or {})
    display_map = {str(d["id"]): d for d in displays}

    routes = {str(r.get("id")): r for r in (config.get("routes") or []) if isinstance(r, dict)}
    route_status = route_manager.status()

    for stream in config["streams"]:
        stream_id = str(stream["id"])
        display_id = config.get("mapping", {}).get(stream_id)

        if not display_id or str(display_id) not in display_map:
            player_manager.stop_player(stream_id)
            results[stream_id] = PlayerLaunchResult(ok=False, reason="Aucun écran assigné")
            continue

        display = display_map[str(display_id)]

        source = str(stream.get("source") or "srt").strip().lower()
        if source == "route":
            route_id = str(stream.get("sourceRouteId") or "")
            route = routes.get(route_id)
            if not route_id or not route:
                player_manager.stop_player(stream_id)
                results[stream_id] = PlayerLaunchResult(ok=False, reason="Route introuvable")
                continue
            if not route_status.get(route_id, False):
                player_manager.stop_player(stream_id)
                results[stream_id] = PlayerLaunchResult(ok=False, reason=f"Route arrêtée: {route.get('name', route_id)}")
                continue

            stream_copy = dict(stream)
            stream_copy["source"] = "udp"
            stream_copy["udpAddr"] = str(route.get("multicastAddr") or "").strip()
            stream_copy["udpPort"] = int(route.get("multicastPort") or 0)
            results[stream_id] = player_manager.start_player(stream_copy, display)
        else:
            results[stream_id] = player_manager.start_player(stream, display)

    return results
