from typing import Dict, Any, List
import math
import random
import time

from .patterns import (
    Enemy,
    GoblinFactory,
    BossFactory,
    BaseCharacter,
    GameObjectGroup,
    PlayerContext,
    UINotifier,
    AudioEngine,
    GameLoopSubject,
)


class GameEngine:
    def __init__(self, width: float = 920.0, height: float = 540.0):
        self.width = width
        self.height = height
        self.goblin_factory = GoblinFactory()
        self.boss_factory = BossFactory()

        self.ui_notifier = UINotifier()
        self.audio_engine = AudioEngine()
        self.loop_subject = GameLoopSubject()
        self.loop_subject.attach(self.ui_notifier)
        self.loop_subject.attach(self.audio_engine)

        self.reset()

    def reset(self) -> None:
        self._id_counter = 0
        self.frame = 0
        self.wave = 1
        self.score = 0
        self.running = False
        self.events: List[Dict[str, Any]] = []
        self.fx_list: List[Dict[str, Any]] = []
        self.enemies: List[Enemy] = []

        self.player = PlayerContext("player_1", "Hero", self.width * 0.5, self.height * 0.5)
        self.scene_root = GameObjectGroup("scene_root", "ArenaScene")
        self.player_node = BaseCharacter(self.player, role="player")
        self.active_wave_group = GameObjectGroup("wave_1_group", "Wave 1 Squad")

        self.scene_root.add(self.player_node)
        self.scene_root.add(self.active_wave_group)

        self.record_event("Engine", "Engine initialized & reset")
        self.spawn_wave(1)

    def _next_id(self, prefix: str) -> str:
        self._id_counter += 1
        return f"{prefix}_{self._id_counter}"

    def record_event(self, pattern: str, message: str) -> None:
        self.events.insert(0, {
            "frame": self.frame,
            "pattern": pattern,
            "message": message,
            "ts": round(time.time(), 2),
        })
        self.events = self.events[:35]

    def _random_edge_position(self) -> tuple[float, float]:
        side = random.choice(["top", "bottom", "left", "right"])
        margin = 36.0
        if side == "top":
            return random.uniform(margin, self.width - margin), margin
        if side == "bottom":
            return random.uniform(margin, self.width - margin), self.height - margin
        if side == "left":
            return margin, random.uniform(margin, self.height - margin)
        return self.width - margin, random.uniform(margin, self.height - margin)

    def spawn_enemy(self, enemy_type: str) -> Dict[str, Any]:
        scale = 1.0 + (self.wave - 1) * 0.15
        x, y = self._random_edge_position()
        if enemy_type.lower() == "boss":
            enemy = self.boss_factory.create_enemy(self._next_id("boss"), x, y, scale)
            creator_name = "BossFactory"
        else:
            enemy = self.goblin_factory.create_enemy(self._next_id("goblin"), x, y, scale)
            creator_name = "GoblinFactory"

        self.enemies.append(enemy)
        leaf = BaseCharacter(enemy, role="enemy")
        self.active_wave_group.add(leaf)
        self.audio_engine.emit_cue("spawn")
        self.record_event("Factory Method", f"{creator_name} created {enemy.name} ({enemy.id})")
        return enemy.to_dict()

    def spawn_wave(self, wave_num: int) -> None:
        self.wave = wave_num
        self.active_wave_group = GameObjectGroup(f"wave_{wave_num}_group", f"Wave {wave_num} Squad")
        self.scene_root.children = [self.player_node, self.active_wave_group]

        goblin_count = 3 + wave_num * 2
        for _ in range(goblin_count):
            self.spawn_enemy("goblin")

        if wave_num % 2 == 0:
            self.spawn_enemy("boss")

        self.record_event("Composite", f"Built {self.active_wave_group.name} with {len(self.enemies)} enemies")

    def resolve_player_attack(self, player: PlayerContext) -> None:
        self.audio_engine.emit_cue("slash")
        self.fx_list.append({
            "kind": "slash",
            "x": round(player.x + player.facing_x * 26, 1),
            "y": round(player.y + player.facing_y * 26, 1),
            "radius": player.attack_radius,
            "ttl": 0.22,
        })

        hit_any = False
        for enemy in list(self.enemies):
            if not enemy.alive:
                continue
            dx = enemy.x - player.x
            dy = enemy.y - player.y
            dist = math.hypot(dx, dy)
            if dist <= player.attack_radius + enemy.radius:
                hit_any = True
                nx = dx / (dist or 1.0)
                ny = dy / (dist or 1.0)
                enemy.hp -= player.attack_damage
                enemy.vx += nx * 260.0
                enemy.vy += ny * 260.0
                enemy.hit_flash = 1.0
                self.fx_list.append({
                    "kind": "hit",
                    "x": round(enemy.x, 1),
                    "y": round(enemy.y, 1),
                    "dmg": int(player.attack_damage),
                    "ttl": 0.45,
                })
                if enemy.hp <= 0:
                    enemy.alive = False
                    self.score += 100 if enemy.enemy_type() == "boss" else 25
                    self.audio_engine.emit_cue("kill")
                    self.record_event("Physics", f"{enemy.name} defeated (+{100 if enemy.enemy_type() == 'boss' else 25} pts)")

        if hit_any:
            self.audio_engine.emit_cue("hit")

        alive_enemies = []
        for enemy in self.enemies:
            if enemy.alive:
                alive_enemies.append(enemy)
            else:
                child = self.active_wave_group.get_child(enemy.id)
                if child:
                    self.active_wave_group.remove(child)
        self.enemies = alive_enemies

        if len(self.enemies) == 0 and player.alive:
            self.score += 50 * self.wave
            self.spawn_wave(self.wave + 1)

    def _resolve_enemy_collisions(self, dt: float) -> None:
        for i in range(len(self.enemies)):
            for j in range(i + 1, len(self.enemies)):
                a = self.enemies[i]
                b = self.enemies[j]
                if not (a.alive and b.alive):
                    continue
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.hypot(dx, dy)
                min_dist = a.radius + b.radius
                if 0 < dist < min_dist:
                    overlap = (min_dist - dist) * 0.5
                    nx = dx / dist
                    ny = dy / dist
                    a.x -= nx * overlap
                    a.y -= ny * overlap
                    b.x += nx * overlap
                    b.y += ny * overlap

        if not self.player.alive:
            return
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = math.hypot(dx, dy)
            min_dist = self.player.radius + enemy.radius
            if dist < min_dist and self.player.state.name != "AttackingState":
                nx = dx / (dist or 1.0)
                ny = dy / (dist or 1.0)
                self.player.take_damage(enemy.attack_damage * dt * 2.2, nx * 90.0, ny * 90.0, self)

    def step(self, dt: float = 1.0 / 60.0) -> Dict[str, Any]:
        self.frame += 1

        world_context = {
            "player": self.player,
            "width": self.width,
            "height": self.height,
        }

        self.scene_root.update(dt, world_context)
        self.player.update(dt, self)
        self._resolve_enemy_collisions(dt)

        next_fx = []
        for fx in self.fx_list:
            fx["ttl"] -= dt
            if fx["ttl"] > 0:
                next_fx.append(fx)
        self.fx_list = next_fx

        snapshot = self.get_snapshot()
        self.loop_subject.notify(self.frame, dt, snapshot)
        snapshot["audio_cues"] = self.audio_engine.consume_cues()
        snapshot["ui_summary"] = self.ui_notifier.last_summary
        return snapshot

    def get_snapshot(self) -> Dict[str, Any]:
        return {
            "frame": self.frame,
            "wave": self.wave,
            "score": self.score,
            "running": self.running,
            "width": self.width,
            "height": self.height,
            "player": self.player.to_dict(),
            "enemies": [e.to_dict() for e in self.enemies if e.alive],
            "fx": self.fx_list,
            "scene_tree": self.scene_root.to_tree(),
            "events": self.events[:15],
        }