"""
Robo-Arena Main Entry Point

Top-down arena shooter with ECS architecture.
"""

import sys
from engine.core.game_engine import GameEngine
from engine.core.entity import EntityManager
from engine.systems.physics_system import PhysicsSystem
from engine.systems.collision_system import CollisionSystem
from engine.systems.render_system import RenderSystem
from engine.systems.player_system import PlayerSystem
from engine.systems.weapon_system import WeaponSystem
from engine.systems.health_system import HealthSystem
from engine.systems.ai_system import AISystem
from engine.systems.wave_system import WaveSystem
from engine.systems.pathfinding_system import PathfindingSystem
from engine.systems.powerup_system import PowerUpSystem
from engine.systems.particle_system import ParticleSystem
from game.config import *
from game.factory import *


class RoboArena:
    """Main game class."""
    
    def __init__(self):
        self.engine = GameEngine(
            width=ARENA_WIDTH,
            height=ARENA_HEIGHT,
            target_fps=TARGET_FPS
        )
        
        # Systems will be created after engine initialization
        self.collision_system = None
        self.weapon_system = None
        self.wave_system = None
        self.particle_system = None
    
    def setup(self):
        """Setup game systems and initial entities."""
        print("\n" + "="*50)
        print("ROBO-ARENA - ECS Game Engine")
        print("="*50)
        print("\nInitializing engine...")
        
        # Initialize engine
        self.engine.initialize()
        
        print("Creating systems...")
        
        # Create systems in priority order
        # Priority determines execution order (lower = earlier)
        
        # Player input (priority 0 - first)
        player_system = PlayerSystem(
            self.engine.entity_manager,
            self.engine.input_manager,
            priority=0
        )
        
        # AI (priority 5)
        ai_system = AISystem(
            self.engine.entity_manager,
            priority=5
        )
        
        # Physics (priority 10)
        physics_system = PhysicsSystem(
            self.engine.entity_manager,
            priority=10
        )
        
        # Weapon system (priority 15)
        self.weapon_system = WeaponSystem(
            self.engine.entity_manager,
            priority=15
        )
        
        # Connect weapon system to player and AI
        player_system.weapon_system = self.weapon_system
        ai_system.weapon_system = self.weapon_system
        
        # Collision detection (priority 20)
        self.collision_system = CollisionSystem(
            self.engine.entity_manager,
            priority=20
        )
        
        # Health system (priority 30)
        health_system = HealthSystem(
            self.engine.entity_manager,
            self.collision_system,
            priority=30
        )
        
        # Wave system (priority 40)
        self.wave_system = WaveSystem(
            self.engine.entity_manager,
            priority=40
        )
        
        # Pathfinding (priority 50)
        pathfinding_system = PathfindingSystem(
            self.engine.entity_manager,
            priority=50
        )
        
        # Power-up system (priority 60)
        powerup_system = PowerUpSystem(
            self.engine.entity_manager,
            self.collision_system,
            priority=60
        )
        
        # Particle system (priority 80)
        self.particle_system = ParticleSystem(
            self.engine.entity_manager,
            priority=80
        )
        
        # Render system (priority 90 - last before display)
        render_system = RenderSystem(
            self.engine.entity_manager,
            self.engine.screen,
            priority=90
        )
        
        # Add all systems to engine
        self.engine.add_system(player_system)
        self.engine.add_system(ai_system)
        self.engine.add_system(physics_system)
        self.engine.add_system(self.weapon_system)
        self.engine.add_system(self.collision_system)
        self.engine.add_system(health_system)
        self.engine.add_system(self.wave_system)
        self.engine.add_system(pathfinding_system)
        self.engine.add_system(powerup_system)
        self.engine.add_system(self.particle_system)
        self.engine.add_system(render_system)
        
        print(f"Created {len(self.engine.system_manager.systems)} systems")
        
        # Create initial entities
        print("\nCreating game entities...")
        self._create_game_world()
        
        # Register enemy spawn functions with wave system
        self.wave_system.set_spawn_function('chaser', create_chaser)
        self.wave_system.set_spawn_function('turret', create_turret)
        self.wave_system.set_spawn_function('swarm', create_swarm)
        self.wave_system.set_spawn_function('boss', create_boss)
        
        print(f"Created {self.engine.entity_manager.entity_count()} initial entities")
        
        print("\n" + "="*50)
        print("CONTROLS:")
        print("  WASD / Arrow Keys - Move")
        print("  Q/E - Rotate")
        print("  SPACE - Fire")
        print("  ESC - Pause")
        print("  Q (in menu) - Quit")
        print("="*50)
        print("\nStarting game...\n")
    
    def _create_game_world(self):
        """Create initial game entities."""
        em = self.engine.entity_manager
        
        # Create arena
        create_arena(em)
        
        # Create player at center
        create_player(em, 0, 0)
        
        # Create some walls for cover
        walls_positions = [
            (-200, -150),
            (200, -150),
            (-200, 150),
            (200, 150),
            (0, 100),
            (0, -100),
        ]
        
        for x, y in walls_positions:
            create_wall(em, x, y)
        
        # Wave system will spawn enemies
    
    def run(self):
        """Run the game."""
        try:
            self.engine.start()
        except KeyboardInterrupt:
            print("\n\nGame interrupted by user")
        except Exception as e:
            print(f"\n\nError: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.engine.cleanup()
            print("\nThanks for playing Robo-Arena!")


def main():
    """Main entry point."""
    game = RoboArena()
    game.setup()
    game.run()


if __name__ == "__main__":
    main()
