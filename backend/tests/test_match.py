from cardgame.cards.registry import all_mercs, get_merc
from cardgame.engine.actions import EndTurnAction, UseMoveAction
from cardgame.engine.match import apply_action, start_match
from cardgame.engine.models import GameState, MatchPhase, PlayerSlot


def _standard_match() -> GameState:
    party_ids: list[str] = [
        "bruiser",
        "tank",
        "healer",
        "aoe",
        "glass_cannon",
        "buffer",
    ]
    party = [get_merc(merc_id=mid) for mid in party_ids]
    return start_match(
        seed=42,
        player_a_name="Alice",
        player_b_name="Bob",
        player_a_is_bot=False,
        player_b_is_bot=False,
        player_a_party=party,
        player_b_party=party,
    )


def test_registry_loads_all_mercs() -> None:
    mercs = all_mercs()
    assert len(mercs) == 8
    for m in mercs:
        assert m.max_hp > 0
        assert m.attack > 0
        assert m.defense >= 0
        assert len(m.moves) >= 1


def test_match_starts_correctly() -> None:
    state = _standard_match()
    assert state.turn_number == 1
    assert state.phase == MatchPhase.AWAITING_ACTION
    assert len(state.player_a.active) == 3
    assert len(state.player_a.bench) == 3
    assert len(state.player_b.active) == 3
    assert len(state.player_b.bench) == 3
    assert state.winner is None


def test_deterministic_seed() -> None:
    a = _standard_match()
    b = _standard_match()
    assert a.active_player == b.active_player


def test_basic_attack_damages_enemy() -> None:
    state = _standard_match()
    attacker = state.player(slot=state.active_player).active[0]
    original_hps = {
        m.instance_id: m.current_hp for m in state.opponent(slot=state.active_player).active
    }

    action = UseMoveAction(
        actor_player=state.active_player,
        actor_instance_id=attacker.instance_id,
        move_id=attacker.definition.moves[0].move_id,
    )
    state = apply_action(state=state, action=action)

    enemy = state.opponent(slot=state.active_player).active
    damaged = [m for m in enemy if m.current_hp < original_hps[m.instance_id]]
    assert len(damaged) >= 1


def test_end_turn_switches_active_player() -> None:
    state = _standard_match()
    first = state.active_player
    state = apply_action(state=state, action=EndTurnAction(actor_player=first))
    assert state.active_player != first
    assert state.turn_number == 2


def test_full_match_reaches_termination() -> None:
    # Play a quick match with both sides spamming their first move.
    # Just proves the engine converges to a winner rather than looping forever.
    state = _standard_match()
    max_turns = 200
    for _ in range(max_turns):
        if state.phase == MatchPhase.FINISHED:
            break
        player = state.player(slot=state.active_player)

        if state.phase == MatchPhase.AWAITING_REPLACEMENT:
            from cardgame.engine.actions import ReplaceFaintedAction

            fainted = next(m for m in player.active if not m.is_alive)
            replacement = next(m for m in player.bench if m.is_alive)
            state = apply_action(
                state=state,
                action=ReplaceFaintedAction(
                    actor_player=state.active_player,
                    fainted_instance_id=fainted.instance_id,
                    bench_instance_id=replacement.instance_id,
                ),
            )
            continue

        actor = next((m for m in player.active if m.is_alive), None)
        if actor is None:
            state = apply_action(
                state=state, action=EndTurnAction(actor_player=state.active_player)
            )
            continue

        state = apply_action(
            state=state,
            action=UseMoveAction(
                actor_player=state.active_player,
                actor_instance_id=actor.instance_id,
                move_id=actor.definition.moves[0].move_id,
            ),
        )
        # Only end the turn if we're still in a state where that's legal.
        # A move may have caused a faint and pushed us to AWAITING_REPLACEMENT.
        if state.phase == MatchPhase.AWAITING_ACTION:
            state = apply_action(
                state=state, action=EndTurnAction(actor_player=state.active_player)
            )

    assert state.phase == MatchPhase.FINISHED
    assert state.winner in (PlayerSlot.PLAYER_A, PlayerSlot.PLAYER_B)
