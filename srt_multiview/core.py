import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
from collections import deque
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path

from screeninfo import get_monitors

from .paths import CONFIG_PATH, FFMPEG_PATH, FFPLAY_PATH


VALID_STREAM_SOURCES = {"srt", "route", "omt", "udp"}
VALID_RECEIVER_DECODES = {"cpu", "auto", "dxva2", "h264_amf", "h264_cuvid", "h264_qsv"}
VALID_OMT_PIXEL_FORMATS = ("uyvy422", "bgra", "yuv422p10le")


DISPLAY_ID_SCHEMA_VERSION = 2
CCHDEVICENAME = 32
CCHFORMNAME = 32
ENUM_CURRENT_SETTINGS = 0xFFFFFFFF
DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
DISPLAY_DEVICE_PRIMARY_DEVICE = 0x00000004
DISPLAY_DEVICE_MIRRORING_DRIVER = 0x00000008


class POINTL(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class _DEVMODE_DISPLAY(ctypes.Structure):
    _fields_ = [
        ("dmPosition", POINTL),
        ("dmDisplayOrientation", wintypes.DWORD),
        ("dmDisplayFixedOutput", wintypes.DWORD),
    ]


class _DEVMODE_UNION_1(ctypes.Union):
    _fields_ = [
        ("dmOrientation", wintypes.SHORT),
        ("_display", _DEVMODE_DISPLAY),
    ]


class _DEVMODE_UNION_2(ctypes.Union):
    _fields_ = [
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmNup", wintypes.DWORD),
    ]


class DEVMODEW(ctypes.Structure):
    _anonymous_ = ("u1", "u2")
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * CCHDEVICENAME),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("u1", _DEVMODE_UNION_1),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * CCHFORMNAME),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("u2", _DEVMODE_UNION_2),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


def _win_creationflags() -> int:
    if sys.platform != "win32":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _terminate_proc(proc: subprocess.Popen | None) -> None:
    if not proc or proc.poll() is not None:
        return

    if sys.platform == "win32":
        try:
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(proc.pid),
                    "/T",
                    "/F",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_win_creationflags(),
                check=False,
            )
        except Exception:
            pass

    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass


def _config_display_schema_version(config: dict | None) -> int:
    try:
        return int((config or {}).get("displayIdSchemaVersion") or 0)
    except (TypeError, ValueError):
        return 0


def _clean_win_text(value) -> str:
    return str(value or "").split("\x00", 1)[0].strip()


def _stable_display_id(identity: str) -> str:
    raw = str(identity or "").strip()
    if not raw:
        raw = "unknown"
    digest = hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:20]
    return f"disp-{digest}"


def _sort_displays(displays: list[dict]) -> list[dict]:
    ordered = sorted(
        displays,
        key=lambda d: (
            int(d.get("y") or 0),
            int(d.get("x") or 0),
            0 if d.get("isPrimary") else 1,
            str(d.get("id") or ""),
        ),
    )
    for i, display in enumerate(ordered):
        display["index"] = i
    return ordered


