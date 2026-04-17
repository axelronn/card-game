from enum import StrEnum

from pydantic import BaseModel, Field

from cardgame.engine.effects import Effect


class MoveDef(BaseModel):
    # Static definition of a move. Lives on a merc's movelist.

    move_id: str
    name: str
    description: str
    effects: list[Effect]


class MercDef(BaseModel):
    # Static definition of a merc. Loaded from the card registry.

    merc_id: str
    name: str
    max_hp: int
    attack: int
    defense: int
    moves: list[MoveDef]


class MercInstance(BaseModel):
    # A merc as it exists inside a specific match.
    # Holds mutable state (current HP, temporary buffs) on top of the static definition.

    instance_id: str
    definition: MercDef
    current_hp: int
    attack_bonus: int = 0
    defense_bonus: int = 0

    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    @property
    def effective_attack(self) -> int:
        return self.definition.attack + self.attack_bonus

    @property
    def effective_defense(self) -> int:
        return self.definition.defense + self.defense_bonus


class PlayerSlot(StrEnum):
    PLAYER_A = "player_a"
    PLAYER_B = "player_b"


class PlayerState(BaseModel):
    # State for one side of the match.

    slot: PlayerSlot
    display_name: str
    is_bot: bool
    active: list[MercInstance] = Field(min_length=0, max_length=3)
    bench: list[MercInstance]

    @property
    def all_mercs(self) -> list[MercInstance]:
        return [*self.active, *self.bench]

    @property
    def living_mercs(self) -> list[MercInstance]:
        return [m for m in self.all_mercs if m.is_alive]

    @property
    def has_lost(self) -> bool:
        return len(self.living_mercs) == 0


class MatchPhase(StrEnum):
    AWAITING_ACTION = "awaiting_action"
    RESOLVING = "resolving"
    AWAITING_REPLACEMENT = "awaiting_replacement"
    FINISHED = "finished"


class GameState(BaseModel):
    # Authoritative state of a match. Engine functions take this in and return a new one.
    # Immutable-in-spirit: we use Pydantic model_copy to produce new states rather than
    # mutating (though the current resolver actually mutates — this is the ideal we should
    # migrate toward).

    match_id: str
    seed: int
    turn_number: int
    active_player: PlayerSlot
    phase: MatchPhase
    player_a: PlayerState
    player_b: PlayerState
    winner: PlayerSlot | None = None
    log: list[str] = Field(default_factory=list)

    def player(self, *, slot: PlayerSlot) -> PlayerState:
        return self.player_a if slot == PlayerSlot.PLAYER_A else self.player_b

    def opponent(self, *, slot: PlayerSlot) -> PlayerState:
        return self.player_b if slot == PlayerSlot.PLAYER_A else self.player_a
