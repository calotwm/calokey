"""Diatonic chord derivation: triads, sevenths, and chord naming.

Operates on the list of scale notes returned by ``scales.scale_notes``.
Degrees are 1-indexed (degree 1 == the tonic). Chords are built by stacking
every-other scale degree; quality is classified from the intervals between
the stacked notes.
"""


def _stacked(scale_notes: list[int], degree: int, count: int) -> list[int]:
    """Return ``count`` notes stacked in diatonic thirds starting at ``degree``.

    ``degree`` is 1-indexed. Stacking wraps within ``len(scale_notes)``
    (no octave extension). Raises ``ValueError`` if the scale has fewer than
    ``count`` notes (e.g. building a 7th on a 5-note pentatonic scale).
    """
    if not isinstance(degree, int) or isinstance(degree, bool):
        raise ValueError(f"degree must be an int, got {type(degree).__name__}")
    if not 1 <= degree <= len(scale_notes):
        raise ValueError(f"degree out of range [1, {len(scale_notes)}]: {degree}")
    if count > len(scale_notes):
        raise ValueError(
            f"cannot build a {count}-note chord from a {len(scale_notes)}-note scale"
        )
    notes = []
    for i in range(count):
        idx = (degree - 1 + 2 * i) % len(scale_notes)
        notes.append(scale_notes[idx])
    return notes


def triad(scale_notes: list[int], degree: int) -> list[int]:
    """Return the 3-note diatonic triad for ``degree``."""
    return _stacked(scale_notes, degree, 3)


def seventh(scale_notes: list[int], degree: int) -> list[int]:
    """Return the 4-note diatonic seventh chord for ``degree``.

    Raises ``ValueError`` for scales with fewer than 7 notes (pentatonic,
    blues), where a 7th cannot be formed without octave wrapping. The
    corresponding pads 6-7 are INACTIVE for those scales.
    """
    if len(scale_notes) < 7:
        raise ValueError(
            f"a seventh chord requires 7 scale degrees, "
            f"got a {len(scale_notes)}-note scale"
        )
    return _stacked(scale_notes, degree, 4)


def _quality(scale_notes: list[int], degree: int) -> str:
    """Classify a triad's quality from its ascending internal semitone intervals.

    The stacked notes are in stacking order (root, third, fifth). Each pair gap
    is measured ascending (mod 12), so wrapped chords like degree 7 (e.g.
    B=11, D=2, F=5) resolve to correct stacked thirds.
    """
    notes = _stacked(scale_notes, degree, 3)
    first_third = (notes[1] - notes[0]) % 12
    second_third = (notes[2] - notes[1]) % 12
    if first_third == 4 and second_third == 3:
        return "major"
    if first_third == 3 and second_third == 4:
        return "minor"
    if first_third == 3 and second_third == 3:
        return "diminished"
    # Non-tertian spellings (e.g. doubled intervals from wrap-around): best effort.
    return "major"


def chord_name(scale_notes: list[int], degree: int, root_name: str) -> str:
    """Return the chord name, e.g. 'C', 'Dm', 'Bdim'."""
    quality = _quality(scale_notes, degree)
    if quality == "major":
        return root_name
    if quality == "minor":
        return f"{root_name}m"
    if quality == "diminished":
        return f"{root_name}dim"
    return root_name


def chord_quality(scale_notes: list[int], degree: int) -> str:
    """Return the triad quality string: 'major', 'minor', or 'diminished'."""
    return _quality(scale_notes, degree)
