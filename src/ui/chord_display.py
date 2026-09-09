"""Chord display: renders the current chord name and its note names.

Keeps the textual chord label (name + note names) as a pure computation so it
is testable without a display; ``draw`` renders it to a pygame Surface.
"""

import pygame

from theory import notes

TEXT_COLOR = (255, 255, 255)
MUTED_COLOR = (150, 150, 150)


def chord_label(chord_name: str, chord_notes: list[int]) -> str:
    """Return the display label, e.g. ``"C — C E G"``, for a chord."""
    note_names = " ".join(notes.midi_to_name(n % 12 + 60) for n in chord_notes)
    return f"{chord_name} — {note_names}"


class ChordDisplay:
    """Renders a chord name plus its note names at a fixed position."""

    def __init__(self, x: int, y: int, font=None):
        self.x, self.y = x, y
        self.font = font or pygame.font.Font(None, 36)
        self.current_label = ""

    def set_chord(self, chord_name: str, chord_notes: list[int]) -> None:
        """Update the label for a chord (name + note names)."""
        self.current_label = chord_label(chord_name, chord_notes)

    def clear(self) -> None:
        """Clear the label (no chord sounding)."""
        self.current_label = ""

    def draw(self, surface: pygame.Surface) -> None:
        rendered = self.font.render(self.current_label, True, TEXT_COLOR)
        surface.blit(rendered, (self.x, self.y))
