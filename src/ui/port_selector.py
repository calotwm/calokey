"""MIDI output-port selector UI.

Shows the available output ports and returns the selected name. Selection
logic is pure and testable; persistence is delegated to a callback so the
widget stays free of filesystem knowledge.
"""

import pygame

WHITE = (255, 255, 255)
SELECTED_BG = (60, 120, 220)
NORMAL_BG = (40, 40, 40)
ITEM_HEIGHT = 28
PADDING_X = 12


class PortSelector:
    """A simple vertical list of output ports; one is selected."""

    def __init__(self, x: int, y: int, width: int, font=None):
        self.x, self.y, self.width = x, y, width
        self.font = font or pygame.font.Font(None, 28)
        self.ports = []          # list of str names, in order
        self.selected_index = 0
        self.on_select = None    # callback(name) on change

    def set_ports(self, port_names: list[str], current: str | None = None) -> None:
        """Refresh the list; keep ``current`` selected if present, else index 0."""
        self.ports = list(port_names)
        if not self.ports:
            self.selected_index = 0
            return
        if current is not None and current in self.ports:
            self.selected_index = self.ports.index(current)
        else:
            self.selected_index = 0

    def selected_name(self) -> str | None:
        """Return the selected port name, or None if the list is empty."""
        if not self.ports:
            return None
        return self.ports[self.selected_index]

    def move_selection(self, delta: int) -> None:
        """Move the selection up/down, wrapping within the list."""
        if not self.ports:
            return
        self.selected_index = (self.selected_index + delta) % len(self.ports)

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Select the item under ``pos``; return True if a port was clicked."""
        if not (self.x <= pos[0] <= self.x + self.width):
            return False
        rel_y = pos[1] - self.y
        if rel_y < 0 or rel_y >= len(self.ports) * ITEM_HEIGHT:
            return False
        idx = rel_y // ITEM_HEIGHT
        if idx != self.selected_index:
            self.selected_index = idx
            if self.on_select is not None:
                self.on_select(self.selected_name())
        return True

    def draw(self, surface: pygame.Surface) -> None:
        for i, name in enumerate(self.ports):
            rect = pygame.Rect(self.x, self.y + i * ITEM_HEIGHT, self.width, ITEM_HEIGHT - 2)
            color = SELECTED_BG if i == self.selected_index else NORMAL_BG
            pygame.draw.rect(surface, color, rect)
            rendered = self.font.render(name, True, WHITE)
            surface.blit(rendered, (rect.x + PADDING_X, rect.y + 4))
