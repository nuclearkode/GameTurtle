"""
GameState - manages overall game state (playing, paused, game over, etc.)
"""

from enum import Enum
from dataclasses import dataclass


class GameStateType(Enum):
    """Game state types"""
    MENU = "menu"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    UPGRADE_SCREEN = "upgrade_screen"


@dataclass
class GameState:
    """Current game state"""
    state: GameStateType = GameStateType.PLAYING
    score: int = 0
    wave: int = 0
    
    def is_playing(self) -> bool:
        """Check if game is actively playing"""
        return self.state == GameStateType.PLAYING
    
    def pause(self) -> None:
        """Pause the game"""
        if self.state == GameStateType.PLAYING:
            self.state = GameStateType.PAUSED
    
    def resume(self) -> None:
        """Resume the game"""
        if self.state == GameStateType.PAUSED:
            self.state = GameStateType.PLAYING
    
    def toggle_pause(self) -> None:
        """Toggle pause state"""
        if self.state == GameStateType.PLAYING:
            self.pause()
        elif self.state == GameStateType.PAUSED:
            self.resume()