def _get_displays_windows(exclude_primary: bool = False, *, name_overrides: dict[str, str] | None = None) -> list[dict]:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    enum_display_devices = user32.EnumDisplayDevicesW
    enum_display_devices.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DISPLAY_DEVICEW), wintypes.DWORD]
    enum_display_devices.restype = wintypes.BOOL

    enum_display_settings = user32.EnumDisplaySettingsExW
    enum_display_settings.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODEW), wintypes.DWORD]
    enum_display_settings.restype = wintypes.BOOL

    overrides = name_overrides or {}
    displays: list[dict] = []
    adapter_index = 0
    while True:
        adapter = DISPLAY_DEVICEW()
        adapter.cb = ctypes.sizeof(DISPLAY_DEVICEW)
        if not enum_display_devices(None, adapter_index, ctypes.byref(adapter), 0):
            break
        adapter_index += 1

        state_flags = int(adapter.StateFlags or 0)
        if not (state_flags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP):
            continue
        if state_flags & DISPLAY_DEVICE_MIRRORING_DRIVER:
            continue

        devmode = DEVMODEW()
        devmode.dmSize = ctypes.sizeof(DEVMODEW)
        adapter_device_name = _clean_win_text(adapter.DeviceName)
        if not adapter_device_name:
            continue
        if not enum_display_settings(adapter_device_name, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode), 0):
            continue

        is_primary = bool(state_flags & DISPLAY_DEVICE_PRIMARY_DEVICE)
        if exclude_primary and is_primary:
            continue

        adapter_label = _clean_win_text(adapter.DeviceString)
        adapter_device_id = _clean_win_text(adapter.DeviceID)
        adapter_device_key = _clean_win_text(adapter.DeviceKey)

        monitor_label = ""
        monitor_device_id = ""
        monitor_device_key = ""
        monitor_index = 0
        while True:
            monitor = DISPLAY_DEVICEW()
            monitor.cb = ctypes.sizeof(DISPLAY_DEVICEW)
            if not enum_display_devices(adapter_device_name, monitor_index, ctypes.byref(monitor), 0):
                break
            monitor_index += 1

            current_label = _clean_win_text(monitor.DeviceString)
            current_device_id = _clean_win_text(monitor.DeviceID)
            current_device_key = _clean_win_text(monitor.DeviceKey)
            if current_label and not monitor_label:
                monitor_label = current_label
            if current_device_id or current_device_key:
                monitor_device_id = current_device_id
                monitor_device_key = current_device_key
                if current_label:
                    monitor_label = current_label
                break

        identity_parts = [monitor_device_id, monitor_device_key, adapter_device_id, adapter_device_key]
        identity = "|".join(part for part in identity_parts if part)
        position = devmode._display.dmPosition

        if not identity:
            identity = (
                f"geom|{int(position.x)}|{int(position.y)}|"
                f"{int(devmode.dmPelsWidth)}|{int(devmode.dmPelsHeight)}|{1 if is_primary else 0}"
            )

        display_id = _stable_display_id(identity)
        display_name = monitor_label or adapter_label or adapter_device_name or f"Écran {len(displays) + 1}"
        if overrides.get(display_id):
            display_name = str(overrides[display_id])

        displays.append(
            {
                "id": display_id,
                "index": len(displays),
                "name": display_name,
                "width": int(devmode.dmPelsWidth),
                "height": int(devmode.dmPelsHeight),
                "x": int(position.x),
                "y": int(position.y),
                "isPrimary": is_primary,
                "identity": identity,
                "deviceName": adapter_device_name,
            }
        )

    return _sort_displays(displays)


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
            loaded = json.load(f)
        schema_before = _config_display_schema_version(loaded)
        config = normalize_config(loaded)
        if schema_before != DISPLAY_ID_SCHEMA_VERSION:
            save_config(config)
        return config
    except (json.JSONDecodeError, ValueError, OSError):
        try:
            backup = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".bak")
            CONFIG_PATH.replace(backup)
        except OSError:
            pass
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
    reset_display_bindings = _config_display_schema_version(config) != DISPLAY_ID_SCHEMA_VERSION
    config["displayIdSchemaVersion"] = DISPLAY_ID_SCHEMA_VERSION

    config.setdefault("streams", [])
    config.setdefault("mapping", {})
    config.setdefault("displayNames", {})
    config.setdefault("routes", [])
    config.setdefault("receiver", {})
    config["excludePrimaryDisplay"] = bool(config.get("excludePrimaryDisplay", True))
    config["autoStartReceiver"] = bool(config.get("autoStartReceiver", False))
    config["autoStartSender"] = bool(config.get("autoStartSender", False))

    display_names = config.get("displayNames") or {}
    if reset_display_bindings:
        config["displayNames"] = {}
    elif isinstance(display_names, dict):
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
    sender["displayId"] = "" if reset_display_bindings else str(sender.get("displayId") or "")
    sender["name"] = str(sender.get("name") or "SRT Multiview").strip() or "SRT Multiview"
    try:
        fps = int(sender.get("fps") or 30)
    except (TypeError, ValueError):
        fps = 30
    sender["fps"] = max(1, min(60, fps))
    pf = str(sender.get("pixelFormat") or "uyvy422").strip().lower()
    if pf not in VALID_OMT_PIXEL_FORMATS:
        pf = "uyvy422"
    sender["pixelFormat"] = pf
    sender["clockOutput"] = bool(sender.get("clockOutput", False))
    try:
        sender["referenceLevel"] = float(sender.get("referenceLevel", 1.0))
    except (TypeError, ValueError):
        sender["referenceLevel"] = 1.0
    # Drop legacy SRT-sender fields and the in-development audio fields.
    for legacy in (
        "host", "port", "latency", "bitrateK", "encoder", "includeSystemAudio",
        "noAudio", "audioDevice", "audioSampleRate", "audioChannels",
    ):
        sender.pop(legacy, None)
    config["sender"] = sender

    receiver = dict(config.get("receiver") or {})
    receiver.setdefault("decode", "cpu")
    decode = str(receiver.get("decode") or "cpu").strip().lower()
    if decode == "gpu":
        decode = "auto"
    if decode not in VALID_RECEIVER_DECODES:
        decode = "cpu"
    receiver["decode"] = decode
    config["receiver"] = receiver

    mapping = {} if reset_display_bindings else (config.get("mapping") or {})
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
        stream.setdefault("omtSource", "")
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
        if source not in VALID_STREAM_SOURCES:
            source = "srt"
        stream["source"] = source
        stream["sourceRouteId"] = str(stream.get("sourceRouteId") or "")
        stream["udpAddr"] = str(stream.get("udpAddr") or "").strip()
        try:
            stream["udpPort"] = int(stream.get("udpPort") or 0)
        except (TypeError, ValueError):
            stream["udpPort"] = 0
        stream["omtSource"] = str(stream.get("omtSource") or "").strip()
        normalized_streams.append(stream)

    config["streams"] = normalized_streams
    return config


