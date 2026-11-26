from abc import ABC, abstractmethod
from typing import Dict, Any
import random


class Enemy(ABC):
    def __init__(self, obj_id: str, name: str, x: float, y: float, hp: float, speed: float, attack_damage: float, radius: float):
        self.id = obj_id
        self.name = name
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.attack_damage = attack_damage
        self.radius = radius
        self.alive = True
        self.hit_flash = 0.0

    @abstractmethod
    def enemy_type(self) -> str:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.enemy_type(),
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "hp": round(max(0.0, self.hp), 1),
            "max_hp": self.max_hp,
            "radius": self.radius,
            "alive": self.alive,
            "hit_flash": round(self.hit_flash, 2),
        }


class Goblin(Enemy):
    def __init__(self, obj_id: str, x: float, y: float, level_scale: float = 1.0):
        super().__init__(
            obj_id=obj_id,
            name="Goblin",
            x=x,
            y=y,
            hp=45.0 * level_scale,
            speed=115.0,
            attack_damage=10.0 * level_scale,
            radius=16.0,
        )

    def enemy_type(self) -> str:
        return "goblin"


class Boss(Enemy):
    def __init__(self, obj_id: str, x: float, y: float, level_scale: float = 1.0):
        super().__init__(
            obj_id=obj_id,
            name="Boss",
            x=x,
            y=y,
            hp=220.0 * level_scale,
            speed=65.0,
            attack_damage=24.0 * level_scale,
            radius=30.0,
        )

    def enemy_type(self) -> str:
        return "boss"


class EnemyFactory(ABC):
    @abstractmethod
    def create_enemy(self, obj_id: str, x: float, y: float, level_scale: float = 1.0) -> Enemy:
        pass


class GoblinFactory(EnemyFactory):
    def create_enemy(self, obj_id: str, x: float, y: float, level_scale: float = 1.0) -> Enemy:
        jitter_x = random.uniform(-18, 18)
        jitter_y = random.uniform(-18, 18)
        return Goblin(obj_id=obj_id, x=x + jitter_x, y=y + jitter_y, level_scale=level_scale)


class BossFactory(EnemyFactory):
    def create_enemy(self, obj_id: str, x: float, y: float, level_scale: float = 1.0) -> Enemy:
        return Boss(obj_id=obj_id, x=x, y=y, level_scale=level_scale)