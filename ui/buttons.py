import pygame
from settings import COLORS, SCREEN_WIDTH


class Button:
    def __init__(self, rect, text, callback=None, color=COLORS["DARK_BLUE"],
                 hover_color=COLORS["BLUE"], text_color=COLORS["WHITE"],
                 border_color=None, font_size=24):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.border_color = border_color
        self.font_size = font_size
        self.hovered = False
        self.visible = True
        self.active = True
        self.animation = 0.0
        self.font = None

    def _get_font(self):
        if self.font is None:
            self.font = pygame.font.Font(None, self.font_size)
        return self.font

    def handle_event(self, event):
        if not self.visible or not self.active:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.callback:
                self.callback()
                return True
        return False

    def update(self, dt):
        self.animation += dt * 2

    def draw(self, surface):
        if not self.visible:
            return
        color = self.hover_color if self.hovered else self.color
        if not self.active:
            color = tuple(c // 2 for c in color)
        rect = self.rect
        # Shadow
        pygame.draw.rect(surface, (0, 0, 0, 80), rect.move(2, 2), border_radius=6)
        # Body
        pygame.draw.rect(surface, color, rect, border_radius=6)
        if self.border_color:
            pygame.draw.rect(surface, self.border_color, rect, 2, border_radius=6)
        # Highlight
        if self.hovered:
            highlight = pygame.Surface((rect.width, rect.height // 2), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 20))
            surface.blit(highlight, rect.topleft)
        # Text
        font = self._get_font()
        text = font.render(self.text, True, self.text_color)
        text_rect = text.get_rect(center=rect.center)
        surface.blit(text, text_rect)


class ToggleButton(Button):
    def __init__(self, rect, text, getter, setter, color=COLORS["DARK_BLUE"],
                 hover_color=COLORS["BLUE"], text_color=COLORS["WHITE"]):
        super().__init__(rect, text, self._toggle, color, hover_color, text_color)
        self.getter = getter
        self.setter = setter

    def _toggle(self):
        self.setter(not self.getter())

    def draw(self, surface):
        val = self.getter()
        self.text_color = COLORS["GREEN"] if val else COLORS["RED"]
        state = "ON" if val else "OFF"
        display_text = f"{self.text}: {state}"
        original = self.text
        self.text = display_text
        super().draw(surface)
        self.text = original
