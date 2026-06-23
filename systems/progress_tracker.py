import json
import os

PLAYER_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "player_data.json")

class ProgressTracker:
    def __init__(self):
        self.data = {
            "nickname": "",
            "stars": 0,
            "bananas": 0,
            "completed_levels": [],
            "current_level": 0,
            "monkey_stage": 0,
            "badges": [],
            "mistakes_tracker": {},
            "speed_tracker": {}
        }
        self.load_progress()
        
    def load_progress(self):
        try:
            if os.path.exists(PLAYER_DATA_PATH):
                with open(PLAYER_DATA_PATH, "r") as f:
                    loaded = json.load(f)
                    # Merge loaded data with defaults to avoid missing keys
                    for k, v in loaded.items():
                        self.data[k] = v
                    # Clean any existing badges with emojis for backward compatibility
                    from game_core import clean_emojis
                    if "badges" in self.data:
                        self.data["badges"] = [clean_emojis(b) for b in self.data["badges"]]
        except Exception as e:
            print(f"Error loading player progress: {e}")
            
    def save_progress(self):
        try:
            # Create data folder if not exists
            os.makedirs(os.path.dirname(PLAYER_DATA_PATH), exist_ok=True)
            with open(PLAYER_DATA_PATH, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving player progress: {e}")

    def set_nickname(self, name):
        name = name.strip()
        if self.data["nickname"].strip().upper() != name.upper():
            # Reset all progress if username is not the same!
            self.data = {
                "nickname": name,
                "stars": 0,
                "bananas": 0,
                "completed_levels": [],
                "current_level": 0,
                "monkey_stage": 0,
                "badges": [],
                "mistakes_tracker": {},
                "speed_tracker": {}
            }
        else:
            self.data["nickname"] = name
        self.save_progress()

    def get_nickname(self):
        return self.data["nickname"] or "Explorer"

    def add_stars(self, count):
        self.data["stars"] += count
        self.save_progress()
        return self.data["stars"]

    def add_bananas(self, count):
        self.data["bananas"] += count
        # Evolve monkey guide based on bananas collected
        # 0-5 bananas: Stage 0 (Small)
        # 6-12 bananas: Stage 1 (Medium)
        # 13+ bananas: Stage 2 (Large)
        old_stage = self.data["monkey_stage"]
        if self.data["bananas"] >= 13:
            self.data["monkey_stage"] = 2
        elif self.data["bananas"] >= 6:
            self.data["monkey_stage"] = 1
        else:
            self.data["monkey_stage"] = 0
            
        evolved = (self.data["monkey_stage"] > old_stage)
        self.save_progress()
        return self.data["bananas"], evolved

    def complete_level(self, level_idx):
        if level_idx not in self.data["completed_levels"]:
            self.data["completed_levels"].append(level_idx)
            
            # Badge Awards
            badge_map = {
                0: "Animal Master",
                1: "Food Expert",
                2: "Object Explorer",
                3: "Color Genius",
                4: "Action Hero",
                5: "Star Explorer",
                6: "Words Land Champion"
            }
            badge = badge_map.get(level_idx)
            if badge and badge not in self.data["badges"]:
                self.data["badges"].append(badge)
                
            self.save_progress()
            return True
        return False

    def unlock_next_level(self):
        # We have 7 levels total (indices 0 to 6)
        if len(self.data["completed_levels"]) > 0:
            next_lvl = max(self.data["completed_levels"]) + 1
            self.data["current_level"] = min(next_lvl, 6)
            self.save_progress()

    def log_word_attempt(self, word, errors_made, time_spent):
        # Log errors per word
        word = word.upper()
        if "mistakes_tracker" not in self.data:
            self.data["mistakes_tracker"] = {}
        if word not in self.data["mistakes_tracker"]:
            self.data["mistakes_tracker"][word] = 0
        self.data["mistakes_tracker"][word] += errors_made
        
        # Log response speed
        if "speed_tracker" not in self.data:
            self.data["speed_tracker"] = {}
        if word not in self.data["speed_tracker"]:
            self.data["speed_tracker"][word] = []
        self.data["speed_tracker"][word].append(time_spent)
        
        self.save_progress()

    def get_weak_words(self, limit=5):
        # Return words sorted by highest errors
        tracker = self.data.get("mistakes_tracker", {})
        sorted_words = sorted(tracker.items(), key=lambda item: item[1], reverse=True)
        return [w for w in sorted_words if w[1] > 0][:limit]

    def get_level_accuracy(self, level_words):
        # Calculate percentage accuracy for a set of words
        tracker = self.data.get("mistakes_tracker", {})
        total_attempts = 0
        total_errors = 0
        
        for w in level_words:
            w = w.upper()
            if w in tracker:
                total_attempts += 1
                total_errors += tracker[w]
                
        if total_attempts == 0:
            return 100 # No data yet, assume fresh
        
        # Simple formula: 100 - (errors / (attempts * 3)) * 100, capped
        acc = int(100 - (total_errors / (total_attempts * 2.5)) * 100)
        return max(10, min(100, acc))
