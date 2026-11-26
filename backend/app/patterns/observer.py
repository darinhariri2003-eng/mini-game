from abc import ABC, abstractmethod
from typing import List, Dict, Any


class GameObserver(ABC):
    @abstractmethod
    def on_frame_tick(self, frame: int, dt: float, state_snapshot: Dict[str, Any]) -> None:
        pass


class UINotifier(GameObserver):
    def __init__(self):
        self.last_summary: str = ""

    def on_frame_tick(self, frame: int, dt: float, state_snapshot: Dict[str, Any]) -> None:
        enemy_count = len(state_snapshot.get("enemies", []))
        wave = state_snapshot.get("wave", 1)
        player_state = state_snapshot.get("player", {}).get("state", "IdleState")
        self.last_summary = f"Frame #{frame} | Wave {wave} | Enemies: {enemy_count} | {player_state}"


class AudioEngine(GameObserver):
    def __init__(self):
        self.queued_cues: List[str] = []

    def emit_cue(self, cue: str) -> None:
        self.queued_cues.append(cue)

    def consume_cues(self) -> List[str]:
        cues = list(self.queued_cues)
        self.queued_cues.clear()
        return cues

    def on_frame_tick(self, frame: int, dt: float, state_snapshot: Dict[str, Any]) -> None:
        if frame % 120 == 0:
            self.emit_cue("heartbeat")


class GameLoopSubject:
    def __init__(self):
        self._observers: List[GameObserver] = []

    def attach(self, observer: GameObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: GameObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, frame: int, dt: float, state_snapshot: Dict[str, Any]) -> None:
        for obs in list(self._observers):
            obs.on_frame_tick(frame, dt, state_snapshot)