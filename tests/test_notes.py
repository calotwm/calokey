"""Tests for ``src.theory.notes`` — MIDI<->name mapping and root names."""

import unittest

from theory import notes


class RootNamesTests(unittest.TestCase):
    def test_all_twelve_root_names_with_sharps(self):
        expected = [
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B",
        ]
        for i, name in enumerate(expected):
            with self.subTest(root_index=i):
                self.assertEqual(notes.root_index_to_name(i), name)

    def test_invalid_root_index_raises(self):
        for bad in (-1, 12, 13):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    notes.root_index_to_name(bad)

    def test_non_int_root_index_raises(self):
        for bad in ("C", 1.5, None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    notes.root_index_to_name(bad)


class MidiNameMappingTests(unittest.TestCase):
    def test_middle_c(self):
        self.assertEqual(notes.midi_to_name(60), "C4")

    def test_sharp_name(self):
        self.assertEqual(notes.midi_to_name(61), "C#4")

    def test_boundary_zero_and_127(self):
        self.assertEqual(notes.midi_to_name(0), "C-1")
        self.assertEqual(notes.midi_to_name(127), "G9")

    def test_octave_wraps_at_c(self):
        # C (pitch 0) is the start of each octave.
        self.assertEqual(notes.midi_to_name(12), "C0")
        self.assertEqual(notes.midi_to_name(59), "B3")

    def test_invalid_midi_raises(self):
        for bad in (-1, 128):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    notes.midi_to_name(bad)

    def test_name_to_midi_round_trip(self):
        for midi in (0, 60, 61, 127):
            with self.subTest(midi=midi):
                self.assertEqual(notes.name_to_midi(notes.midi_to_name(midi)), midi)

    def test_name_to_midi_examples(self):
        self.assertEqual(notes.name_to_midi("C4"), 60)
        self.assertEqual(notes.name_to_midi("C#4"), 61)
        self.assertEqual(notes.name_to_midi("G9"), 127)

    def test_name_to_midi_invalid_raises(self):
        for bad in ("", "H4", "C", "4"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    notes.name_to_midi(bad)


if __name__ == "__main__":
    unittest.main()
