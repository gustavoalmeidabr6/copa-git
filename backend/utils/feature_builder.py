"""
utils/feature_builder.py — VERSÃO v6 (Com Weighted Star Rating e Desfalques)

NOVIDADES DESTA VERSÃO (v6):
  - Weighted Star Rating (_calculate_weighted_rating): A nota do time não é mais
    uma média simples inútil. O melhor jogador (ex: Mbappé, Vini Jr) tem Peso 4, 
    o segundo tem Peso 3, o terceiro Peso 2, e os demais Peso 1.
    Tirar o craque do time agora destrói a média geral, simulando o peso tático
    real que um extraclasse tem.
"""

import pandas as pd
import requests
import copy
import re
from difflib import get_close_matches
from utils.data_loader import DataLoader, WORLD_CUP_2026_TEAMS

STADIUM_COORDS = {
    "New York":      {"lat": 40.8135, "lon": -74.0745, "city": "East Rutherford, NJ"},
    "Los Angeles":   {"lat": 34.0141, "lon": -118.2880, "city": "Los Angeles, CA"},
    "Dallas":        {"lat": 32.7478, "lon": -97.0929, "city": "Dallas, TX"},
    "San Francisco": {"lat": 37.4033, "lon": -121.9694, "city": "Santa Clara, CA"},
    "Miami":         {"lat": 25.9580, "lon": -80.2389, "city": "Miami, FL"},
    "Seattle":       {"lat": 47.5952, "lon": -122.3316, "city": "Seattle, WA"},
    "Boston":        {"lat": 42.0909, "lon": -71.2643, "city": "Foxborough, MA"},
    "Atlanta":       {"lat": 33.7553, "lon": -84.4006, "city": "Atlanta, GA"},
    "Houston":       {"lat": 29.6847, "lon": -95.4107, "city": "Houston, TX"},
    "Kansas City":   {"lat": 38.9187, "lon": -94.8201, "city": "Kansas City, MO"},
    "Philadelphia":  {"lat": 39.9008, "lon": -75.1674, "city": "Philadelphia, PA"},
    "Vancouver":     {"lat": 49.2777, "lon": -123.1128, "city": "Vancouver, BC"},
    "Toronto":       {"lat": 43.6332, "lon": -79.5892, "city": "Toronto, ON"},
    "Guadalajara":   {"lat": 20.6668, "lon": -103.3121, "city": "Guadalajara, MX"},
    "Mexico City":   {"lat": 19.3029, "lon": -99.1505, "city": "Mexico City, MX"},
    "Monterrey":     {"lat": 25.6691, "lon": -100.3099, "city": "Monterrey, MX"},
}

HOME_ADVANTAGE_TEAMS = {
    "USA": 1, "Mexico": 1, "Canada": 1,
}

GROUP_STADIUMS = {
    "A": "Mexico City",   "B": "Dallas",       "C": "Los Angeles",
    "D": "New York",      "E": "Seattle",       "F": "Miami",
    "G": "Houston",       "H": "Kansas City",   "I": "Boston",
    "J": "Philadelphia",  "K": "Atlanta",       "L": "San Francisco",
}

