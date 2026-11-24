"""Lokale, beschermde opslag voor de sleutel en de vertaaltabellen van Nest-privacy.

- Windows: versleuteld met DPAPI (CryptProtectData). Alleen jouw Windows-account op deze computer kan het teruglezen.
- macOS/Linux: een bestand met rechten 600 in je eigen thuismap (alleen jouw account kan het lezen).
Alles staat in ~/.koekoek/nest-privacy (of NEST_PRIVACY_MAP). Er gaat niets over het netwerk.
Alleen de standaardbibliotheek.
"""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

MAP = Path(os.environ.get("NEST_PRIVACY_MAP") or Path.home() / ".koekoek" / "nest-privacy")


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(data: bytes, beschermen: bool) -> bytes:
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32  # type: ignore[attr-defined]
    buf = ctypes.create_string_buffer(data, len(data))
    invoer, uit = _Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char))), _Blob()
    functie = crypt32.CryptProtectData if beschermen else crypt32.CryptUnprotectData
    # dwFlags 0x1 = CRYPTPROTECT_UI_FORBIDDEN: nooit een venster
    if not functie(ctypes.byref(invoer), None, None, None, None, 0x1, ctypes.byref(uit)):
        raise OSError("Windows kon de gegevens niet beschermen of teruglezen (DPAPI).")
    try:
        return ctypes.string_at(uit.pbData, uit.cbData)
    finally:
        kernel32.LocalFree(uit.pbData)


def bewaar(naam: str, data: bytes) -> Path:
    MAP.mkdir(parents=True, exist_ok=True)
    pad = MAP / naam
    pad.parent.mkdir(parents=True, exist_ok=True)
    inhoud = _dpapi(data, True) if sys.platform == "win32" else data
    tijdelijk = pad.with_name(pad.name + ".tmp")
    fd = os.open(tijdelijk, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(inhoud)
    os.replace(tijdelijk, pad)
    if sys.platform != "win32":
        os.chmod(pad, 0o600)
    return pad


def lees(naam: str) -> bytes | None:
    pad = MAP / naam
    if not pad.is_file():
        return None
    data = pad.read_bytes()
    return _dpapi(data, False) if sys.platform == "win32" else data
