"""
models/simulator.py — VERSÃO v36 (Vegas Blend Ativado)

MUDANÇAS v36:
  - VEGAS BLEND: O simulador agora baixa as Odds Reais do mercado de apostas na inicialização.
    Ele usa a percepção dos apostadores para guiar e corrigir as previsões da nossa Inteligência
    Artificial num peso de até 20%. Isso garante que coisas inexplicáveis (lesões misteriosas,
    crises na seleção) que a IA não sabe, sejam incorporadas via precificação de mercado.
"""

import numpy as np
import pandas as pd
import joblib
from scipy.stats import poisson
from pathlib import Path
from utils.feature_builder import FeatureBuilder
import random
import itertools
from collections import defaultdict
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import os
import time

# IMPORTAÇÃO DA API DE CASAS DE APOSTAS
import sys
sys.path.append(str(Path(__file__).parent.parent))
from api_clients.football_api import TheOddsAPI

MODEL_PATH = Path(__file__).parent.parent / "data" / "xgboost_model.pkl"
PLAYER_ML_PATH = Path(__file__).parent.parent / "data" / "player_ml_models.pkl"

_LAMBDA_WORLD_CUP_AVG = 1.25  

# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZAÇÃO E ALIASES
# ─────────────────────────────────────────────────────────────────────────────
_TRANS = str.maketrans(
    "áéíóúãõçÁÉÍÓÚÃÕÇàèìòùÀÈÌÒÙäëïöüÄËÏÖÜ",
    "aeiouaocAEIOUAOCaeiouAEIOUaeiouAEIOU"
)

def _normalize_name(n: str) -> str:
    n = str(n).lower().translate(_TRANS).replace('-', ' ')
    return " ".join(c for c in n.split() if c.isalnum() or ' ' in c)

ALIAS_GROUPS = [
    {"yamal", "lamine yamal", "lamine"},
    {"nico williams", "n williams", "nicholas williams"},
    {"pedri", "pedro gonzalez lopez"},
    {"rodri", "rodrigo hernandez cascante", "rodrigo hernandez"},
    {"ferran", "ferran torres"},
    {"oyarzabal", "mikel oyarzabal"},
    {"cubarsi", "pau cubarsi"},
    {"grimaldo", "alejandro grimaldo"},
    {"fabian", "fabian ruiz"},
    {"llorente", "marcos llorente"},
    {"laporte", "aymeric laporte"},
    {"cucurella", "marc cucurella"},
    {"zubimendi", "martin zubimendi"},
    {"gavi", "pablo martin paez gavira", "pablo gavi"},
    {"baena", "alex baena"},
    {"dani olmo", "daniel olmo"},
    {"mbappe", "kylian mbappe"},
    {"dembele", "ousmane dembele"},
    {"doue", "desire doue"},
    {"olise", "michael olise"},
    {"tchouameni", "aurelien tchouameni"},
    {"rabiot", "adrien rabiot"},
    {"upamecano", "dayot upamecano"},
    {"maignan", "mike maignan"},
    {"kounde", "jules kounde"},
    {"griezmann", "antoine griezmann"},
    {"barcola", "bradley barcola"},
    {"camavinga", "eduardo camavinga"},
    {"hernandez", "theo hernandez", "lucas hernandez"},
    {"saka", "bukayo saka"},
    {"bellingham", "jude bellingham"},
    {"kane", "harry kane"},
    {"eze", "eberechi eze"},
    {"foden", "phil foden"},
    {"vinicius jr", "vini jr", "vinicius junior", "vinicius"},
    {"raphinha", "raphael dias belloli"},
    {"cunha", "matheus cunha"},
    {"luis henrique", "luiz henrique"},
    {"endrick", "endrick felipe"},
    {"rodrygo", "rodrygo silva de goes"},
    {"paqueta", "lucas paqueta"},
    {"bruno fernandes", "b fernandes"},
    {"cristiano ronaldo", "c ronaldo", "ronaldo"},
    {"pepe", "kepler laveran"},
    {"vitinha", "vitor machado ferreira"},
    {"leao", "rafael leao"},
    {"joao felix", "j felix"},
    {"bernardo silva", "b silva"},
    {"ruben dias", "r dias"},
    {"musiala", "jamal musiala"},
    {"wirtz", "florian wirtz"},
    {"havertz", "kai havertz"},
    {"sane", "leroy sane"},
    {"son", "son heung min", "heung min son"},
    {"kante", "ngolo kante", "golo kante"},
    {"depay", "memphis depay"},
    {"james", "james rodriguez"},
    {"valencia", "enner valencia"},
    {"caicedo", "moises caicedo"},
    {"yeboah", "john yeboah"},
    {"kramaric", "andrej kramaric"},
    {"perisic", "ivan perisic"},
    {"budimir", "ante budimir"},
    {"gakpo", "cody gakpo"},
    {"de jong", "frenkie de jong"},
    {"darwin", "darwin nunez"},
    {"messi", "lionel messi"},
    {"alvarez", "julian alvarez"}
]

def _build_alias_map() -> dict:
    alias_map = {}
    for group in ALIAS_GROUPS:
        canonical = sorted(group, key=len)[-1]  
        for name in group:
            alias_map[_normalize_name(name)] = _normalize_name(canonical)
    return alias_map

ALIAS_MAP = _build_alias_map()

def _canonical(name_norm: str) -> str:
    return ALIAS_MAP.get(name_norm, name_norm)

def _build_lookup(raw_dict: dict) -> dict:
    lookup = {}
    for raw_key, val in raw_dict.items():
        canonical = _canonical(raw_key)
        lookup[canonical] = val
        lookup[raw_key] = val
    return lookup

def _get_value(lookup: dict, name_norm: str, default):
    canonical = _canonical(name_norm)
    if canonical in lookup: return lookup[canonical]
    if name_norm in lookup: return lookup[name_norm]
    
    parts = name_norm.split()
    if len(parts) == 1:
        for k in lookup:
            k_parts = k.split()
            if parts[0] in k_parts and parts[0] not in {
                "martinez", "williams", "silva", "santos", "garcia",
                "rodriguez", "gomez", "fernandez", "lopez", "gonzalez",
                "perez", "hernandez", "da", "de", "dos"
            }:
                return lookup[k]
    return default

