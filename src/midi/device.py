"""MIDI device discovery and opening via ``pygame.midi`` (PortMidi).

Discovery matches a PortMidi device whose name contains ``"nanoKEY"``
(case-insensitive) and opens its input interface. Output ports are enumerated
for the port selector and opened by name (for config persistence).

No hardware is touched at import time: ``pygame.midi`` is initialized lazily
inside each function so the module stays importable in headless tests.
"""

import pygame.midi

DEVICE_NAME_SUBSTRING = "nanoKEY"


def _ensure_init() -> None:
    if not pygame.midi.get_init():
        pygame.midi.init()


def _device_name(device_id: int) -> str:
    info = pygame.midi.get_device_info(device_id)
    if info is None:
        return ""
    raw = info[1]
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return str(raw)


def discover_nanokey() -> int | None:
    """Return the input device id of the first connected nanoKEY, or ``None``."""
    _ensure_init()
    for device_id in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(device_id)
        if info is None:
            continue
        if not bool(info[2]):  # skip non-input interfaces
            continue
        name = _device_name(device_id)
        if DEVICE_NAME_SUBSTRING.lower() in name.lower():
            return device_id
    return None


def open_input(device_id: int) -> pygame.midi.Input:
    """Open the MIDI input interface for ``device_id``."""
    _ensure_init()
    return pygame.midi.Input(device_id)


def list_output_ports() -> list[tuple[int, str]]:
    """Return ``[(device_id, name), ...]`` for every output port."""
    _ensure_init()
    ports = []
    for device_id in range(pygame.midi.get_count()):
        info = pygame.midi.get_device_info(device_id)
        if info is None:
            continue
        if bool(info[3]):  # is output
            ports.append((device_id, _device_name(device_id)))
    return ports


def open_output(name: str) -> pygame.midi.Output | None:
    """Open an output port by exact name; returns ``None`` if not found."""
    _ensure_init()
    for device_id, port_name in list_output_ports():
        if port_name == name:
            return pygame.midi.Output(device_id)
    return None
