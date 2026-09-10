"""Application state: root/scale selection, fader hysteresis, and pad-8 modifier.

``AppState`` owns the musical selection (root note + scale type) plus the pad-8
momentary flag. Fader CC values map to discrete positions via
``pos = clamp(round(cc * 11 / 127), 0, 11)`` and are committed through a
Schmitt-trigger hysteresis with ``DEAD_ZONE_CC = 2``: a ±1 CC jitter around a
position boundary never changes the selection, while a clear move of ≥2 CC past
the boundary commits exactly once.
"""

from theory import chords, notes, scales

DEAD_ZONE_CC = 2
CC_MAX = 127
MAX_POSITION = 11  # positions 0..11 = 12 roots / 12 scale types

FADER_ROOT = 0  # knob 1 (CC 20) selects the root note
FADER_TYPE = 1  # knob 2 (CC 21) selects the scale type


class DeviceConfig:
    """Runtime-discovered nanoKEY Studio configuration.

    Holds the actual knob CC numbers and pad note assignments read from the
    device via SysEx bulk dump (rather than assumed defaults), plus the device's
    global MIDI channel observed from live traffic.

    ``DeviceConfig.defaults()`` is the pre-discovery fallback and matches the
    nanoKEY Studio factory defaults (knobs 1-8 = CC 20..27; pads 1-8 = the
    C-major note set). The app replaces it with discovered values as soon as the
    device answers a bulk-dump inquiry.
    """

    DEFAULT_KNOB_CCS = (20, 21, 22, 23, 24, 25, 26, 27)
    DEFAULT_PAD_NOTES = (60, 62, 64, 65, 67, 69, 71, 72)

    def __init__(self, knob_ccs=None, pad_notes=None, global_channel: int = 0):
        self.knob_ccs: list[int] = (
            list(knob_ccs) if knob_ccs is not None else list(self.DEFAULT_KNOB_CCS)
        )
        self.pad_notes: list[int] = (
            list(pad_notes) if pad_notes is not None else list(self.DEFAULT_PAD_NOTES)
        )
        self.global_channel = global_channel

    @classmethod
    def defaults(cls) -> "DeviceConfig":
        return cls()

    def fader_for_cc(self, control: int) -> int | None:
        """Map a knob CC number to a fader index (``FADER_ROOT``/``FADER_TYPE``).

        Returns ``None`` for CC numbers that are not knob 1 or knob 2 (knobs 3-8
        and unrelated controls are ignored by the scale engine).
        """
        try:
            index = self.knob_ccs.index(control)
        except ValueError:
            return None
        if index in (FADER_ROOT, FADER_TYPE):
            return index
        return None

    def pad_for_note(self, note: int) -> int | None:
        """Map an incoming note number to a pad number (1-8), or ``None``."""
        try:
            return self.pad_notes.index(note) + 1
        except ValueError:
            return None


def cc_to_position(cc: int) -> int:
    """Map a MIDI CC value (0..127) to a position (0..11)."""
    if not isinstance(cc, int) or isinstance(cc, bool):
        raise ValueError(f"CC value must be an int, got {type(cc).__name__}")
    if not 0 <= cc <= CC_MAX:
        raise ValueError(f"CC value out of range [0, 127]: {cc}")
    return max(0, min(MAX_POSITION, round(cc * MAX_POSITION / CC_MAX)))


def _boundary_cc(lower_position: int) -> float:
    """CC value at the midpoint between ``lower_position`` and ``lower_position+1``."""
    return CC_MAX * (lower_position + 0.5) / MAX_POSITION


def _validate_index(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{label} must be an int, got {type(value).__name__}")
    if not 0 <= value <= MAX_POSITION:
        raise ValueError(f"{label} out of range [0, 11]: {value}")
    return value


class AppState:
    """Holds root note, scale type, pad-8 modifier, and current chord state."""

    def __init__(self, root: int = 0, scale_type: int = 0):
        self.root = _validate_index(root, "root")
        self.scale_type = _validate_index(scale_type, "scale type")
        self.pad8_held = False

    # -- fader handling -------------------------------------------------

    def apply_fader_cc(self, fader: int, cc: int) -> bool:
        """Apply a fader CC value; return ``True`` if the selection changed.

        ``fader`` is ``FADER_ROOT`` (0) for root or ``FADER_TYPE`` (1) for scale
        type. The Schmitt-trigger hysteresis ignores ±1 CC jitter around a
        boundary and commits a clear move exactly once.
        """
        if fader not in (FADER_ROOT, FADER_TYPE):
            raise ValueError(f"unknown fader: {fader}")
        pos = cc_to_position(cc)
        attr = "root" if fader == FADER_ROOT else "scale_type"
        committed = getattr(self, attr)
        if pos == committed:
            return False
        if pos > committed:
            boundary = _boundary_cc(committed)
            switched = cc >= boundary + DEAD_ZONE_CC
        else:
            boundary = _boundary_cc(committed - 1)
            switched = cc <= boundary - DEAD_ZONE_CC
        if not switched:
            return False
        setattr(self, attr, pos)
        return True

    # -- pad-8 modifier --------------------------------------------------

    def set_pad8_held(self, held: bool) -> None:
        """Set the pad-8 momentary flag: True => seventh chords, False => triads."""
        self.pad8_held = bool(held)

    # -- current chord state ---------------------------------------------

    def scale_notes(self) -> list[int]:
        """Return the current scale's MIDI notes."""
        return scales.scale_notes(self.root, self.scale_type)

    def chord_notes(self, pad: int) -> list[int]:
        """Return the chord notes for pad ``pad`` (1-7), honoring the pad-8 flag."""
        current = self.scale_notes()
        if self.pad8_held:
            return chords.seventh(current, pad)
        return chords.triad(current, pad)

    def chord_name(self, pad: int) -> str:
        """Return the chord name (e.g. 'C', 'Dm') for pad ``pad`` (1-7)."""
        current = self.scale_notes()
        root_note = current[pad - 1]
        root_name = notes.root_index_to_name(root_note % 12)
        return chords.chord_name(current, pad, root_name)
