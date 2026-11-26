from pydantic import BaseModel


class InputPayload(BaseModel):
    mx: float = 0.0
    my: float = 0.0


class SpawnPayload(BaseModel):
    enemy_type: str = "goblin"