# Climas Nativos
# COLD: < 15°C | MODERATE: 15°C - 25°C | HOT: > 25°C
TEAM_NATIVE_CLIMATE = {
    # Américas Quentes
    "Brazil": "HOT", "Colombia": "HOT", "Ecuador": "HOT", "Paraguay": "HOT", "Venezuela": "HOT",
    "Mexico": "HOT", "Panama": "HOT", "Costa Rica": "HOT", "Jamaica": "HOT", "Haiti": "HOT", "Curacao": "HOT",
    # África / Oriente Médio Quentes
    "Morocco": "HOT", "Senegal": "HOT", "Egypt": "HOT", "Algeria": "HOT", "Nigeria": "HOT",
    "Ghana": "HOT", "Tunisia": "HOT", "Mali": "HOT", "Cameroon": "HOT", "Ivory Coast": "HOT", "South Africa": "HOT",
    "DR Congo": "HOT", "Cape Verde": "HOT",
    "Saudi Arabia": "HOT", "Qatar": "HOT", "UAE": "HOT", "Iran": "HOT", "Iraq": "HOT", "Jordan": "HOT",
    # Frios
    "Canada": "COLD", "Sweden": "COLD", "Norway": "COLD", "Scotland": "COLD", "Switzerland": "COLD",
    "Denmark": "COLD", "Finland": "COLD", "Iceland": "COLD", "Russia": "COLD", "Poland": "COLD",
    "Bosnia and Herzegovina": "COLD", "Croatia": "COLD", "Serbia": "COLD", "Austria": "COLD",
    "Czech Republic": "COLD", "Wales": "COLD", "Ireland": "COLD", "Northern Ireland": "COLD",
    # Default (resto é MODERATE)
}


