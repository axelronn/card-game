from typing import Literal

from pydantic import BaseModel

from cardgame.engine.models import PlayerSlot


class UseMoveAction(BaseModel):
    kind: Literal["use_move"] = "use_move"
    actor_player: PlayerSlot
    actor_instance_id: str
    move_id: str


class SwapAction(BaseModel):
    kind: Literal["swap"] = "swap"
    actor_player: PlayerSlot
    active_instance_id: str
    bench_instance_id: str


class ReplaceFaintedAction(BaseModel):
    kind: Literal["replace_fainted"] = "replace_fainted"
    actor_player: PlayerSlot
    fainted_instance_id: str
    bench_instance_id: str


class EndTurnAction(BaseModel):
    kind: Literal["end_turn"] = "end_turn"
    actor_player: PlayerSlot


Action = UseMoveAction | SwapAction | ReplaceFaintedAction | EndTurnAction
