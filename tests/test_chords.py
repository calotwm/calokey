"""Tests for ``src.theory.chords`` — triads, sevenths, naming, pads-inactive."""

import unittest

from theory import chords, scales


class TriadTests(unittest.TestCase):
    def setUp(self):
        self.c_major = scales.scale_notes(0, 0)  # C Ionian (major)

    def test_ionian_triads(self):
        # I, ii, iii, IV, V, vi, vii° spelled in scale-relative terms.
        self.assertEqual(chords.triad(self.c_major, 1), [0, 4, 7])   # C major
        self.assertEqual(chords.triad(self.c_major, 2), [2, 5, 9])   # D minor
        self.assertEqual(chords.triad(self.c_major, 7), [11, 2, 5])  # B diminished (wrapped)

    def test_triad_quality(self):
        self.assertEqual(chords.chord_quality(self.c_major, 1), "major")
        self.assertEqual(chords.chord_quality(self.c_major, 2), "minor")
        self.assertEqual(chords.chord_quality(self.c_major, 3), "minor")
        self.assertEqual(chords.chord_quality(self.c_major, 7), "diminished")

    def test_wrap_degree_1_and_7(self):
        # Degree 1 stacks 1-3-5; degree 7 wraps to 7-2-4 within the 7 notes.
        self.assertEqual(chords.triad(self.c_major, 1), [0, 4, 7])
        self.assertEqual(len(chords.triad(self.c_major, 1)), 3)


class SeventhTests(unittest.TestCase):
    def setUp(self):
        self.c_major = scales.scale_notes(0, 0)

    def test_seventh_adds_fourth_note(self):
        # I seventh = 1-3-5-7.
        self.assertEqual(chords.seventh(self.c_major, 1), [0, 4, 7, 11])
        # V seventh = 5-7-2-4 (wrapped).
        self.assertEqual(chords.seventh(self.c_major, 5), [7, 11, 2, 5])

    def test_seventh_is_four_notes(self):
        for degree in range(1, 8):
            with self.subTest(degree=degree):
                self.assertEqual(len(chords.seventh(self.c_major, degree)), 4)


class ChordNameTests(unittest.TestCase):
    def setUp(self):
        self.c_major = scales.scale_notes(0, 0)
        self.root_names = {
            1: "C", 2: "D", 3: "E", 4: "F", 5: "G", 6: "A", 7: "B",
        }

    def test_names_major_minor_diminished(self):
        self.assertEqual(chords.chord_name(self.c_major, 1, self.root_names[1]), "C")
        self.assertEqual(chords.chord_name(self.c_major, 2, self.root_names[2]), "Dm")
        self.assertEqual(chords.chord_name(self.c_major, 7, self.root_names[7]), "Bdim")


class PadsInactiveTests(unittest.TestCase):
    """Pads 6-7 are INACTIVE for <7-note scales (pentatonic, blues)."""

    def test_seventh_raises_for_pentatonic(self):
        for type_index in (9, 10):  # major/minor pentatonic
            with self.subTest(type_index=type_index):
                notes = scales.scale_notes(0, type_index)
                self.assertEqual(len(notes), 5)
                with self.assertRaises(ValueError):
                    chords.seventh(notes, 1)

    def test_seventh_raises_for_blues(self):
        notes = scales.scale_notes(0, 11)
        self.assertEqual(len(notes), 6)
        with self.assertRaises(ValueError):
            chords.seventh(notes, 1)

    def test_degree_out_of_range_for_pentatonic(self):
        notes = scales.scale_notes(0, 9)  # major pentatonic, 5 notes
        with self.assertRaises(ValueError):
            chords.triad(notes, 6)  # degree 6 does not exist

    def test_triad_valid_on_pentatonic_degrees(self):
        notes = scales.scale_notes(0, 9)
        for degree in range(1, 6):
            with self.subTest(degree=degree):
                self.assertEqual(len(chords.triad(notes, degree)), 3)


if __name__ == "__main__":
    unittest.main()
