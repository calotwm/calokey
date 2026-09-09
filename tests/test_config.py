"""Tests for ``src.config.store`` — JSON load/save and fallback behavior."""

import json
import tempfile
import unittest
from pathlib import Path

from config import store


class SaveLoadTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "config.json"

    def test_round_trip(self):
        cfg = {"output_port": "My Synth", "root": 5, "scale_type": 7}
        store.save_config(cfg, self.path)
        self.assertEqual(store.load_config(self.path), cfg)

    def test_missing_file_returns_defaults(self):
        self.assertEqual(store.load_config(self.path), store.DEFAULT_CONFIG)

    def test_corrupt_file_returns_defaults(self):
        self.path.write_text("{not valid json", encoding="utf-8")
        self.assertEqual(store.load_config(self.path), store.DEFAULT_CONFIG)

    def test_partial_config_fills_defaults(self):
        self.path.write_text(json.dumps({"root": 3}), encoding="utf-8")
        cfg = store.load_config(self.path)
        self.assertEqual(cfg["root"], 3)
        self.assertIsNone(cfg["output_port"])
        self.assertEqual(cfg["scale_type"], 0)

    def test_save_creates_parent_directory(self):
        nested = Path(self._tmp.name) / "sub" / "dir" / "config.json"
        store.save_config({"root": 1}, nested)
        self.assertTrue(nested.exists())


class LoadSettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "config.json"

    def test_defaults_when_missing(self):
        self.assertEqual(store.load_settings(self.path), (0, 0, None))

    def test_loads_saved_values(self):
        store.save_config({"root": 6, "scale_type": 4, "output_port": "DAW"}, self.path)
        self.assertEqual(store.load_settings(self.path), (6, 4, "DAW"))

    def test_out_of_range_indices_fall_back(self):
        store.save_config({"root": 99, "scale_type": -3, "output_port": "X"}, self.path)
        self.assertEqual(store.load_settings(self.path), (0, 0, "X"))

    def test_non_int_indices_fall_back(self):
        store.save_config({"root": "C", "scale_type": 3.5}, self.path)
        self.assertEqual(store.load_settings(self.path), (0, 0, None))


if __name__ == "__main__":
    unittest.main()
