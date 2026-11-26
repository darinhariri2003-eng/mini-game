import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .engine import GameEngine
from .models import InputPayload, SpawnPayload

app = FastAPI(title="Mini Game Physics & Loop Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GameEngine()


@app.get("/api/state")
def get_state():
    return engine.get_snapshot()


@app.post("/api/control/{action}")
def control_action(action: str):
    if action == "start":
        engine.running = True
        engine.record_event("Observer", "Game loop started (running=True)")
    elif action == "pause":
        engine.running = False
        engine.record_event("Observer", "Game loop paused (running=False)")
    elif action == "step":
        return engine.step(1.0 / 60.0)
    elif action == "reset":
        engine.reset()
    elif action == "revive":
        engine.player.revive(engine)
    return engine.get_snapshot()


@app.post("/api/spawn")
def spawn_enemy(payload: SpawnPayload):
    engine.spawn_enemy(payload.enemy_type)
    return engine.get_snapshot()


@app.post("/api/input")
def set_input(payload: InputPayload):
    engine.player.set_input(payload.mx, payload.my)
    return {"ok": True}


@app.post("/api/attack")
def trigger_attack():
    started = engine.player.attack(engine)
    return {"ok": started, "state": engine.player.state.name}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json(engine.get_snapshot())
    try:
        while True:
            try:
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.016)
                mtype = msg.get("type")
                if mtype == "input":
                    engine.player.set_input(float(msg.get("mx", 0.0)), float(msg.get("my", 0.0)))
                elif mtype == "attack":
                    engine.player.attack(engine)
                elif mtype == "spawn":
                    engine.spawn_enemy(str(msg.get("enemy_type", "goblin")))
                elif mtype == "toggle_run":
                    engine.running = bool(msg.get("running", not engine.running))
                elif mtype == "step":
                    snap = engine.step(1.0 / 60.0)
                    await websocket.send_json(snap)
                    continue
                elif mtype == "reset":
                    engine.reset()
            except asyncio.TimeoutError:
                pass

            if engine.running:
                snap = engine.step(1.0 / 60.0)
                await websocket.send_json(snap)
            await asyncio.sleep(1.0 / 60.0)
    except WebSocketDisconnect:
        pass