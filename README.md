# 🌟 Words Land - The Great Vocabulary Adventure

Welcome to **Words Land**, a modular, interactive, and child-friendly vocabulary learning game. Built with Python, Pygame, and PyTTSx3, this educational adventure is designed to make learning vocabulary engaging and accessible for young explorers!

---

## 🎨 Game Overview

Words Land takes young learners on a journey where they become official vocabulary explorers. Guided by **Tweety the Bird**, children complete vocabulary games, earn stars, collect badges, and fill out their very own **Explorer Passport**.

---

## ✨ Key Features

### 1. 🪪 Explorer Passport System
- **Custom Nickname & Rank**: Players type a custom explorer name to fill out their passport.
- **Polaroid Photo Frame**: Displays their official explorer avatar (Tweety the Bird).
- **Gold Star Stamp**: Once a nickname is approved, an official gold stamp certifies them as a Words Land Explorer!

### 2. 🗺️ Interactive Map & Levels
- A beautifully styled game map with progress-locked levels.
- Themed levels include **Animals 🦁**, **Food 🍎**, **Objects 🚗**, **Colors 🌈**, **Actions 🏃**, and **Space 🚀**.

### 3. 🎮 Educational Game Modules
- **👂 Listening Game**: Audio cues prompt players to select the corresponding words/pictures.
- **🃏 Matching Game**: Interactive card matching challenges.
- **✍️ Drag & Spell**: Spell words correctly by arranging randomized letters.
- **🖼️ Picture Choice**: Visually pick the correct image representing a word.
- **⚡ Speed Game**: A fast-paced vocabulary recognition challenge.

### 4. 🗣️ Accessibility Voice System
- **Asynchronous Text-to-Speech (TTS)**: Seamless narration using the `pyttsx3` engine, preconfigured with kid-friendly slow speech rates.
- **Music Ducking**: Game background music volume automatically ducks whenever Tweety speaks, making voice instructions clear.
- **Accessibility Subtitles**: Clean, wrapped, real-time subtitle banners render at the bottom of the screen.
- **Robust Fallback**: Gracefully falls back to visual subtitle simulation if a speech engine is unavailable.

### 5. 🤖 AI Adaptive Engine & Progress Tracker
- **Smart Mistake Tracking**: Identifies which words the learner struggled with.
- **Adaptive Vocabulary**: Dynamically tunes word selection/difficulty as the player's skills improve.
- **Teacher Dashboard**: Accessible from the map to track total stars, badges, error analysis, and response speed analytics per word.

---

## 🚀 Getting Started

### 📋 Prerequisites
Ensure you have Python 3.10+ installed.

### ⚙️ Installation
1. Clone the repository and navigate to the project directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 🎮 Running the Game
Launch the game using:
   ```bash
   python main.py
   ```

---

## 🛠️ Developer & Asset Tools
This repository includes custom helper scripts for preparing and verifying the game's graphical assets:
- **`crop_bird.py`**: Automated floodfill-based image utility that extracts bird avatar expressions from sheets, removes background colors, and trims borders cleanly.
- **`find_lines.py`**: Scans pixel coordinates to detect grid divider lines for asset sheet parsing.
- **`verify_images.py`**: Verifies transparency layer alignments on extracted avatar images.

---

Have fun exploring **Words Land**! 🐦✨
