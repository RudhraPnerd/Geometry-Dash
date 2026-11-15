# Geometry Dash - Stereo Madness (Pygame Edition)

A modular Geometry Dash clone built in Python and Pygame with Cube and Ship game modes, Practice Mode checkpoints, particle effects, custom soundtrack & sound effects, and persistent JSON configuration.

## Folder Structure

```text
GeometryDashPygame/
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # Documentation
├── config/
│   └── config.json             # Physics, window, audio, colors & saved high scores
├── assets/
│   └── audio/
│       ├── music/              # home.wav, stereo_madness.wav, practice.wav
│       └── sfx/                # start.wav, death.wav, jump.wav, orb.wav, pad.wav, portal.wav, checkpoint.wav, win.wav
└── src/
    ├── core/
    │   ├── audio_manager.py    # Music & sound effect playback controller
    │   ├── camera.py           # Horizontal/vertical camera tracking & screen shake
    │   └── game.py             # Main loop and game state machine
    ├── entities/
    │   ├── obstacles.py        # Blocks, slabs, spikes, jump orbs, jump pads, portals & finish gate
    │   ├── particles.py        # Trail sparks, jump dust, orb bursts & shatter explosions
    │   └── player.py           # Cube & Ship physics and procedural icon rendering
    ├── level/
    │   ├── collision.py        # Platform landing, hazard detection & interactive triggers
    │   └── level_loader.py     # Stereo Madness multi-section level builder
    ├── ui/
    │   └── renderer.py         # Parallax background, floor grid, HUD & menu/pause/victory screens
    └── utils/
        ├── config_manager.py   # Reads & persists config/config.json
        └── math_helpers.py     # Interpolation, angle snapping & pulse math
```

## Quick Start

1. Install Pygame:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the game from inside the `GeometryDashPygame` folder:
   ```bash
   python main.py
   ```

## Controls

- **Space / Up / W / Left Click**: Start game, Jump (Cube), or Hold to Fly (Ship)
- **Tab** (on Main Menu): Toggle between **Normal Mode** and **Practice Mode**
- **Z** (in Practice Mode): Place a manual checkpoint
- **P**: Pause / Resume
- **R**: Quick Restart
- **M**: Mute / Unmute Audio
- **Esc**: Return to Main Menu
