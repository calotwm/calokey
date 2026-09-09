"""Tests for ``src.state`` — fader mapping, hysteresis, and the pad-8 modifier."""

import unittest

from state import AppState, cc_to_position


class CCToPositionTests(unittest.TestCase):
    def test_extremes(self):
        self.assertEqual(cc_to_position(0), 0)
        self.assertEqual(cc_to_position(127), 11)

    def test_every_position_reachable(self):
        positions = {cc_to_position(cc) for cc in range(128)}
        self.assertEqual(positions, set(range(12)))

    def test_invalid_cc_raises(self):
        for bad in (-1, 128, 1.5, "50", None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    cc_to_position(bad)


class FaderMappingTests(unittest.TestCase):
    def test_fader_root_changes_root(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 58))  # 58*11/127 -> 5
        self.assertEqual(state.root, 5)

    def test_fader_type_changes_scale_type(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(1, 58))
        self.assertEqual(state.scale_type, 5)

    def test_fader_root_does_not_change_type(self):
        state = AppState()
        state.apply_fader_cc(0, 58)
        self.assertEqual(state.scale_type, 0)

    def test_returns_true_only_on_change(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 58))
        self.assertFalse(state.apply_fader_cc(0, 58))

    def test_unknown_fader_raises(self):
        state = AppState()
        with self.assertRaises(ValueError):
            state.apply_fader_cc(2, 50)


class HysteresisTests(unittest.TestCase):
    def test_jitter_does_not_change(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 10))  # settle at position 1
        self.assertEqual(state.root, 1)
        # ±1 CC jitter around the 1<->2 boundary (at cc ~17.32) stays put.
        state.apply_fader_cc(0, 17)
        state.apply_fader_cc(0, 18)
        state.apply_fader_cc(0, 19)
        self.assertEqual(state.root, 1)

    def test_clear_move_commits_once(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 10))  # -> 1
        self.assertEqual(state.root, 1)
        self.assertTrue(state.apply_fader_cc(0, 20))  # -> 2
        self.assertEqual(state.root, 2)
        # Settling within position 2 does not re-commit.
        self.assertFalse(state.apply_fader_cc(0, 21))
        self.assertFalse(state.apply_fader_cc(0, 22))

    def test_dead_zone_requires_two_cc_past_boundary(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 10))  # root=1
        # boundary 1<->2 at cc ~17.32; +2 dead zone means cc >= ~19.32.
        self.assertFalse(state.apply_fader_cc(0, 19))
        self.assertTrue(state.apply_fader_cc(0, 20))
        self.assertEqual(state.root, 2)

    def test_downward_move_symmetry(self):
        state = AppState()
        state.apply_fader_cc(0, 20)  # -> 2
        self.assertEqual(state.root, 2)
        # boundary 2<->1 at ~17.32; -2 dead zone means cc <= ~15.32.
        self.assertFalse(state.apply_fader_cc(0, 16))
        self.assertTrue(state.apply_fader_cc(0, 15))
        self.assertEqual(state.root, 1)

    def test_large_jump_commits_once_to_final_position(self):
        state = AppState()
        self.assertTrue(state.apply_fader_cc(0, 100))  # 100*11/127 -> 9
        self.assertEqual(state.root, 9)


class Pad8ModifierTests(unittest.TestCase):
    def setUp(self):
        self.state = AppState(root=0, scale_type=0)  # C Ionian

    def test_triad_by_default(self):
        self.assertFalse(self.state.pad8_held)
        self.assertEqual(len(self.state.chord_notes(1)), 3)

    def test_seventh_when_held(self):
        self.state.set_pad8_held(True)
        self.assertTrue(self.state.pad8_held)
        self.assertEqual(self.state.chord_notes(1), [0, 4, 7, 11])

    def test_restore_triad_on_release(self):
        self.state.set_pad8_held(True)
        self.state.set_pad8_held(False)
        self.assertFalse(self.state.pad8_held)
        self.assertEqual(len(self.state.chord_notes(1)), 3)

    def test_pads_inactive_for_pentatonic(self):
        state = AppState(root=0, scale_type=9)  # major pentatonic (5 notes)
        for pad in (6, 7):
            with self.subTest(pad=pad):
                with self.assertRaises(ValueError):
                    state.chord_notes(pad)


class ChordNameTests(unittest.TestCase):
    def test_chord_names_c_major(self):
        state = AppState(root=0, scale_type=0)
        self.assertEqual(state.chord_name(1), "C")
        self.assertEqual(state.chord_name(2), "Dm")
        self.assertEqual(state.chord_name(7), "Bdim")


class InitValidationTests(unittest.TestCase):
    def test_invalid_root_raises(self):
        with self.assertRaises(ValueError):
            AppState(root=12)

    def test_invalid_scale_type_raises(self):
        with self.assertRaises(ValueError):
            AppState(scale_type=-1)

    def test_defaults(self):
        state = AppState()
        self.assertEqual(state.root, 0)
        self.assertEqual(state.scale_type, 0)


if __name__ == "__main__":
    unittest.main()