def save_config(config: dict) -> None:
    config = normalize_config(config)
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = CONFIG_PATH.with_suffix(CONFIG_PATH.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp_path, CONFIG_PATH)


def get_displays(exclude_primary: bool = False, *, name_overrides: dict[str, str] | None = None) -> list[dict]:
    if sys.platform == "win32":
        try:
            return _get_displays_windows(exclude_primary=exclude_primary, name_overrides=name_overrides)
        except Exception:
            return []

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
    return _sort_displays(displays)


@dataclass
class PlayerLaunchResult:
    ok: bool
    reason: str | None = None


class PlayerManager:
    def __init__(self, ffplay_path: Path):
        self.ffplay_path = ffplay_path
        self.players: dict[str, subprocess.Popen] = {}
        self.player_logs: dict[str, dict] = {}

    def _set_log_info(self, stream_id: str, **kwargs) -> None:
        info = dict(self.player_logs.get(stream_id) or {})
        info.setdefault("stderr", deque(maxlen=120))
        info.update(kwargs)
        self.player_logs[stream_id] = info

    def _capture_stderr(self, stream_id: str, proc: subprocess.Popen) -> None:
        stderr = getattr(proc, "stderr", None)
        if stderr is None:
            return
        try:
            for line in stderr:
                text = str(line).rstrip()
                if not text:
                    continue
                info = self.player_logs.get(stream_id)
                if not info:
                    continue
                buffer = info.get("stderr")
                if isinstance(buffer, deque):
                    buffer.append(text)
        except Exception:
            pass
        finally:
            try:
                stderr.close()
            except Exception:
                pass

    def debug_info(self, stream_id: str) -> dict:
        info = dict(self.player_logs.get(stream_id) or {})
        proc = self.players.get(stream_id)
        if proc is not None:
            info["running"] = proc.poll() is None
            info["pid"] = proc.pid
            if proc.poll() is not None:
                info["returncode"] = proc.returncode
        info.setdefault("path", str(self.ffplay_path))
        stderr_lines = info.get("stderr")
        if isinstance(stderr_lines, deque):
            info["stderr"] = list(stderr_lines)
        elif not isinstance(stderr_lines, list):
            info["stderr"] = []
        return info

    def stop_player(self, stream_id: str) -> None:
        proc = self.players.get(stream_id)
        _terminate_proc(proc)
        self.players.pop(stream_id, None)
        info = self.player_logs.get(stream_id)
        if info is not None:
            info["running"] = False
            if proc is not None and proc.poll() is not None:
                info["returncode"] = proc.returncode

    def stop_all(self) -> None:
        for stream_id in list(self.players.keys()):
            self.stop_player(stream_id)

    def clear_logs(self, stream_id: str) -> None:
        self.player_logs.pop(stream_id, None)

    def _input_args(self, stream: dict) -> tuple[list[str], str | None]:
        """Return ffplay/ffmpeg input args (everything that goes before any output)."""
        source = str(stream.get("source") or "srt").strip().lower()
        if source not in {"srt", "udp", "omt"}:
            source = "srt"

        if source == "udp":
            addr = str(stream.get("udpAddr") or "").strip()
            udp_port = int(stream.get("udpPort") or 0)
            if not addr or udp_port <= 0:
                return ([], "Source UDP invalide")
            return (["-i", f"udp://@{addr}:{udp_port}"], None)

        if source == "omt":
            name = str(stream.get("omtSource") or "").strip()
            if not name:
                return ([], "Source OMT vide")
            return (["-f", "libomt", "-i", name], None)

        latency_ms = int(stream.get("latency", 120))
        port = int(stream.get("port"))
        return (["-i", f"srt://0.0.0.0:{port}?mode=listener&latency={latency_ms * 1000}"], None)

    def _vf(self, stream: dict, display: dict, *, hwaccel: str = "cpu") -> str:
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
            vf = f"transpose=1,{vf}"
        elif rotate == 270:
            vf = f"transpose=2,{vf}"
        elif rotate == 180:
            vf = f"hflip,vflip,{vf}"

        hwaccel = str(hwaccel or "cpu").strip().lower()
        if hwaccel == "h264_qsv":
            return f"hwdownload,format=nv12,format=yuv420p,{vf}"
        if hwaccel in {"auto", "dxva2", "h264_amf", "h264_cuvid"}:
            return f"format=yuv420p,{vf}"
        return vf

    def start_player(self, stream: dict, display: dict, *, hwaccel: str = "cpu") -> PlayerLaunchResult:
        if not self.ffplay_path.exists():
            return PlayerLaunchResult(ok=False, reason=f"ffplay introuvable: {self.ffplay_path}")

        stream_id = str(stream.get("id"))
        self.stop_player(stream_id)

        input_args, input_err = self._input_args(stream)
        if input_err:
            return PlayerLaunchResult(ok=False, reason=input_err)

        hwaccel = str(hwaccel or "cpu").strip().lower()
        if hwaccel == "gpu":
            hwaccel = "auto"
        if hwaccel not in VALID_RECEIVER_DECODES:
            hwaccel = "cpu"

        vf = self._vf(stream, display, hwaccel=hwaccel)

        source = str(stream.get("source") or "srt").strip().lower()
        if source not in {"srt", "udp", "omt"}:
            source = "srt"

        args = [
            str(self.ffplay_path),
        ]

        if hwaccel == "auto":
            args.extend([
                "-hwaccel",
                "auto",
            ])
        elif hwaccel == "dxva2":
            args.extend([
                "-hwaccel",
                "dxva2",
            ])
        elif hwaccel == "h264_qsv":
            args.extend([
                "-hwaccel",
                "qsv",
                "-vcodec",
                "h264_qsv",
            ])
        elif hwaccel in {"h264_amf", "h264_cuvid"}:
            args.extend([
                "-vcodec",
                hwaccel,
            ])

        args.extend([
            "-fflags",
            "nobuffer",
            "-flags",
            "low_delay",
            "-probesize",
            "131072",
            "-analyzeduration",
            "250000",
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
        ])

        if source == "udp":
            args.extend([
                "-framedrop",
                "-sync",
                "ext",
            ])

        if bool(stream.get("muteAudio")):
            args.append("-an")

        args.extend(input_args)

        self._set_log_info(
            stream_id,
            path=str(self.ffplay_path),
            command=list(args),
            command_text=subprocess.list2cmdline(args),
            running=False,
            pid=None,
            returncode=None,
            launch_error=None,
            stderr=deque(maxlen=120),
        )

        creationflags = _win_creationflags()

        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=creationflags,
            )
            self.players[stream_id] = proc
            self._set_log_info(stream_id, running=True, pid=proc.pid, launch_error=None)
            threading.Thread(target=self._capture_stderr, args=(stream_id, proc), daemon=True).start()
            return PlayerLaunchResult(ok=True)
        except Exception as e:
            self._set_log_info(stream_id, running=False, returncode=None, launch_error=str(e))
            return PlayerLaunchResult(ok=False, reason=str(e))

    def status(self) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for stream_id, proc in list(self.players.items()):
            alive = proc.poll() is None
            status[stream_id] = alive
            if not alive:
                info = self.player_logs.get(stream_id)
                if info is not None:
                    info["running"] = False
                    info["returncode"] = proc.returncode
                self.players.pop(stream_id, None)
        return status