class FeatureBuilder:
    def __init__(self):
        self.data_loader = DataLoader()
        self._weather_cache: dict = {}

    def get_weather(self, stadium_city: str) -> float:
        if stadium_city in self._weather_cache:
            return self._weather_cache[stadium_city]

        coords = STADIUM_COORDS.get(stadium_city, STADIUM_COORDS["Miami"])
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={coords['lat']}&longitude={coords['lon']}"
                f"&current_weather=true"
            )
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                temp = r.json().get("current_weather", {}).get("temperature", 25.0)
                self._weather_cache[stadium_city] = float(temp)
                return float(temp)
        except Exception:
            pass

        june_temps = {
            "Mexico City": 18.0, "Guadalajara": 24.0, "Monterrey": 33.0,
            "Miami": 30.0, "Houston": 32.0, "Dallas": 34.0,
            "Atlanta": 29.0, "Kansas City": 28.0, "Philadelphia": 27.0,
            "New York": 26.0, "Boston": 23.0, "Seattle": 19.0,
            "Los Angeles": 22.0, "San Francisco": 17.0,
            "Vancouver": 18.0, "Toronto": 22.0,
        }
        temp = june_temps.get(stadium_city, 25.0)
        self._weather_cache[stadium_city] = temp
        return temp

    def _get_stadium_for_match(self, home_team: str) -> str:
        group = WORLD_CUP_2026_TEAMS.get(home_team, {}).get("group", "A")
        return GROUP_STADIUMS.get(group, "Miami")

    @staticmethod
    def _calculate_weighted_rating(players: list[dict]) -> float:
        """
        Calcula a nota do time baseada no "Weighted Star Rating".
        O melhor jogador (Top 1) tem peso 4, o Top 2 tem peso 3, o Top 3 peso 2.
        Os demais têm peso 1. Isso garante que perder um extraclasse afunde a média.
        """
        if not players:
            return 7.0
        
        # Ordena os jogadores do melhor para o pior
        sorted_players = sorted(players, key=lambda x: x.get("rating", 7.0), reverse=True)
        
        weights = [4.0, 3.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        
        total_score = 0.0
        total_weight = 0.0
        
        for i, p in enumerate(sorted_players):
            w = weights[i] if i < len(weights) else 1.0
            total_score += p.get("rating", 7.0) * w
            total_weight += w
            
        return round(total_score / total_weight, 2)

    def _apply_custom_starters(self, squad_data: dict, custom_starters: list) -> dict:
        if not custom_starters:
            return squad_data
        
        all_players = squad_data.get("top_players", []) + squad_data.get("bench_players", [])
        new_top = []
        new_bench = []
        
        # 1. Pega os jogadores requisitados pelo frontend
        for name in custom_starters:
            found = next((p for p in all_players if p["name"] == name), None)
            if found:
                new_top.append(found)
            else:
                new_top.append({"name": name, "rating": 7.0, "position": "Midfielder"})
                
        # 2. O resto vai pro banco
        used_names = {p["name"] for p in new_top}
        for p in all_players:
            if p["name"] not in used_names:
                new_bench.append(p)
                
        squad_data["top_players"] = new_top
        squad_data["bench_players"] = new_bench
        return squad_data

    def build_match_features(self, home_team: str, away_team: str, is_friendly: int = 0, home_excluded: list = None, away_excluded: list = None, stadium: str = None, home_starters: list = None, away_starters: list = None) -> dict:
        if home_excluded is None: home_excluded = []
        if away_excluded is None: away_excluded = []

        # ── 1. ELO ────────────────────────────────────────────────────────────
        home_elo = self.data_loader.get_team_elo(home_team)
        away_elo = self.data_loader.get_team_elo(away_team)
        home_adv = HOME_ADVANTAGE_TEAMS.get(home_team, 0)

        # ── 2. Médias históricas de gols ──────────────────────────────────────
        home_goals = self.data_loader.get_historical_goals(home_team)
        away_goals = self.data_loader.get_historical_goals(away_team)

        # ── 3. DataFrame para o modelo — 10 features ──────────────────────────
        df_ml = pd.DataFrame([{
            "home_adv":           home_adv,
            "is_friendly":        is_friendly,
            "is_world_cup":       1 if is_friendly == 0 else 0,
            "home_elo_pre_match": home_elo,
            "away_elo_pre_match": away_elo,
            "elo_diff":           home_elo - away_elo,
            "home_avg_scored":    home_goals["scored"],
            "home_avg_conceded":  home_goals["conceded"],
            "away_avg_scored":    away_goals["scored"],
            "away_avg_conceded":  away_goals["conceded"],
        }])

        # ── 4. Elencos reais (Cópia profunda para evitar poluir cache) ────────
        home_squad = copy.deepcopy(self.data_loader.get_real_squad_data(home_team))
        away_squad = copy.deepcopy(self.data_loader.get_real_squad_data(away_team))

        if home_starters:
            home_squad = self._apply_custom_starters(home_squad, home_starters)
        if away_starters:
            away_squad = self._apply_custom_starters(away_squad, away_starters)

        # ── EXCLUSÕES MANUAIS (Simulação do Menu de Lesões) ───────────────────
        if home_excluded:
            home_squad = self._apply_manual_exclusions(home_squad, home_excluded)
        if away_excluded:
            away_squad = self._apply_manual_exclusions(away_squad, away_excluded)

        # ── 5. Ajuste de elenco por lesões genéricas de banco ─────────────────
        home_players = self._apply_injury_penalty(
            home_squad.get("top_players", []),
            home_squad.get("injured_count", 0),
        )
        away_players = self._apply_injury_penalty(
            away_squad.get("top_players", []),
            away_squad.get("injured_count", 0),
        )

        # Aplica a matemática pesada das estrelas
        final_home_rating = self._calculate_weighted_rating(home_players)
        final_away_rating = self._calculate_weighted_rating(away_players)

        # ── 6. Clima da sede ──────────────────────────────────────────────────
        stadium_city = stadium if stadium else self._get_stadium_for_match(home_team)
        temp = self.get_weather(stadium_city)

        # ── 6.5 Impacto do Clima (Debuff) ─────────────────────────────────────
        # Times adaptados ao frio sofrendo no calor extremo (>26) e vice-versa (<15)
        home_climate = TEAM_NATIVE_CLIMATE.get(home_team, "MODERATE")
        away_climate = TEAM_NATIVE_CLIMATE.get(away_team, "MODERATE")

        home_modifier = 1.0
        away_modifier = 1.0

        if temp >= 26.0:
            if home_climate == "COLD": home_modifier = 0.975
            if away_climate == "COLD": away_modifier = 0.975
        elif temp <= 15.0:
            if home_climate == "HOT": home_modifier = 0.975
            if away_climate == "HOT": away_modifier = 0.975

        final_home_rating *= home_modifier
        final_away_rating *= away_modifier

        # ── 7. Diagnóstico ────────────────────────────────────────────────────
        _verify_squad(home_team, home_players)
        _verify_squad(away_team, away_players)

        return {
            "df_ml":           df_ml,
            "temperature":     round(temp, 1),
            "stadium":         stadium_city,
            "home_modifiers":  1.0,  
            "away_modifiers":  1.0,  
            "home_elo":        home_elo,   
            "away_elo":        away_elo,   
            "home_confidence": home_squad.get("confidence", 1.0),
            "away_confidence": away_squad.get("confidence", 1.0),
            "home_injuries":   home_squad.get("injured_count", 0),
            "away_injuries":   away_squad.get("injured_count", 0),
            "home_rating":     final_home_rating,
            "away_rating":     final_away_rating,
            "home_players":    home_players,
            "away_players":    away_players,
            "home_bench":      home_squad.get("bench_players", []),
            "away_bench":      away_squad.get("bench_players", []),
            "home_data_source": home_squad.get("data_source", "Desconhecido"),
            "away_data_source": away_squad.get("data_source", "Desconhecido"),
        }

    def _apply_manual_exclusions(self, squad: dict, excluded_names: list) -> dict:
        """
        Remove o jogador exato da lista de titulares, 
        sobe o reserva adequado e recalcula a nota com pesos.
        """
        top = squad.get("top_players", [])
        bench = squad.get("bench_players", [])
        
        for name in excluded_names:
            if not name or name == "Nenhum":
                continue
                
            # Busca exata primeiro (já que vem do menu) ou aproximada como fallback
            top_names = [p["name"] for p in top]
            if name in top_names:
                match_top = [name]
            else:
                match_top = get_close_matches(name, top_names, n=1, cutoff=0.6)
            
            if match_top:
                removed_player = next(p for p in top if p["name"] == match_top[0])
                top.remove(removed_player)
                
                if bench:
                    same_pos = [p for p in bench if p["position"] == removed_player["position"]]
                    if same_pos:
                        sub = max(same_pos, key=lambda x: x["rating"])
                    else:
                        sub = max(bench, key=lambda x: x["rating"])
                    
                    bench.remove(sub)
                    top.append(sub)
                
                squad["data_source"] = f"{squad.get('data_source')} (Sem {match_top[0]})"
                continue
                
            # Se estava só no banco, tira de lá
            bench_names = [p["name"] for p in bench]
            if name in bench_names:
                match_bench = [name]
            else:
                match_bench = get_close_matches(name, bench_names, n=1, cutoff=0.6)
                
            if match_bench:
                removed_player = next(p for p in bench if p["name"] == match_bench[0])
                bench.remove(removed_player)
                
        if top:
            squad["squad_rating"] = self._calculate_weighted_rating(top)
            
        squad["top_players"] = top
        squad["bench_players"] = bench
        return squad

    @staticmethod
    def _apply_injury_penalty(players: list[dict], injured_count: int) -> list[dict]:
        if injured_count <= 0 or not players:
            return players
        sorted_players = sorted(players, key=lambda p: p.get("rating", 7.0))
        remove_n = min(injured_count, 3, len(sorted_players) - 7)
        if remove_n <= 0:
            return players
        removed_names = {p["name"] for p in sorted_players[:remove_n]}
        return [p for p in players if p["name"] not in removed_names]


def _verify_squad(team_name: str, players: list) -> None:
    if not players:
        print(f"[FeatureBuilder] AVISO: elenco de '{team_name}' está VAZIO.")
        return
    real_names = [p["name"] for p in players[:3] if not re.match(r"^[A-Z]{2,3}\s+\w+\d", p["name"])]
    if len(real_names) == 0:
        print(f"[FeatureBuilder] AVISO: '{team_name}' usando elenco genérico mínimo.")