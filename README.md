# 🚗 NeonRush — Python Car Race

> **A fast-paced, neon-styled top-down car racing game built with Python & Pygame.**

---

## 📸 Preview

```
╔══════════════════════════════════════════════╗
║         NeonRush — Python Car Race           ║
║         Built with Pygame  (Python 3.8+)     ║
╚══════════════════════════════════════════════╝
```

Race through a glowing neon highway, dodge incoming traffic, collect power-ups, and survive as long as you can while the speed keeps climbing!

---

## 🎮 Features

- 🌆 **Neon-themed visuals** — animated starfield background, glowing road edges, and color-coded cars
- 🚦 **4-lane highway** with animated kerb strips and lane dividers
- 🧠 **Progressive difficulty** — speed and enemy spawn rate scale with every level
- ❤️ **3 lives system** — survive crashes with brief invincibility windows
- ⭐ **Star power-ups** — collect for big bonus points
- 🛡️ **Shield power-ups** — 6 seconds of full collision immunity
- 💥 **Particle effects** — burst animations on crashes and power-up pickups
- 📳 **Screen shake** — impactful crash feedback
- 🏆 **Persistent high score & level** — saved to `race_save.json`
- ⏸️ **Pause / Resume** — press ESC anytime during play

---

## 🕹️ Controls

| Action             | Keys                          |
|--------------------|-------------------------------|
| Move Left          | `←` or `A`                   |
| Move Right         | `→` or `D`                   |
| Accelerate / Up    | `↑` or `W`                   |
| Brake / Down       | `↓` or `S`                   |
| Pause / Resume     | `ESC`                         |
| Quit (from menu)   | `ESC`                         |

---

## 📦 Requirements

| Dependency | Version     |
|------------|-------------|
| Python     | 3.8 or later |
| Pygame     | Any modern version (`2.x` recommended) |

---

## ⚙️ Installation

1. **Clone or download** this repository:
   ```bash
   git clone https://github.com/your-username/neon-rush.git
   cd neon-rush
   ```

2. **Install Pygame** (if not already installed):
   ```bash
   pip install pygame
   ```

3. **Run the game:**
   ```bash
   python car_race.py
   ```

---

## 🗂️ Project Structure

```
car race/
├── car_race.py       # Main game file (all logic, rendering, and classes)
├── race_save.json    # Auto-generated save file (best score & top level)
└── README.md         # This file
```

---

## 🧩 Game Architecture

The game is structured around a single **`NeonRush`** main class with modular helper classes:

| Class / Component | Description |
|-------------------|-------------|
| `NeonRush`        | Core game loop, state machine, rendering dispatch |
| `EnemyCar`        | Oncoming traffic with random lane and speed offset |
| `PowerUp`         | Animated star / shield collectibles |
| `Particle`        | Gravity-affected burst particles for FX |
| `LaneStripe`      | Scrolling lane divider decorations |
| `StarField`       | Parallax scrolling background stars |
| `Button`          | Hover-animated UI buttons with glow effects |

### Game States

```
S_MENU  →  S_PLAYING  ⇄  S_PAUSED
                ↓
           S_GAMEOVER  →  S_MENU
```

---

## 📈 Scoring System

| Event             | Points                      |
|-------------------|-----------------------------|
| Surviving         | `+level` every 0.08 seconds |
| Collecting a Star | `+50 × current level`       |
| Level Up          | Every 500 score points      |

---

## 🛡️ Power-Ups

| Icon | Type   | Effect                                    | Duration |
|------|--------|-------------------------------------------|----------|
| ⭐   | Star   | Instant score bonus (`50 × level`)        | Instant  |
| 🛡️  | Shield | Full immunity from enemy collisions       | 6 seconds |

---

## 🔥 Difficulty Scaling

| Level | Road Speed (px/s) | Enemy Spawn Interval |
|-------|-------------------|----------------------|
| 1     | ~255              | 1.8 s                |
| 5     | ~447              | ~1.15 s (2 per wave) |
| 10    | ~720 (max)        | ~0.5 s               |

Speed is capped at **720 px/s**. From level 5+, two enemies spawn per wave.

---

## 💾 Save File

The game auto-saves your **best score** and **highest level reached** to:

```
race_save.json
```

This file is created automatically on first game over. You can safely delete it to reset your progress.

---

## 🛠️ Known Requirements / Notes

- The game window is fixed at **900 × 700 pixels**.
- Fonts fall back gracefully through `Consolas → Courier New → Lucida Console → Monospace → default`.
- The game runs at a locked **60 FPS** target.

---

## 📄 License

This project is open source and free to use for learning and personal projects.

---

*Built with ❤️ and Python — NeonRush*
