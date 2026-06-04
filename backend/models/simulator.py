"""
models/simulator.py — REESCRITA TOTAL v13 (Correção do Paradoxo do Placar Provável)

MUDANÇAS v13:
  - CORREÇÃO DO "EXPECTED SCORE": Arrumado o Paradoxo Matemático onde o placar 
    de empate (ex: 1x1) aparecia como "Placar Provável" mesmo quando um time tinha 
    grande favoritismo (ex: 45% vs 28%). 
  - Agora a lógica trava o Placar Provável na Probabilidade Dominante. Se a
    Vitória do Mandante é a maior %, ele filtra apenas os placares de vitória 
    para eleger o resultado provável, alinhando 100% com a expectativa real.
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
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
import time

MODEL_PATH = Path(__file__).parent.parent / "data" / "xgboost_model.pkl"

_LAMBDA_SHRINKAGE = 0.45   
_LAMBDA_WORLD_CUP_AVG = 1.25  

class MatchSimulator:
    def __init__(self):
        self.feature_builder = FeatureBuilder()
        self.teams_info = self.feature_builder.data_loader.get_all_teams()

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Modelo não encontrado. Execute train_model.py primeiro.\n"
                f"Esperado em: {MODEL_PATH}"
            )
        self.models = joblib.load(MODEL_PATH)
        self.rho = -0.13   

        self.season_stats = {}
        season_csv = Path(__file__).parent.parent / "data" / "players_data-2025_2026.csv"
        if season_csv.exists():
            try:
                df_season = pd.read_csv(season_csv)
                name_col = next((c for c in df_season.columns if c.lower() in ['name', 'player', 'jogador', 'nome']), None)
                goal_col = next((c for c in df_season.columns if c.lower() in ['goals', 'gls', 'gols']), None)
                ast_col  = next((c for c in df_season.columns if c.lower() in ['assists', 'ast', 'assistencias']), None)
                
                if name_col:
                    for _, row in df_season.iterrows():
                        p_name = str(row[name_col]).strip()
                        g = float(row[goal_col]) if goal_col and pd.notna(row[goal_col]) else 0.0
                        a = float(row[ast_col]) if ast_col and pd.notna(row[ast_col]) else 0.0
                        self.season_stats[p_name] = {'goals': g, 'assists': a}
                print(f"[Motor Quântico] Dados da Temporada 25/26 carregados! ({len(self.season_stats)} jogadores mapeados).")
            except Exception as e:
                print(f"[Motor Quântico] Aviso: Falha ao processar players_data-2025_2026.csv: {e}")

    def _dixon_coles(self, x: int, y: int, lx: float, ly: float) -> float:
        if   x == 0 and y == 0: return max(0.01, 1 - lx * ly * self.rho)
        elif x == 0 and y == 1: return max(0.01, 1 + lx * self.rho)
        elif x == 1 and y == 0: return max(0.01, 1 + ly * self.rho)
        elif x == 1 and y == 1: return max(0.01, 1 - self.rho)
        return 1.0

    def _compute_lambdas(
        self,
        home_team: str,
        away_team: str,
        home_rating: float,
        away_rating: float,
        home_elo: float,
        away_elo: float,
        df_home: object,
        df_away: object,
    ) -> tuple[float, float, float, float]:
        lh_p1 = float(self.models["home"].predict(df_home)[0])
        la_p1 = float(self.models["away"].predict(df_home)[0])

        lh_p2 = float(self.models["away"].predict(df_away)[0])
        la_p2 = float(self.models["home"].predict(df_away)[0])

        base_lh = (lh_p1 + lh_p2) / 2.0
        base_la = (la_p1 + la_p2) / 2.0

        elo_gap = abs(home_elo - away_elo)
        adaptive_shrinkage = float(np.interp(elo_gap, [0, 400], [0.45, 0.18]))
        base_lh = (1 - adaptive_shrinkage) * base_lh + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG
        base_la = (1 - adaptive_shrinkage) * base_la + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG

        modifier_home = self._squad_elo_modifier(home_rating, away_rating, home_elo, away_elo)
        modifier_away = self._squad_elo_modifier(away_rating, home_rating, away_elo, home_elo)

        HOME_ADV = {"USA": 1.05, "Mexico": 1.06, "Canada": 1.04}
        hadv = HOME_ADV.get(home_team, 1.0)

        lh_final = float(np.clip(base_lh * modifier_home * hadv, 0.10, 4.00))
        la_final = float(np.clip(base_la * modifier_away,        0.10, 4.00))

        return lh_final, la_final, modifier_home, modifier_away

    def _squad_elo_modifier(
        self,
        own_rating: float, opp_rating: float,
        own_elo: float,    opp_elo: float,
    ) -> float:
        rating_diff  = (own_rating - opp_rating) * 0.15
        elo_diff_pct = (own_elo - opp_elo) / 5500.0
        raw = 1.0 + rating_diff + elo_diff_pct
        return float(np.clip(raw, 0.50, 2.00))

    def _build_prob_matrix(self, lh: float, la: float, max_goals: int = 9) -> np.ndarray:
        mat = np.zeros((max_goals, max_goals))
        for i in range(max_goals):
            for j in range(max_goals):
                p = poisson.pmf(i, lh) * poisson.pmf(j, la)
                mat[i, j] = max(0.0, p * self._dixon_coles(i, j, lh, la))
        mat /= mat.sum()
        return mat

    def _player_goal_rate(self, player: dict) -> float:
        pos = player.get("position", "Midfielder")
        rating = player.get("rating", 7.0)
        name = player.get("name", "")

        base_rates = {
            "Attacker":   0.20,
            "Midfielder": 0.06,
            "Defender":   0.02,
            "Goalkeeper": 0.001
        }
        rate = base_rates.get(pos, 0.06)

        season_goals = 0
        for k, v in self.season_stats.items():
            if name in k or k in name:
                season_goals = max(season_goals, v['goals']) 
                
        recent_goals = 0
        try:
            goals_dict = self.feature_builder.data_loader.recent_goals_dict
            for k, v in goals_dict.items():
                if isinstance(k, str) and (name in k or k in name):
                    recent_goals += v
        except Exception:
            pass

        rate += (season_goals * 0.02) + (recent_goals * 0.01)

        rating_multiplier = max(0.5, (rating - 5.0) / 3.0) 
        final_rate = rate * rating_multiplier
        return round(float(np.clip(final_rate, 0.001, 0.85)), 3)

    def _player_assist_rate(self, player: dict) -> float:
        pos = player.get("position", "Midfielder")
        rating = player.get("rating", 7.0)
        name = player.get("name", "")

        base_rates = {
            "Midfielder": 0.18,
            "Attacker":   0.12,
            "Defender":   0.05,
            "Goalkeeper": 0.001
        }
        rate = base_rates.get(pos, 0.10)

        season_assists = 0
        for k, v in self.season_stats.items():
            if name in k or k in name:
                season_assists = max(season_assists, v['assists'])

        rating_bonus = max(0.0, (rating - 7.0) ** 2 * 0.03)

        if pos == "Attacker" and rating >= 8.5:
            rating_bonus += 0.05

        final_rate = rate + rating_bonus + (season_assists * 0.025)
        return round(float(np.clip(final_rate, 0.001, 0.60)), 3)

    def _performance_rating(
        self,
        player: dict,
        scored: bool,
        assisted: bool,
        gf: int,
        ga: int,
        is_home: bool,
    ) -> float:
        pos = player.get("position", "Midfielder")
        base = player.get("rating", 7.0)
        goals_conceded = ga if is_home else gf
        goals_scored   = gf if is_home else ga
        noise = random.gauss(0, 0.20)   

        if pos == "Goalkeeper":
            if   goals_conceded == 0: bonus = +0.9
            elif goals_conceded == 1: bonus = +0.2
            elif goals_conceded == 2: bonus = -0.2
            else:                     bonus = -0.6
        elif pos == "Defender":
            if   goals_conceded == 0: bonus = +0.6
            elif goals_conceded == 1: bonus = +0.1
            elif goals_conceded >= 3: bonus = -0.5
            else:                     bonus = -0.1
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

    def simulate_match(
        self,
        home_team: str,
        away_team: str,
        num_simulations: int = 200,
        is_friendly: int = 0,
        home_excluded: list = None,
        away_excluded: list = None,
    ) -> dict:
        if home_excluded is None: home_excluded = []
        if away_excluded is None: away_excluded = []

        feats      = self.feature_builder.build_match_features(home_team, away_team, is_friendly, home_excluded, away_excluded)
        feats_inv  = self.feature_builder.build_match_features(away_team, home_team, is_friendly, away_excluded, home_excluded)

        home_rating = feats["home_rating"]
        away_rating = feats["away_rating"]
        home_elo    = feats["home_elo"]
        away_elo    = feats["away_elo"]

        lh, la, mod_h, mod_a = self._compute_lambdas(
            home_team, away_team,
            home_rating, away_rating,
            home_elo, away_elo,
            feats["df_ml"], feats_inv["df_ml"],
        )

        prob_matrix = self._build_prob_matrix(lh, la)
        max_goals   = prob_matrix.shape[0]

        home_win_prob = float(np.sum(np.tril(prob_matrix, -1))) * 100   
        draw_prob     = float(np.trace(prob_matrix)) * 100
        away_win_prob = float(np.sum(np.triu(prob_matrix, 1))) * 100

        home_players: list[dict] = feats["home_players"]
        away_players: list[dict] = feats["away_players"]

        if not home_players:
            from utils.data_loader import DataLoader
            home_players = DataLoader._build_minimal_squad(home_team)
        if not away_players:
            from utils.data_loader import DataLoader
            away_players = DataLoader._build_minimal_squad(away_team)

        h_rates = [self._player_goal_rate(p) for p in home_players]
        a_rates = [self._player_goal_rate(p) for p in away_players]
        h_ast_rates = [self._player_assist_rate(p) for p in home_players]
        a_ast_rates = [self._player_assist_rate(p) for p in away_players]

        if sum(h_rates) == 0: h_rates = [1.0] * len(home_players)
        if sum(a_rates) == 0: a_rates = [1.0] * len(away_players)
        if sum(h_ast_rates) == 0: h_ast_rates = [1.0] * len(home_players)
        if sum(a_ast_rates) == 0: a_ast_rates = [1.0] * len(away_players)

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

        # ── NOVA LÓGICA DO PLACAR PROVÁVEL MÉDIO (Correção de Tendência) ──
        if home_win_prob > away_win_prob and home_win_prob > draw_prob:
            outcome = "home"
        elif away_win_prob > home_win_prob and away_win_prob > draw_prob:
            outcome = "away"
        else:
            outcome = "draw"

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

        sampled    = np.random.choice(len(flat_probs), size=num_simulations, p=flat_probs)
        home_sims  = sampled // max_goals
        away_sims  = sampled % max_goals

        player_goals:      defaultdict = defaultdict(int)
        player_assists:    defaultdict = defaultdict(int)
        player_perf_sum:   defaultdict = defaultdict(float)
        player_perf_count: defaultdict = defaultdict(int)
        sim_logs: list[str] = []

        ha = home_team[:3].upper()
        aa = away_team[:3].upper()

        for k in range(num_simulations):
            hg = int(home_sims[k])
            ag = int(away_sims[k])

            home_log: list[str] = []
            away_log: list[str] = []
            home_scorers: set   = set()
            away_scorers: set   = set()
            home_ast_set: set   = set()
            away_ast_set: set   = set()

            if hg > 0:
                _assign_goals_and_assists(home_players, h_rates, h_ast_rates, hg, player_goals, player_assists, home_log, home_scorers, home_ast_set)
            if ag > 0:
                _assign_goals_and_assists(away_players, a_rates, a_ast_rates, ag, player_goals, player_assists, away_log, away_scorers, away_ast_set)

            log = f"Sim {k+1:03d}: {ha} {hg} x {ag} {aa}"
            parts = []
            if home_log: parts.append(f"[{ha}] {', '.join(home_log)}")
            if away_log: parts.append(f"[{aa}] {', '.join(away_log)}")
            if parts:    log += " | Gols: " + " - ".join(parts)
            sim_logs.append(log)

            for p in home_players:
                sc   = p["name"] in home_scorers
                ast  = p["name"] in home_ast_set
                perf = self._performance_rating(p, sc, ast, hg, ag, True)
                player_perf_sum[p["name"]]   += perf
                player_perf_count[p["name"]] += 1

            for p in away_players:
                sc   = p["name"] in away_scorers
                ast  = p["name"] in away_ast_set
                perf = self._performance_rating(p, sc, ast, hg, ag, False)
                player_perf_sum[p["name"]]   += perf
                player_perf_count[p["name"]] += 1

        top_scorers = sorted(player_goals.items(), key=lambda x: x[1], reverse=True)[:3]
        top_assists = sorted(player_assists.items(), key=lambda x: x[1], reverse=True)[:3]
        
        avg_perf    = {
            k: round(v / player_perf_count[k], 2)
            for k, v in player_perf_sum.items()
            if player_perf_count[k] > 0
        }
        top_ratings = sorted(avg_perf.items(), key=lambda x: x[1], reverse=True)[:3]

        score_series = pd.Series(most_likely)

        return {
            "home_win_prob":      round(home_win_prob, 1),
            "draw_prob":          round(draw_prob, 1),
            "away_win_prob":      round(away_win_prob, 1),
            "most_likely_scores": score_series,
            "expected_score":     expected_score_str,
            "home_lambda":        round(lh, 2),
            "away_lambda":        round(la, 2),
            "modifier_home":      round(mod_h, 3),
            "modifier_away":      round(mod_a, 3),
            "temperature":        feats["temperature"],
            "stadium":            feats.get("stadium", "Miami"),
            "home_rating":        home_rating,
            "away_rating":        away_rating,
            "home_injuries":      feats["home_injuries"],
            "away_injuries":      feats["away_injuries"],
            "home_data_source":   feats["home_data_source"],
            "away_data_source":   feats["away_data_source"],
            "home_elo":           home_elo,
            "away_elo":           away_elo,
            "sim_logs":           sim_logs,
            "top_scorers":        top_scorers,
            "top_assists":        top_assists,  
            "top_ratings":        top_ratings,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # DASHBOARD: INFERÊNCIA VETORIZADA (BATCH INFERENCE)
    # ──────────────────────────────────────────────────────────────────────────
    def _build_vectorized_match_cache(self) -> dict:
        print("[Motor Quântico] Coletando atributos dinâmicos dos elencos...")
        teams = list(self.teams_info.keys())
        all_pairs = list(itertools.combinations(teams, 2))
        
        t_data = {}
        for t in teams:
            sq = self.feature_builder.data_loader.get_real_squad_data(t)
            top = sq.get("top_players", [])
            if not top: 
                top = self.feature_builder.data_loader._build_minimal_squad(t)
            
            elo = self.feature_builder.data_loader.get_team_elo(t)
            goals = self.feature_builder.data_loader.get_historical_goals(t)
            rating = FeatureBuilder._calculate_weighted_rating(top) 
            
            gr = [self._player_goal_rate(p) for p in top]
            ar = [self._player_assist_rate(p) for p in top]
            if sum(gr) == 0: gr = [1.0]*len(top)
            if sum(ar) == 0: ar = [1.0]*len(top)
            
            t_data[t] = {"elo": elo, "goals": goals, "rating": rating, "p": top, "gr": gr, "ar": ar}

        print("[Motor Quântico] Vetorizando 1.128 cenários...")
        rows_p1 = []
        rows_p2 = []
        HOME_ADV_TEAMS = {"USA", "Mexico", "Canada"}
        
        for h, a in all_pairs:
            rows_p1.append({
                "home_adv": 1 if h in HOME_ADV_TEAMS else 0,
                "is_friendly": 0, "is_world_cup": 1,
                "home_elo_pre_match": t_data[h]["elo"], "away_elo_pre_match": t_data[a]["elo"],
                "elo_diff": t_data[h]["elo"] - t_data[a]["elo"],
                "home_avg_scored": t_data[h]["goals"]["scored"],
                "home_avg_conceded": t_data[h]["goals"]["conceded"],
                "away_avg_scored": t_data[a]["goals"]["scored"],
                "away_avg_conceded": t_data[a]["goals"]["conceded"],
            })
            rows_p2.append({
                "home_adv": 1 if a in HOME_ADV_TEAMS else 0,
                "is_friendly": 0, "is_world_cup": 1,
                "home_elo_pre_match": t_data[a]["elo"], "away_elo_pre_match": t_data[h]["elo"],
                "elo_diff": t_data[a]["elo"] - t_data[h]["elo"],
                "home_avg_scored": t_data[a]["goals"]["scored"],
                "home_avg_conceded": t_data[a]["goals"]["conceded"],
                "away_avg_scored": t_data[h]["goals"]["scored"],
                "away_avg_conceded": t_data[h]["goals"]["conceded"],
            })

        df_p1 = pd.DataFrame(rows_p1)
        df_p2 = pd.DataFrame(rows_p2)

        print("[Motor Quântico] Acionando núcleo preditivo LightGBM/XGBoost...")
        lh_p1 = self.models["home"].predict(df_p1)
        la_p1 = self.models["away"].predict(df_p1)
        lh_p2 = self.models["away"].predict(df_p2)
        la_p2 = self.models["home"].predict(df_p2)
        
        print("[Motor Quântico] Criptografando matrizes de Poisson em Cache...")
        match_cache = {}
        for i, (h, a) in enumerate(all_pairs):
            base_lh = (lh_p1[i] + lh_p2[i]) / 2.0
            base_la = (la_p1[i] + la_p2[i]) / 2.0
            
            elo_gap = abs(t_data[h]["elo"] - t_data[a]["elo"])
            adaptive_shrinkage = float(np.interp(elo_gap, [0, 400], [0.45, 0.18]))
            base_lh = (1 - adaptive_shrinkage) * base_lh + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG
            base_la = (1 - adaptive_shrinkage) * base_la + adaptive_shrinkage * _LAMBDA_WORLD_CUP_AVG
            
            mod_h = self._squad_elo_modifier(t_data[h]["rating"], t_data[a]["rating"], t_data[h]["elo"], t_data[a]["elo"])
            mod_a = self._squad_elo_modifier(t_data[a]["rating"], t_data[h]["rating"], t_data[a]["elo"], t_data[h]["elo"])
            
            hadv = 1.05 if h == "USA" else 1.06 if h == "Mexico" else 1.04 if h == "Canada" else 1.0
            
            lh_final = float(np.clip(base_lh * mod_h * hadv, 0.10, 4.00))
            la_final = float(np.clip(base_la * mod_a, 0.10, 4.00))
            
            mat = self._build_prob_matrix(lh_final, la_final)
            hw_prob = float(np.sum(np.tril(mat, -1))) * 100
            aw_prob = float(np.sum(np.triu(mat, 1))) * 100
            
            key = tuple(sorted([h, a]))
            match_cache[key] = {
                h: {"mat": mat, "p": t_data[h]["p"], "gr": t_data[h]["gr"], "ar": t_data[h]["ar"], "wp": hw_prob},
                a: {"mat": mat.T, "p": t_data[a]["p"], "gr": t_data[a]["gr"], "ar": t_data[a]["ar"], "wp": aw_prob}
            }
            
        return match_cache


    def run_full_tournament(self, num_tournaments: int = 200) -> dict:
        print("\n[Motor Quântico] Desbloqueando GIL do Python e ativando Vetorização...")

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

        champions = defaultdict(int)
        player_goals = defaultdict(int)
        player_assists = defaultdict(int)
        team_goals_f = defaultdict(int)
        team_goals_a = defaultdict(int)
        team_matches = defaultdict(int)
        team_stage_points = defaultdict(int)

        cores = multiprocessing.cpu_count()
        print(f"[Motor Quântico] Cache gerado. Disparando {num_tournaments} Copas em {cores} threads lógicas...")
        
        chunks = [num_tournaments // cores] * cores
        for i in range(num_tournaments % cores):
            chunks[i] += 1
            
        final_results = {
            "champions": defaultdict(int),
            "player_goals": defaultdict(int),
            "player_assists": defaultdict(int),
            "team_goals_f": defaultdict(int),
            "team_goals_a": defaultdict(int),
            "team_matches": defaultdict(int),
            "team_stage_points": defaultdict(int)
        }

        with ProcessPoolExecutor(max_workers=cores) as p_exec:
            futures = []
            for c in chunks:
                if c > 0:
                    futures.append(p_exec.submit(_worker_simulate_tournament_batch, groups_setup, match_cache, c))
                    
            for future in futures:
                res = future.result()
                for k, v in res["champions"].items(): final_results["champions"][k] += v
                for k, v in res["player_goals"].items(): final_results["player_goals"][k] += v
                for k, v in res["player_assists"].items(): final_results["player_assists"][k] += v
                for k, v in res["team_goals_f"].items(): final_results["team_goals_f"][k] += v
                for k, v in res["team_goals_a"].items(): final_results["team_goals_a"][k] += v
                for k, v in res["team_matches"].items(): final_results["team_matches"][k] += v
                for k, v in res["team_stage_points"].items(): final_results["team_stage_points"][k] += v
                
        top_champions = sorted(final_results["champions"].items(), key=lambda x: x[1], reverse=True)[:5]
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
            "favorites": fav_list,
            "top_scorers": scorer_list,
            "top_assists": ast_list,
            "best_attack": best_attack,
            "best_defense": best_defense,
            "biggest_zebra": best_zebra[0] if best_zebra else None
        }

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Distribui GOLS e ASSISTÊNCIAS Dinamicamente
# ─────────────────────────────────────────────────────────────────────────────
def _assign_goals_and_assists(
    players:      list[dict],
    goal_rates:   list[float],
    ast_rates:    list[float],
    total_goals:  int,
    goals_dict:   dict,
    assists_dict: dict,
    log_list:     list[str],
    scorer_set:   set,
    ast_set:      set,
) -> None:
    available = list(range(len(players)))
    goal_count: dict[int, int] = defaultdict(int)

    for _ in range(total_goals):
        eligible_scorers = [i for i in available if goal_count[i] < 3]
        if not eligible_scorers:
            eligible_scorers = available

        w_g = [goal_rates[i] for i in eligible_scorers]
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
                w_a = [ast_rates[i] for i in eligible_assistants]
                w_a_sum = sum(w_a)
                probs_a = [r / w_a_sum for r in w_a] if w_a_sum > 0 else [1.0 / len(eligible_assistants)] * len(eligible_assistants)
                
                idx_ast_in_list = random.choices(range(len(eligible_assistants)), weights=probs_a, k=1)[0]
                ast_idx = eligible_assistants[idx_ast_in_list]
                assistant = players[ast_idx]
                
                assists_dict[assistant["name"]] += 1
                ast_set.add(assistant["name"])
                log_entry += f" (Ast: {assistant['name']})"

        log_list.append(log_entry)


# ─────────────────────────────────────────────────────────────────────────────
# WORKER MULTICORE TOP-LEVEL
# ─────────────────────────────────────────────────────────────────────────────
def _worker_simulate_tournament_batch(groups_setup, match_cache, num_tournaments):
    np.random.seed((os.getpid() * int(time.time() * 1000)) % 123456789)
    random.seed((os.getpid() * int(time.time() * 1000)) % 123456789)
    
    champions = defaultdict(int)
    player_goals = defaultdict(int)
    player_assists = defaultdict(int)
    team_goals_f = defaultdict(int)
    team_goals_a = defaultdict(int)
    team_matches = defaultdict(int)
    team_stage_points = defaultdict(int)
    
    for _ in range(num_tournaments):
        standings = {
            g: {t: {"pts": 0, "gf": 0, "ga": 0, "gd": 0} for t in teams}
            for g, teams in groups_setup.items()
        }
        
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
            firsts.append(st[0][0])
            seconds.append(st[1][0])
            thirds.append(st[2][0])
            
            team_stage_points[st[0][0]] += 2 
            team_stage_points[st[1][0]] += 2 
            team_stage_points[st[2][0]] += 1 
            team_stage_points[st[3][0]] += 1

        def get_pts(t):
            for g in standings:
                if t in standings[g]: return standings[g][t]
            return {"pts":0, "gd":0, "gf":0}

        thirds_sorted = sorted(thirds, key=lambda t: (get_pts(t)["pts"], get_pts(t)["gd"], get_pts(t)["gf"]), reverse=True)
        best_thirds = thirds_sorted[:8]
        for t in best_thirds:
            team_stage_points[t] += 1
            
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
                    p1_pen = 0.5 + ((h_data["wp"] - a_data["wp"]) / 100.0) * 0.1
                    p1_pen = np.clip(p1_pen, 0.40, 0.60)
                    winner = t1 if random.random() < p1_pen else t2
                    
                if hg > 0: _assign_goals_and_assists(h_data["p"], h_data["gr"], h_data["ar"], hg, player_goals, player_assists, [], set(), set())
                if ag > 0: _assign_goals_and_assists(a_data["p"], a_data["gr"], a_data["ar"], ag, player_goals, player_assists, [], set(), set())
                    
                winners.append(winner)
                team_stage_points[winner] += stage_val_points
            return winners

        r16 = play_knockout(round_32, 1)
        qf  = play_knockout(r16, 1)
        sf  = play_knockout(qf, 1)
        finalists = play_knockout(sf, 1)
        champ = play_knockout(finalists, 1)
        
        champions[champ[0]] += 1
        
    return {
        "champions": dict(champions),
        "player_goals": dict(player_goals),
        "player_assists": dict(player_assists),
        "team_goals_f": dict(team_goals_f),
        "team_goals_a": dict(team_goals_a),
        "team_matches": dict(team_matches),
        "team_stage_points": dict(team_stage_points)
    }