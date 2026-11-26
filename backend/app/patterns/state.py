from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from ..engine import GameEngine


class PlayerState(ABC):
    name: str = "BaseState"

    @abstractmethod
    def enter(self, ctx: "PlayerContext") -> None:
        pass

    @abstractmethod
    def update(self, ctx: "PlayerContext", dt: float, engine: "GameEngine") -> None:
        pass

    @abstractmethod
    def request_attack(self, ctx: "PlayerContext", engine: "GameEngine") -> bool:
        pass


class IdleState(PlayerState):
    name = "IdleState"

    def enter(self, ctx: "PlayerContext") -> None:
        ctx.attack_cooldown = 0.0

    def update(self, ctx: "PlayerContext", dt: float, engine: "GameEngine") -> None:
        if ctx.hp <= 0:
            ctx.set_state(DeadState(), engine)
            return

        ctx.stamina = min(ctx.max_stamina, ctx.stamina + 24.0 * dt)
        ctx.apply_movement_physics(dt, engine.width, engine.height, speed_multiplier=1.0)

    def request_attack(self, ctx: "PlayerContext", engine: "GameEngine") -> bool:
        if ctx.stamina >= 20.0:
            ctx.stamina -= 20.0
            ctx.set_state(AttackingState(), engine)
            return True
        return False


class AttackingState(PlayerState):
    name = "AttackingState"

    def enter(self, ctx: "PlayerContext") -> None:
        ctx.attack_timer = 0.28
        ctx.has_dealt_swing_damage = False

    def update(self, ctx: "PlayerContext", dt: float, engine: "GameEngine") -> None:
        if ctx.hp <= 0:
            ctx.set_state(DeadState(), engine)
            return

        ctx.attack_timer -= dt
        ctx.apply_movement_physics(dt, engine.width, engine.height, speed_multiplier=1.25)

        if not ctx.has_dealt_swing_damage:
            ctx.has_dealt_swing_damage = True
            engine.resolve_player_attack(ctx)

        if ctx.attack_timer <= 0:
            ctx.set_state(IdleState(), engine)

    def request_attack(self, ctx: "PlayerContext", engine: "GameEngine") -> bool:
        return False


class DeadState(PlayerState):
    name = "DeadState"

    def enter(self, ctx: "PlayerContext") -> None:
        ctx.hp = 0.0
        ctx.vx = 0.0
        ctx.vy = 0.0
        ctx.move_x = 0.0
        ctx.move_y = 0.0

    def update(self, ctx: "PlayerContext", dt: float, engine: "GameEngine") -> None:
        pass

    def request_attack(self, ctx: "PlayerContext", engine: "GameEngine") -> bool:
        return False


class PlayerContext:
    def __init__(self, obj_id: str, name: str, x: float, y: float):
        self.id = obj_id
        self.name = name
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.move_x = 0.0
        self.move_y = 0.0
        self.facing_x = 1.0
        self.facing_y = 0.0
        self.hp = 100.0
        self.max_hp = 100.0
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.speed = 230.0
        self.attack_damage = 35.0
        self.attack_radius = 95.0
        self.radius = 18.0
        self.alive = True
        self.hit_flash = 0.0
        self.attack_timer = 0.0
        self.attack_cooldown = 0.0
        self.has_dealt_swing_damage = False
        self.state: PlayerState = IdleState()
        self.state.enter(self)

    def set_input(self, mx: float, my: float) -> None:
        mag = math.hypot(mx, my)
        if mag > 1.0:
            mx /= mag
            my /= mag
        self.move_x = mx
        self.move_y = my
        if mag > 0.05:
            self.facing_x = mx
            self.facing_y = my

    def set_state(self, new_state: PlayerState, engine: "GameEngine") -> None:
        prev = self.state.name
        self.state = new_state
        self.state.enter(self)
        if prev != new_state.name:
            engine.record_event("State", f"Player state: {prev} -> {new_state.name}")

    def apply_movement_physics(self, dt: float, width: float, height: float, speed_multiplier: float = 1.0) -> None:
        if self.hit_flash > 0:
            self.hit_flash = max(0.0, self.hit_flash - dt * 4.0)

        target_vx = self.move_x * self.speed * speed_multiplier
        target_vy = self.move_y * self.speed * speed_multiplier

        damping = math.exp(-11.0 * dt)
        self.vx = self.vx * damping + target_vx * (1.0 - damping)
        self.vy = self.vy * damping + target_vy * (1.0 - damping)

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.x = max(self.radius, min(width - self.radius, self.x))
        self.y = max(self.radius, min(height - self.radius, self.y))

    def update(self, dt: float, engine: "GameEngine") -> None:
        self.state.update(self, dt, engine)

    def attack(self, engine: "GameEngine") -> bool:
        return self.state.request_attack(self, engine)

    def take_damage(self, amount: float, kx: float, ky: float, engine: "GameEngine") -> None:
        if not self.alive:
            return
        self.hp = max(0.0, self.hp - amount)
        self.vx += kx
        self.vy += ky
        self.hit_flash = 1.0
        engine.record_event("Physics", f"Player took {amount:.0f} DMG (HP: {self.hp:.0f})")
        if self.hp <= 0:
            self.alive = False
            self.set_state(DeadState(), engine)

    def revive(self, engine: "GameEngine") -> None:
        self.alive = True
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.vx = 0.0
        self.vy = 0.0
        self.set_state(IdleState(), engine)
        engine.record_event("State", "Player revived -> IdleState")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "vx": round(self.vx, 1),
            "vy": round(self.vy, 1),
            "facing_x": round(self.facing_x, 2),
            "facing_y": round(self.facing_y, 2),
            "hp": round(self.hp, 1),
            "max_hp": self.max_hp,
            "stamina": round(self.stamina, 1),
            "max_stamina": self.max_stamina,
            "radius": self.radius,
            "attack_radius": self.attack_radius,
            "state": self.state.name,
            "alive": self.alive,
            "hit_flash": round(self.hit_flash, 2),
        }