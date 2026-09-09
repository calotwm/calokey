"""MIDI-number <-> note-name mapping.

Note names use sharps for display (C, C#, D, ... B). Root indices 0-11 map to
C..B in chromatic order. The octave shift keeps C the start of each octave:
C4 (MIDI 60) is the conventional "middle C".
"""

ROOT_NAMES: tuple[str, ...] = (
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
)

_C_BASE = 60  # MIDI number of C4


def root_index_to_name(root_index: int) -> str:
    """Return the name (with sharps) of a chromatic root index 0-11."""
    if not isinstance(root_index, int) or isinstance(root_index, bool):
        raise ValueError(f"root index must be an int, got {type(root_index).__name__}")
    if not 0 <= root_index <= 11:
        raise ValueError(f"root index out of range [0, 11]: {root_index}")
    return ROOT_NAMES[root_index]


def midi_to_name(midi_number: int) -> str:
    """Return the note name (with sharps), e.g. 60 -> 'C4', 61 -> 'C#4'."""
    if not isinstance(midi_number, int) or isinstance(midi_number, bool):
        raise ValueError(f"MIDI number must be an int, got {type(midi_number).__name__}")
    if not 0 <= midi_number <= 127:
        raise ValueError(f"MIDI number out of range [0, 127]: {midi_number}")
    pitch = midi_number % 12
    octave = midi_number // 12 - 1
    return f"{ROOT_NAMES[pitch]}{octave}"


def name_to_midi(name: str) -> int:
    """Return the MIDI number for a note name like 'C4' or 'C#4'."""
    if len(name) < 2:
        raise ValueError(f"invalid note name: {name!r}")
    letter = name[0].upper()
    rest = name[1:]
    if rest.startswith("#"):
        offset = 1
        octave_str = rest[1:]
    else:
        offset = 0
        octave_str = rest
    if letter not in "ABCDEFG":
        raise ValueError(f"invalid note name: {name!r}")
    try:
        octave = int(octave_str)
    except ValueError:
        raise ValueError(f"invalid octave in note name: {name!r}") from None
    letter_index = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[letter]
    pitch = letter_index + offset
    midi_number = (octave + 1) * 12 + pitch
    if not 0 <= midi_number <= 127:
        raise ValueError(f"note name out of MIDI range [0, 127]: {name!r}")
    return midi_number
