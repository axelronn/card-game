from cardgame.cards.sets.core import ALL_MERCS, MERCS_BY_ID
from cardgame.engine.models import MercDef


def all_mercs() -> list[MercDef]:
    return ALL_MERCS


def get_merc(*, merc_id: str) -> MercDef:
    if merc_id not in MERCS_BY_ID:
        raise KeyError(f"No merc with id {merc_id!r}")
    return MERCS_BY_ID[merc_id]
