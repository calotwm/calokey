"""CaloKey entry point.

Wires device discovery, the input thread, application state, the chord sender,
and the pygame UI into a single loop. Re-scans for the nanoKEY on a 1-second
timer while it is absent, showing a "waiting for device" state.
"""

import queue
import time

from config import store
from midi import device
from midi.input_thread import InputThread
from midi.output import ChordSender
from state import AppState
from ui.app import App

RESCAN_INTERVAL = 1.0  # seconds between port re-scans while device absent


def _remembered_port_name() -> str | None:
    return store.load_settings()[2]


def build_app(config_path=None) -> tuple[App, queue.Queue, InputThread | None, ChordSender | None]:
    """Construct the app plus its runtime objects for the current hardware.

    Returns ``(app, queue, input_thread, sender)``. ``input_thread`` and
    ``sender`` are ``None`` when no device/output is yet available.
    """
    root, scale_type, output_name = store.load_settings(config_path)
    state = AppState(root=root, scale_type=scale_type)
    sender = None
    if output_name:
        output = device.open_output(output_name)
        if output is not None:
            sender = ChordSender(output)

    q = queue.Queue()
    thread = None
    device_id = device.discover_nanokey()
    if device_id is not None:
        midi_input = device.open_input(device_id)
        thread = InputThread(midi_input, q)

    app = App(state, sender or _NullSender())
    if output_name:
        names = [name for _, name in device.list_output_ports()]
        app.port_selector.set_ports(names, output_name)
        app.port_selector.on_select = _save_port_selection
    app.set_device_state(device_id is not None)
    return app, q, thread, sender


def _save_port_selection(name: str | None) -> None:
    if name is None:
        return
    cfg = store.load_config()
    cfg["output_port"] = name
    store.save_config(cfg)


class _NullSender:
    """Drop-in no-op sender used before an output port exists."""

    def send_chord(self, notes, velocity=100, channel=None):
        pass

    def release_chord(self, notes, channel=None):
        pass


def main() -> None:
    """Run the application until the window is closed."""
    app, q, thread, _ = build_app()
    if thread is not None:
        thread.start()
    last_rescan = time.monotonic()

    try:
        while app.running:
            app.process_pygame_events()
            app.drain_queue(q)
            if not app.device_connected and time.monotonic() - last_rescan >= RESCAN_INTERVAL:
                last_rescan = time.monotonic()
                device_id = device.discover_nanokey()
                if device_id is not None:
                    midi_input = device.open_input(device_id)
                    thread = InputThread(midi_input, q)
                    thread.start()
                    app.set_device_state(True)
            app.draw()
    finally:
        if thread is not None:
            thread.stop()
            thread.join(timeout=1)
        app.shutdown()


if __name__ == "__main__":
    main()
