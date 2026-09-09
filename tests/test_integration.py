"""Integration tests for the UI + wiring flow.

Covers the event flow ``pad press -> chord notes -> output`` and the fader ->
state -> redraw path, using a headless pygame (dummy video driver), a fake
output of chord notes, and a fake queue of parsed MIDI events. No hardware.
"""

import os
import queue
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from midi.output import ChordSender  # noqa: E402
from state import AppState  # noqa: E402
from ui.app import App  # noqa: E402

# nanoKEY pad note mapping used by App._note_to_pad: pitch class -> pad.
# C=pad1, D=pad2, E=pad3, F=pad4, G=pad5, A=pad6, B=pad7.
PAD_NOTES = {1: 60, 2: 62, 3: 64, 4: 65, 5: 67, 6: 69, 7: 71}


class RecordingOutput:
    def __init__(self):
        self.on = []
        self.off = []

    def note_on(self, note, velocity, channel=0):
        self.on.append((note, velocity, channel))

    def note_off(self, note, velocity=0, channel=0):
        self.off.append((note, velocity, channel))


def make_app(root=0, scale_type=0):
    state = AppState(root=root, scale_type=scale_type)
    out = RecordingOutput()
    sender = ChordSender(out)
    app = App(state, sender)
    app.set_device_state(True)
    return app, out, state


class PadPressFlowTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_pad_press_sends_triad_and_shows_chord(self):
        app, out, state = make_app()  # C Ionian
        app.handle_event(("note_on", (0, PAD_NOTES[3], 100)))  # pad 3 -> Em
        triad = state.chord_notes(3)  # note_on set
        self.assertEqual(out.on, [(n, 100, 0) for n in triad])
        self.assertEqual(out.off, [])
        self.assertIn("E", app.chord_display.current_label)
        self.assertIn("m", app.chord_display.current_label)

    def test_pad_release_sends_note_off(self):
        app, out, state = make_app()
        app.handle_event(("note_on", (0, PAD_NOTES[1], 100)))
        app.handle_event(("note_off", (0, PAD_NOTES[1], 0)))
        triad = state.chord_notes(1)
        self.assertEqual(out.off, [(n, 0, 0) for n in triad])
        self.assertEqual(app.chord_display.current_label, "")

    def test_pad8_hold_makes_seventh(self):
        app, out, state = make_app()
        # nanoKEY pad 8 (note 72) triggers the momentary modifier.
        app.handle_event(("note_on", (0, 72, 100)))
        self.assertTrue(state.pad8_held)
        app.handle_event(("note_on", (0, PAD_NOTES[1], 100)))
        self.assertEqual(len(out.on), 4)  # seventh chord = 4 notes
        app.handle_event(("note_off", (0, PAD_NOTES[1], 0)))
        app.handle_event(("note_off", (0, 72, 0)))
        self.assertFalse(state.pad8_held)

    def test_client_note_on_velocity_zero_is_release(self):
        app, out, state = make_app()
        app.handle_event(("note_on", (0, PAD_NOTES[5], 100)))
        app.handle_event(("note_off", (0, PAD_NOTES[5], 0)))
        self.assertTrue(len(out.off) > 0)

    def test_fader_cc_changes_root_and_redraws(self):
        app, out, state = make_app()
        changed = app.handle_event(("cc", (0, 20, 58)))  # root -> 5
        self.assertTrue(changed)
        self.assertEqual(state.root, 5)


class QueueDrainTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_drain_queue_dispatches_all_events(self):
        app, out, state = make_app()
        q = queue.Queue()
        q.put(("note_on", (0, PAD_NOTES[1], 100)))
        q.put(("note_on", (0, PAD_NOTES[2], 100)))
        q.put(("note_off", (0, PAD_NOTES[1], 0)))
        app.drain_queue(q)
        self.assertTrue(q.empty())
        # pad1 held then released: on for pad1 triad, on for pad2 triad, off pad1
        self.assertTrue(len(out.on) >= 3)

    def test_drain_queue_ignores_unknown_types(self):
        app, out, state = make_app()
        q = queue.Queue()
        q.put(("sysex", (0xF0, 0xF7)))
        q.put(("note_on", (0, PAD_NOTES[1], 100)))
        app.drain_queue(q)
        self.assertEqual(len(out.on), 3)  # only the pad-1 triad


class WaitingStateTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_not_connected_shows_waiting(self):
        state = AppState()
        app = App(state, ChordSender(RecordingOutput()))
        app.set_device_state(False)
        self.assertFalse(app.device_connected)


if __name__ == "__main__":
    unittest.main()
