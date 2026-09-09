"""SysEx handling for the Korg nanoKEY Studio.

The device announces scene changes with::

    F0 42 40 00 01 36 02 00 00 4F NN F7

where ``NN`` is the active scene number (0-7). A best-effort bulk-dump inquiry
is also provided, but its exact request bytes are only partially documented
(design open question) — runtime discovery of CC/note traffic remains the
reliable fallback.
"""

SYSEX_START = 0xF0
SYSEX_END = 0xF7

# Bytes that identify a nanoKEY scene-change SysEx (up to the scene byte).
SCENE_CHANGE_PREFIX = (0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F)

MAX_SCENE = 7

# Best-effort bulk-dump request. The verified inquiry trigger for the nanoKEY
# Studio is not fully documented; this emits a Korg request-shaped message.
BULK_DUMP_REQUEST = bytes([
    SYSEX_START, 0x42, 0x40, 0x00, 0x01, 0x36, 0x01, SYSEX_END,
])


def parse_scene_change(data) -> int | None:
    """Return the scene number from a scene-change SysEx, or ``None``.

    ``data`` is a sequence of ints; a leading 0xF0 and/or trailing 0xF7 are
    stripped before matching the known prefix.
    """
    if not data:
        return None
    body = list(data)
    if body[0] == SYSEX_START:
        body = body[1:]
    if body and body[-1] == SYSEX_END:
        body = body[:-1]
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
