from fastapi.testclient import TestClient

from cardgame.api.main import app

client: TestClient = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_mercs() -> None:
    response = client.get("/mercs")
    assert response.status_code == 200
    mercs = response.json()
    assert len(mercs) == 8
    assert all("merc_id" in m for m in mercs)
    assert all("moves" in m for m in mercs)


def test_new_match_requires_six_mercs() -> None:
    response = client.post(
        "/match/new",
        json={"seed": 1, "player_name": "Axel", "party_merc_ids": ["bruiser", "tank"]},
    )
    assert response.status_code == 400


def test_new_match_rejects_unknown_merc() -> None:
    response = client.post(
        "/match/new",
        json={
            "seed": 1,
            "player_name": "Axel",
            "party_merc_ids": ["not_a_real_merc"] * 6,
        },
    )
    assert response.status_code == 400


def test_new_match_returns_valid_state() -> None:
    response = client.post(
        "/match/new",
        json={
            "seed": 1,
            "player_name": "Axel",
            "party_merc_ids": [
                "bruiser",
                "tank",
                "healer",
                "aoe",
                "glass_cannon",
                "buffer",
            ],
        },
    )
    assert response.status_code == 200
    state = response.json()
    assert "match_id" in state
    assert state["turn_number"] >= 1
    assert len(state["player_a"]["active"]) == 3
    assert len(state["player_a"]["bench"]) == 3
    # After new_match we've auto-advanced past any bot turn, so either
    # it's player_a's turn, or (rare) the match already ended.
    assert state["active_player"] == "player_a" or state["phase"] == "finished"


def test_full_match_via_api() -> None:
    # Create a match, then spam first-move-of-first-active-merc until it ends.
    response = client.post(
        "/match/new",
        json={
            "seed": 123,
            "player_name": "Axel",
            "party_merc_ids": [
                "bruiser",
                "tank",
                "healer",
                "aoe",
                "glass_cannon",
                "buffer",
            ],
        },
    )
    assert response.status_code == 200
    state = response.json()
    match_id: str = state["match_id"]

    max_actions: int = 300
    for _ in range(max_actions):
        if state["phase"] == "finished":
            break

        if state["phase"] == "awaiting_replacement":
            fainted = next(m for m in state["player_a"]["active"] if m["current_hp"] == 0)
            replacement = next(m for m in state["player_a"]["bench"] if m["current_hp"] > 0)
            action_payload: dict[str, object] = {
                "action": {
                    "kind": "replace_fainted",
                    "actor_player": "player_a",
                    "fainted_instance_id": fainted["instance_id"],
                    "bench_instance_id": replacement["instance_id"],
                }
            }
        else:
            actor = next((m for m in state["player_a"]["active"] if m["current_hp"] > 0), None)
            if actor is None:
                action_payload = {"action": {"kind": "end_turn", "actor_player": "player_a"}}
            else:
                action_payload = {
                    "action": {
                        "kind": "use_move",
                        "actor_player": "player_a",
                        "actor_instance_id": actor["instance_id"],
                        "move_id": actor["definition"]["moves"][0]["move_id"],
                    }
                }

        response = client.post(f"/match/{match_id}/action", json=action_payload)
        assert response.status_code == 200, response.text
        state = response.json()

        # If we just used a move and the phase is still awaiting_action, end the turn
        # so the bot gets to play. (Otherwise we'd spam moves with the same merc.)
        if (
            action_payload["action"]["kind"] == "use_move"  # type: ignore[index]
            and state["phase"] == "awaiting_action"
            and state["active_player"] == "player_a"
        ):
            response = client.post(
                f"/match/{match_id}/action",
                json={"action": {"kind": "end_turn", "actor_player": "player_a"}},
            )
            assert response.status_code == 200
            state = response.json()

    assert state["phase"] == "finished"
    assert state["winner"] in ("player_a", "player_b")


def test_action_on_unknown_match_returns_404() -> None:
    response = client.post(
        "/match/does-not-exist/action",
        json={"action": {"kind": "end_turn", "actor_player": "player_a"}},
    )
    assert response.status_code == 404
