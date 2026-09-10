"""CaloKey entry point.

Wires device discovery, the input thread, application state, the chord sender,
and the pygame UI into a single loop. Re-scans for the nanoKEY on a 1-second
timer while it is absent, showing a "waiting for device" state. On device
connect it requests the device's actual knob/pad config via SysEx bulk dump and
rebinds the chord output live when the user picks a different port.
"""

import queue
import time

from config import store
from midi import device, sysex
from midi.input_thread import InputThread
from midi.output import ChordSender
from state import AppState
from ui.app import App

RESCAN_INTERVAL = 1.0  # seconds between port re-scans while device absent


def _remembered_port_name() -> str | None:
    return store.load_settings()[2]


def _request_device_config() -> None:
    """Send a bulk-dump inquiry to the connected nanoKEY (best-effort, 9.1).

    The reply arrives back on the input thread as a ``sysex`` event and is parsed
    by ``App._handle_sysex``. If the device does not answer (the exact request
    bytes are only partially documented), the app keeps its default config.
    """
    output = device.open_nanokey_output()
    if output is None:
        return
    try:
        device.send_sysex(output, sysex.build_bulk_dump_request())
    finally:
        output.close()


def _initial_output(output_name: str | None):
    """Resolve the initial output port: remembered name, else first available.

    Returns ``(active_name, output)`` where ``output`` is a ``pygame.midi.Output``
    or ``None`` when no output ports exist.
    """
    names = [name for _, name in device.list_output_ports()]
    if not names:
        return None, None
    target = output_name if output_name in names else names[0]
    return target, device.open_output(target)


def build_app(config_path=None) -> tuple[App, queue.Queue, InputThread | None, ChordSender | None]:
    """Construct the app plus its runtime objects for the current hardware.

    Returns ``(app, queue, input_thread, sender)``. ``input_thread`` and
    ``sender`` are ``None`` when no device/output is yet available.
    """
    root, scale_type, output_name = store.load_settings(config_path)
    state = AppState(root=root, scale_type=scale_type)

    q = queue.Queue()
    thread = None
    device_id = device.discover_nanokey()
    if device_id is not None:
        midi_input = device.open_input(device_id)
        if midi_input is not None:
            thread = InputThread(midi_input, q)
            _request_device_config()  # 9.1: read actual config on connect

    active_name, current_output = _initial_output(output_name)
    sender = ChordSender(current_output) if current_output is not None else None

    app = App(state, sender or _NullSender())

    def on_select(name: str | None) -> None:
        """Rebind the chord output live and persist the choice (9.3)."""
        nonlocal sender, current_output
        if name is None:
            return
        new_output = device.open_output(name)
        if new_output is None:
            return
        new_sender = ChordSender(new_output)
        if current_output is not None:
            current_output.close()
        current_output = new_output
        sender = new_sender
        app.sender = new_sender
        _save_port_selection(name)

    names = [name for _, name in device.list_output_ports()]
    app.port_selector.set_ports(names, active_name)
    app.port_selector.on_select = on_select  # pyright: ignore[reportAttributeAccessIssue]

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
                    if midi_input is not None:
                        thread = InputThread(midi_input, q)
                        thread.start()
                        app.set_device_state(True)
                        _request_device_config()  # 9.1: read config on (re)connect
            app.draw()
    finally:
        if thread is not None:
            thread.stop()
            thread.join(timeout=1)
        app.shutdown()


if __name__ == "__main__":
    main()
