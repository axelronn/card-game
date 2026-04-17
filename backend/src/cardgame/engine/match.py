import uuid

from cardgame.engine.actions import (
    Action,
    EndTurnAction,
    ReplaceFaintedAction,
    SwapAction,
    UseMoveAction,
)
from cardgame.engine.models import (
    GameState,
    MatchPhase,
    MercDef,
    MercInstance,
    PlayerSlot,
    PlayerState,
)
from cardgame.engine.resolver import apply_effect
from cardgame.engine.rng import SeededRng


class InvalidActionError(Exception):
    pass


def _instantiate_merc(*, definition: MercDef) -> MercInstance:
    return MercInstance(
        instance_id=str(uuid.uuid4()),
        definition=definition,
        current_hp=definition.max_hp,
    )


def start_match(
    *,
    seed: int,
    player_a_name: str,
    player_b_name: str,
    player_a_is_bot: bool,
    player_b_is_bot: bool,
    player_a_party: list[MercDef],
    player_b_party: list[MercDef],
) -> GameState:
    # Assumption: party is exactly 6 mercs. First 3 go to active, last 3 to bench.
    # Caller is responsible for ordering within the party (a user-facing decision
    # made at party-build time).
    if len(player_a_party) != 6 or len(player_b_party) != 6:
        raise InvalidActionError("Each party must contain exactly 6 mercs")

    rng: SeededRng = SeededRng(seed=seed)
    first_player: PlayerSlot = rng.choice(items=[PlayerSlot.PLAYER_A, PlayerSlot.PLAYER_B])

    a_instances: list[MercInstance] = [_instantiate_merc(definition=d) for d in player_a_party]
    b_instances: list[MercInstance] = [_instantiate_merc(definition=d) for d in player_b_party]

    return GameState(
        match_id=str(uuid.uuid4()),
        seed=seed,
        turn_number=1,
        active_player=first_player,
        phase=MatchPhase.AWAITING_ACTION,
        player_a=PlayerState(
            slot=PlayerSlot.PLAYER_A,
            display_name=player_a_name,
            is_bot=player_a_is_bot,
            active=a_instances[:3],
            bench=a_instances[3:],
        ),
        player_b=PlayerState(
            slot=PlayerSlot.PLAYER_B,
            display_name=player_b_name,
            is_bot=player_b_is_bot,
            active=b_instances[:3],
            bench=b_instances[3:],
        ),
        log=[f"Match begins. {first_player.value} goes first."],
    )


def _find_active(*, player_state: PlayerState, instance_id: str) -> MercInstance | None:
    return next((m for m in player_state.active if m.instance_id == instance_id), None)


def _find_bench(*, player_state: PlayerState, instance_id: str) -> MercInstance | None:
    return next((m for m in player_state.bench if m.instance_id == instance_id), None)


def _check_for_fainted_and_end(*, state: GameState, rng: SeededRng) -> GameState:
    # After each action: check for faints, check for match end.
    for player_slot in (PlayerSlot.PLAYER_A, PlayerSlot.PLAYER_B):
        player: PlayerState = state.player(slot=player_slot)
        if player.has_lost:
            state.phase = MatchPhase.FINISHED
            state.winner = (
                PlayerSlot.PLAYER_B if player_slot == PlayerSlot.PLAYER_A else PlayerSlot.PLAYER_A
            )
            state.log.append(f"{state.winner.value} wins the match!")
            return state

    # Check if active player has any fainted mercs in active slots that need replacement.
    active_player: PlayerState = state.player(slot=state.active_player)
    fainted_active: list[MercInstance] = [m for m in active_player.active if not m.is_alive]
    if fainted_active and any(m.is_alive for m in active_player.bench):
        state.phase = MatchPhase.AWAITING_REPLACEMENT
    # If fainted but no bench replacements, merc stays in slot but is dead (can't act).

    return state


