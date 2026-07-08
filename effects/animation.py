import pygame
import math
from utils import clamp, lerp, ease_out_cubic


class Animation:
    def __init__(self, frames, loop=True, speed=1.0):
        self.frames = frames
        self.loop = loop
        self.speed = speed
        self.index = 0.0
        self.playing = True
        self.finished = False

    def update(self, dt):
        if not self.playing or self.finished:
            return
        self.index += self.speed * dt * 60
        total = len(self.frames)
        if self.index >= total:
            if self.loop:
                self.index %= total
            else:
                self.index = total - 1
                self.finished = True

    def current_frame(self):
        return self.frames[int(self.index) % len(self.frames)]

    def reset(self):
        self.index = 0.0
        self.finished = False
        self.playing = True

    def copy(self):
        a = Animation(self.frames, self.loop, self.speed)
        a.index = self.index
        a.playing = self.playing
        a.finished = self.finished
        return a


class Tween:
    def __init__(self, start, end, duration, easing=ease_out_cubic):
        self.start = start
        self.end = end
        self.duration = duration
        self.easing = easing
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt):
        if self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.finished = True

    def value(self):
        t = self.easing(self.elapsed / self.duration) if self.duration > 0 else 1.0
        return lerp(self.start, self.end, t)

    def reset(self):
        self.elapsed = 0.0
        self.finished = False


class SpriteAnimation:
    def __init__(self, width, height, frame_count, frames_per_row=1, loop=True, speed=1.0):
        self.frame_w = width
        self.frame_h = height
        self.frame_count = frame_count
        self.frames_per_row = frames_per_row
        self.loop = loop
        self.speed = speed
        self.index = 0.0
        self.playing = True
        self.finished = False
        self.sheet = None

    def load_sheet(self, path):
        self.sheet = pygame.image.load(path).convert_alpha()

    def set_surface(self, surface):
        self.sheet = surface

    def update(self, dt):
        if not self.playing or self.finished:
            return
        self.index += self.speed * dt * 60
        total = self.frame_count
        if self.index >= total:
            if self.loop:
                self.index %= total
            else:
                self.index = total - 1
                self.finished = True

    def current_frame_rect(self):
        idx = int(self.index) % self.frame_count
        x = (idx % self.frames_per_row) * self.frame_w
        y = (idx // self.frames_per_row) * self.frame_h
        return pygame.Rect(x, y, self.frame_w, self.frame_h)

    def draw(self, surface, dest):
        if self.sheet is None:
            return
        rect = self.current_frame_rect()
        surface.blit(self.sheet, dest, rect)

    def copy(self):
        a = SpriteAnimation(self.frame_w, self.frame_h, self.frame_count,
                            self.frames_per_row, self.loop, self.speed)
        a.sheet = self.sheet
        a.index = self.index
        a.playing = self.playing
        a.finished = self.finished
        return a
