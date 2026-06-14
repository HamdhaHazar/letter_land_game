import os
import struct
import wave
import math
import random
import pygame

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

class AudioManager:
    def __init__(self):
        # Create directories if they do not exist
        os.makedirs(SOUNDS_DIR, exist_ok=True)
        os.makedirs(MUSIC_DIR, exist_ok=True)
        
        # Paths to sound files
        self.sounds_paths = {
            "click": os.path.join(SOUNDS_DIR, "click.wav"),
            "success": os.path.join(SOUNDS_DIR, "success.wav"),
            "fail": os.path.join(SOUNDS_DIR, "fail.wav"),
            "banana": os.path.join(SOUNDS_DIR, "banana.wav"),
            "unlock": os.path.join(SOUNDS_DIR, "unlock.wav")
        }
        
        # Paths to BGM files
        self.music_paths = {
            "intro": os.path.join(MUSIC_DIR, "intro.wav"),
            "jungle": os.path.join(MUSIC_DIR, "jungle.wav"),
            "food": os.path.join(MUSIC_DIR, "food.wav"),
            "objects": os.path.join(MUSIC_DIR, "objects.wav"),
            "space": os.path.join(MUSIC_DIR, "space.wav")
        }
        
        # Synthesize missing files
        self.check_and_synthesize_assets()
        
        # Load Pygame Sound objects
        self.sounds = {}
        for name, path in self.sounds_paths.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading SFX {name}: {e}")
                self.sounds[name] = None
                
        self.current_bgm = None
        self.target_bgm_volume = 0.4
        self.bgm_volume = 0.4
        
    def check_and_synthesize_assets(self):
        """Generates all WAV audio assets dynamically if they do not exist."""
        # 1. SFX Synthesis
        if not os.path.exists(self.sounds_paths["click"]):
            self.synthesize_wav(self.sounds_paths["click"], 0.08, lambda t: math.sin(2 * math.pi * 900 * t) * math.exp(-t * 60))
            
        if not os.path.exists(self.sounds_paths["success"]):
            # C5 -> E5 -> G5 -> C6 pentatonic arpeggio
            def success_melody(t):
                note = int(t * 10)
                freqs = [523.25, 659.25, 783.99, 1046.50]
                freq = freqs[min(3, note)]
                decay = math.exp(-(t % 0.1) * 12)
                return math.sin(2 * math.pi * freq * t) * 0.4 * decay
            self.synthesize_wav(self.sounds_paths["success"], 0.45, success_melody)
            
        if not os.path.exists(self.sounds_paths["fail"]):
            # Buzz slide down
            def fail_sound(t):
                freq = max(100.0, 300.0 - t * 450.0)
                val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
                return val * 0.15 * math.exp(-t * 5.0)
            self.synthesize_wav(self.sounds_paths["fail"], 0.35, fail_sound)
            
        if not os.path.exists(self.sounds_paths["banana"]):
            # Crunch sound (noise + chirp)
            def banana_chew(t):
                noise = random.uniform(-0.3, 0.3) * math.exp(-t * 22)
                chirp = math.sin(2 * math.pi * (350 + 600 * t) * t) * 0.25 * math.exp(-t * 15)
                return noise + chirp
            self.synthesize_wav(self.sounds_paths["banana"], 0.18, banana_chew)
            
        if not os.path.exists(self.sounds_paths["unlock"]):
            # Rising synth chime
            def unlock_chime(t):
                note = int(t * 8)
                freqs = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99, 1046.50, 1318.51]
                freq = freqs[min(7, note)]
                decay = math.exp(-(t % 0.08) * 10)
                return math.sin(2 * math.pi * freq * t) * 0.3 * decay
            self.synthesize_wav(self.sounds_paths["unlock"], 0.6, unlock_chime)

        # 2. BGM Synthesis (4-second looping sound clips)
        # Intro: Soft Ambient chords
        if not os.path.exists(self.music_paths["intro"]):
            def intro_bgm(t):
                # slow floating pad chord Cmaj7 -> Fmaj7
                chord = int(t / 2.0) % 2
                f1, f2, f3 = (130.81, 196.00, 261.63) if chord == 0 else (174.61, 261.63, 349.23)
                lfo = 1.0 + 0.03 * math.sin(2 * math.pi * 3 * t)
                wave1 = math.sin(2 * math.pi * f1 * t * lfo) * 0.2
                wave2 = math.sin(2 * math.pi * f2 * t) * 0.15
                wave3 = math.sin(2 * math.pi * f3 * t) * 0.1
                return (wave1 + wave2 + wave3) * 0.5
            self.synthesize_wav(self.music_paths["intro"], 4.0, intro_bgm)

        # Jungle/Animals: Plucked forest marimba arpeggio
        if not os.path.exists(self.music_paths["jungle"]):
            def jungle_bgm(t):
                # Bassline
                beat = int(t * 2) # 120 BPM
                bass_notes = [130.81, 196.00, 164.81, 220.00] # C3, G3, E3, A3
                bass_f = bass_notes[beat % 4]
                bass = math.sin(2 * math.pi * bass_f * t) * 0.25
                # Melody
                sub_beat = int(t * 6)
                mel_notes = [523.25, 659.25, 783.99, 880.00, 1046.50, 880.00]
                mel_f = mel_notes[sub_beat % 6]
                decay = math.exp(-(t % 0.166) * 12)
                mel = math.sin(2 * math.pi * mel_f * t) * 0.15 * decay
                return (bass + mel) * 0.4
            self.synthesize_wav(self.music_paths["jungle"], 4.0, jungle_bgm)

        # Food: Sweet, cute bubbly melody
        if not os.path.exists(self.music_paths["food"]):
            def food_bgm(t):
                beat = int(t * 3)
                bass_notes = [261.63, 329.63, 392.00]
                bass_f = bass_notes[beat % 3]
                bass = math.sin(2 * math.pi * bass_f * t) * 0.22
                
                sub_beat = int(t * 6)
                mel_notes = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33]
                mel_f = mel_notes[sub_beat % 6]
                decay = math.exp(-(t % 0.166) * 8)
                mel = math.sin(2 * math.pi * mel_f * t) * 0.1 * decay
                return (bass + mel) * 0.4
            self.synthesize_wav(self.music_paths["food"], 4.0, food_bgm)

        # Objects: Happy retro bounce theme
        if not os.path.exists(self.music_paths["objects"]):
            def objects_bgm(t):
                beat = int(t * 4) # 120 BPM
                bass_notes = [130.81, 164.81, 196.00, 164.81]
                bass_f = bass_notes[beat % 4]
                # square wave bass
                bass = (0.15 if math.sin(2 * math.pi * bass_f * t) > 0 else -0.15)
                
                sub_beat = int(t * 8)
                mel_notes = [523.25, 0, 659.25, 0, 783.99, 659.25, 880.00, 1046.50]
                mel_f = mel_notes[sub_beat % 8]
                mel = 0.0
                if mel_f > 0:
                    decay = math.exp(-(t % 0.125) * 15)
                    mel = math.sin(2 * math.pi * mel_f * t) * 0.12 * decay
                return (bass + mel) * 0.35
            self.synthesize_wav(self.music_paths["objects"], 4.0, objects_bgm)

        # Space: Deep space modulated cosmic sweeps
        if not os.path.exists(self.music_paths["space"]):
            def space_bgm(t):
                # Modulating frequency LFO
                lfo = math.sin(2 * math.pi * 0.25 * t)
                f1 = 200 + lfo * 80
                f2 = 400 - lfo * 100
                wave1 = math.sin(2 * math.pi * f1 * t) * 0.18
                wave2 = math.sin(2 * math.pi * f2 * t) * 0.12
                # Pulsing beat
                pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 2 * t)
                return (wave1 + wave2) * pulse * 0.35
            self.synthesize_wav(self.music_paths["space"], 4.0, space_bgm)

    def synthesize_wav(self, filepath, duration, wave_func, samplerate=22050):
        """Writes sound waves to a 16-bit PCM WAV file."""
        with wave.open(filepath, 'wb') as w:
            w.setnchannels(1) # mono
            w.setsampwidth(2) # 16-bit
            w.setframerate(samplerate)
            num_frames = int(samplerate * duration)
            for i in range(num_frames):
                t = i / samplerate
                amp = wave_func(t)
                # Clamp amplitude to prevent overflow popping
                amp = max(-0.95, min(0.95, amp))
                val = int(amp * 32767)
                w.writeframesraw(struct.pack('<h', val))

    def play_sfx(self, name):
        """Plays a sound effect by name."""
        sfx = self.sounds.get(name)
        if sfx:
            sfx.play()

    def play_music(self, theme_name):
        """Plays backing music loop for a given theme."""
        path = self.music_paths.get(theme_name)
        if path and os.path.exists(path):
            try:
                if self.current_bgm == theme_name:
                    return # Already playing
                pygame.mixer.music.load(path)
                # Play continuously (-1)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(self.bgm_volume)
                self.current_bgm = theme_name
            except Exception as e:
                print(f"Error playing BGM {theme_name}: {e}")

    def duck_music(self):
        """Reduces BGM volume to make voice narration prominent."""
        self.target_bgm_volume = 0.08
        pygame.mixer.music.set_volume(self.target_bgm_volume)

    def restore_music(self):
        """Restores original background music volume levels."""
        self.target_bgm_volume = 0.35
        pygame.mixer.music.set_volume(self.target_bgm_volume)

    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_bgm = None
