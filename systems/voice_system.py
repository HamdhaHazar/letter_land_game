import threading
import queue
import time
import sys

# Global flag to check if speech is happening
IS_SPEAKING = False
SUBTITLE_TEXT = ""
SUBTITLE_TIMER = 0.0

class VoiceSystem:
    def __init__(self, audio_manager=None):
        self.audio_manager = audio_manager
        self.speech_queue = queue.Queue()
        self.is_running = True
        self.engine_initialized = False
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
        
    def _speech_worker(self):
        global IS_SPEAKING, SUBTITLE_TEXT, SUBTITLE_TIMER
        
        # Initialize pyttsx3 in the worker thread.
        # On Windows, pyttsx3 is COM-based and COM requires initialization on the thread it is run on.
        engine = None
        try:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except Exception as ce:
                print(f"pythoncom CoInitialize warning: {ce}")
            import pyttsx3
            engine = pyttsx3.init()
            # Set child-friendly voice properties
            rate = engine.getProperty('rate')
            engine.setProperty('rate', max(110, rate - 40)) # speak slightly slower for kids
            volume = engine.getProperty('volume')
            engine.setProperty('volume', 1.0)
            self.engine_initialized = True
        except Exception as e:
            print(f"Warning: TTS engine initialization failed: {e}. Falling back to subtitles only.")
            self.engine_initialized = False
            
        while self.is_running:
            try:
                # Blocks for 200ms
                text = self.speech_queue.get(timeout=0.2)
            except queue.Empty:
                continue
                
            IS_SPEAKING = True
            SUBTITLE_TEXT = text
            # Estimate subtitle display duration based on word count
            word_count = len(text.split())
            SUBTITLE_TIMER = max(2.5, word_count * 0.45)
            
            # Duck music
            if self.audio_manager:
                self.audio_manager.duck_music()
                
            if self.engine_initialized and engine:
                try:
                    # Clean punctuation to avoid weird TTS pronunciation
                    cleaned_text = text.replace("🐵", "").replace("🍎", "").replace("🚗", "").replace("🌈", "").replace("🏃", "").replace("🚀", "").replace("⭐", "").replace("🍌", "")
                    engine.say(cleaned_text)
                    engine.runAndWait()
                except Exception as ex:
                    print(f"TTS say error: {ex}")
            else:
                # Simulated TTS delay if engine is not working
                # 300ms per word
                time.sleep(max(1.5, word_count * 0.35))
                
            self.speech_queue.task_done()
            
            # If no more items in queue, restore music
            if self.speech_queue.empty():
                IS_SPEAKING = False
                if self.audio_manager:
                    # Small delay before restoring music for natural sound
                    time.sleep(0.3)
                    self.audio_manager.restore_music()

    def speak(self, text):
        """Queues a text line to be spoken aloud."""
        if not text:
            return
        self.speech_queue.put(text)

    def is_speaking(self):
        """Returns True if the guide character is speaking."""
        return IS_SPEAKING

    def is_busy(self):
        """Returns True if voice is currently speaking or has pending speech in queue."""
        return IS_SPEAKING or not self.speech_queue.empty()

    def get_subtitle(self):
        """Returns the current speech text for subtitles."""
        global SUBTITLE_TEXT
        return SUBTITLE_TEXT

    def update(self, dt):
        """Call this in the game loop to manage subtitle timer."""
        global SUBTITLE_TEXT, SUBTITLE_TIMER
        if SUBTITLE_TIMER > 0:
            SUBTITLE_TIMER -= dt
            if SUBTITLE_TIMER <= 0:
                SUBTITLE_TEXT = ""

    def draw_subtitles(self, surface, font, screen_w, screen_h):
        """Draws bubble subtitle banner at the bottom of the screen."""
        global SUBTITLE_TEXT
        if not SUBTITLE_TEXT:
            return
            
        # Draw translucent subtitle bar at the bottom center
        import pygame
        from game_core import CREAM_WHITE, PURPLE, WHITE, draw_rounded_rect_with_shadow
        
        # Word wrap text
        words = SUBTITLE_TEXT.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            if font.size(test_line)[0] > screen_w - 180:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        line_height = font.get_linesize()
        padding = 14
        box_h = len(lines) * line_height + padding * 2
        box_w = screen_w - 120
        box_x = 60
        box_y = screen_h - box_h - 25
        
        # Subtitle Bubble
        draw_rounded_rect_with_shadow(surface, (30, 25, 45, 230), (box_x, box_y, box_w, box_h), radius=15, shadow_offset=(2, 3))
        pygame.draw.rect(surface, PURPLE, (box_x, box_y, box_w, box_h), 2, border_radius=15)
        
        for idx, line in enumerate(lines):
            lbl = font.render(line, True, CREAM_WHITE)
            surface.blit(lbl, lbl.get_rect(center=(screen_w // 2, box_y + padding + idx * line_height + line_height // 2)))

    def clear_queue(self):
        """Clears all pending speech in the queue without stopping the thread."""
        global IS_SPEAKING, SUBTITLE_TEXT, SUBTITLE_TIMER
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
        IS_SPEAKING = False
        SUBTITLE_TEXT = ""
        SUBTITLE_TIMER = 0.0
        if self.audio_manager:
            self.audio_manager.restore_music()

    def stop(self):
        self.is_running = False
        # Clear queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
