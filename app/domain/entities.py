from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Pokemon:
    id: int
    name: str
    types: List[str]
    stats: Dict[str, int]  # hp, attack, defense, speed


@dataclass
class LobbyEntry:
    user_id: int
    pokemon_ids: List[int]


@dataclass
class BattleSeed:
    value: int


@dataclass
class BattleTurn:
    attacker_id: int
    defender_id: int
    action: str
    result: Dict


@dataclass
class BattleContext:
    id: int
    status: str
    p1_id: int
    p2_id: int
    p1_team: List[Pokemon]
    p2_team: List[Pokemon]
    p1_pokemon: Pokemon
    p2_pokemon: Pokemon
    seed: BattleSeed
    type_chart: Dict[str, Dict[str, float]]
    pending_actions: Dict[str, dict | None]
    log: List[BattleTurn]
    state: dict
    created_at: int | None = None
