# Quick Start Guide

## Running the Game

```bash
python main.py
```

## Controls

- **W/A/S/D**: Move player
- **Q/E**: Rotate left/right  
- **Spacebar**: Fire weapon
- **P**: Pause/Unpause
- **Escape**: Quit game

## What You'll See

1. **Player**: Blue triangle in the center
2. **Arena**: Gray grid with boundaries
3. **Enemies**: 
   - Red circles = Chasers (rush toward you)
   - Orange squares = Turrets (stationary, shoot at you)
   - Pink circles = Swarm bots (flocking behavior)
   - Purple circles = Bosses (every 5 waves)

4. **Projectiles**: Yellow circles fired by player and enemies

## Gameplay

- Waves of enemies spawn automatically
- Defeat all enemies to complete a wave
- New waves spawn after a short delay
- Difficulty increases with each wave
- Boss enemies appear every 5 waves

## Architecture Highlights

### ECS Pattern
- **Entities**: Just IDs (UUIDs)
- **Components**: Pure data (Transform, Health, Weapon, etc.)
- **Systems**: Behavior/logic (PhysicsSystem, AISystem, etc.)

### Key Files
- `main.py`: Entry point
- `game_engine/game/game_loop.py`: Main game loop
- `game_engine/core/`: ECS primitives
- `game_engine/systems/`: Game systems

### Extending the Game

See `DESIGN_SUMMARY.md` for detailed instructions on:
- Adding new enemy types
- Creating new components
- Implementing new systems
- Adding features

## Troubleshooting

**Game won't start?**
- Ensure Python 3.7+ is installed
- Check that all files are present

**Performance issues?**
- Reduce target FPS in `GameLoop.__init__()`
- Reduce enemy spawn count in `WaveSystem._spawn_wave()`

**Want to modify gameplay?**
- Player stats: `GameLoop._create_player()`
- Enemy stats: `WaveSystem._spawn_enemy()`
- Weapon stats: `Weapon` component defaults

## Next Steps

1. Play the game and understand the mechanics
2. Read `ARCHITECTURE.md` for design details
3. Read `DESIGN_SUMMARY.md` for extension guide
4. Modify components/systems to add features
5. Experiment with new enemy types and behaviors
