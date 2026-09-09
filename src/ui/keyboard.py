"""On-screen piano keyboard with scale-note highlighting.

Renders a chromatic span of keys as rectangles on a pygame Surface. The active
scale's notes are highlighted; when a chord is playing, its notes get a second
(pressed) highlight. Layout geometry is computed by pure functions so the
keyboard is unit-testable without a display.
"""

import pygame

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
WHITE_KEY_COLOR = (240, 240, 240)
WHITE_KEY_BORDER = (120, 120, 120)
BLACK_KEY_COLOR = (10, 10, 10)
SCALE_HIGHLIGHT = (90, 170, 255)
CHORD_HIGHLIGHT = (255, 200, 70)

# Chromatic pitch classes for the white keys (octave positions).
_WHITE_PITCHES = (0, 2, 4, 5, 7, 9, 11)
# Black-key pitch classes and a per-octave fractional column (0..len(white)-2).
_BLACK_KEYS = (
    (1, 0.5), (3, 1.5), (6, 3.5), (8, 4.5), (10, 5.5),
)


def _octave_bounds(low_midi: int, high_midi: int) -> tuple[int, int]:
    """Normalize bounds to whole octaves (C .. B) covering the given span."""
    low_octave = low_midi // 12
    high_octave = high_midi // 12
    return low_octave * 12, high_octave * 12 + 11


class Keyboard:
    """Renders a piano spanning ``low_midi``..``high_midi`` and tracks highlights."""

    def __init__(self, low_midi: int, high_midi: int, x: int, y: int, width: int, height: int):
        self.low_midi, self.high_midi = _octave_bounds(low_midi, high_midi)
        self.x, self.y, self.width, self.height = x, y, width, height
        self.white_keys = [
            p for p in range(self.low_midi, self.high_midi + 1)
            if p % 12 in _WHITE_PITCHES
        ]
        self.black_keys = [
            p for p in range(self.low_midi, self.high_midi + 1)
            if p % 12 not in _WHITE_PITCHES
        ]
        self.highlighted = set()   # scale notes
        self.pressed = set()       # chord notes pressed/playing

    def white_key_rect(self, pitch: int) -> pygame.Rect:
        """Return the on-screen rectangle for a white-key pitch."""
        idx = self.white_keys.index(pitch)
        key_width = self.width // len(self.white_keys)
        return pygame.Rect(self.x + idx * key_width, self.y, key_width, self.height)

    def black_key_rect(self, pitch: int) -> pygame.Rect:
        """Return the on-screen rectangle for a black-key pitch."""
        key_width = self.width // len(self.white_keys)
        black_width = int(key_width * 0.62)
        for pc, frac in _BLACK_KEYS:
            if pitch % 12 == pc:
                col = (pitch // 12) - (self.low_midi // 12)
                center = self.x + int((col + frac) * key_width)
                return pygame.Rect(
                    center - black_width // 2, self.y, black_width, int(self.height * 0.6)
                )
        raise ValueError(f"not a black-key pitch: {pitch}")

    def set_scale_notes(self, notes: list[int]) -> None:
        """Highlight the pitches of the active scale."""
        self.highlighted = set(note % 12 for note in notes)

    def set_pressed_notes(self, notes: list[int]) -> None:
        """Highlight the chord notes currently sounding."""
        self.pressed = set(note % 12 for note in notes)

    def draw(self, surface: pygame.Surface) -> None:
        """Render white keys, then black keys, with highlight layers."""
        for pitch in self.white_keys:
            color = WHITE_KEY_COLOR
            if pitch % 12 in self.highlighted:
                color = SCALE_HIGHLIGHT
            if pitch % 12 in self.pressed:
                color = CHORD_HIGHLIGHT
            pygame.draw.rect(surface, color, self.white_key_rect(pitch))
            pygame.draw.rect(surface, WHITE_KEY_BORDER, self.white_key_rect(pitch), 2)
        for pitch in self.black_keys:
            color = BLACK_KEY_COLOR
            if pitch % 12 in self.highlighted:
                color = SCALE_HIGHLIGHT
            if pitch % 12 in self.pressed:
                color = CHORD_HIGHLIGHT
            pygame.draw.rect(surface, color, self.black_key_rect(pitch))
