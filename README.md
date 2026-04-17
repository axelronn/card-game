# Cardgame (codename)

A physical-digital collectable card game prototype. Long-term vision: kids at a summer camp buy packs from the kiosk, scan the cards with their phone, and play each other with their collected mercs in a digital client.

## Design summary (v0)

- **1v1, turn-based.** Sequential turns — you take a full turn, opponent takes a full turn.
- **Party of 6 mercs, 3 active, 3 on bench.** Pokémon VGC-doubles-ish format.
- **Each merc has a fixed moveset** of 2–3 moves. Moves are part of the merc, not separately collected.
- **Each active merc acts once per turn**: use a move or swap with a bench merc.
- **Within your turn you choose action order** — synergies are reliable.
- **No speed stat in v0**, no types, no status effects. Stats are HP / Attack / Defense only.
- **Match ends** when one side has no living mercs.

## Roadmap

- **v0** (this scaffold): single-player vs bot, core engine, ~8 starter mercs, web UI later
- **v1**: 1v1 multiplayer via WebSockets, invite-link matches
- **v2**: accounts, pack scanning, collection binder, party builder
- **v3**: tournament mode, camp admin tools
- **v4+**: more mercs, types, status effects, progression

## Structure

```
backend/
  src/cardgame/
    engine/    # pure game logic, zero framework deps
    cards/     # merc & move definitions as data
    bots/      # AI opponents
    sim/       # simulator CLI for balance testing
    api/       # FastAPI wrapper around engine
  tests/
```

Frontend will be added once the backend engine is playable via API.

## Development

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```
cd backend
uv sync
uv run pytest
uv run uvicorn cardgame.api.main:app --reload
```
