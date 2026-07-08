import pygame
from utils import clamp, lerp
from settings import COLORS


class ProgressBar:
    def __init__(self, rect, min_val=0, max_val=100, current=100,
                 fg_color=COLORS["GREEN"], bg_color=COLORS["DARK_GRAY"],
                 border_color=COLORS["WHITE"], label=""):
        self.rect = pygame.Rect(rect)
        self.min_val = min_val
        self.max_val = max_val
        self.current = current
        self.display = float(current)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border_color = border_color
        self.label = label
        self.font = pygame.font.Font(None, 18)
        self.animation_speed = 5.0

    def set_value(self, val):
        self.current = clamp(val, self.min_val, self.max_val)

    def update(self, dt):
        self.display = lerp(self.display, self.current, self.animation_speed * dt)
        if abs(self.display - self.current) < 0.5:
            self.display = float(self.current)

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=4)
        if self.max_val > self.min_val:
            ratio = (self.display - self.min_val) / (self.max_val - self.min_val)
            fill_w = int(self.rect.width * ratio)
            if fill_w > 0:
                fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
                pygame.draw.rect(surface, self.fg_color, fill_rect, border_radius=4)
        if self.border_color:
            pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=4)
        if self.label:
            text = self.font.render(f"{self.label} {int(self.current)}/{int(self.max_val)}",
                                   True, COLORS["WHITE"])
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)


class TextDisplay:
    def __init__(self, pos, text="", font_size=24, color=COLORS["WHITE"],
                 align="center", alpha=255):
        self.pos = pos
        self.text = text
        self.font_size = font_size
        self.color = color
        self.align = align
        self.alpha = alpha
        self.anim_offset = 0.0
        self.font = None

    def _get_font(self):
        if self.font is None or self.font.size(self.text)[0] == 0:
            self.font = pygame.font.Font(None, self.font_size)
        return self.font

    def update(self, dt):
        pass

    def draw(self, surface):
        font = self._get_font()
        text = font.render(self.text, True, self.color)
        text.set_alpha(max(0, min(255, self.alpha)))
        x, y = self.pos
        if self.align == "center":
            text_rect = text.get_rect(center=(x, y))
        elif self.align == "left":
            text_rect = text.get_rect(midleft=(x, y))
        elif self.align == "right":
            text_rect = text.get_rect(midright=(x, y))
        else:
            text_rect = text.get_rect(topleft=(x, y))
        surface.blit(text, text_rect)


class Slider:
    def __init__(self, rect, label="", min_val=0.0, max_val=1.0, current=0.5,
                 callback=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.current = current
        self.callback = callback
        self.dragging = False
        self.font = pygame.font.Font(None, 18)
        self.knob_color = COLORS["BLUE"]
        self.track_color = COLORS["DARK_GRAY"]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_from_pos(event.pos[0])

    def _update_from_pos(self, mx):
        rel = mx - self.rect.x
        ratio = clamp(rel / self.rect.width, 0.0, 1.0)
        self.current = self.min_val + ratio * (self.max_val - self.min_val)
        if self.callback:
            self.callback(self.current)

    def draw(self, surface):
        # Track
        pygame.draw.rect(surface, self.track_color, self.rect, border_radius=4)
        # Fill
        ratio = (self.current - self.min_val) / (self.max_val - self.min_val) if self.max_val > self.min_val else 0
        fill_w = int(self.rect.width * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.height)
            pygame.draw.rect(surface, self.knob_color, fill_rect, border_radius=4)
        # Knob
        kx = self.rect.x + fill_w
        ky = self.rect.centery
        pygame.draw.circle(surface, COLORS["WHITE"], (kx, ky), 8)
        # Label
        if self.label:
            txt = self.font.render(f"{self.label}: {self.current:.2f}", True, COLORS["WHITE"])
            surface.blit(txt, (self.rect.x, self.rect.y - 20))


class Panel:
    def __init__(self, rect, color=(0, 0, 0, 180), border_color=None):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.border_color = border_color

    def draw(self, surface):
        if len(self.color) == 4:
            bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            bg.fill(self.color)
            surface.blit(bg, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect, border_radius=8)
        if self.border_color:
            pygame.draw.rect(surface, self.border_color, self.rect, 2, border_radius=8)
