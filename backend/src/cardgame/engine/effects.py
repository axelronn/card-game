from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class TargetRule(StrEnum):
    # Who a move targets. Kept coarse in v0 - no player-chosen targeting.

    SELF = "self"
    RANDOM_ENEMY_ACTIVE = "random_enemy_active"
    LOWEST_HP_ENEMY_ACTIVE = "lowest_hp_enemy_active"
    ALL_ENEMY_ACTIVE = "all_enemy_active"
    RANDOM_ALLY_ACTIVE = "random_ally_active"
    LOWEST_HP_ALLY_ACTIVE = "lowest_hp_ally_active"
    ALL_ALLY_ACTIVE = "all_ally_active"


class DealDamageEffect(BaseModel):
    kind: Literal["deal_damage"] = "deal_damage"
    amount: int
    target: TargetRule


class HealEffect(BaseModel):
    kind: Literal["heal"] = "heal"
    amount: int
    target: TargetRule


class BuffAttackEffect(BaseModel):
    kind: Literal["buff_attack"] = "buff_attack"
    amount: int
    target: TargetRule


class BuffDefenseEffect(BaseModel):
    kind: Literal["buff_defense"] = "buff_defense"
    amount: int
    target: TargetRule


Effect = DealDamageEffect | HealEffect | BuffAttackEffect | BuffDefenseEffect
