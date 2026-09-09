"""Tests for the pygame UI widgets (keyboard geometry, chord display, port selector).

The video driver is forced to ``dummy`` so these tests run headless. Logic
(highlighting, label formatting, selection) is asserted without a real display;
rendering is exercised once to catch Surface/layout errors.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from theory import notes  # noqa: E402
from ui.chord_display import ChordDisplay, chord_label  # noqa: E402
from ui.keyboard import Keyboard  # noqa: E402
from ui.port_selector import PortSelector  # noqa: E402


class KeyboardGeometryTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.surface = pygame.Surface((960, 540))

    def test_octave_normalization_white_key_count(self):
        # 0..24 normalizes to whole octaves C0..B2 (3 octaves = 21 white keys)
        kb = Keyboard(0, 24, 0, 0, 700, 200)
        self.assertEqual(len(kb.white_keys), 21)

    def test_black_key_count_per_octave(self):
        # 0..12 normalizes to C0..B1 (2 octaves = 10 black keys)
        kb = Keyboard(0, 12, 0, 0, 700, 200)
        self.assertEqual(len(kb.black_keys), 10)

    def test_highlight_tracks_pitch_class(self):
        kb = Keyboard(0, 12, 0, 0, 700, 200)
        kb.set_scale_notes([0, 4, 7])  # C E G
        self.assertEqual(kb.highlighted, {0, 4, 7})

    def test_pressed_notes_follow_chord(self):
        kb = Keyboard(0, 12, 0, 0, 700, 200)
        kb.set_pressed_notes([0, 4, 7])
        self.assertEqual(kb.pressed, {0, 4, 7})

    def test_draw_produces_pixels(self):
        kb = Keyboard(0, 24, 0, 0, 700, 200)
        kb.set_scale_notes([0, 2, 4, 5, 7, 9, 11])
        kb.set_pressed_notes([0, 4, 7])
        kb.draw(self.surface)  # must not raise


class ChordLabelTests(unittest.TestCase):
    def test_label_format(self):
        self.assertEqual(chord_label("C", [60, 64, 67]), "C — C4 E4 G4")

    def test_label_uses_note_names(self):
        self.assertEqual(chord_label("Dm", [62, 65, 69]), "Dm — D4 F4 A4")


class ChordDisplayTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.surface = pygame.Surface((400, 100))

    def test_set_and_clear(self):
        cd = ChordDisplay(0, 0)
        cd.set_chord("C", [60, 64, 67])
        self.assertEqual(cd.current_label, "C — C4 E4 G4")
        cd.clear()
        self.assertEqual(cd.current_label, "")
        cd.draw(self.surface)  # must not raise


class PortSelectorTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_empty_list_has_no_selection(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports([])
        self.assertIsNone(ps.selected_name())

    def test_selects_defaults_to_first(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B", "C"])
        self.assertEqual(ps.selected_name(), "A")

    def test_keeps_current_if_present(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B", "C"], current="B")
        self.assertEqual(ps.selected_name(), "B")

    def test_current_missing_falls_back_to_first(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B"], current="ZZZ")
        self.assertEqual(ps.selected_name(), "A")

    def test_move_selection_wraps(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B", "C"])
        ps.move_selection(1)
        self.assertEqual(ps.selected_name(), "B")
        ps.move_selection(1)
        ps.move_selection(1)
        self.assertEqual(ps.selected_name(), "A")

    def test_click_selects_item_and_fires_callback(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B", "C"])
        calls = []
        ps.on_select = calls.append
        hit = ps.handle_click((10, 28 + 14))  # second item
        self.assertTrue(hit)
        self.assertEqual(ps.selected_name(), "B")
        self.assertEqual(calls, ["B"])

    def test_click_outside_list_returns_false(self):
        ps = PortSelector(0, 0, 300)
        ps.set_ports(["A", "B", "C"])
        self.assertFalse(ps.handle_click((999, 10)))
        self.assertFalse(ps.handle_click((10, -5)))


class NoteNameReferenceTests(unittest.TestCase):
    """Guard the note-name helper the chord display relies on."""

    def test_midi_to_name_octave(self):
        self.assertEqual(notes.midi_to_name(60), "C4")
        self.assertEqual(notes.midi_to_name(61), "C#4")


if __name__ == "__main__":
    unittest.main()
