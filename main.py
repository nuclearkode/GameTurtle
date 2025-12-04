#!/usr/bin/env python3
"""
Main entry point for Robo Arena game.
Advanced Turtle Arena Game Engine with ECS architecture.
"""

import turtle
from game_engine.game.game_loop import GameLoop


def main():
    """Main function"""
    # Create screen
    screen = turtle.Screen()
    screen.setup(width=900, height=900)
    
    # Create and run game loop
    game_loop = GameLoop(screen, target_fps=60)
    game_loop.run()


if __name__ == "__main__":
    main()
