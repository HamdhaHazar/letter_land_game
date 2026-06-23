import queue
import time

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
        self.engine = None
        self.is_speaking_state = False
        self.sim_speech_timer = 0.0
        
        # Initialize pyttsx3 on the main thread asynchronously
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            # Set child-friendly voice properties
            rate = self.engine.getProperty('rate')
            self.engine.setProperty('rate', max(110, rate - 40)) # speak slightly slower for kids
            self.engine.setProperty('volume', 1.0)
            
            # Start the pyttsx3 loop asynchronously (non-blocking)
            self.engine.startLoop(False)
            self.engine_initialized = True
            print("VoiceSystem: Async speech loop initialized successfully.")
        except Exception as e:
            print(f"Warning: TTS engine initialization failed: {e}. Falling back to subtitles only.")
            self.engine_initialized = False
            self.engine = None
        
    def speak(self, text):
        """Queues a text line to be spoken aloud."""
        if not text:
            return
        self.speech_queue.put(text)

    def is_speaking(self):
        """Returns True if the guide character is speaking."""
        global IS_SPEAKING
        return IS_SPEAKING

    def is_busy(self):
        """Returns True if voice is currently speaking or has pending speech in queue."""
        global IS_SPEAKING
        return IS_SPEAKING or not self.speech_queue.empty()

    def get_subtitle(self):
        """Returns the current speech text for subtitles."""
        global SUBTITLE_TEXT
        return SUBTITLE_TEXT

    def update(self, dt):
        """Call this in the game loop to manage subtitle timer and speech updates."""
        global SUBTITLE_TEXT, SUBTITLE_TIMER, IS_SPEAKING
        
        # 1. Manage subtitle countdown timer
        if SUBTITLE_TIMER > 0:
            SUBTITLE_TIMER -= dt
            if SUBTITLE_TIMER <= 0:
                SUBTITLE_TEXT = ""

        # 2. Update engine state and process speech queue
        if self.engine_initialized and self.engine:
            try:
                # Pump COM events for pyttsx3 (non-blocking)
                self.engine.iterate()
            except Exception as ex:
                print(f"TTS iterate error: {ex}")
                
            # Check if engine finished speaking
            is_busy = False
            try:
                is_busy = self.engine.isBusy()
            except Exception as ex:
                print(f"TTS check busy error: {ex}")
                
            if self.is_speaking_state and not is_busy:
                # Finished speaking the current queued item
                if self.speech_queue.empty():
                    IS_SPEAKING = False
                    self.is_speaking_state = False
                    if self.audio_manager:
                        self.audio_manager.restore_music()
                else:
                    self.is_speaking_state = False # trigger next word in queue

            # Process next item if engine is not busy
            if not self.is_speaking_state and not is_busy and not self.speech_queue.empty():
                try:
                    text = self.speech_queue.get_nowait()
                except queue.Empty:
                    return
                
                from game_core import clean_emojis
                text = clean_emojis(text)
                
                IS_SPEAKING = True
                SUBTITLE_TEXT = text
                word_count = len(text.split())
                SUBTITLE_TIMER = max(2.5, word_count * 0.45)
                
                # Duck music
                if self.audio_manager:
                    self.audio_manager.duck_music()
                    
                # Clean punctuation for speech
                cleaned_text = text
                try:
                    self.engine.say(cleaned_text)
                    self.is_speaking_state = True
                except Exception as ex:
                    print(f"TTS say error: {ex}")
                    self.is_speaking_state = False
                    
                self.speech_queue.task_done()

        # 3. Fallback simulation if engine is not initialized
        else:
            if not self.is_speaking_state and not self.speech_queue.empty():
                try:
                    text = self.speech_queue.get_nowait()
                except queue.Empty:
                    return
                
                from game_core import clean_emojis
                text = clean_emojis(text)
                
                IS_SPEAKING = True
                SUBTITLE_TEXT = text
                word_count = len(text.split())
                SUBTITLE_TIMER = max(2.5, word_count * 0.45)
                self.sim_speech_timer = max(1.5, word_count * 0.35)
                self.is_speaking_state = True
                
                if self.audio_manager:
                    self.audio_manager.duck_music()
            elif self.is_speaking_state:
                self.sim_speech_timer -= dt
                if self.sim_speech_timer <= 0:
                    self.speech_queue.task_done()
                    if self.speech_queue.empty():
                        IS_SPEAKING = False
                        self.is_speaking_state = False
                        if self.audio_manager:
                            self.audio_manager.restore_music()
                    else:
                        self.is_speaking_state = False # trigger next word

    def draw_subtitles(self, surface, font, screen_w, screen_h):
        """Draws bubble subtitle banner at the bottom of the screen."""
        global SUBTITLE_TEXT
        if not SUBTITLE_TEXT:
            return
            
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
        """Clears all pending speech in the queue."""
        global IS_SPEAKING, SUBTITLE_TEXT, SUBTITLE_TIMER
        
        # Stop currently playing speech if engine initialized
        if self.engine_initialized and self.engine:
            try:
                self.engine.stop()
            except Exception as e:
                print(f"TTS stop error: {e}")
                
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except queue.Empty:
                break
                
        IS_SPEAKING = False
        SUBTITLE_TEXT = ""
        SUBTITLE_TIMER = 0.0
        self.is_speaking_state = False
        if self.audio_manager:
            self.audio_manager.restore_music()

    def stop(self):
        self.is_running = False
        self.clear_queue()
        if self.engine_initialized and self.engine:
            try:
                self.engine.endLoop()
            except:
                pass