def apply_action(*, state: GameState, action: Action) -> GameState:
    # Apply an action from the active player to the state. Returns the updated state.
    if state.phase == MatchPhase.FINISHED:
        raise InvalidActionError("Match is already over")

    if action.actor_player != state.active_player:
        raise InvalidActionError(
            f"Not {action.actor_player.value}'s turn (active: {state.active_player.value})"
        )

    rng: SeededRng = SeededRng(seed=state.seed + state.turn_number)
    player: PlayerState = state.player(slot=state.active_player)

    match action:
        case UseMoveAction():
            if state.phase != MatchPhase.AWAITING_ACTION:
                raise InvalidActionError(f"Cannot use move during phase {state.phase.value}")
            actor: MercInstance | None = _find_active(
                player_state=player, instance_id=action.actor_instance_id
            )
            if actor is None:
                raise InvalidActionError("Actor not found in active slots")
            if not actor.is_alive:
                raise InvalidActionError("Actor is fainted")
            move_def = next(
                (mv for mv in actor.definition.moves if mv.move_id == action.move_id), None
            )
            if move_def is None:
                raise InvalidActionError(f"Move {action.move_id} not on this merc")
            state.log.append(f"{actor.definition.name} uses {move_def.name}")
            for effect in move_def.effects:
                state = apply_effect(
                    state=state,
                    effect=effect,
                    actor_slot=state.active_player,
                    actor_instance_id=actor.instance_id,
                    rng=rng,
                )
            state = _check_for_fainted_and_end(state=state, rng=rng)

        case SwapAction():
            if state.phase != MatchPhase.AWAITING_ACTION:
                raise InvalidActionError(f"Cannot swap during phase {state.phase.value}")
            active_merc: MercInstance | None = _find_active(
                player_state=player, instance_id=action.active_instance_id
            )
            bench_merc: MercInstance | None = _find_bench(
                player_state=player, instance_id=action.bench_instance_id
            )
            if active_merc is None:
                raise InvalidActionError("Active merc not found")
            if bench_merc is None:
                raise InvalidActionError("Bench merc not found")
            if not bench_merc.is_alive:
                raise InvalidActionError("Cannot swap in a fainted merc")
            # Perform the swap
            active_idx: int = player.active.index(active_merc)
            bench_idx: int = player.bench.index(bench_merc)
            player.active[active_idx] = bench_merc
            player.bench[bench_idx] = active_merc
            state.log.append(
                f"{player.display_name} swaps {active_merc.definition.name} for "
                f"{bench_merc.definition.name}"
            )

        case ReplaceFaintedAction():
            if state.phase != MatchPhase.AWAITING_REPLACEMENT:
                raise InvalidActionError(f"No replacement needed during phase {state.phase.value}")
            fainted: MercInstance | None = _find_active(
                player_state=player, instance_id=action.fainted_instance_id
            )
            replacement: MercInstance | None = _find_bench(
                player_state=player, instance_id=action.bench_instance_id
            )
            if fainted is None or fainted.is_alive:
                raise InvalidActionError("No fainted merc at that slot")
            if replacement is None or not replacement.is_alive:
                raise InvalidActionError("Replacement merc invalid")
            active_idx = player.active.index(fainted)
            bench_idx = player.bench.index(replacement)
            player.active[active_idx] = replacement
            player.bench[bench_idx] = fainted
            state.log.append(f"{player.display_name} sends out {replacement.definition.name}")
            # Check if more replacements needed
            still_fainted: list[MercInstance] = [m for m in player.active if not m.is_alive]
            if not still_fainted or not any(m.is_alive for m in player.bench):
                state.phase = MatchPhase.AWAITING_ACTION

        case EndTurnAction():
            if state.phase not in (MatchPhase.AWAITING_ACTION,):
                raise InvalidActionError(f"Cannot end turn during phase {state.phase.value}")
            # Pass turn to opponent
            state.active_player = (
                PlayerSlot.PLAYER_B
                if state.active_player == PlayerSlot.PLAYER_A
                else PlayerSlot.PLAYER_A
            )
            state.turn_number += 1
            state.log.append(f"--- Turn {state.turn_number}: {state.active_player.value} ---")

    return state
