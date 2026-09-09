"""Pygame application: main render loop and event dispatch.

Owns the pygame window, drains the MIDI input queue each frame, dispatches
events to ``AppState`` and the chord sender, and redraws the keyboard, chord
display, and port selector. Device discovery/reconnection is driven by the
caller via ``set_device_state``.
"""

import pygame

from midi.input_thread import parse_event
from state import FADER_ROOT, FADER_TYPE
from ui.chord_display import ChordDisplay
from ui.keyboard import Keyboard
from ui.port_selector import PortSelector

FPS = 60
BACKGROUND = (30, 30, 40)
WAITING_COLOR = (220, 220, 220)

# Default nanoKEY Studio pad note numbers (pads 1..8). Runtime discovery
# (slice 4 concern) refines these from live traffic; this is the best-effort
# default mapping until the device's actual note set is observed.
DEFAULT_PAD_NOTES = (60, 62, 64, 65, 67, 69, 71, 72)


class App:
    """Renders the app and routes MIDI events to state + output."""

    def __init__(self, state, sender, width: int = 960, height: int = 540):
        pygame.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode((width, height))
        pygame.display.set_caption("CaloKey")

        self.state = state
        self.sender = sender
        self.running = True
        self.device_connected = False
        self.pad_notes = list(DEFAULT_PAD_NOTES)  # pad 1..8 note numbers

        font = pygame.font.Font(None, 36)
        self.keyboard = Keyboard(0, 127, 20, 300, width - 40, 200)
        self.chord_display = ChordDisplay(20, 40, pygame.font.Font(None, 48))
        self.port_selector = PortSelector(20, 120, width - 40, font)
        self._pending_sounding_pad = None  # pad whose chord is currently held

        self.keyboard.set_scale_notes(self.state.scale_notes())

    # -- device / state wiring -----------------------------------------

    def set_device_state(self, connected: bool) -> None:
        self.device_connected = connected

    # -- MIDI event dispatch -------------------------------------------

    def handle_event(self, event: tuple) -> bool:
        """Handle one parsed queue event; return True if a redraw is needed."""
        kind, data = event
        if kind == "cc":
            _, control, value = data
            if control == 20:
                changed = self.state.apply_fader_cc(FADER_ROOT, value)
            elif control == 21:
                changed = self.state.apply_fader_cc(FADER_TYPE, value)
            else:
                return False
            if changed:
                self.keyboard.set_scale_notes(self.state.scale_notes())
            return changed
        if kind == "note_on":
            _, note, velocity = data
            pad = self._note_to_pad(note)
            if pad == 8:
                self.state.set_pad8_held(True)
                self._refresh_chord_display()
                return True
            if pad is not None and 1 <= pad <= 7:
                self._sound_pad(pad)
                return True
            return False
        if kind == "note_off":
            _, note, velocity = data
            pad = self._note_to_pad(note)
            if pad == 8:
                self.state.set_pad8_held(False)
                self._refresh_chord_display()
                return True
            if pad is not None and 1 <= pad <= 7:
                self._release_pad(pad)
                return True
            return False
        return False  # "sysex" and unknown: no redraw

    def _note_to_pad(self, note: int) -> int | None:
        """Map an incoming MIDI note to a nanoKEY pad number (1-8).

        Looks up the note in the configured pad-note set; returns ``None`` for
        notes not belonging to a pad (e.g. keyboard keys).
        """
        try:
            return self.pad_notes.index(note) + 1
        except ValueError:
            return None

    def _sound_pad(self, pad: int) -> None:
        try:
            notes = self.state.chord_notes(pad)
        except ValueError:
            self._refresh_chord_display()
            return
        self.sender.send_chord(notes)
        self._pending_sounding_pad = pad
        self.keyboard.set_pressed_notes(notes)
        self.chord_display.set_chord(self.state.chord_name(pad), notes)

    def _release_pad(self, pad: int) -> None:
        if self._pending_sounding_pad != pad:
            if self._pending_sounding_pad is None:
                self._refresh_chord_display()
            return
        try:
            notes = self.state.chord_notes(pad)
        except ValueError:
            notes = []
        if notes:
            self.sender.release_chord(notes)
        self._pending_sounding_pad = None
        self.keyboard.set_pressed_notes([])
        self._refresh_chord_display()

    def _refresh_chord_display(self) -> None:
        pad = self._pending_sounding_pad
        if pad is None:
            self.chord_display.clear()
        else:
            try:
                notes = self.state.chord_notes(pad)
            except ValueError:
                self.chord_display.clear()
                return
            self.chord_display.set_chord(self.state.chord_name(pad), notes)

    # -- main loop ------------------------------------------------------

    def drain_queue(self, queue) -> None:
        """Pull all queued MIDI events and dispatch them."""
        while not queue.empty():
            event = queue.get_nowait()
            if not isinstance(event, tuple):
                continue
            self.handle_event(event)

    def process_pygame_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.port_selector.handle_click(event.pos)

    def draw(self) -> None:
        self.surface.fill(BACKGROUND)
        if not self.device_connected:
            font = pygame.font.Font(None, 36)
            msg = font.render("Waiting for device…", True, WAITING_COLOR)
            self.surface.blit(msg, (20, 40))
            self.keyboard.draw(self.surface)
        else:
            self.keyboard.draw(self.surface)
            self.chord_display.draw(self.surface)
            self.port_selector.draw(self.surface)
        pygame.display.flip()

    def shutdown(self) -> None:
        pygame.quit()

    def run_loop(self, queue) -> None:
        """Blocking main loop: dispatch, draw, and clock at ``FPS``."""
        clock = pygame.time.Clock()
        while self.running:
            self.process_pygame_events()
            self.drain_queue(queue)
            self.draw()
            clock.tick(FPS)
        self.shutdown()
