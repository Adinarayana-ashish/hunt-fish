import pygame
import math
import struct
from io import BytesIO

SAMPLE_RATE = 22050
BITS_PER_SAMPLE = 16


def _generate_wave(frequency, duration, volume=0.5, wave_type="sine"):
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    max_amp = int(32767 * volume)
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        if wave_type == "sine":
            val = math.sin(2 * math.pi * frequency * t)
        elif wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * frequency * t) >= 0 else -1.0
        elif wave_type == "noise":
            val = (hash((i, int(frequency))) % 200 - 100) / 100.0
        elif wave_type == "sweep":
            freq = frequency + (200 * t / duration)
            val = math.sin(2 * math.pi * freq * t)
        else:
            val = math.sin(2 * math.pi * frequency * t)
        # envelope
        envelope = min(1.0, t * 30, (duration - t) * 30)
        samples.append(int(val * max_amp * envelope))
    return samples


def _samples_to_sound(samples):
    buf = BytesIO()
    for s in samples:
        buf.write(struct.pack("<h", max(-32768, min(32767, s))))
    buf.seek(0)
    return pygame.mixer.Sound(buffer=buf.read())


class AudioManager:
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.master_volume = 0.7
        self.sfx_volume = 0.8
        self.music_volume = 0.5

    def init(self):
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-BITS_PER_SAMPLE, channels=2)
        self._generate_all()

    def _generate_all(self):
        self.add_sound("splash", _generate_wave(300, 0.3, 0.4, "noise"))
        self.add_sound("coin", _generate_wave(880, 0.1, 0.6, "sine") +
                                _generate_wave(1320, 0.15, 0.5, "sine"))
        self.add_sound("explosion", _generate_wave(80, 0.6, 0.7, "noise"))
        self.add_sound("harpoon", _generate_wave(400, 0.15, 0.4, "sweep"))
        self.add_sound("hit", _generate_wave(200, 0.1, 0.5, "square"))
        self.add_sound("boss_roar", _generate_wave(40, 1.5, 0.8, "noise"))
        self.add_sound("bubble", _generate_wave(600, 0.08, 0.2, "sine"))
        self.add_sound("buy", _generate_wave(600, 0.1, 0.5, "sine") +
                              _generate_wave(900, 0.15, 0.4, "sine"))
        self.add_sound("error", _generate_wave(200, 0.3, 0.5, "square"))
        self.add_sound("level_up", _generate_wave(440, 0.1, 0.5, "sine") +
                                    _generate_wave(660, 0.1, 0.5, "sine") +
                                    _generate_wave(880, 0.15, 0.5, "sine"))
        self.add_sound("stun", _generate_wave(150, 0.4, 0.4, "sine"))
        self.add_sound("critical", _generate_wave(1000, 0.1, 0.7, "sine") +
                                    _generate_wave(1500, 0.15, 0.6, "sine"))

    def add_sound(self, name, samples):
        self.sounds[name] = _samples_to_sound(samples)

    def play(self, name):
        if name in self.sounds:
            sound = self.sounds[name]
            sound.set_volume(self.master_volume * self.sfx_volume)
            sound.play()

    def set_master_volume(self, vol):
        self.master_volume = vol
        pygame.mixer.music.set_volume(self.master_volume * self.music_volume)

    def set_sfx_volume(self, vol):
        self.sfx_volume = vol

    def set_music_volume(self, vol):
        self.music_volume = vol
        pygame.mixer.music.set_volume(self.master_volume * self.music_volume)

    def play_music(self, path=None, loop=-1):
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.master_volume * self.music_volume)
                pygame.mixer.music.play(loop)
                self.music_playing = True
            except pygame.error:
                pass
