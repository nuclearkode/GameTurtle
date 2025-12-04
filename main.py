#!/usr/bin/env python3
"""
Advanced Turtle Arena Game Engine - Main Entry Point

A modern ECS-based game engine built on Python's turtle library.
"""

from game_engine.game import GameLoop


def main():
    """Main entry point."""
    print("Starting Robo-Arena Game Engine...")
    print("Controls:")
    print("  W/A/S/D - Move")
    print("  Q/E - Rotate")
    print("  Space - Fire")
    print("  Escape - Quit")
    print()
    
    # Create and start game
    game = GameLoop(target_fps=60.0, arena_size=800)
    try:
        game.start()
    except KeyboardInterrupt:
        print("\nGame interrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
