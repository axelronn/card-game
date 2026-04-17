import argparse
import random
import sys
from dataclasses import dataclass, field

from cardgame.bots.heuristic import choose_action
from cardgame.cards.registry import all_mercs
from cardgame.engine.actions import EndTurnAction
from cardgame.engine.match import InvalidActionError, apply_action, start_match
from cardgame.engine.models import GameState, MatchPhase, MercDef, PlayerSlot


@dataclass
class MercStats:
    merc_id: str
    name: str
    matches_played: int = 0
    matches_won: int = 0

    @property
    def win_rate(self) -> float:
        if self.matches_played == 0:
            return 0.0
        return self.matches_won / self.matches_played


@dataclass
class SimReport:
    matches_run: int
    matches_drawn: int
    matches_completed: int
    per_merc: dict[str, MercStats] = field(default_factory=dict)


def _random_party(*, pool: list[MercDef], rng: random.Random) -> list[MercDef]:
    # Assumption: parties are 6 mercs drawn without replacement from the pool.
    # If pool has exactly 6, parties are always identical; with 8+ mercs they vary.
    return rng.sample(pool, k=6)


def _bot_take_full_turn(*, state: GameState, max_actions_per_turn: int = 10) -> GameState:
    # The bot is a one-action-at-a-time oracle. We drive it until it ends its turn
    # or the match finishes. max_actions_per_turn is a safety fuse against infinite loops.
    # Assumption: the bot uses each of its living active mercs at most once per turn;
    # we enforce that here by tracking used instance ids.
    used_instance_ids: set[str] = set()
    turn_started_as: PlayerSlot = state.active_player

    for _ in range(max_actions_per_turn):
        if state.phase == MatchPhase.FINISHED:
            return state
        if state.active_player != turn_started_as:
            # Turn already ended (e.g. via EndTurnAction)
            return state

        action = choose_action(state=state)

        # If the bot wants to use a merc that's already acted this turn, force end.
        if action.__class__.__name__ == "UseMoveAction":
            actor_id = getattr(action, "actor_instance_id", None)
            if actor_id in used_instance_ids:
                action = EndTurnAction(actor_player=state.active_player)
            elif actor_id is not None:
                used_instance_ids.add(actor_id)

        try:
            state = apply_action(state=state, action=action)
        except InvalidActionError:
            # Bot produced an illegal action; force end turn.
            state = apply_action(
                state=state,
                action=EndTurnAction(actor_player=state.active_player),
            )
            return state

    # Fuse blown — force end turn to guarantee progress.
    if state.active_player == turn_started_as and state.phase == MatchPhase.AWAITING_ACTION:
        state = apply_action(state=state, action=EndTurnAction(actor_player=state.active_player))
    return state


def _run_one_match(*, seed: int, party_a: list[MercDef], party_b: list[MercDef]) -> GameState:
    state: GameState = start_match(
        seed=seed,
        player_a_name="BotA",
        player_b_name="BotB",
        player_a_is_bot=True,
        player_b_is_bot=True,
        player_a_party=party_a,
        player_b_party=party_b,
    )
    max_turns: int = 200
    for _ in range(max_turns):
        if state.phase == MatchPhase.FINISHED:
            break
        state = _bot_take_full_turn(state=state)
    return state


def run_simulation(*, n_matches: int, seed: int) -> SimReport:
    pool: list[MercDef] = all_mercs()
    report: SimReport = SimReport(matches_run=n_matches, matches_drawn=0, matches_completed=0)
    for merc in pool:
        report.per_merc[merc.merc_id] = MercStats(merc_id=merc.merc_id, name=merc.name)

    meta_rng: random.Random = random.Random(seed)

    for match_index in range(n_matches):
        match_seed: int = seed * 100003 + match_index
        party_a: list[MercDef] = _random_party(pool=pool, rng=meta_rng)
        party_b: list[MercDef] = _random_party(pool=pool, rng=meta_rng)
        final_state: GameState = _run_one_match(seed=match_seed, party_a=party_a, party_b=party_b)

        if final_state.phase != MatchPhase.FINISHED or final_state.winner is None:
            report.matches_drawn += 1
            continue

        report.matches_completed += 1
        winning_party: list[MercDef] = (
            party_a if final_state.winner == PlayerSlot.PLAYER_A else party_b
        )
        losing_party: list[MercDef] = (
            party_b if final_state.winner == PlayerSlot.PLAYER_A else party_a
        )
        for m in winning_party:
            stats: MercStats = report.per_merc[m.merc_id]
            stats.matches_played += 1
            stats.matches_won += 1
        for m in losing_party:
            stats = report.per_merc[m.merc_id]
            stats.matches_played += 1

    return report


def _format_report(*, report: SimReport) -> str:
    lines: list[str] = []
    lines.append(
        f"Matches run: {report.matches_run} | completed: {report.matches_completed} | "
        f"drawn: {report.matches_drawn}"
    )
    lines.append("")
    lines.append(f"{'Merc':<30} {'Played':>8} {'Won':>6} {'Win%':>7}")
    lines.append("-" * 55)
    sorted_stats: list[MercStats] = sorted(
        report.per_merc.values(), key=lambda s: s.win_rate, reverse=True
    )
    for s in sorted_stats:
        lines.append(
            f"{s.name:<30} {s.matches_played:>8} {s.matches_won:>6} {s.win_rate * 100:>6.1f}%"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cardgame balance simulator")
    parser.add_argument("--n-matches", type=int, default=1000, help="Number of matches to run")
    parser.add_argument("--seed", type=int, default=0, help="Master seed")
    args = parser.parse_args(argv)

    report: SimReport = run_simulation(n_matches=args.n_matches, seed=args.seed)
    print(_format_report(report=report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
