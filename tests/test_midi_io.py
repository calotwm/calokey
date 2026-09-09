"""Integration-style tests for the MIDI layer using fakes (no hardware).

Covers raw-event parsing, the input thread's queue draining, chord output
routing, and SysEx scene-change parsing — all against recording fakes.
"""

import queue
import time
import unittest

from midi import sysex
from midi.input_thread import InputThread, parse_event
from midi.output import ChordSender


class ParseEventTests(unittest.TestCase):
    def test_note_on(self):
        event = [[0x90, 60, 100], 12345]
        self.assertEqual(parse_event(event), ("note_on", (0, 60, 100)))

    def test_note_off(self):
        event = [[0x80, 60, 0], 12345]
        self.assertEqual(parse_event(event), ("note_off", (0, 60, 0)))

    def test_note_on_velocity_zero_is_note_off(self):
        event = [[0x90, 60, 0], 12345]
        self.assertEqual(parse_event(event), ("note_off", (0, 60, 0)))

    def test_cc(self):
        event = [[0xB0, 20, 64], 12345]
        self.assertEqual(parse_event(event), ("cc", (0, 20, 64)))

    def test_cc_channel_preserved(self):
        event = [[0xB3, 21, 127], 0]
        self.assertEqual(parse_event(event), ("cc", (3, 21, 127)))

    def test_sysex(self):
        event = [[0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x00, 0xF7], 0]
        kind, data = parse_event(event)
        self.assertEqual(kind, "sysex")
        self.assertEqual(data[0], 0xF0)

    def test_unsupported_returns_none(self):
        self.assertIsNone(parse_event([[0xC0, 5], 0]))  # program change

    def test_empty_event_returns_none(self):
        self.assertIsNone(parse_event(None))
        self.assertIsNone(parse_event([]))


class FakeInput:
    def __init__(self, events):
        self._events = list(events)

    def poll(self):
        return bool(self._events)

    def read(self, n):
        batch = self._events[:n]
        self._events = self._events[n:]
        return batch


class InputThreadTests(unittest.TestCase):
    def test_drains_fake_input_into_queue(self):
        events = [
            [[0x90, 60, 100], 1],
            [[0x90, 62, 100], 2],
            [[0x80, 60, 0], 3],
        ]
        fake = FakeInput(events)
        q = queue.Queue()
        thread = InputThread(fake, q)
        thread.start()
        deadline = time.monotonic() + 2
        while q.qsize() < 3 and time.monotonic() < deadline:
            time.sleep(0.01)
        thread.stop()
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())
        got = [q.get_nowait() for _ in range(3)]
        self.assertEqual(got, [
            ("note_on", (0, 60, 100)),
            ("note_on", (0, 62, 100)),
            ("note_off", (0, 60, 0)),
        ])

    def test_ignores_unsupported_events(self):
        fake = FakeInput([[[0xC0, 5], 1], [[0x90, 64, 100], 2]])
        q = queue.Queue()
        thread = InputThread(fake, q)
        thread.start()
        deadline = time.monotonic() + 2
        while q.qsize() < 1 and time.monotonic() < deadline:
            time.sleep(0.01)
        thread.stop()
        thread.join(timeout=1)
        self.assertEqual(q.get_nowait(), ("note_on", (0, 64, 100)))
        self.assertTrue(q.empty())


class FakeOutput:
    def __init__(self):
        self.on = []
        self.off = []

    def note_on(self, note, velocity, channel=0):
        self.on.append((note, velocity, channel))

    def note_off(self, note, velocity=0, channel=0):
        self.off.append((note, velocity, channel))


class ChordSenderTests(unittest.TestCase):
    def test_send_chord_note_on_all(self):
        out = FakeOutput()
        sender = ChordSender(out, channel=0)
        sender.send_chord([0, 4, 7])
        self.assertEqual(out.on, [(0, 100, 0), (4, 100, 0), (7, 100, 0)])
        self.assertEqual(out.off, [])

    def test_release_chord_note_off_all(self):
        out = FakeOutput()
        sender = ChordSender(out, channel=0)
        sender.release_chord([0, 4, 7])
        self.assertEqual(out.off, [(0, 0, 0), (4, 0, 0), (7, 0, 0)])

    def test_channel_override(self):
        out = FakeOutput()
        sender = ChordSender(out, channel=0)
        sender.send_chord([60], channel=3)
        self.assertEqual(out.on, [(60, 100, 3)])


class SysexTests(unittest.TestCase):
    def test_parse_scene_change(self):
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x03, 0xF7]
        self.assertEqual(sysex.parse_scene_change(msg), 3)

    def test_parse_scene_change_without_framing(self):
        msg = [0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x07]
        self.assertEqual(sysex.parse_scene_change(msg), 7)

    def test_parse_scene_out_of_range_returns_none(self):
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x08, 0xF7]
        self.assertIsNone(sysex.parse_scene_change(msg))

    def test_parse_wrong_prefix_returns_none(self):
        msg = [0xF0, 0x43, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x00, 0xF7]
        self.assertIsNone(sysex.parse_scene_change(msg))

    def test_bulk_dump_request_is_framed(self):
        req = sysex.build_bulk_dump_request()
        self.assertEqual(req[0], 0xF0)
        self.assertEqual(req[-1], 0xF7)


if __name__ == "__main__":
    unittest.main()
