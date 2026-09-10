"""Tests for the post-verify fixes (tasks 9.1-9.4).

Covers runtime device-config discovery, dynamic CC/pad mapping in the app, and
live output-port rebinding. Uses a headless pygame (dummy video driver), fake
outputs, and mocked device/config modules so no hardware is required.
"""

import os
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import main  # noqa: E402
from midi import sysex  # noqa: E402
from midi.output import ChordSender  # noqa: E402
from state import AppState, DeviceConfig  # noqa: E402
from ui.app import App  # noqa: E402


class RecordingOutput:
    """Fake chord output that records note_on/note_off calls."""

    def __init__(self):
        self.on = []
        self.off = []

    def note_on(self, note, velocity, channel=0):
        self.on.append((note, velocity, channel))

    def note_off(self, note, velocity=0, channel=0):
        self.off.append((note, velocity, channel))


def make_app(device_config=None):
    state = AppState()
    out = RecordingOutput()
    app = App(state, ChordSender(out), device_config=device_config)
    app.set_device_state(True)
    return app, out, state


class DeviceConfigTests(unittest.TestCase):
    def test_defaults_match_factory_mapping(self):
        cfg = DeviceConfig.defaults()
        self.assertEqual(cfg.knob_ccs, [20, 21, 22, 23, 24, 25, 26, 27])
        self.assertEqual(cfg.pad_notes, [60, 62, 64, 65, 67, 69, 71, 72])

    def test_fader_for_cc_maps_knob1_and_knob2(self):
        cfg = DeviceConfig(knob_ccs=[30, 31, 32, 33, 34, 35, 36, 37])
        self.assertEqual(cfg.fader_for_cc(30), 0)  # knob 1 -> root
        self.assertEqual(cfg.fader_for_cc(31), 1)  # knob 2 -> scale type
        self.assertIsNone(cfg.fader_for_cc(32))    # knob 3 unmapped
        self.assertIsNone(cfg.fader_for_cc(20))    # unrelated CC

    def test_pad_for_note_uses_discovered_notes(self):
        cfg = DeviceConfig(pad_notes=[48, 50, 52, 53, 55, 57, 59, 60])
        self.assertEqual(cfg.pad_for_note(48), 1)
        self.assertEqual(cfg.pad_for_note(60), 8)
        self.assertIsNone(cfg.pad_for_note(62))


class ParseBulkDumpTests(unittest.TestCase):
    def test_parses_knob_and_pad_payload(self):
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02,
               30, 31, 32, 33, 34, 35, 36, 37,
               48, 50, 52, 53, 55, 57, 59, 60, 0xF7]
        cfg = sysex.parse_bulk_dump(msg)
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.knob_ccs, [30, 31, 32, 33, 34, 35, 36, 37])
        self.assertEqual(cfg.pad_notes, [48, 50, 52, 53, 55, 57, 59, 60])

    def test_scene_change_is_not_a_bulk_dump(self):
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 0x00, 0x00, 0x4F, 0x03, 0xF7]
        self.assertIsNone(sysex.parse_bulk_dump(msg))

    def test_wrong_prefix_returns_none(self):
        msg = [0xF0, 0x43, 0x40, 0x00, 0x01, 0x36, 0x02,
               30, 31, 32, 33, 34, 35, 36, 37,
               48, 50, 52, 53, 55, 57, 59, 60, 0xF7]
        self.assertIsNone(sysex.parse_bulk_dump(msg))

    def test_wrong_length_returns_none(self):
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02, 30, 31, 0xF7]
        self.assertIsNone(sysex.parse_bulk_dump(msg))


class AppDynamicMappingTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_cc_uses_discovered_knob_ccs(self):
        cfg = DeviceConfig(knob_ccs=[30, 31, 32, 33, 34, 35, 36, 37])
        app, out, state = make_app(device_config=cfg)
        changed = app.handle_event(("cc", (0, 30, 58)))  # knob 1 -> root 5
        self.assertTrue(changed)
        self.assertEqual(state.root, 5)
        # the factory default CC 20 is no longer a fader under this config
        self.assertFalse(app.handle_event(("cc", (0, 20, 58))))

    def test_note_uses_discovered_pad_notes(self):
        cfg = DeviceConfig(pad_notes=[48, 50, 52, 53, 55, 57, 59, 60])
        app, out, state = make_app(device_config=cfg)
        app.handle_event(("note_on", (0, 48, 100)))  # pad 1 (discovered note)
        self.assertEqual(out.on, [(n, 100, 0) for n in state.chord_notes(1)])
        # the factory default pad note 60 is no longer a pad under this config
        out.on.clear()
        app.handle_event(("note_on", (0, 60, 100)))
        self.assertEqual(out.on, [])

    def test_sysex_bulk_dump_updates_config(self):
        app, out, state = make_app()
        msg = [0xF0, 0x42, 0x40, 0x00, 0x01, 0x36, 0x02,
               30, 31, 32, 33, 34, 35, 36, 37,
               48, 50, 52, 53, 55, 57, 59, 60, 0xF7]
        self.assertTrue(app.handle_event(("sysex", tuple(msg))))
        self.assertEqual(app.device_config.knob_ccs, [30, 31, 32, 33, 34, 35, 36, 37])
        # the newly discovered CC now drives the root fader
        app.handle_event(("cc", (0, 30, 58)))
        self.assertEqual(state.root, 5)


class PortRebindingTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()

    def test_on_select_rebinds_sender_and_persists(self):
        class FakeMidiOutput:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        out_a = FakeMidiOutput()
        out_b = FakeMidiOutput()

        with mock.patch.object(main, "store") as store, \
                mock.patch.object(main, "device") as device:
            store.load_settings.return_value = (0, 0, None)  # first-ever run
            store.load_config.return_value = {"output_port": None}
            device.discover_nanokey.return_value = None
            device.list_output_ports.return_value = [(0, "Port A"), (1, "Port B")]
            device.open_output.side_effect = (
                lambda name: out_a if name == "Port A" else out_b
            )

            app, q, thread, sender = main.build_app()

            # fallback to first available port and wire on_select unconditionally
            self.assertIsInstance(app.sender, ChordSender)
            self.assertIs(app.sender._output, out_a)
            self.assertIsNotNone(app.port_selector.on_select)

            app.port_selector.on_select("Port B")

            self.assertIsInstance(app.sender, ChordSender)
            self.assertIs(app.sender._output, out_b)
            self.assertTrue(out_a.closed)
            self.assertFalse(out_b.closed)
            store.save_config.assert_called_once()
            self.assertEqual(store.save_config.call_args[0][0]["output_port"], "Port B")

    def test_request_device_config_sends_bulk_dump(self):
        class FakeMidiOutput:
            def __init__(self):
                self.closed = False

            def close(self):
                self.closed = True

        out = FakeMidiOutput()
        with mock.patch.object(main, "device") as device, \
                mock.patch.object(main, "sysex") as sysex_mod:
            device.open_nanokey_output.return_value = out
            req = sysex_mod.build_bulk_dump_request.return_value = (
                b"\xF0\x42\x40\x00\x01\x36\x01\xF7"
            )

            main._request_device_config()

            device.send_sysex.assert_called_once_with(out, req)
            self.assertTrue(out.closed)


if __name__ == "__main__":
    unittest.main()