player_manager = PlayerManager(FFPLAY_PATH)


@dataclass
class SenderLaunchResult:
    ok: bool
    reason: str | None = None


class SenderManager:
    """Publish a Windows screen capture as an OMT source via FFmpeg/libomt."""

    def __init__(self, ffmpeg_path: Path):
        self.ffmpeg_path = ffmpeg_path
        self.proc: subprocess.Popen | None = None
        self.last_error: str | None = None

    def stop(self) -> None:
        _terminate_proc(self.proc)
        self.proc = None

    def status(self) -> bool:
        return bool(self.proc and self.proc.poll() is None)

    def start(
        self,
        display: dict,
        *,
        name: str,
        fps: int = 30,
        pixel_format: str = "uyvy422",
        clock_output: bool = False,
        reference_level: float = 1.0,
    ) -> SenderLaunchResult:
        if not self.ffmpeg_path.exists():
            self.last_error = f"ffmpeg introuvable: {self.ffmpeg_path}"
            return SenderLaunchResult(ok=False, reason=self.last_error)

        self.stop()

        capture_x = int(display.get("x", 0))
        capture_y = int(display.get("y", 0))
        width = int(display["width"])
        height = int(display["height"])

        fps = max(1, min(60, int(fps)))
        pf = str(pixel_format or "uyvy422").strip().lower()
        if pf not in VALID_OMT_PIXEL_FORMATS:
            pf = "uyvy422"
        omt_name = str(name or "").strip() or "SRT Multiview"

        args = [
            str(self.ffmpeg_path),
            "-hide_banner",
            "-loglevel", "warning",
            "-fflags", "+nobuffer",
            "-flags", "low_delay",
            "-thread_queue_size", "512",
            "-use_wallclock_as_timestamps", "1",
            "-f", "gdigrab",
            "-framerate", str(fps),
            "-offset_x", str(capture_x),
            "-offset_y", str(capture_y),
            "-video_size", f"{width}x{height}",
            "-draw_mouse", "1",
            "-i", "desktop",
            "-map", "0:v:0",
            "-an",
            "-vf", f"format={pf}",
            "-c:v", "wrapped_avframe",
            "-vsync", "passthrough",
            "-clock_output", "1" if clock_output else "0",
            "-reference_level", f"{float(reference_level):.3f}",
            "-f", "libomt",
            omt_name,
        ]

        creationflags = _win_creationflags()

        try:
            self.proc = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
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

    receiver_hwaccel = str((config.get("receiver") or {}).get("decode") or "cpu").strip().lower()
    if receiver_hwaccel == "gpu":
        receiver_hwaccel = "auto"
    if receiver_hwaccel not in VALID_RECEIVER_DECODES:
        receiver_hwaccel = "cpu"

    results: dict[str, PlayerLaunchResult] = {}
    displays = get_displays(exclude_primary=False, name_overrides=config.get("displayNames") or {})
    display_map = {str(d["id"]): d for d in displays}

    routes = {str(r.get("id")): r for r in (config.get("routes") or []) if isinstance(r, dict)}
    route_status = route_manager.status()
    running_players = player_manager.status()

    for stream in config["streams"]:
        stream_id = str(stream["id"])
        display_id = config.get("mapping", {}).get(stream_id)

        if not display_id or str(display_id) not in display_map:
            player_manager.stop_player(stream_id)
            results[stream_id] = PlayerLaunchResult(ok=False, reason="NO_DISPLAY")
            continue

        display = display_map[str(display_id)]

        # Skip restart if the player is already healthy.
        if running_players.get(stream_id):
            results[stream_id] = PlayerLaunchResult(ok=True)
            continue

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
            results[stream_id] = player_manager.start_player(stream_copy, display, hwaccel=receiver_hwaccel)
        else:
            results[stream_id] = player_manager.start_player(stream, display, hwaccel=receiver_hwaccel)

    return results


