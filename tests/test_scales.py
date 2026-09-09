"""Tests for ``src.theory.scales`` — all 12 scale types at C root."""

import unittest

from theory import scales


# Expected ascending MIDI notes (root C at pitch class 0) per scale type.
# Interval tables are embedded here explicitly so any drift from the design is caught.
_C_IONIAN = [0, 2, 4, 5, 7, 9, 11]
_C_DORIAN = [0, 2, 3, 5, 7, 9, 10]
_C_PHRYGIAN = [0, 1, 3, 5, 7, 8, 10]
_C_LYDIAN = [0, 2, 4, 6, 7, 9, 11]
_C_MIXOLYDIAN = [0, 2, 4, 5, 7, 9, 10]
_C_AEOLIAN = [0, 2, 3, 5, 7, 8, 10]
_C_LOCRIAN = [0, 1, 3, 5, 6, 8, 10]
_C_HARMONIC_MINOR = [0, 2, 3, 5, 7, 8, 11]
_C_MELODIC_MINOR = [0, 2, 3, 5, 7, 9, 11]
_C_MAJOR_PENT = [0, 2, 4, 7, 9]
_C_MINOR_PENT = [0, 3, 5, 7, 10]
_C_BLUES = [0, 3, 5, 6, 7, 10]

_ALL_EXPECTED = [
    _C_IONIAN,
    _C_DORIAN,
    _C_PHRYGIAN,
    _C_LYDIAN,
    _C_MIXOLYDIAN,
    _C_AEOLIAN,
    _C_LOCRIAN,
    _C_HARMONIC_MINOR,
    _C_MELODIC_MINOR,
    _C_MAJOR_PENT,
    _C_MINOR_PENT,
    _C_BLUES,
]


class ScaleDerivationTests(unittest.TestCase):
    def test_twelve_scale_types_at_c(self):
        self.assertEqual(len(scales.SCALE_NAMES), 12)
        for type_index, expected in enumerate(_ALL_EXPECTED):
            with self.subTest(type_index=type_index):
                self.assertEqual(scales.scale_notes(0, type_index), expected)

    def test_heptatonic_scales_have_seven_notes(self):
        for type_index in range(7):
            with self.subTest(type_index=type_index):
                self.assertEqual(len(scales.scale_notes(0, type_index)), 7)

    def test_pentatonic_scales_have_five_notes(self):
        self.assertEqual(len(scales.scale_notes(0, 9)), 5)   # major pentatonic
        self.assertEqual(len(scales.scale_notes(0, 10)), 5)  # minor pentatonic

    def test_blues_scale_has_six_notes(self):
        self.assertEqual(len(scales.scale_notes(0, 11)), 6)

    def test_root_offsets_transpose(self):
        # D Dorian == C Dorian shifted up a whole step.
        self.assertEqual(scales.scale_notes(2, 1), [n + 2 for n in _C_DORIAN])

    def test_invalid_root_index_raises(self):
        with self.assertRaises(ValueError):
            scales.scale_notes(12, 0)

    def test_invalid_type_index_raises(self):
        with self.assertRaises(ValueError):
            scales.scale_notes(0, 12)


if __name__ == "__main__":
    unittest.main()
