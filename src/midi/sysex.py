"""SysEx handling for the Korg nanoKEY Studio.

The device announces scene changes with::

    F0 42 40 00 01 36 02 00 00 4F NN F7

where ``NN`` is the active scene number (0-7). A best-effort bulk-dump inquiry
(``build_bulk_dump_request``) is also provided; its exact request bytes are only
partially documented (design open question). When the device answers, the reply
is parsed by ``parse_bulk_dump`` into a ``DeviceConfig``::

    F0 42 40 00 01 36 02 <8 knob CCs> <8 pad notes> F7

Unrecognized SysEx payloads return ``None`` so the app keeps its current config.
"""

from state import DeviceConfig

SYSEX_START = 0xF0
SYSEX_END = 0xF7

# Bytes that identify a nanoKEY scene-change SysEx (up to the scene byte).
SCENE_CHANGE_PREFIX = (0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F)

# Bytes shared by the bulk-dump reply (header up to the config payload).
BULK_DUMP_REPLY_PREFIX = (0x42, 0x40, 0x00, 0x01, 0x36, 0x02)

MAX_SCENE = 7
NUM_KNOBS = 8
NUM_PADS = 8

# Best-effort bulk-dump request. The verified inquiry trigger for the nanoKEY
# Studio is not fully documented; this emits a Korg request-shaped message.
BULK_DUMP_REQUEST = bytes([
    SYSEX_START, 0x42, 0x40, 0x00, 0x01, 0x36, 0x01, SYSEX_END,
])


def _strip_framing(data) -> list[int]:
    """Strip a leading 0xF0 and/or trailing 0xF7 from a SysEx byte sequence."""
    body = list(data) if data else []
    if body and body[0] == SYSEX_START:
        body = body[1:]
    if body and body[-1] == SYSEX_END:
        body = body[:-1]
    return body


def parse_scene_change(data) -> int | None:
    """Return the scene number from a scene-change SysEx, or ``None``.

    ``data`` is a sequence of ints; a leading 0xF0 and/or trailing 0xF7 are
    stripped before matching the known prefix.
    """
    body = _strip_framing(data)
    if len(body) < len(SCENE_CHANGE_PREFIX) + 1:
        return None
    if tuple(body[: len(SCENE_CHANGE_PREFIX)]) != SCENE_CHANGE_PREFIX:
        return None
    scene = body[len(SCENE_CHANGE_PREFIX)]
    if not 0 <= scene <= MAX_SCENE:
        return None
    return scene


def build_bulk_dump_request() -> bytes:
    """Return the best-effort bulk-dump inquiry SysEx bytes."""
    return BULK_DUMP_REQUEST


def parse_bulk_dump(data) -> DeviceConfig | None:
    """Parse a bulk-dump reply into a ``DeviceConfig``, or ``None``.

    Expected best-effort format (see module docstring)::

        F0 42 40 00 01 36 02 <8 knob CCs> <8 pad notes> F7

    Scene-change notifications and any unknown payloads return ``None`` so the
    caller keeps its current config.
    """
    body = _strip_framing(data)
    if tuple(body[: len(BULK_DUMP_REPLY_PREFIX)]) != BULK_DUMP_REPLY_PREFIX:
        return None
    payload = body[len(BULK_DUMP_REPLY_PREFIX):]
    if len(payload) != NUM_KNOBS + NUM_PADS:
        return None
    knobs = payload[:NUM_KNOBS]
    pads = payload[NUM_KNOBS:]
    if not all(0 <= byte <= 127 for byte in knobs + pads):
        return None
    return DeviceConfig(knob_ccs=list(knobs), pad_notes=list(pads))
