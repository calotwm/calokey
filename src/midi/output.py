"""Chord output via ``pygame.midi.Output``.

``ChordSender`` turns chord note lists into ``note_on``/``note_off`` calls on a
``pygame.midi.Output``. It only depends on the Output interface
(``note_on(note, velocity, channel)`` / ``note_off(note, velocity, channel)``),
so tests can substitute a recording fake.
"""

DEFAULT_VELOCITY = 100


class ChordSender:
    def __init__(self, output, channel: int = 0):
        self._output = output
        self._channel = channel

    def note_on(self, note: int, velocity: int = DEFAULT_VELOCITY, channel: int | None = None) -> None:
        self._output.note_on(note, velocity, self._channel if channel is None else channel)

    def note_off(self, note: int, velocity: int = 0, channel: int | None = None) -> None:
        self._output.note_off(note, velocity, self._channel if channel is None else channel)

    def send_chord(self, notes, velocity: int = DEFAULT_VELOCITY, channel: int | None = None) -> None:
        """Send ``note_on`` for every note in ``notes``."""
        for note in notes:
            self.note_on(note, velocity, channel)

    def release_chord(self, notes, channel: int | None = None) -> None:
        """Send ``note_off`` for every note in ``notes``."""
        for note in notes:
            self.note_off(note, 0, channel)
