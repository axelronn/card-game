from cardgame.bots.heuristic import choose_action
from cardgame.engine.actions import EndTurnAction, UseMoveAction
from cardgame.engine.match import InvalidActionError, apply_action
from cardgame.engine.models import GameState, MatchPhase, PlayerSlot


def advance_bot_turns(*, state: GameState, max_actions_per_turn: int = 10) -> GameState:
    # Drive the bot until it's no longer the active player, or the match is over.
    # Handles multiple consecutive bot turns if (hypothetically) both players are bots.
    # Assumption: if the current active player is a bot, we keep calling the bot
    # for actions until it ends its turn.
    while True:
        if state.phase == MatchPhase.FINISHED:
            return state
        current_player = state.player(slot=state.active_player)
        if not current_player.is_bot:
            return state

        turn_started_as: PlayerSlot = state.active_player
        used_instance_ids: set[str] = set()

        for _ in range(max_actions_per_turn):
            if state.phase == MatchPhase.FINISHED:
                return state
            if state.active_player != turn_started_as:
                break

            action = choose_action(state=state)

            if isinstance(action, UseMoveAction):
                if action.actor_instance_id in used_instance_ids:
                    action = EndTurnAction(actor_player=state.active_player)
                else:
                    used_instance_ids.add(action.actor_instance_id)

            try:
                state = apply_action(state=state, action=action)
            except InvalidActionError:
                state = apply_action(
                    state=state,
                    action=EndTurnAction(actor_player=state.active_player),
                )
                break
        else:
            # Safety fuse: force end turn if still the same player after max actions
            if state.active_player == turn_started_as and state.phase == MatchPhase.AWAITING_ACTION:
                state = apply_action(
                    state=state,
                    action=EndTurnAction(actor_player=state.active_player),
                )