_OMT_LINE_RE = re.compile(r"^\[libomt[^\]]*\]\s+(.*)$")


def list_omt_sources(timeout_seconds: float = 8.0) -> tuple[list[str], str | None]:
    """Discover OMT sources visible on the network using ``ffmpeg -find_sources``.

    Returns ``(sources, error)``. ``error`` is set when discovery itself failed
    (e.g. ffmpeg missing, libomt unavailable). An empty ``sources`` list with a
    ``None`` error means the discovery ran but nothing was advertised.
    """
    if not FFMPEG_PATH.exists():
        return ([], f"ffmpeg introuvable: {FFMPEG_PATH}")

    args = [
        str(FFMPEG_PATH),
        "-hide_banner",
        "-loglevel",
        "info",
        "-nostdin",
        "-find_sources",
        "1",
        "-f",
        "libomt",
        "-i",
        "",
        "-frames:v",
        "1",
        "-f",
        "null",
        "-",
    ]

    try:
        proc = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=max(1.0, float(timeout_seconds)),
            check=False,
            creationflags=_win_creationflags(),
        )
    except subprocess.TimeoutExpired:
        return ([], f"Timeout après {timeout_seconds:.0f}s lors de la découverte OMT")
    except OSError as exc:
        return ([], f"Impossible de lancer ffmpeg: {exc}")

    stderr = (proc.stderr or b"").decode("utf-8", errors="ignore").splitlines()
    sources: list[str] = []
    in_block = False
    for raw in stderr:
        line = raw.strip()
        if not line:
            continue
        if "OMT Sources" in line:
            in_block = True
            continue
        if in_block and set(line) == {"-"}:
            continue
        if in_block and "Error opening input" in line:
            break
        if in_block:
            match = _OMT_LINE_RE.match(line)
            if match:
                candidate = match.group(1).strip()
                if candidate and candidate not in sources:
                    sources.append(candidate)

    if not sources and proc.returncode != 0 and not in_block:
        detail = "\n".join(stderr[-5:]).strip() or "aucun détail"
        if "libomt" in detail.lower() and "unknown" in detail.lower():
            return ([], "Cette build de ffmpeg ne supporte pas libomt.")
        return ([], f"Découverte OMT échouée: {detail}")

    return (sources, None)
