import numpy as np
import pygame
import threading

SAMPLE_RATE = 44100

def _make_sound(arr):
    arr = np.clip(arr, -1.0, 1.0)
    stereo = np.stack([arr, arr], axis=-1)
    buf = (stereo * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(np.ascontiguousarray(buf))

def _sine(freq, duration, volume=0.5, fade_out=True):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t) * volume
    if fade_out:
        fade = np.linspace(1, 0, len(wave))
        wave *= fade
    return wave

def _noise(duration, volume=0.3):
    n = int(SAMPLE_RATE * duration)
    return (np.random.uniform(-1, 1, n) * volume).astype(np.float32)


def _envelope(wave, attack=0.01, decay=0.1, sustain=0.7, release=0.2):
    n = len(wave)
    env = np.ones(n)
    a = int(attack * n)
    d = int(decay * n)
    r = int(release * n)
    s = n - a - d - r
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0:
        env[a:a+d] = np.linspace(1, sustain, d)
    if s > 0:
        env[a+d:a+d+s] = sustain
    if r > 0:
        env[a+d+s:] = np.linspace(sustain, 0, r)
    return wave * env

def _gen_shot():
    dur = 0.4
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = np.linspace(120, 40, len(t))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * 0.5
    noise = _noise(dur, 0.4)
    wave = tone + noise
    env = np.exp(-t * 8)
    return (wave * env).astype(np.float32)

def _gen_hit():
    dur = 0.5
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    crack = _noise(0.05, 0.8)
    sizzle = _noise(dur, 0.3) * np.exp(-t * 6)
    crack_full = np.zeros(len(t), dtype=np.float32)
    crack_full[:len(crack)] = crack
    return (crack_full + sizzle).astype(np.float32)

def _gen_miss():
    dur = 0.6
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = np.linspace(600, 200, len(t))
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * 0.3
    splash = _noise(dur, 0.15) * np.exp(-t * 5)
    wave = tone + splash
    env = np.exp(-t * 4)
    return (wave * env).astype(np.float32)

def _gen_sunk():
    dur = 1.2
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq = np.linspace(80, 20, len(t))
    boom = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE) * 0.6
    noise = _noise(dur, 0.5) * np.exp(-t * 3)
    creak = np.sin(2 * np.pi * 300 * t) * 0.2 * np.exp(-t * 5)
    wave = boom + noise + creak
    env = np.exp(-t * 2)
    return (wave * env).astype(np.float32)

def _gen_victory():
    notes = [261, 329, 392, 523, 659, 784]
    note_dur = 0.15
    gap = 0.03
    parts = []
    for freq in notes:
        tone = _sine(freq, note_dur, volume=0.6, fade_out=False)
        env = np.exp(-np.linspace(0, 5, len(tone)))
        parts.append((tone * env).astype(np.float32))
        parts.append(np.zeros(int(SAMPLE_RATE * gap), dtype=np.float32))
    chord_dur = 0.8
    chord = sum(_sine(f, chord_dur, volume=0.25) for f in [523, 659, 784])
    parts.append(chord.astype(np.float32))
    return np.concatenate(parts)

def _gen_defeat():
    notes = [392, 349, 330, 294, 261]
    note_dur = 0.25
    parts = []
    for freq in notes:
        tone = _sine(freq, note_dur, volume=0.5, fade_out=True)
        parts.append(tone.astype(np.float32))
    drone = _sine(130, 1.0, volume=0.3)
    parts.append(drone.astype(np.float32))
    return np.concatenate(parts)

def _gen_bg_music():
    sr = SAMPLE_RATE
    dur_bar = 2.0
    chords = [
        [130, 164, 196],
        [110, 138, 164],
        [146, 174, 220],
        [130, 155, 196],
    ]
    bars = []
    for chord in chords:
        bar = np.zeros(int(sr * dur_bar), dtype=np.float32)
        t = np.linspace(0, dur_bar, len(bar), endpoint=False)
        for freq in chord:
            vibrato = 1 + 0.003 * np.sin(2 * np.pi * 5 * t)
            wave = np.sin(2 * np.pi * freq * vibrato * t) * 0.18
            env = np.sin(np.pi * t / dur_bar) ** 0.5
            bar += (wave * env).astype(np.float32)
        bar += (_noise(dur_bar, 0.03) * np.sin(np.pi * t / dur_bar)).astype(np.float32)
        bars.append(bar)
    return np.concatenate(bars * 4)  # loop 4x

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.music_enabled = True
        self._ready = False
        self._music_channel = None
        self._sounds = {}
        threading.Thread(target=self._init, daemon=True).start()

    def _init(self):
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self._sounds = {
                'shot':    _make_sound(_gen_shot()),
                'hit':     _make_sound(_gen_hit()),
                'miss':    _make_sound(_gen_miss()),
                'sunk':    _make_sound(_gen_sunk()),
                'victory': _make_sound(_gen_victory()),
                'defeat':  _make_sound(_gen_defeat()),
            }
            # bg music as looping channel
            bg = _make_sound(_gen_bg_music())
            self._bg_sound = bg
            self._ready = True
            self._start_bg()
        except Exception as e:
            print(f"Sound init failed: {e}")

    def _start_bg(self):
        if not self._ready or not self.music_enabled:
            return
        try:
            import os
            music_path = os.path.join(os.path.dirname(__file__), 'Hull_Integrity.mp3')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(loops=-1)
            else:
                # fallback to generated if file not found
                self._music_channel = self._bg_sound.play(loops=-1)
                if self._music_channel:
                    self._music_channel.set_volume(0.4)
        except Exception as e:
            print(f"Music load failed: {e}")

    def play(self, name):
        if not self.enabled or not self._ready:
            return
        try:
            s = self._sounds.get(name)
            if s:
                s.play()
        except Exception:
            pass

    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self._ready:
            return self.music_enabled
        try:
            if self.music_enabled:
                self._start_bg()
            else:
                pygame.mixer.music.stop()
                if self._music_channel:
                    self._music_channel.stop()
        except Exception:
            pass
        return self.music_enabled

    def toggle_sfx(self):
        self.enabled = not self.enabled
        return self.enabled