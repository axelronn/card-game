from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from cardgame.cards.registry import all_mercs, get_merc
from cardgame.engine.actions import (
    EndTurnAction,
    ReplaceFaintedAction,
    SwapAction,
    UseMoveAction,
)
from cardgame.engine.bot_driver import advance_bot_turns
from cardgame.engine.match import InvalidActionError, apply_action, start_match
from cardgame.engine.models import GameState, MercDef, PlayerSlot

app: FastAPI = FastAPI(title="Cardgame API", version="0.0.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory match store. Assumption: single-process, no persistence.
# Matches are lost on server restart. Fine for v0.
_matches: dict[str, GameState] = {}


class NewMatchRequest(BaseModel):
    seed: int = 0
    player_name: str = "Player"
    party_merc_ids: list[str]


class ActionRequest(BaseModel):
    # Discriminated union so the client can submit any legal action shape.
    action: UseMoveAction | SwapAction | ReplaceFaintedAction | EndTurnAction


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/mercs")
def list_mercs() -> list[MercDef]:
    return all_mercs()


@app.post("/match/new")
def new_match(*, req: NewMatchRequest) -> GameState:
    if len(req.party_merc_ids) != 6:
        raise HTTPException(status_code=400, detail="Party must contain exactly 6 merc ids")
    try:
        player_party: list[MercDef] = [get_merc(merc_id=mid) for mid in req.party_merc_ids]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Bot party is the first 6 mercs in the registry for now.
    # Assumption: bot party is fixed. We'll add difficulty tiers / randomised parties later.
    bot_party: list[MercDef] = all_mercs()[:6]

    state: GameState = start_match(
        seed=req.seed,
        player_a_name=req.player_name,
        player_b_name="Bot",
        player_a_is_bot=False,
        player_b_is_bot=True,
        player_a_party=player_party,
        player_b_party=bot_party,
    )

    # If the bot happens to go first, play its turn immediately so the client
    # always sees a state where it's their turn (or the match is over).
    state = advance_bot_turns(state=state)

    _matches[state.match_id] = state
    return state


@app.get("/match/{match_id}")
def get_match(*, match_id: str) -> GameState:
    state: GameState | None = _matches.get(match_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return state


@app.post("/match/{match_id}/action")
def submit_action(*, match_id: str, req: ActionRequest) -> GameState:
    state: GameState | None = _matches.get(match_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Match not found")

    # Only the human (player A) should be submitting actions via this endpoint.
    if req.action.actor_player != PlayerSlot.PLAYER_A:
        raise HTTPException(
            status_code=400, detail="Only player_a can submit actions via this endpoint"
        )

    try:
        state = apply_action(state=state, action=req.action)
    except InvalidActionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # After the human's action, let the bot take any turns it owes.
    state = advance_bot_turns(state=state)

    _matches[match_id] = state
    return state
