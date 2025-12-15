import random
from typing import Dict, List

TypeChart = Dict[str, Dict[str, float]]  # attack_type -> defender_type -> multiplier


def type_multiplier(type_chart: TypeChart, attack_type: str, defender_types: List[str]) -> float:
    attack_type = attack_type.lower()
    mult = 1.0
    chart_for_attack = type_chart.get(attack_type, {})
    for defender_type in defender_types:
        mult *= float(chart_for_attack.get(defender_type.lower(), 1.0))
    return mult


class BattleEngine:
    def __init__(self, seed: int, type_chart: TypeChart):
        self.rng = random.Random(seed)
        self.type_chart = type_chart

    def initiative_detail(self, spd_a: int, spd_b: int) -> tuple[str, dict]:
        spd_a = int(spd_a)
        spd_b = int(spd_b)
        if spd_a > spd_b:
            return "a", {"method": "speed", "a_speed": spd_a, "b_speed": spd_b}
        if spd_b > spd_a:
            return "b", {"method": "speed", "a_speed": spd_a, "b_speed": spd_b}
        roll = int(self.rng.randint(0, 1))
        return ("a" if roll == 0 else "b"), {"method": "tiebreak", "a_speed": spd_a, "b_speed": spd_b, "tiebreak": roll}

    def initiative(self, spd_a: int, spd_b: int) -> str:
        winner, _ = self.initiative_detail(spd_a, spd_b)
        return winner

    @staticmethod
    def hit_chance(atk: int, defense: int) -> int:
        return max(30, min(95, 60 + 2 * (int(atk) - int(defense))))

    def roll_hit_detail(self, atk: int, defense: int) -> tuple[bool, int, int]:
        chance = self.hit_chance(atk, defense)
        roll = int(self.rng.randint(1, 100))
        return roll <= chance, roll, chance

    def roll_hit(self, atk: int, defense: int) -> bool:
        hit, _roll, _chance = self.roll_hit_detail(atk, defense)
        return hit

    @staticmethod
    def crit_chance(spd: int) -> int:
        return max(5, int(spd) // 10)

    def roll_crit_detail(self, spd: int) -> tuple[bool, int, int]:
        chance = self.crit_chance(spd)
        roll = int(self.rng.randint(1, 100))
        return roll <= chance, roll, chance

    def roll_crit(self, spd: int) -> bool:
        crit, _roll, _chance = self.roll_crit_detail(spd)
        return crit

    @staticmethod
    def base_damage(atk: int, defense: int) -> int:
        return max(1, int(atk) - int(defense) // 2)

    def damage_detail(
        self,
        atk: int,
        defense: int,
        att_type: str,
        def_types: List[str],
        mod: float,
        *,
        crit: bool,
        defending: bool,
    ) -> tuple[int, float, int]:
        base = self.base_damage(atk, defense)
        mult = type_multiplier(self.type_chart, att_type, def_types)
        dmg = int(base * mult * float(mod))
        if crit:
            dmg = int(dmg * 1.5)
        if defending:
            dmg = dmg // 2
        return dmg, mult, base

    def damage(self, atk: int, defense: int, att_type: str, def_types: List[str], mod: float) -> tuple[int, float]:
        dmg, mult, _base = self.damage_detail(atk, defense, att_type, def_types, mod, crit=False, defending=False)
        return dmg, mult

    @staticmethod
    def decay_effects(state: dict) -> None:
        for key in ("a", "b"):
            side = state.get(key, {})
            if not isinstance(side, dict):
                continue
            effects = side.get("effects", {})
            if not isinstance(effects, dict):
                continue
            turns_left = int(effects.get("atk_turns", 0) or 0)
            if turns_left > 0:
                turns_left -= 1
                effects["atk_turns"] = turns_left
                if turns_left == 0:
                    effects["atk_mod"] = 1.0

    def step(self, battle, role: str, action: Dict, state: dict | None = None) -> tuple[list[dict], dict]:
        if role not in {"a", "b"}:
            raise ValueError("Invalid role.")

        log: list[dict] = []
        base_state = state if state is not None else (battle.state or {})
        if not isinstance(base_state, dict):
            base_state = {}
        state = base_state.copy()
        turn_no = int(state.get("turn", 0) or 0) + 1

        def default_effects():
            return {"atk_mod": 1.0, "atk_turns": 0, "defend": 0}

        def ensure_side(key: str, team) -> dict:
            side = state.get(key, {})
            if not isinstance(side, dict):
                side = {}

            active = int(side.get("active", 0) or 0)
            active = max(0, min(active, max(0, len(team) - 1)))

            hp_list = side.get("hp", [])
            if not isinstance(hp_list, list) or len(hp_list) != len(team):
                hp_list = [int(p.stats["hp"]) for p in team]
            else:
                norm = []
                for idx, p in enumerate(team):
                    try:
                        val = int(hp_list[idx])
                    except (TypeError, ValueError):
                        val = int(p.stats["hp"])
                    norm.append(max(0, val))
                hp_list = norm

            eff = side.get("effects", {})
            if not isinstance(eff, dict):
                eff = {}
            effects = {
                "atk_mod": float(eff.get("atk_mod", 1.0) or 1.0),
                "atk_turns": int(eff.get("atk_turns", 0) or 0),
                "defend": int(eff.get("defend", 0) or 0),
            }
            return {"active": active, "hp": hp_list, "effects": effects}

        if "a" not in state or "b" not in state:
            state.setdefault(
                "a",
                {
                    "active": 0,
                    "hp": [int(state.get("p1_hp", battle.p1_pokemon.stats["hp"]))],
                    "effects": default_effects(),
                },
            )
            state.setdefault(
                "b",
                {
                    "active": 0,
                    "hp": [int(state.get("p2_hp", battle.p2_pokemon.stats["hp"]))],
                    "effects": default_effects(),
                },
            )

        state["a"] = ensure_side("a", battle.p1_team)
        state["b"] = ensure_side("b", battle.p2_team)

        def team_for(r: str):
            return battle.p1_team if r == "a" else battle.p2_team

        def active_pokemon(r: str):
            idx = int(state[r]["active"])
            team = team_for(r)
            idx = max(0, min(idx, max(0, len(team) - 1)))
            return team[idx], idx

        def reset_effects(r: str):
            state[r]["effects"] = default_effects()

        def choose_next_alive(r: str) -> int | None:
            hp_list = state[r]["hp"]
            for idx, hp_val in enumerate(hp_list):
                if int(hp_val) > 0:
                    return idx
            return None

        def apply_switch(r: str, to_idx: int, *, auto: bool):
            team = team_for(r)
            to_idx = max(0, min(int(to_idx), max(0, len(team) - 1)))
            state[r]["active"] = to_idx
            reset_effects(r)
            if team:
                p = team[to_idx]
                log.append(
                    {
                        "turn": turn_no,
                        "actor": r,
                        "action": "autoswitch" if auto else "switch",
                        "to": to_idx,
                        "to_id": p.id,
                    }
                )
            else:
                log.append({"turn": turn_no, "actor": r, "action": "autoswitch" if auto else "switch", "to": to_idx})

        if state.get("finished"):
            return log, state

        action = action or {}
        action_type = str(action.get("type") or "attack").lower()
        opp = "b" if role == "a" else "a"

        _, role_idx = active_pokemon(role)
        try:
            current_hp = int(state[role]["hp"][role_idx])
        except Exception:
            current_hp = 0
        if current_hp <= 0:
            next_idx = choose_next_alive(role)
            if next_idx is None:
                state.update({"finished": True, "winner": opp, "loser": role})
                return log, state
            apply_switch(role, next_idx, auto=True)

        attacker, _ = active_pokemon(role)
        defender, _ = active_pokemon(opp)

        if action_type == "switch":
            apply_switch(role, int(action.get("to", 0)), auto=False)
            return log, state

        if action_type == "defend":
            state[role]["effects"]["defend"] = 2
            log.append({"turn": turn_no, "actor": role, "action": "defend"})
            return log, state

        if action_type == "buff":
            state[role]["effects"]["atk_mod"] *= 1.1
            state[role]["effects"]["atk_turns"] = 2
            log.append({"turn": turn_no, "actor": role, "action": "buff"})
            return log, state

        if action_type == "debuff":
            state[opp]["effects"]["atk_mod"] *= 0.9
            state[opp]["effects"]["atk_turns"] = 2
            log.append({"turn": turn_no, "actor": role, "action": "debuff"})
            return log, state

        att_type = str(action.get("attack_type") or (attacker.types[0] if attacker.types else "")).lower()
        atk = int(attacker.stats["attack"])
        defense = int(defender.stats["defense"])

        hit, hit_roll, hit_chance = self.roll_hit_detail(atk, defense)
        if not hit:
            log.append(
                {
                    "turn": turn_no,
                    "actor": role,
                    "action": "miss",
                    "attack_type": att_type,
                    "hit_roll": hit_roll,
                    "hit_chance": hit_chance,
                }
            )
            return log, state

        spd = int(attacker.stats["speed"])
        crit, crit_roll, crit_chance = self.roll_crit_detail(spd)
        mod = float(state[role]["effects"]["atk_mod"])
        defend_before = int(state[opp]["effects"]["defend"])
        dmg, eff, base = self.damage_detail(
            atk, defense, att_type, defender.types, mod, crit=crit, defending=defend_before > 0
        )
        if defend_before > 0:
            state[opp]["effects"]["defend"] -= 1

        def_idx = int(state[opp]["active"])
        state[opp]["hp"][def_idx] = int(state[opp]["hp"][def_idx]) - int(dmg)
        if int(state[opp]["hp"][def_idx]) < 0:
            state[opp]["hp"][def_idx] = 0

        log.append(
            {
                "turn": turn_no,
                "actor": role,
                "action": "hit",
                "attack_type": att_type,
                "effectiveness": eff,
                "base": int(base),
                "atk_mod": float(mod),
                "hit_roll": hit_roll,
                "hit_chance": int(hit_chance),
                "crit_roll": crit_roll,
                "crit_chance": int(crit_chance),
                "defend_before": defend_before,
                "dmg": int(dmg),
                "crit": bool(crit),
                "target_hp": int(state[opp]["hp"][def_idx]),
                "target_slot": def_idx,
            }
        )

        if int(state[opp]["hp"][def_idx]) <= 0:
            next_idx = choose_next_alive(opp)
            if next_idx is None:
                state.update({"finished": True, "winner": role, "loser": opp})
                return log, state
            apply_switch(opp, next_idx, auto=True)

        return log, state
