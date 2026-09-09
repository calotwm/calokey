"""Dedicated MIDI input polling thread that pushes parsed events to a queue.

The thread polls a ``pygame.midi.Input`` at ~1ms and translates raw PortMidi
events into ``(type, data)`` tuples on a ``queue.Queue``::

    ("cc",       (channel, control, value))
    ("note_on",  (channel, note, velocity))
    ("note_off", (channel, note, velocity))
    ("sysex",    (byte, byte, ...))

``parse_event`` is a pure function so parsing is unit-testable with fake event
lists and no hardware.
"""

import threading

POLL_INTERVAL = 0.001  # ~1 ms

NOTE_OFF = 0x80
NOTE_ON = 0x90
CONTROL_CHANGE = 0xB0
SYSEX_START = 0xF0


def parse_event(event: list) -> tuple | None:
    """Parse one raw PortMidi event ``[message, timestamp]``.

    Returns ``(type, data)`` or ``None`` for unsupported messages. A note-on
    with velocity 0 is normalized to ``note_off`` per MIDI convention.
    """
    if not event or not isinstance(event[0], list):
        return None
    message = event[0]
    if not message:
        return None
    status = message[0]
    if status == SYSEX_START:
        return ("sysex", tuple(message))
    kind = status & 0xF0
    channel = status & 0x0F
    if kind == NOTE_ON:
        note, velocity = message[1], message[2]
        if velocity == 0:
            return ("note_off", (channel, note, 0))
        return ("note_on", (channel, note, velocity))
    if kind == NOTE_OFF:
        note, velocity = message[1], message[2]
        return ("note_off", (channel, note, velocity))
    if kind == CONTROL_CHANGE:
        control, value = message[1], message[2]
        return ("cc", (channel, control, value))
    return None


class InputThread(threading.Thread):
    """Polls ``midi_input`` and pushes parsed events onto ``queue``."""

    def __init__(self, midi_input, queue, poll_interval: float = POLL_INTERVAL):
        super().__init__(daemon=True, name="midi-input")
        self._input = midi_input
        self._queue = queue
        self._interval = poll_interval
        self._stop = threading.Event()

    def stop(self) -> None:
        """Signal the thread to stop after the current poll."""
        self._stop.set()

    def run(self) -> None:
        while not self._stop.is_set():
            if self._input.poll():
                for event in self._input.read(64):
                    parsed = parse_event(event)
                    if parsed is not None:
                        self._queue.put(parsed)
            else:
                self._stop.wait(self._interval)