def _get_league_weight(league_name: str, player_name_norm: str = "") -> float:
    base = 0.80
    lname = str(league_name).lower()
    if any(x in lname for x in ['premier', 'england', 'la liga', 'spain', 'champions']): base = 1.00
    elif any(x in lname for x in ['serie a', 'italy', 'bundesliga', 'germany']):          base = 0.92
    elif any(x in lname for x in ['ligue 1', 'france']):                                  base = 0.85
    elif any(x in lname for x in ['portugal', 'primeira']):                               base = 0.78
    elif any(x in lname for x in ['saudi', 'mls', 'brasil', 'argentina', 'eredivisie']): base = 0.65
    return base


class MatchSimulator:
    def __init__(self):
        self.feature_builder = FeatureBuilder()
        self.teams_info = self.feature_builder.data_loader.get_all_teams()

        if not MODEL_PATH.exists():
            raise FileNotFoundError("Modelo principal de times não encontrado.")
        self.models = joblib.load(MODEL_PATH)
        self.rho = -0.13   

        # ── INTEGRAÇÃO: APIS DE CASAS DE APOSTAS ──
        self.odds_client = TheOddsAPI()
        raw_odds_data = self.odds_client.get_world_cup_odds()
        self.vegas_probs = self._parse_vegas_odds(raw_odds_data)

        season_raw = {}
        season_csv = Path(__file__).parent.parent / "data" / "players_data-2025_2026.csv"
        if season_csv.exists():
            try:
                df_season = pd.read_csv(season_csv)
                name_col = next((c for c in df_season.columns if c.lower() in ['name', 'player', 'jogador', 'nome']), None)
                comp_col = next((c for c in df_season.columns if c.lower() in ['comp', 'league', 'liga', 'competition', 'campeonato']), None)
                age_col  = next((c for c in df_season.columns if c.lower() in ['age', 'idade']), None)
                pk_col   = next((c for c in df_season.columns if c == 'PK'), None) 
                
                if name_col:
                    for _, row in df_season.iterrows():
                        p_name = str(row[name_col]).strip()
                        norm_name = _normalize_name(p_name)
                        c = str(row[comp_col]).strip().lower() if comp_col and pd.notna(row[comp_col]) else "unknown"
                        age = float(row[age_col]) if age_col and pd.notna(row[age_col]) else 25.0
                        pk = float(row[pk_col]) if pk_col and pd.notna(row[pk_col]) else 0.0
                        season_raw[norm_name] = {'league': c, 'age': age, 'pk': pk}
            except Exception as e:
                pass
        self._season_lookup = _build_lookup(season_raw)

        tm_raw = {}
        df_tm = self.feature_builder.data_loader.tm_players
        if not df_tm.empty:
            name_c = "name" if "name" in df_tm.columns else "first_name"
            val_c = "market_value_in_eur"
            if name_c in df_tm.columns and val_c in df_tm.columns:
                for _, row in df_tm.iterrows():
                    try:
                        mv = float(row[val_c]) / 1_000_000.0
                        tm_raw[_normalize_name(row[name_c])] = mv
                    except: pass
        self._tm_lookup = _build_lookup(tm_raw)

        fifa_raw = {}
        df_fifa = self.feature_builder.data_loader.players_db
        if not df_fifa.empty and "Name" in df_fifa.columns:
            for _, row in df_fifa.iterrows():
                p_name = _normalize_name(str(row["Name"]))
                fifa_raw[p_name] = float(row.get("OVR", 70))
        self._fifa_lookup = _build_lookup(fifa_raw)

        self.ai_player_rates = {}
        self.player_models = None
        if PLAYER_ML_PATH.exists():
            try:
                self.player_models = joblib.load(PLAYER_ML_PATH)
                self._init_ai_player_rates()
            except Exception as e:
                pass

    def _parse_vegas_odds(self, raw_data: list) -> dict:
        """Converte as Odds decimais (ex: 2.10) em Probabilidade Implícita e salva no cache em RAM."""
        vegas = {}
        if not raw_data: return vegas
        
        # Pega a base de aliases para converter "United States" em "USA", etc.
        from utils.data_loader import SQUAD_NAME_ALIASES
        alias_reverse = {}
        for std, aliases in SQUAD_NAME_ALIASES.items():
            for a in aliases:
                alias_reverse[_canonical(_normalize_name(a))] = std

        for event in raw_data:
            h_raw = event.get('home_team', '')
            a_raw = event.get('away_team', '')
            
            h_canon = _canonical(_normalize_name(h_raw))
            a_canon = _canonical(_normalize_name(a_raw))
            
            home_team = alias_reverse.get(h_canon, h_raw)
            away_team = alias_reverse.get(a_canon, a_raw)

            bookmakers = event.get('bookmakers', [])
            if not bookmakers: continue
            
            # Pega o primeiro bookmaker disponível (geralmente DraftKings ou Pinnacle)
            markets = bookmakers[0].get('markets', [])
            h2h = next((m for m in markets if m['key'] == 'h2h'), None)
            if not h2h: continue
            
            outcomes = h2h.get('outcomes', [])
            price_h, price_a, price_d = 0, 0, 0
            
            for out in outcomes:
                o_canon = _canonical(_normalize_name(out['name']))
                if o_canon == h_canon: price_h = out['price']
                elif o_canon == a_canon: price_a = out['price']
                elif out['name'].lower() == 'draw': price_d = out['price']
                
            if price_h and price_a and price_d:
                # Remove o Juice/Vig da Casa de Aposta e pega a probabilidade pura
                impl_h = 1 / price_h
                impl_a = 1 / price_a
                impl_d = 1 / price_d
                total = impl_h + impl_a + impl_d
                
                vegas[(home_team, away_team)] = (impl_h/total, impl_d/total, impl_a/total)
                vegas[(away_team, home_team)] = (impl_a/total, impl_d/total, impl_h/total)
                
        return vegas

    def _apply_vegas_boost(self, lh: float, la: float, home: str, away: str) -> tuple[float, float]:
        """
        Mistura a Inteligência Artificial com o Conhecimento de Mercado (Casas de Apostas).
        Puxa as previsões de Gols em até 15% na direção do que Vegas acredita.
        """
        v_probs = self.vegas_probs.get((home, away))
        if v_probs:
            v_ph, v_pd, v_pa = v_probs
            
            # Razão de Força de Vegas vs Razão de Força da Máquina
            v_ratio = v_ph / max(v_pa, 0.01)
            ai_ratio = lh / max(la, 0.01)
            
            # Quão distante estamos do mercado? (Damos peso de 35% à sabedoria das massas)
            correction = (v_ratio / ai_ratio) ** 0.35 
            
            # Para evitar quebra da matemática Poisson, limitamos a influência a ±15%
            correction = np.clip(correction, 0.85, 1.15)
            
            lh *= correction
            la /= correction
            
        return lh, la

    def _get_true_rating(self, n_norm: str, default_rating: float) -> float:
        ea_ovr = _get_value(self._fifa_lookup, n_norm, None)
        if ea_ovr is not None:
            r = ea_ovr / 10.0
        else:
            r = default_rating
            
        mv = _get_value(self._tm_lookup, n_norm, 5.0)
        
        if mv >= 120.0: r = max(r, 9.2) 
        elif mv >= 90.0: r = max(r, 8.9)
        elif mv >= 60.0: r = max(r, 8.6)
        elif mv >= 40.0: r = max(r, 8.3)
        elif mv >= 20.0: r = max(r, 8.0)
        
        return float(np.clip(r, 5.0, 9.9))

    def _init_ai_player_rates(self):
        player_features = []
        player_names = []
        pos_mapping = {"Attacker": 3, "Midfielder": 2, "Defender": 1, "Goalkeeper": 0}

        for team in self.teams_info.keys():
            sq = self.feature_builder.data_loader.get_real_squad_data(team)
            roster = sq.get("top_players", []) + sq.get("bench_players", [])
            if not roster:
                roster = self.feature_builder.data_loader._build_minimal_squad(team)

            for p in roster:
                if p["name"] in self.ai_player_rates: continue

                n_norm = _normalize_name(p["name"])
                season_data = _get_value(self._season_lookup, n_norm, {'league':'unknown', 'age':25.0, 'pk':0.0})
                
                mv = _get_value(self._tm_lookup, n_norm, 5.0)
                league_w = _get_league_weight(season_data['league'], n_norm)
                pos_code = pos_mapping.get(p.get("position", "Midfielder"), 2)
                
                true_rating = self._get_true_rating(n_norm, p.get("rating", 7.0))

                player_features.append({
                    "Age": season_data['age'],
                    "Pos_Code": pos_code,
                    "EA_Rating": true_rating * 10.0, 
                    "League_Weight": league_w,
                    "Market_Value": np.log1p(mv)
                })
                player_names.append(p["name"])
                self.ai_player_rates[p["name"]] = {"xg": 0.05, "xa": 0.05}

        if player_features and self.player_models:
            df_features = pd.DataFrame(player_features)
            pred_g = self.player_models["model_goals"].predict(df_features)
            pred_a = self.player_models["model_assists"].predict(df_features)

            for i, name in enumerate(player_names):
                self.ai_player_rates[name] = {"xg": float(pred_g[i]), "xa": float(pred_a[i])}

    def _dixon_coles(self, x: int, y: int, lx: float, ly: float) -> float:
        if x == 0 and y == 0: return max(0.01, 1 - lx * ly * self.rho)
        elif x == 0 and y == 1: return max(0.01, 1 + lx * self.rho)
        elif x == 1 and y == 0: return max(0.01, 1 + ly * self.rho)
        elif x == 1 and y == 1: return max(0.01, 1 - self.rho)
        return 1.0

    def _squad_elo_modifier(self, own_rating: float, opp_rating: float) -> float:
        rating_diff = (own_rating - opp_rating) * 0.07 
        raw = 1.0 + rating_diff
        return float(np.clip(raw, 0.85, 1.15))

    def _compute_lambdas(self, home_team: str, away_team: str, home_rating: float, away_rating: float, home_elo: float, away_elo: float, df_home: object, df_away: object) -> tuple[float, float, float, float]:
        lh_p1 = float(self.models["home"].predict(df_home)[0])
        la_p1 = float(self.models["away"].predict(df_home)[0])
        lh_p2 = float(self.models["away"].predict(df_away)[0])
        la_p2 = float(self.models["home"].predict(df_away)[0])

        base_lh = (lh_p1 + lh_p2) / 2.0
        base_la = (la_p1 + la_p2) / 2.0

        if home_elo >= 1880 and away_elo >= 1880:
            adaptive_shrinkage = 0.70  
        else:
            elo_gap = abs(home_elo - away_elo)
            adaptive_shrinkage = float(np.interp(elo_gap, [0, 400], [0.55, 0.20]))
            
        base_lh = (1 - adaptive_shrinkage) * base_lh + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG
        base_la = (1 - adaptive_shrinkage) * base_la + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG

        modifier_home = self._squad_elo_modifier(home_rating, away_rating)
        modifier_away = self._squad_elo_modifier(away_rating, home_rating)

        HOME_ADV = {"USA": 1.05, "Mexico": 1.06, "Canada": 1.04}
        hadv = HOME_ADV.get(home_team, 1.0)

        GOAL_BOOST = 1.30

        lh_final = float(np.clip(base_lh * modifier_home * hadv, 0.25, 3.20)) * GOAL_BOOST
        la_final = float(np.clip(base_la * modifier_away, 0.25, 3.20)) * GOAL_BOOST

        # 🎰 APLICAÇÃO DO VEGAS BLEND
        lh_final, la_final = self._apply_vegas_boost(lh_final, la_final, home_team, away_team)

        return lh_final, la_final, modifier_home, modifier_away

    def _build_prob_matrix(self, lh: float, la: float, max_goals: int = 9) -> np.ndarray:
        mat = np.zeros((max_goals, max_goals))
        for i in range(max_goals):
            for j in range(max_goals):
                p = poisson.pmf(i, lh) * poisson.pmf(j, la)
                mat[i, j] = max(0.0, p * self._dixon_coles(i, j, lh, la))
        mat /= mat.sum()
        return mat

    def _calculate_team_dynamics(self, roster: list[dict]):
        starters = roster[:11]
        best_pk_score = -1
        pk_taker = ""
        
        for p in starters:
            name = p["name"]
            n_norm = _normalize_name(name)
            season_data = _get_value(self._season_lookup, n_norm, {'pk': 0.0})
            pk = season_data['pk']
            
            if p.get("position") in ["Attacker", "Midfielder"]:
                score = (pk * 20) + p.get("rating", 7.0)
                if score > best_pk_score:
                    best_pk_score = score
                    pk_taker = name
                    
        gr_list, ar_list = [], []
        
        for i, p in enumerate(roster):
            is_pk = (p["name"] == pk_taker)
            time_w = 1.0 if i < 11 else (0.55 if i < 16 else 0.15)
            
            gr = self._player_goal_rate(p, is_pk)
            ar = self._player_assist_rate(p)
            
            gr_list.append(gr * time_w)
            ar_list.append(ar * time_w)
            
        return gr_list, ar_list

    def _player_goal_rate(self, player: dict, is_pk: bool) -> float:
        name = player.get("name", "")
        pos = player.get("position", "Midfielder")
        n_norm = _normalize_name(name)

        true_rating = self._get_true_rating(n_norm, player.get("rating", 7.0))
        ai_rate = max(0.01, self.ai_player_rates.get(name, {}).get("xg", 0.08))
        
        rating_mult = (true_rating / 7.0) ** 1.8 
        final_rate = ai_rate * rating_mult

        if is_pk: final_rate += 0.08 

        if pos == "Defender": final_rate *= 0.15
        elif pos == "Goalkeeper": final_rate = 0.001
        elif pos == "Midfielder": final_rate *= 0.60
        elif pos == "Attacker": final_rate *= 1.25

        if "haaland" in n_norm: final_rate *= 1.35        
        elif "mbappe" in n_norm: final_rate *= 1.30       
        elif "messi" in n_norm: final_rate *= 1.30        
        elif "kane" in n_norm: final_rate *= 1.30         
        elif "raphinha" in n_norm: final_rate *= 1.25     
        elif "ferran" in n_norm: final_rate *= 1.25       
        elif "vinicius" in n_norm or "vini" in n_norm: 
            final_rate *= 0.85                            

        return float(np.clip(final_rate, 0.001, 5.0))

    def _player_assist_rate(self, player: dict) -> float:
        name = player.get("name", "")
        pos = player.get("position", "Midfielder")
        n_norm = _normalize_name(name)

        true_rating = self._get_true_rating(n_norm, player.get("rating", 7.0))
        ai_rate = max(0.01, self.ai_player_rates.get(name, {}).get("xa", 0.08))
        
        rating_mult = (true_rating / 7.0) ** 1.8 
        final_rate = ai_rate * rating_mult

        if pos == "Defender": final_rate *= 0.35
        elif pos == "Goalkeeper": final_rate = 0.001
        elif pos == "Attacker": final_rate *= 0.80
        elif pos == "Midfielder": final_rate *= 1.30

        if "olise" in n_norm: final_rate *= 1.35          
        elif "yamal" in n_norm: final_rate *= 1.30        
        elif "cherki" in n_norm: final_rate *= 1.35       
        elif "bruno fernandes" in n_norm or "b fernandes" in n_norm: 
            final_rate *= 1.30                            

        return float(np.clip(final_rate, 0.001, 5.0))

    def _performance_rating(self, player: dict, scored: bool, assisted: bool, gf: int, ga: int, is_home: bool) -> float:
        pos = player.get("position", "Midfielder")
        base = player.get("rating", 7.0)
        goals_conceded = ga if is_home else gf
        goals_scored = gf if is_home else ga
        noise = random.gauss(0, 0.20)

        if pos == "Goalkeeper":
            if goals_conceded == 0: bonus = +0.9
            elif goals_conceded == 1: bonus = +0.2
            elif goals_conceded == 2: bonus = -0.2
            else: bonus = -0.6
        elif pos == "Defender":
            if goals_conceded == 0: bonus = +0.6
            elif goals_conceded == 1: bonus = +0.1
            elif goals_conceded >= 3: bonus = -0.5
            else: bonus = -0.1
            if scored: bonus += 0.5
        elif pos == "Midfielder":
            bonus = 0.0
            if scored: bonus += 0.35
            if assisted: bonus += 0.25
            if goals_scored > goals_conceded: bonus += 0.15
        elif pos == "Attacker":
            bonus = -0.15
            if scored: bonus += 0.45
            if assisted: bonus += 0.20
        else:
            bonus = 0.10 if scored else 0.0

        return round(float(np.clip(base + bonus + noise, 4.5, 9.5)), 2)

    def simulate_match(self, home_team: str, away_team: str, num_simulations: int = 400, is_friendly: int = 0, home_excluded: list = None, away_excluded: list = None) -> dict:
        if home_excluded is None: home_excluded = []
        if away_excluded is None: away_excluded = []

        feats = self.feature_builder.build_match_features(home_team, away_team, is_friendly, home_excluded, away_excluded)
        feats_inv = self.feature_builder.build_match_features(away_team, home_team, is_friendly, away_excluded, home_excluded)

        home_rating = feats["home_rating"]
        away_rating = feats["away_rating"]
        home_elo = feats["home_elo"]
        away_elo = feats["away_elo"]

        lh, la, mod_h, mod_a = self._compute_lambdas(
            home_team, away_team, home_rating, away_rating, home_elo, away_elo, feats["df_ml"], feats_inv["df_ml"],
        )

        prob_matrix = self._build_prob_matrix(lh, la)
        max_goals = prob_matrix.shape[0]

        home_win_prob = float(np.sum(np.tril(prob_matrix, -1))) * 100
        draw_prob = float(np.trace(prob_matrix)) * 100
        away_win_prob = float(np.sum(np.triu(prob_matrix, 1))) * 100

        home_sq_full = self.feature_builder.data_loader.get_real_squad_data(home_team)
        away_sq_full = self.feature_builder.data_loader.get_real_squad_data(away_team)
        
        home_bench = [p for p in home_sq_full.get("bench_players", []) if p["name"] not in home_excluded]
        away_bench = [p for p in away_sq_full.get("bench_players", []) if p["name"] not in away_excluded]

        home_roster = feats["home_players"] + home_bench
        away_roster = feats["away_players"] + away_bench

        if not home_roster: home_roster = self.feature_builder.data_loader._build_minimal_squad(home_team)
        if not away_roster: away_roster = self.feature_builder.data_loader._build_minimal_squad(away_team)

        h_rates, h_ast_rates = self._calculate_team_dynamics(home_roster)
        a_rates, a_ast_rates = self._calculate_team_dynamics(away_roster)

        if sum(h_rates) == 0: h_rates = [1.0] * len(home_roster)
        if sum(a_rates) == 0: a_rates = [1.0] * len(away_roster)
        if sum(h_ast_rates) == 0: h_ast_rates = [1.0] * len(home_roster)
        if sum(a_ast_rates) == 0: a_ast_rates = [1.0] * len(away_roster)

        _scale_h = lh / _LAMBDA_WORLD_CUP_AVG
        _scale_a = la / _LAMBDA_WORLD_CUP_AVG
        h_rates     = [r * _scale_h for r in h_rates]
        h_ast_rates = [r * _scale_h for r in h_ast_rates]
        a_rates     = [r * _scale_a for r in a_rates]
        a_ast_rates = [r * _scale_a for r in a_ast_rates]

        N_SCORE_SAMPLES = 1000
        flat_probs = prob_matrix.flatten()
        sampled_scores = np.random.choice(len(flat_probs), size=N_SCORE_SAMPLES, p=flat_probs)
        score_freq: dict[str, int] = defaultdict(int)
        for s in sampled_scores:
            sg = int(s // max_goals)
            ag_ = int(s % max_goals)
            score_freq[f"{sg} x {ag_}"] += 1

        most_likely = {
            sc: round(cnt / N_SCORE_SAMPLES * 100, 1)
            for sc, cnt in sorted(score_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        }

        if home_win_prob > away_win_prob and home_win_prob > draw_prob: outcome = "home"
        elif away_win_prob > home_win_prob and away_win_prob > draw_prob: outcome = "away"
        else: outcome = "draw"

        best_score = "0 x 0"
        best_count = -1
        for sc, cnt in score_freq.items():
            parts = sc.split(" x ")
            hg_sc, ag_sc = int(parts[0]), int(parts[1])
            if outcome == "home" and hg_sc > ag_sc:
                if cnt > best_count: best_count = cnt; best_score = sc
            elif outcome == "away" and ag_sc > hg_sc:
                if cnt > best_count: best_count = cnt; best_score = sc
            elif outcome == "draw" and hg_sc == ag_sc:
                if cnt > best_count: best_count = cnt; best_score = sc

        if best_count == -1:
            best_score = max(score_freq.items(), key=lambda x: x[1])[0]

        expected_score_str = f"{home_team} {best_score} {away_team}"

        sampled = np.random.choice(len(flat_probs), size=num_simulations, p=flat_probs)
        home_sims = sampled // max_goals
        away_sims = sampled % max_goals

        player_goals: defaultdict = defaultdict(int)
        player_assists: defaultdict = defaultdict(int)
        player_perf_sum: defaultdict = defaultdict(float)
        player_perf_count: defaultdict = defaultdict(int)
        sim_logs: list[str] = []

        ha = home_team[:3].upper()
        aa = away_team[:3].upper()

        for k in range(num_simulations):
            hg = int(home_sims[k])
            ag = int(away_sims[k])

            home_log: list[str] = []
            away_log: list[str] = []
            home_scorers: set = set()
            away_scorers: set = set()
            home_ast_set: set = set()
            away_ast_set: set = set()

            if hg > 0:
                _assign_goals_and_assists(home_roster, h_rates, h_ast_rates, hg, player_goals, player_assists, home_log, home_scorers, home_ast_set)
            if ag > 0:
                _assign_goals_and_assists(away_roster, a_rates, a_ast_rates, ag, player_goals, player_assists, away_log, away_scorers, away_ast_set)

            log = f"Sim {k+1:03d}: {ha} {hg} x {ag} {aa}"
            parts = []
            if home_log: parts.append(f"[{ha}] {', '.join(home_log)}")
            if away_log: parts.append(f"[{aa}] {', '.join(away_log)}")
            if parts: log += " | Gols: " + " - ".join(parts)
            sim_logs.append(log)

        for p in home_roster:
            sc = p["name"] in home_scorers
            ast = p["name"] in home_ast_set
            perf = self._performance_rating(p, sc, ast, hg, ag, True)
            player_perf_sum[p["name"]] += perf
            player_perf_count[p["name"]] += 1

        for p in away_roster:
            sc = p["name"] in away_scorers
            ast = p["name"] in away_ast_set
            perf = self._performance_rating(p, sc, ast, hg, ag, False)
            player_perf_sum[p["name"]] += perf
            player_perf_count[p["name"]] += 1

        top_scorers = sorted(player_goals.items(), key=lambda x: x[1], reverse=True)[:5]
        top_assists = sorted(player_assists.items(), key=lambda x: x[1], reverse=True)[:5]

        avg_perf = {k: round(v / player_perf_count[k], 2) for k, v in player_perf_sum.items() if player_perf_count[k] > 0}
        top_ratings = sorted(avg_perf.items(), key=lambda x: x[1], reverse=True)[:5]

        score_series = pd.Series(most_likely)

        return {
            "home_win_prob": round(home_win_prob, 1),
            "draw_prob": round(draw_prob, 1),
            "away_win_prob": round(away_win_prob, 1),
            "most_likely_scores": score_series,
            "expected_score": expected_score_str,
            "home_lambda": round(lh, 2),
            "away_lambda": round(la, 2),
            "modifier_home": round(mod_h, 3),
            "modifier_away": round(mod_a, 3),
            "temperature": feats["temperature"],
            "stadium": feats.get("stadium", "Miami"),
            "home_rating": home_rating,
            "away_rating": away_rating,
            "home_injuries": feats["home_injuries"],
            "away_injuries": feats["away_injuries"],
            "home_data_source": feats["home_data_source"],
            "away_data_source": feats["away_data_source"],
            "home_elo": home_elo,
            "away_elo": away_elo,
            "sim_logs": sim_logs,
            "top_scorers": top_scorers,
            "top_assists": top_assists,
            "top_ratings": top_ratings,
        }

    def _build_vectorized_match_cache(self) -> dict:
        teams = list(self.teams_info.keys())
        all_pairs = list(itertools.combinations(teams, 2))

        t_data = {}
        for t in teams:
            sq = self.feature_builder.data_loader.get_real_squad_data(t)
            top = sq.get("top_players", [])
            bench = sq.get("bench_players", [])
            if not top:
                top = self.feature_builder.data_loader._build_minimal_squad(t)
                bench = []
            roster = top + bench
            
            elo = self.feature_builder.data_loader.get_team_elo(t)
            goals = self.feature_builder.data_loader.get_historical_goals(t)
            rating = FeatureBuilder._calculate_weighted_rating(top)

            gr, ar = self._calculate_team_dynamics(roster)
            if sum(gr) == 0: gr = [1.0]*len(roster)
            if sum(ar) == 0: ar = [1.0]*len(roster)

            t_data[t] = {"elo": elo, "goals": goals, "rating": rating, "p": roster, "gr": gr, "ar": ar}

        rows_p1 = []
        rows_p2 = []
        HOME_ADV_TEAMS = {"USA", "Mexico", "Canada"}

        for h, a in all_pairs:
            rows_p1.append({
                "home_adv": 1 if h in HOME_ADV_TEAMS else 0, "is_friendly": 0, "is_world_cup": 1,
                "home_elo_pre_match": t_data[h]["elo"], "away_elo_pre_match": t_data[a]["elo"],
                "elo_diff": t_data[h]["elo"] - t_data[a]["elo"],
                "home_avg_scored": t_data[h]["goals"]["scored"], "home_avg_conceded": t_data[h]["goals"]["conceded"],
                "away_avg_scored": t_data[a]["goals"]["scored"], "away_avg_conceded": t_data[a]["goals"]["conceded"],
            })
            rows_p2.append({
                "home_adv": 1 if a in HOME_ADV_TEAMS else 0, "is_friendly": 0, "is_world_cup": 1,
                "home_elo_pre_match": t_data[a]["elo"], "away_elo_pre_match": t_data[h]["elo"],
                "elo_diff": t_data[a]["elo"] - t_data[h]["elo"],
                "home_avg_scored": t_data[a]["goals"]["scored"], "home_avg_conceded": t_data[a]["goals"]["conceded"],
                "away_avg_scored": t_data[h]["goals"]["scored"], "away_avg_conceded": t_data[h]["goals"]["conceded"],
            })

        df_p1 = pd.DataFrame(rows_p1)
        df_p2 = pd.DataFrame(rows_p2)

        lh_p1 = self.models["home"].predict(df_p1)
        la_p1 = self.models["away"].predict(df_p1)
        lh_p2 = self.models["away"].predict(df_p2)
        la_p2 = self.models["home"].predict(df_p2)

        match_cache = {}
        for i, (h, a) in enumerate(all_pairs):
            base_lh = (lh_p1[i] + lh_p2[i]) / 2.0
            base_la = (la_p1[i] + la_p2[i]) / 2.0

            elo_h = t_data[h]["elo"]
            elo_a = t_data[a]["elo"]
            
            if elo_h >= 1880 and elo_a >= 1880:
                adaptive_shrinkage = 0.70  
            else:
                elo_gap = abs(elo_h - elo_a)
                adaptive_shrinkage = float(np.interp(elo_gap, [0, 400], [0.55, 0.20]))
                
            base_lh = (1 - adaptive_shrinkage) * base_lh + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG
            base_la = (1 - adaptive_shrinkage) * base_la + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG

            mod_h = self._squad_elo_modifier(t_data[h]["rating"], t_data[a]["rating"])
            mod_a = self._squad_elo_modifier(t_data[a]["rating"], t_data[h]["rating"])

            hadv = 1.05 if h == "USA" else 1.06 if h == "Mexico" else 1.04 if h == "Canada" else 1.0

            GOAL_BOOST = 1.30

            lh_final = float(np.clip(base_lh * mod_h * hadv, 0.25, 3.20)) * GOAL_BOOST
            la_final = float(np.clip(base_la * mod_a, 0.25, 3.20)) * GOAL_BOOST

            # 🎰 APLICAÇÃO DO VEGAS BLEND NO MODO COPA
            lh_final, la_final = self._apply_vegas_boost(lh_final, la_final, h, a)

            mat = self._build_prob_matrix(lh_final, la_final)
            hw_prob = float(np.sum(np.tril(mat, -1))) * 100
            aw_prob = float(np.sum(np.triu(mat, 1))) * 100

            _BASE_LAMBDA = _LAMBDA_WORLD_CUP_AVG * GOAL_BOOST
            scale_h = lh_final / _BASE_LAMBDA
            scale_a = la_final / _BASE_LAMBDA

            gr_h_scaled = [r * scale_h for r in t_data[h]["gr"]]
            ar_h_scaled = [r * scale_h for r in t_data[h]["ar"]]
            gr_a_scaled = [r * scale_a for r in t_data[a]["gr"]]
            ar_a_scaled = [r * scale_a for r in t_data[a]["ar"]]

            key = tuple(sorted([h, a]))
            match_cache[key] = {
                h: {"mat": mat,   "p": t_data[h]["p"], "gr": gr_h_scaled, "ar": ar_h_scaled, "wp": hw_prob},
                a: {"mat": mat.T, "p": t_data[a]["p"], "gr": gr_a_scaled, "ar": ar_a_scaled, "wp": aw_prob}
            }

        return match_cache

    def run_full_tournament(self, num_tournaments: int = 400) -> dict:
        import utils.data_loader
        if not getattr(utils.data_loader, "_orig_gcm_patched", False):
            _orig_gcm = utils.data_loader.get_close_matches

            def _fast_gcm(word, possibilities, n=1, cutoff=0.6):
                if len(possibilities) > 5000:
                    possibilities_set = set(possibilities)
                    if word in possibilities_set: return [word]
                    return []
                if word in possibilities: return [word]
                return _orig_gcm(word, possibilities, n, cutoff)

            utils.data_loader.get_close_matches = _fast_gcm
            utils.data_loader._orig_gcm_patched = True

        match_cache = self._build_vectorized_match_cache()

        groups_setup: dict = {}
        for team, info in self.teams_info.items():
            g = info.get("group", "A")
            groups_setup.setdefault(g, []).append(team)

        cores = multiprocessing.cpu_count()
        chunks = [num_tournaments // cores] * cores
        for i in range(num_tournaments % cores): chunks[i] += 1

        final_results = {
            "champions": defaultdict(int), "player_goals": defaultdict(int),
            "player_assists": defaultdict(int), "team_goals_f": defaultdict(int),
            "team_goals_a": defaultdict(int), "team_matches": defaultdict(int),
            "team_stage_points": defaultdict(int)
        }

        with ProcessPoolExecutor(max_workers=cores) as p_exec:
            futures = [p_exec.submit(_worker_simulate_tournament_batch, groups_setup, match_cache, c) for c in chunks if c > 0]
            for future in futures:
                res = future.result()
                for k, v in res["champions"].items(): final_results["champions"][k] += v
                for k, v in res["player_goals"].items(): final_results["player_goals"][k] += v
                for k, v in res["player_assists"].items(): final_results["player_assists"][k] += v
                for k, v in res["team_goals_f"].items(): final_results["team_goals_f"][k] += v
                for k, v in res["team_goals_a"].items(): final_results["team_goals_a"][k] += v
                for k, v in res["team_matches"].items(): final_results["team_matches"][k] += v
                for k, v in res["team_stage_points"].items(): final_results["team_stage_points"][k] += v

        top_champions = sorted(final_results["champions"].items(), key=lambda x: x[1], reverse=True)[:48]
        fav_list = [{"team": t, "prob": (c/num_tournaments)*100} for t, c in top_champions]

        top_scorers = sorted(final_results["player_goals"].items(), key=lambda x: x[1], reverse=True)[:5]
        scorer_list = [{"player": p, "avg_goals": g/num_tournaments} for p, g in top_scorers]

        top_asts = sorted(final_results["player_assists"].items(), key=lambda x: x[1], reverse=True)[:5]
        ast_list = [{"player": p, "avg_assists": a/num_tournaments} for p, a in top_asts]

        team_stats = []
        for t in self.teams_info.keys():
            if final_results["team_matches"][t] > 0:
                gf_avg = final_results["team_goals_f"][t] / final_results["team_matches"][t]
                ga_avg = final_results["team_goals_a"][t] / final_results["team_matches"][t]
                team_stats.append({"team": t, "gf": gf_avg, "ga": ga_avg, "matches": final_results["team_matches"][t]})

        best_attack = sorted(team_stats, key=lambda x: x["gf"], reverse=True)[:5]
        best_defense = sorted([t for t in team_stats if t["matches"] >= num_tournaments * 4], key=lambda x: x["ga"])[:5]

        zebras = []
        for t in self.teams_info.keys():
            elo = self.feature_builder.data_loader.get_team_elo(t)
            if elo < 1780:
                avg_stage = final_results["team_stage_points"][t] / num_tournaments
                zebras.append({"team": t, "avg_stage_score": avg_stage, "elo": elo})

        best_zebra = sorted(zebras, key=lambda x: x["avg_stage_score"], reverse=True)[:1]

        return {
            "total_sims": num_tournaments,
            "favorites": fav_list, "top_scorers": scorer_list,
            "top_assists": ast_list, "best_attack": best_attack,
            "best_defense": best_defense, "biggest_zebra": best_zebra[0] if best_zebra else None
        }

def _assign_goals_and_assists(players: list[dict], goal_rates: list[float], ast_rates: list[float], total_goals: int, goals_dict: dict, assists_dict: dict, log_list: list[str], scorer_set: set, ast_set: set) -> None:
    available = list(range(len(players)))
    goal_count: dict[int, int] = defaultdict(int)

    for _ in range(total_goals):
        eligible_scorers = [i for i in available if goal_count[i] < 3]
        if not eligible_scorers: eligible_scorers = available

        w_g = [( (goal_rates[i] ** 1.05) * random.uniform(0.9, 1.1) ) + 0.05 for i in eligible_scorers]
        w_g_sum = sum(w_g)
        probs_g = [r / w_g_sum for r in w_g] if w_g_sum > 0 else [1.0 / len(eligible_scorers)] * len(eligible_scorers)

        idx_scorer_in_list = random.choices(range(len(eligible_scorers)), weights=probs_g, k=1)[0]
        scorer_idx = eligible_scorers[idx_scorer_in_list]
        scorer = players[scorer_idx]

        goal_count[scorer_idx] += 1
        goals_dict[scorer["name"]] += 1
        scorer_set.add(scorer["name"])

        log_entry = scorer["name"]
        if random.random() < 0.70:
            eligible_assistants = [i for i in available if i != scorer_idx]
            if eligible_assistants:
                w_a = [( (ast_rates[i] ** 1.05) * random.uniform(0.9, 1.1) ) + 0.05 for i in eligible_assistants]
                w_a_sum = sum(w_a)
                probs_a = [r / w_a_sum for r in w_a] if w_a_sum > 0 else [1.0 / len(eligible_assistants)] * len(eligible_assistants)

                idx_ast_in_list = random.choices(range(len(eligible_assistants)), weights=probs_a, k=1)[0]
                ast_idx = eligible_assistants[idx_ast_in_list]
                assistant = players[ast_idx]

                assists_dict[assistant["name"]] += 1
                ast_set.add(assistant["name"])
                log_entry += f" (Ast: {assistant['name']})"

        log_list.append(log_entry)

def _worker_simulate_tournament_batch(groups_setup, match_cache, num_tournaments):
    np.random.seed((os.getpid() * int(time.time() * 1000)) % 123456789)
    random.seed((os.getpid() * int(time.time() * 1000)) % 123456789)

    champions = defaultdict(int); player_goals = defaultdict(int); player_assists = defaultdict(int)
    team_goals_f = defaultdict(int); team_goals_a = defaultdict(int); team_matches = defaultdict(int)
    team_stage_points = defaultdict(int)

    for _ in range(num_tournaments):
        standings = {g: {t: {"pts": 0, "gf": 0, "ga": 0, "gd": 0} for t in teams} for g, teams in groups_setup.items()}

        for g, teams in groups_setup.items():
            for home, away in itertools.combinations(teams, 2):
                key = tuple(sorted([home, away]))
                h_data, a_data = match_cache[key][home], match_cache[key][away]

                flat_probs = h_data["mat"].flatten()
                sample = np.random.choice(len(flat_probs), p=flat_probs)
                max_g = h_data["mat"].shape[0]
                hg = int(sample // max_g)
                ag = int(sample % max_g)

                team_matches[home] += 1; team_matches[away] += 1
                team_goals_f[home] += hg; team_goals_a[home] += ag
                team_goals_f[away] += ag; team_goals_a[away] += hg

                standings[g][home]["gf"] += hg; standings[g][home]["ga"] += ag; standings[g][home]["gd"] += hg - ag
                standings[g][away]["gf"] += ag; standings[g][away]["ga"] += hg; standings[g][away]["gd"] += ag - hg

                if hg > ag: standings[g][home]["pts"] += 3
                elif ag > hg: standings[g][away]["pts"] += 3
                else: standings[g][home]["pts"] += 1; standings[g][away]["pts"] += 1

                if hg > 0: _assign_goals_and_assists(h_data["p"], h_data["gr"], h_data["ar"], hg, player_goals, player_assists, [], set(), set())
                if ag > 0: _assign_goals_and_assists(a_data["p"], a_data["gr"], a_data["ar"], ag, player_goals, player_assists, [], set(), set())

        firsts, seconds, thirds = [], [], []
        for g in standings:
            st = sorted(standings[g].items(), key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]), reverse=True)
            firsts.append(st[0][0]); seconds.append(st[1][0]); thirds.append(st[2][0])
            team_stage_points[st[0][0]] += 2; team_stage_points[st[1][0]] += 2; team_stage_points[st[2][0]] += 1; team_stage_points[st[3][0]] += 1

        def get_pts(t):
            for g in standings:
                if t in standings[g]: return standings[g][t]
            return {"pts":0, "gd":0, "gf":0}

        thirds_sorted = sorted(thirds, key=lambda t: (get_pts(t)["pts"], get_pts(t)["gd"], get_pts(t)["gf"]), reverse=True)
        best_thirds = thirds_sorted[:8]
        for t in best_thirds: team_stage_points[t] += 1

        firsts.sort(key=lambda t: (get_pts(t)["pts"], get_pts(t)["gd"], get_pts(t)["gf"]), reverse=True)
        seconds.sort(key=lambda t: (get_pts(t)["pts"], get_pts(t)["gd"], get_pts(t)["gf"]), reverse=True)

        seeds = firsts + seconds + best_thirds
        bracket_idx = [0, 31, 15, 16, 8, 23, 7, 24, 4, 27, 11, 20, 12, 19, 3, 28, 2, 29, 13, 18, 10, 21, 5, 26, 6, 25, 9, 22, 14, 17, 1, 30]
        round_32 = [seeds[i] for i in bracket_idx]

        def play_knockout(teams: list, stage_val_points: int):
            winners = []
            for i in range(0, len(teams), 2):
                t1, t2 = teams[i], teams[i+1]
                key = tuple(sorted([t1, t2]))
                h_data, a_data = match_cache[key][t1], match_cache[key][t2]

                flat_probs = h_data["mat"].flatten()
                sample = np.random.choice(len(flat_probs), p=flat_probs)
                max_g = h_data["mat"].shape[0]
                hg = int(sample // max_g)
                ag = int(sample % max_g)

                team_matches[t1] += 1; team_matches[t2] += 1
                team_goals_f[t1] += hg; team_goals_a[t1] += ag
                team_goals_f[t2] += ag; team_goals_a[t2] += hg

                if hg > ag: winner = t1
                elif ag > hg: winner = t2
                else:
                    p1_pen = np.clip(0.5 + ((h_data["wp"] - a_data["wp"]) / 100.0) * 0.1, 0.40, 0.60)
                    winner = t1 if random.random() < p1_pen else t2

                if hg > 0: _assign_goals_and_assists(h_data["p"], h_data["gr"], h_data["ar"], hg, player_goals, player_assists, [], set(), set())
                if ag > 0: _assign_goals_and_assists(a_data["p"], a_data["gr"], a_data["ar"], ag, player_goals, player_assists, [], set(), set())

                winners.append(winner)
                team_stage_points[winner] += stage_val_points
            return winners

        r16 = play_knockout(round_32, 1)
        qf = play_knockout(r16, 1)
        sf = play_knockout(qf, 1)
        finalists = play_knockout(sf, 1)
        champ = play_knockout(finalists, 1)

        champions[champ[0]] += 1

    return {
        "champions": dict(champions), "player_goals": dict(player_goals), "player_assists": dict(player_assists),
        "team_goals_f": dict(team_goals_f), "team_goals_a": dict(team_goals_a), "team_matches": dict(team_matches),
        "team_stage_points": dict(team_stage_points)
    }