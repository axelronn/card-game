from cardgame.engine.effects import (
    BuffAttackEffect,
    BuffDefenseEffect,
    DealDamageEffect,
    Effect,
    HealEffect,
    TargetRule,
)
from cardgame.engine.models import GameState, MercInstance, PlayerSlot, PlayerState
from cardgame.engine.rng import SeededRng


def _select_targets(
    *,
    state: GameState,
    actor_slot: PlayerSlot,
    target_rule: TargetRule,
    actor_instance_id: str,
    rng: SeededRng,
) -> list[MercInstance]:
    # Assumption: targeting operates on currently-active mercs only.
    # Bench mercs are untargetable in v0 (we can relax later, e.g. "hits all enemies
    # including bench").
    ally: PlayerState = state.player(slot=actor_slot)
    enemy: PlayerState = state.opponent(slot=actor_slot)

    ally_active_alive: list[MercInstance] = [m for m in ally.active if m.is_alive]
    enemy_active_alive: list[MercInstance] = [m for m in enemy.active if m.is_alive]

    match target_rule:
        case TargetRule.SELF:
            return [m for m in ally.all_mercs if m.instance_id == actor_instance_id]
        case TargetRule.RANDOM_ENEMY_ACTIVE:
            if not enemy_active_alive:
                return []
            return [rng.choice(items=enemy_active_alive)]
        case TargetRule.LOWEST_HP_ENEMY_ACTIVE:
            if not enemy_active_alive:
                return []
            return [min(enemy_active_alive, key=lambda m: m.current_hp)]
        case TargetRule.ALL_ENEMY_ACTIVE:
            return enemy_active_alive
        case TargetRule.RANDOM_ALLY_ACTIVE:
            if not ally_active_alive:
                return []
            return [rng.choice(items=ally_active_alive)]
        case TargetRule.LOWEST_HP_ALLY_ACTIVE:
            if not ally_active_alive:
                return []
            return [min(ally_active_alive, key=lambda m: m.current_hp)]
        case TargetRule.ALL_ALLY_ACTIVE:
            return ally_active_alive


def _apply_damage(*, attacker: MercInstance, target: MercInstance, raw_amount: int) -> int:
    # Simple damage formula for v0:
    #   damage = max(1, raw * attacker_attack / (attacker_attack + target_defense))
    # Ensures defense matters but never fully negates damage.
    # Assumption: attack stat scales damage, defense reduces it, minimum 1 damage.
    attack_stat: int = attacker.effective_attack
    defense_stat: int = target.effective_defense
    ratio: float = attack_stat / (attack_stat + defense_stat)
    final: int = max(1, int(raw_amount * ratio))
    target.current_hp = max(0, target.current_hp - final)
    return final


def apply_effect(
    *,
    state: GameState,
    effect: Effect,
    actor_slot: PlayerSlot,
    actor_instance_id: str,
    rng: SeededRng,
) -> GameState:
    # Apply one effect, mutating the game state in place and returning it.
    # Assumption: we mutate in place for v0 simplicity. If we later want pure
    # state transitions, wrap in model_copy at the caller.
    actor: MercInstance | None = next(
        (m for m in state.player(slot=actor_slot).all_mercs if m.instance_id == actor_instance_id),
        None,
    )
    if actor is None or not actor.is_alive:
        return state

    targets: list[MercInstance] = _select_targets(
        state=state,
        actor_slot=actor_slot,
        target_rule=effect.target,
        actor_instance_id=actor_instance_id,
        rng=rng,
    )

    for target in targets:
        match effect:
            case DealDamageEffect():
                dealt: int = _apply_damage(attacker=actor, target=target, raw_amount=effect.amount)
                state.log.append(
                    f"{actor.definition.name} hits {target.definition.name} for {dealt} damage "
                    f"(HP: {target.current_hp}/{target.definition.max_hp})"
                )
                if target.current_hp == 0:
                    state.log.append(f"{target.definition.name} fainted!")
            case HealEffect():
                before: int = target.current_hp
                target.current_hp = min(target.definition.max_hp, target.current_hp + effect.amount)
                healed: int = target.current_hp - before
                state.log.append(
                    f"{actor.definition.name} heals {target.definition.name} for {healed} "
                    f"(HP: {target.current_hp}/{target.definition.max_hp})"
                )
            case BuffAttackEffect():
                target.attack_bonus += effect.amount
                state.log.append(
                    f"{actor.definition.name} buffs {target.definition.name}'s "
                    f"attack by {effect.amount}"
                )
            case BuffDefenseEffect():
                target.defense_bonus += effect.amount
                state.log.append(
                    f"{actor.definition.name} buffs {target.definition.name}'s "
                    f"defense by {effect.amount}"
                )

    return state
