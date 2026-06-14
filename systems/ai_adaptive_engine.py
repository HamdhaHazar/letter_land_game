class AIAdaptiveEngine:
    def __init__(self, progress_tracker=None):
        self.progress_tracker = progress_tracker
        self.session_mistakes = {} # Track mistakes in current game session
        self.success_streak = 0
        
    def reset_round(self):
        self.session_mistakes = {}
        
    def record_mistake(self, word):
        word = word.upper()
        if word not in self.session_mistakes:
            self.session_mistakes[word] = 0
        self.session_mistakes[word] += 1
        self.success_streak = 0 # Break streak
        
    def record_success(self, word):
        self.success_streak += 1
        
    def get_hint_level(self, word):
        """Returns visual hint level: 0 (none), 1 (glow slot), 2 (show translucent shadow letter inside slot)."""
        word = word.upper()
        
        # Check historical mistakes from progress tracker
        historical_mistakes = 0
        if self.progress_tracker and "mistakes_tracker" in self.progress_tracker.data:
            historical_mistakes = self.progress_tracker.data["mistakes_tracker"].get(word, 0)
            
        current_mistakes = self.session_mistakes.get(word, 0)
        total_mistakes = historical_mistakes + current_mistakes
        
        if total_mistakes >= 3:
            return 2 # Strong hints: show letter inside slot
        elif total_mistakes >= 1:
            return 1 # Medium hints: highlight correct slots
        return 0

    def get_option_count(self, category):
        """For multiple choice. Returns number of options to show (2, 3, or 4)."""
        # Base is 3 options.
        # If user has a high streak, show 4 options for challenge.
        # If user is struggling with mistakes on this category, show 2.
        historical_mistakes = 0
        if self.progress_tracker and "mistakes_tracker" in self.progress_tracker.data:
            # Aggregate mistakes in this category
            tracker = self.progress_tracker.data["mistakes_tracker"]
            for w, err in tracker.items():
                # Simple heuristic: if any mistakes in category
                historical_mistakes += err
                
        if len(self.session_mistakes) > 0 or historical_mistakes > 5:
            return 2 # Reduce difficulty: 2 options (50/50 chance)
        elif self.success_streak >= 5:
            return 4 # Boost difficulty: 4 options
        return 3 # Normal: 3 options

    def get_speed_multiplier(self):
        """For moving/speed challenges. Returns a multiplier between 0.6 and 1.6."""
        # Adjust base speed of flying objects
        if self.success_streak >= 6:
            return 1.4 # Fast
        elif self.success_streak >= 3:
            return 1.2 # Slightly fast
        
        # Check mistakes
        total_errors = sum(self.session_mistakes.values())
        if total_errors >= 2:
            return 0.75 # Slow down
        return 1.0 # Normal speed
