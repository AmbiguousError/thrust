# PyThrust II

PyThrust II is a classic arcade-style game where you pilot a spaceship through challenging levels. The objective is to navigate your ship, collect beacons, destroy obstacles, manage fuel, and land safely to advance. The game features increasing difficulty with more obstacles in later levels and keeps track of high scores.

## Features

* **Lunar Lander Style Gameplay:** Control your ship's thrust and rotation to navigate.
* **Fuel Management:** Keep an eye on your fuel gauge; landing refuels your ship.
* **Combat:** Shoot lasers to destroy beacons.
* **Boost Mechanic:** Use a high-powered boost for quick maneuvers or a strong takeoff, at the cost of more fuel.
* **Landing System:** Successfully land your ship upright and at a safe speed. Landing gear deploys automatically at low altitudes and correct orientation.
* **Progressive Difficulty:** Levels increase in complexity with more beacons to collect and more obstacles to avoid.
* **Particle Effects:** Visual feedback for thrust, explosions, and smoke.
* **High Score System:** Saves the top high scores locally in a `pythrust_highscores.txt` file.
* **Lives System:** Start with a set number of ships and earn extra lives by reaching score milestones.

## Requirements

* **Python 3.x** (if running from source)
* **Pygame:** A cross-platform set of Python modules designed for writing video games (if running from source).

## How to Play

### Running the Game

There are two ways to run the game:

1.  **Using the Executable (Recommended for most users):**
    * Navigate to the `dist` folder.
    * Run `thrust.exe`.

2.  **Running from Python Source:**
    * **Ensure Python is installed:** If you don't have Python, download and install it from [python.org](https://www.python.org/).
    * **Install Pygame:** Open your terminal or command prompt and run:
        ```bash
        pip install pygame
        ```
    * Save the game script as `thrust.py` (or ensure it is already named this).
    * Open your terminal or command prompt.
    * Navigate to the directory where you saved `thrust.py`.
    * Run the game using the command:
        ```bash
        python thrust.py
        ```

## Controls

* **Up Arrow / W:** Apply thrust
* **Left Arrow / A:** Rotate ship counter-clockwise
* **Right Arrow / D:** Rotate ship clockwise
* **Left Shift / Right Shift + Thrust:** Activate boost
* **Spacebar:** Fire laser (cannot fire when landed)
* **Enter / Keypad Enter (in menu):** Start game
* **Escape:** Quit game / Return to menu

## Goal

* **Collect all beacons** on each level to proceed to the next.
* **Avoid crashing** into obstacles or the ground.
* **Land safely** on the ground (upright, low speed) to refuel and complete landings.
* **Manage your fuel:** Running out of fuel in mid-air will cost you a ship.
* **Achieve the highest score!**

## High Scores

The game saves the top 3 high scores in a file named `pythrust_highscores.txt` in the same directory as the game executable or script.

---

Enjoy playing PyThrust II!
