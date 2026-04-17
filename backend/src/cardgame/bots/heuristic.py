from cardgame.engine.actions import Action, EndTurnAction, ReplaceFaintedAction, UseMoveAction
from cardgame.engine.models import GameState, MatchPhase, MercInstance, PlayerState
from cardgame.engine.rng import SeededRng


def choose_action(*, state: GameState) -> Action:
    # Very naive v0 bot:
    # - If a replacement is needed, send out the highest-HP bench merc
    # - Otherwise pick the first living active merc that hasn't acted and use its first move
    # - End turn once no more actions are available
    #
    # Assumption: the bot tracks per-turn action-taken state externally via the
    # match loop pattern (one action at a time, one merc per action). The caller
    # is responsible for calling choose_action repeatedly until an EndTurnAction
    # is returned.
    #
    # Assumption: we track which mercs have already acted this turn via a sidecar
    # set passed in by the caller. For simplicity in v0 the bot returns an action
    # for the first living active merc every call, and the caller (bot_driver) is
    # responsible for not calling it twice for the same merc within a turn.
    rng: SeededRng = SeededRng(seed=state.seed + state.turn_number * 7919)
    player: PlayerState = state.player(slot=state.active_player)

    if state.phase == MatchPhase.AWAITING_REPLACEMENT:
        fainted: MercInstance | None = next((m for m in player.active if not m.is_alive), None)
        bench_alive: list[MercInstance] = [m for m in player.bench if m.is_alive]
        if fainted is not None and bench_alive:
            # Send out the healthiest bench merc
            replacement: MercInstance = max(bench_alive, key=lambda m: m.current_hp)
            return ReplaceFaintedAction(
                actor_player=state.active_player,
                fainted_instance_id=fainted.instance_id,
                bench_instance_id=replacement.instance_id,
            )

    # Pick the first living active merc and use a random one of its moves.
    # TODO: this bot is deliberately dumb. Replace with a real heuristic in a later iteration.
    living_active: list[MercInstance] = [m for m in player.active if m.is_alive]
    if not living_active:
        return EndTurnAction(actor_player=state.active_player)

    actor: MercInstance = living_active[0]
    move = rng.choice(items=actor.definition.moves)
    return UseMoveAction(
        actor_player=state.active_player,
        actor_instance_id=actor.instance_id,
        move_id=move.move_id,
    )
