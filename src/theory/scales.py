"""The 12 scale types and diatonic note derivation.

Each scale type is defined by the ordered chromatic intervals (semitones from
the root) of its ascending scale. ``scale_notes`` returns the resulting MIDI
note numbers starting from ``root_index`` at octave 0 (i.e. MIDI number ==
the chromatic pitch class, without an octave offset).
"""

# Semitone intervals (ascending) for each scale type, in registry order.
_SCALE_INTERVALS: tuple[tuple[int, ...], ...] = (
    (0, 2, 4, 5, 7, 9, 11),   # Ionian (major)
    (0, 2, 3, 5, 7, 9, 10),   # Dorian
    (0, 1, 3, 5, 7, 8, 10),   # Phrygian
    (0, 2, 4, 6, 7, 9, 11),   # Lydian
    (0, 2, 4, 5, 7, 9, 10),   # Mixolydian
    (0, 2, 3, 5, 7, 8, 10),   # Aeolian (natural minor)
    (0, 1, 3, 5, 6, 8, 10),   # Locrian
    (0, 2, 3, 5, 7, 8, 11),   # Harmonic minor
    (0, 2, 3, 5, 7, 9, 11),   # Melodic minor
    (0, 2, 4, 7, 9),          # Major pentatonic
    (0, 3, 5, 7, 10),         # Minor pentatonic
    (0, 3, 5, 6, 7, 10),      # Blues
)

SCALE_NAMES: tuple[str, ...] = (
    "Ionian",
    "Dorian",
    "Phrygian",
    "Lydian",
    "Mixolydian",
    "Aeolian",
    "Locrian",
    "Harmonic minor",
    "Melodic minor",
    "Major pentatonic",
    "Minor pentatonic",
    "Blues",
)

NUM_SCALE_TYPES = len(_SCALE_INTERVALS)


def scale_intervals(type_index: int) -> tuple[int, ...]:
    """Return the ascending semitone intervals for a scale type."""
    if not isinstance(type_index, int) or isinstance(type_index, bool):
        raise ValueError(f"type index must be an int, got {type(type_index).__name__}")
    if not 0 <= type_index < NUM_SCALE_TYPES:
        raise ValueError(f"type index out of range [0, {NUM_SCALE_TYPES - 1}]: {type_index}")
    return _SCALE_INTERVALS[type_index]


def scale_notes(root_index: int, type_index: int) -> list[int]:
    """Return the scale's MIDI note numbers (root at octave 0).

    Heptatonic scales yield 7 notes; the major/minor pentatonic yield 5 and
    the blues scale 6. Notes are ascending and the first note equals the root
    pitch class.
    """
    if not isinstance(root_index, int) or isinstance(root_index, bool):
        raise ValueError(f"root index must be an int, got {type(root_index).__name__}")
    if not 0 <= root_index <= 11:
        raise ValueError(f"root index out of range [0, 11]: {root_index}")
    intervals = scale_intervals(type_index)
    return [root_index + interval for interval in intervals]
