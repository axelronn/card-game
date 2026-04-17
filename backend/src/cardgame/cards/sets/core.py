from cardgame.engine.effects import (
    BuffAttackEffect,
    BuffDefenseEffect,
    DealDamageEffect,
    HealEffect,
    TargetRule,
)
from cardgame.engine.models import MercDef, MoveDef

# Eight starter mercs with distinct roles: bruiser, tank, healer, controller,
# glass-cannon, AoE attacker, buffer, finisher. Names are placeholders — you'll
# want to rethink these when the camp theme/lore lands.

BRUISER: MercDef = MercDef(
    merc_id="bruiser",
    name="Torvik the Bruiser",
    max_hp=80,
    attack=20,
    defense=12,
    moves=[
        MoveDef(
            move_id="heavy_swing",
            name="Heavy Swing",
            description="Strike one enemy hard.",
            effects=[DealDamageEffect(amount=30, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="finisher",
            name="Finisher",
            description="Hit the lowest-HP enemy.",
            effects=[DealDamageEffect(amount=35, target=TargetRule.LOWEST_HP_ENEMY_ACTIVE)],
        ),
    ],
)

TANK: MercDef = MercDef(
    merc_id="tank",
    name="Stonewall",
    max_hp=120,
    attack=10,
    defense=25,
    moves=[
        MoveDef(
            move_id="bash",
            name="Bash",
            description="A basic hit.",
            effects=[DealDamageEffect(amount=15, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="shield_wall",
            name="Shield Wall",
            description="Buff the defense of all allies.",
            effects=[BuffDefenseEffect(amount=5, target=TargetRule.ALL_ALLY_ACTIVE)],
        ),
    ],
)

HEALER: MercDef = MercDef(
    merc_id="healer",
    name="Sister Elin",
    max_hp=70,
    attack=8,
    defense=10,
    moves=[
        MoveDef(
            move_id="mend",
            name="Mend",
            description="Heal the lowest-HP ally.",
            effects=[HealEffect(amount=30, target=TargetRule.LOWEST_HP_ALLY_ACTIVE)],
        ),
        MoveDef(
            move_id="smite",
            name="Smite",
            description="A small hit.",
            effects=[DealDamageEffect(amount=12, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
    ],
)

AOE: MercDef = MercDef(
    merc_id="aoe",
    name="Pyra the Scorched",
    max_hp=70,
    attack=15,
    defense=8,
    moves=[
        MoveDef(
            move_id="flame_wave",
            name="Flame Wave",
            description="Hit all enemies.",
            effects=[DealDamageEffect(amount=12, target=TargetRule.ALL_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="fireball",
            name="Fireball",
            description="Single-target heavy hit.",
            effects=[DealDamageEffect(amount=25, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
    ],
)

GLASS_CANNON: MercDef = MercDef(
    merc_id="glass_cannon",
    name="Vex the Assassin",
    max_hp=55,
    attack=30,
    defense=5,
    moves=[
        MoveDef(
            move_id="backstab",
            name="Backstab",
            description="Massive hit on the weakest enemy.",
            effects=[DealDamageEffect(amount=40, target=TargetRule.LOWEST_HP_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="quick_jab",
            name="Quick Jab",
            description="Fast poke.",
            effects=[DealDamageEffect(amount=18, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
    ],
)

BUFFER: MercDef = MercDef(
    merc_id="buffer",
    name="Marshal Rhen",
    max_hp=75,
    attack=12,
    defense=12,
    moves=[
        MoveDef(
            move_id="rally",
            name="Rally",
            description="Buff all allies' attack.",
            effects=[BuffAttackEffect(amount=4, target=TargetRule.ALL_ALLY_ACTIVE)],
        ),
        MoveDef(
            move_id="strike",
            name="Strike",
            description="Basic attack.",
            effects=[DealDamageEffect(amount=16, target=TargetRule.RANDOM_ENEMY_ACTIVE)],
        ),
    ],
)

CONTROLLER: MercDef = MercDef(
    merc_id="controller",
    name="Oren the Tactician",
    max_hp=70,
    attack=14,
    defense=11,
    moves=[
        MoveDef(
            move_id="focused_hit",
            name="Focused Hit",
            description="Hit the lowest-HP enemy.",
            effects=[DealDamageEffect(amount=22, target=TargetRule.LOWEST_HP_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="inspire",
            name="Inspire",
            description="Heal an ally and buff their attack.",
            effects=[
                HealEffect(amount=15, target=TargetRule.LOWEST_HP_ALLY_ACTIVE),
                BuffAttackEffect(amount=3, target=TargetRule.LOWEST_HP_ALLY_ACTIVE),
            ],
        ),
    ],
)

BERSERKER: MercDef = MercDef(
    merc_id="berserker",
    name="Ulla the Fury",
    max_hp=90,
    attack=22,
    defense=8,
    moves=[
        MoveDef(
            move_id="cleave",
            name="Cleave",
            description="Hit all enemies for moderate damage.",
            effects=[DealDamageEffect(amount=15, target=TargetRule.ALL_ENEMY_ACTIVE)],
        ),
        MoveDef(
            move_id="frenzy",
            name="Frenzy",
            description="Buff own attack and hit an enemy.",
            effects=[
                BuffAttackEffect(amount=5, target=TargetRule.SELF),
                DealDamageEffect(amount=20, target=TargetRule.RANDOM_ENEMY_ACTIVE),
            ],
        ),
    ],
)

ALL_MERCS: list[MercDef] = [
    BRUISER,
    TANK,
    HEALER,
    AOE,
    GLASS_CANNON,
    BUFFER,
    CONTROLLER,
    BERSERKER,
]

MERCS_BY_ID: dict[str, MercDef] = {m.merc_id: m for m in ALL_MERCS}
