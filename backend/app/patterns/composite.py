from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import math


class GameObject(ABC):
    def __init__(self, obj_id: str, name: str):
        self.id = obj_id
        self.name = name

    @abstractmethod
    def update(self, dt: float, world_context: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def to_tree(self) -> Dict[str, Any]:
        pass


class BaseCharacter(GameObject):
    def __init__(self, entity: Any, role: str = "enemy"):
        super().__init__(entity.id, entity.name)
        self.entity = entity
        self.role = role

    def update(self, dt: float, world_context: Dict[str, Any]) -> None:
        if not self.entity.alive:
            return

        if getattr(self.entity, "hit_flash", 0.0) > 0:
            self.entity.hit_flash = max(0.0, self.entity.hit_flash - dt * 4.0)

        player = world_context.get("player")
        width = world_context.get("width", 920.0)
        height = world_context.get("height", 540.0)

        if player and self.role == "enemy":
            dx = player.x - self.entity.x
            dy = player.y - self.entity.y
            dist = math.hypot(dx, dy) or 1.0
            desired_vx = (dx / dist) * self.entity.speed
            desired_vy = (dy / dist) * self.entity.speed

            damping = math.exp(-6.5 * dt)
            self.entity.vx = self.entity.vx * damping + desired_vx * (1.0 - damping)
            self.entity.vy = self.entity.vy * damping + desired_vy * (1.0 - damping)

        self.entity.x += self.entity.vx * dt
        self.entity.y += self.entity.vy * dt

        r = self.entity.radius
        self.entity.x = max(r, min(width - r, self.entity.x))
        self.entity.y = max(r, min(height - r, self.entity.y))

    def to_tree(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": "Leaf (BaseCharacter)",
            "role": self.role,
            "alive": self.entity.alive,
            "hp": round(max(0.0, self.entity.hp), 1),
            "children": [],
        }


class GameObjectGroup(GameObject):
    def __init__(self, obj_id: str, name: str):
        super().__init__(obj_id, name)
        self.children: List[GameObject] = []

    def add(self, child: GameObject) -> None:
        self.children.append(child)

    def remove(self, child: GameObject) -> None:
        if child in self.children:
            self.children.remove(child)

    def get_child(self, obj_id: str) -> Optional[GameObject]:
        for child in self.children:
            if child.id == obj_id:
                return child
        return None

    def update(self, dt: float, world_context: Dict[str, Any]) -> None:
        for child in list(self.children):
            child.update(dt, world_context)

    def to_tree(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": "Composite (GameObjectGroup)",
            "alive": True,
            "children": [child.to_tree() for child in self.children],
        }