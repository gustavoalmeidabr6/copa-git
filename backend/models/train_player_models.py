"""
models/train_player_models.py — MOTOR DE MACHINE LEARNING INDIVIDUAL

ESTRATÉGIA DE ALTA PERFORMANCE (RX 7600 + BAYESIAN SMOOTHING):
═══════════════════════════════════════════════════════════════════════════════
  - O PROBLEMA DOS POUCOS DADOS: Jogadores reservas que jogam 15 minutos e 
    marcam 1 gol ficam com uma taxa irreal de "6.0 gols por jogo". Se a IA
    aprender isso, ela vai escalar reservas na Copa e eles farão 10 gols.
  - A SOLUÇÃO (SUAVIZAÇÃO BAYESIANA): Injetamos "Priors" (Conhecimento Prévio).
    O algoritmo assume que todo jogador já tem 10 partidas de experiência 
    com a média de gols da sua posição. Quem joga muito (3000 mins) dilui
    esse prior. Quem joga pouco (50 mins) é "ancorado" na média, impedindo
    que a IA alucine com amostras pequenas.
  - TREINAMENTO GPU: Utiliza o LightGBM (OpenCL) para treinar duas redes
    simultâneas (Player xG e Player xA) consumindo as features do EA FC 26
    e as estatísticas da temporada 2025/2026.
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from pathlib import Path
import time
import warnings
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

warnings.filterwarnings("ignore")

DATA_DIR = Path(__file__).parent.parent / "data"
SEASON_CSV = DATA_DIR / "players_data-2025_2026.csv"
EAFC_CSV   = DATA_DIR / "EAFC26-Men.csv"
MODEL_OUT  = DATA_DIR / "player_ml_models.pkl"

# ─────────────────────────────────────────────────────────────────────────────
# PRIORS (A BASE DA SUAVIZAÇÃO BAYESIANA)
# Média de Gols e Assistências a cada 90 min por posição
# ─────────────────────────────────────────────────────────────────────────────
PRIOR_90S = 10.0  # Assumimos 10 jogos imaginários (900 minutos) de "ancoragem"

PRIORS = {
    "Attacker":   {"G90": 0.35, "A90": 0.15, "Code": 3},
    "Midfielder": {"G90": 0.08, "A90": 0.18, "Code": 2},
    "Defender":   {"G90": 0.03, "A90": 0.05, "Code": 1},
    "Goalkeeper": {"G90": 0.00, "A90": 0.01, "Code": 0},
    "Unknown":    {"G90": 0.10, "A90": 0.10, "Code": 2}
}

def _get_pos_category(pos_str: str) -> str:
    pos_str = str(pos_str).lower()
    if any(x in pos_str for x in ['fw', 'st', 'lw', 'rw', 'cf', 'attacker']): return "Attacker"
    if any(x in pos_str for x in ['mf', 'am', 'dm', 'cm', 'lm', 'rm', 'midfielder']): return "Midfielder"
    if any(x in pos_str for x in ['df', 'cb', 'lb', 'rb', 'lwb', 'rwb', 'defender']): return "Defender"
    if any(x in pos_str for x in ['gk', 'goalkeeper']): return "Goalkeeper"
    return "Unknown"

def _get_league_weight(league_name: str) -> float:
    base = 0.80
    lname = str(league_name).lower()
    if any(x in lname for x in ['premier', 'england', 'la liga', 'spain']): return 1.00
    if any(x in lname for x in ['serie a', 'italy', 'bundesliga', 'germany']): return 0.85
    if any(x in lname for x in ['ligue 1', 'france']): return 0.80
    if any(x in lname for x in ['portugal', 'primeira']): return 0.75
    if any(x in lname for x in ['saudi', 'mls', 'brasil', 'argentina', 'eredivisie']): return 0.65
    return base

# ─────────────────────────────────────────────────────────────────────────────
# 1. ENGENHARIA DE DADOS (CRUZAMENTO E SUAVIZAÇÃO)
# ─────────────────────────────────────────────────────────────────────────────
def prepare_dataset():
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando Extração e Engenharia de Dados...")
    
    if not SEASON_CSV.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {SEASON_CSV}")
        
    df_season = pd.read_csv(SEASON_CSV)
    
    # Padroniza as colunas que podem vir bagunçadas do scraping
    name_col = next((c for c in df_season.columns if c.lower() in ['name', 'player', 'jogador']), None)
    min_col  = next((c for c in df_season.columns if c.lower() in ['min', 'minutes', 'minutos']), None)
    gls_col  = next((c for c in df_season.columns if c.lower() in ['goals', 'gls', 'gols']), None)
    ast_col  = next((c for c in df_season.columns if c.lower() in ['assists', 'ast', 'assistencias']), None)
    pos_col  = next((c for c in df_season.columns if c.lower() in ['pos', 'position', 'posicao']), None)
    age_col  = next((c for c in df_season.columns if c.lower() in ['age', 'idade']), None)
    comp_col = next((c for c in df_season.columns if c.lower() in ['comp', 'league']), None)

    if not all([name_col, min_col, gls_col, ast_col, pos_col]):
        raise ValueError("Faltam colunas essenciais no players_data-2025_2026.csv")

    # Limpeza básica
    df_season[min_col] = pd.to_numeric(df_season[min_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df_season = df_season[df_season[min_col] > 0].copy() # Remove quem não jogou
    
    df_season[gls_col] = pd.to_numeric(df_season[gls_col], errors='coerce').fillna(0)
    df_season[ast_col] = pd.to_numeric(df_season[ast_col], errors='coerce').fillna(0)
    df_season[age_col] = pd.to_numeric(df_season[age_col], errors='coerce').fillna(25)
    
    # ── MÁGICA 1: O Dicionário de Qualidade EA FC ──
    ea_dict = {}
    if EAFC_CSV.exists():
        df_ea = pd.read_csv(EAFC_CSV, low_memory=False)
        if "Name" in df_ea.columns and "OVR" in df_ea.columns:
            for _, row in df_ea.iterrows():
                name_clean = str(row["Name"]).lower().strip()
                ea_dict[name_clean] = float(row["OVR"]) / 10.0 # Transforma 85 em 8.5
                
    # ── CONSTRUINDO AS FEATURES PARA O MODELO ──
    features = []
    
    for _, row in df_season.iterrows():
        p_name = str(row[name_col]).strip()
        p_min = row[min_col]
        p_gls = row[gls_col]
        p_ast = row[ast_col]
        p_age = row[age_col]
        p_pos = _get_pos_category(row[pos_col])
        p_league = str(row[comp_col]) if comp_col else "unknown"
        
        league_w = _get_league_weight(p_league)
        pos_code = PRIORS[p_pos]["Code"]
        
        # Busca o Rating (se não achar, dá nota 7.0 de média)
        rating = 7.0
        n_clean = p_name.lower().strip()
        if n_clean in ea_dict:
            rating = ea_dict[n_clean]
        else:
            # Tenta achar por sobrenome em nomes longos
            for ea_name, ea_score in ea_dict.items():
                if len(n_clean) > 6 and (n_clean in ea_name or ea_name in n_clean):
                    rating = ea_score
                    break
                    
        # ── MÁGICA 2: SUAVIZAÇÃO BAYESIANA ──
        # Formula: (Gols_Reais + Gols_Imaginarios_Prior) / (90s_Reais + 90s_Imaginarios_Prior)
        real_90s = p_min / 90.0
        
        prior_g90 = PRIORS[p_pos]["G90"]
        prior_a90 = PRIORS[p_pos]["A90"]
        
        # Ajusta os gols reais baseados na dificuldade da liga
        adj_gls = p_gls * league_w
        adj_ast = p_ast * league_w
        
        smoothed_g90 = (adj_gls + (prior_g90 * PRIOR_90S)) / (real_90s + PRIOR_90S)
        smoothed_a90 = (adj_ast + (prior_a90 * PRIOR_90S)) / (real_90s + PRIOR_90S)
        
        features.append({
            "Player": p_name,
            "Age": p_age,
            "Pos_Code": pos_code,
            "EA_Rating": rating,
            "League_Weight": league_w,
            "Target_G90": smoothed_g90,
            "Target_A90": smoothed_a90,
            "Sample_Weight": np.log1p(p_min) # Dá mais peso na IA para quem jogou muitos minutos
        })

    df_ml = pd.DataFrame(features)
    print(f"  → Base consolidada: {len(df_ml)} jogadores aptos para treinamento.")
    return df_ml

# ─────────────────────────────────────────────────────────────────────────────
# 2. TREINAMENTO DOS MODELOS DE MACHINE LEARNING NA GPU
# ─────────────────────────────────────────────────────────────────────────────
def train_player_models():
    start_time = time.time()
    
    df = prepare_dataset()
    
    X = df[["Age", "Pos_Code", "EA_Rating", "League_Weight"]]
    y_goals = df["Target_G90"]
    y_assists = df["Target_A90"]
    weights = df["Sample_Weight"]
    
    X_train, X_val, yg_train, yg_val, ya_train, ya_val, w_train, w_val = train_test_split(
        X, y_goals, y_assists, weights, test_size=0.1, random_state=42
    )

    print(f"\n[{time.strftime('%H:%M:%S')}] Iniciando treinamento GPU (LightGBM OpenCL)...")
    
    # Hiperparâmetros baseados em Regressão Poisson (já que Gols/Assists são contagens no tempo)
    lgb_params = {
        "objective": "poisson",
        "metric": "poisson",
        "device_type": "gpu",   # Aciona sua RX 7600
        "gpu_platform_id": 0,
        "gpu_device_id": 0,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "verbose": -1,
        "n_estimators": 1000,
        "random_state": 42
    }
    
    # ── TREINA MODELO DE GOLS ──
    print("  → Treinando Rede Neural de Expected Goals (xG)...")
    model_goals = lgb.LGBMRegressor(**lgb_params)
    try:
        model_goals.fit(
            X_train, yg_train, sample_weight=w_train,
            eval_set=[(X_val, yg_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        gpu_used = True
    except Exception as e:
        print(f"  ⚠️ Falha ao acionar GPU OpenCL: {e}")
        print("  🔄 Recalculando na CPU (Multicore)...")
        lgb_params["device_type"] = "cpu"
        lgb_params["num_threads"] = -1
        model_goals = lgb.LGBMRegressor(**lgb_params)
        model_goals.fit(
            X_train, yg_train, sample_weight=w_train,
            eval_set=[(X_val, yg_val)],
            callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
        )
        gpu_used = False

    # ── TREINA MODELO DE ASSISTÊNCIAS ──
    print("  → Treinando Rede Neural de Expected Assists (xA)...")
    model_assists = lgb.LGBMRegressor(**lgb_params)
    model_assists.fit(
        X_train, ya_train, sample_weight=w_train,
        eval_set=[(X_val, ya_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)]
    )

    # ── VALIDAÇÃO E RELATÓRIO ──
    pred_g = model_goals.predict(X_val)
    pred_a = model_assists.predict(X_val)
    
    mae_g = mean_absolute_error(yg_val, pred_g)
    mae_a = mean_absolute_error(ya_val, pred_a)
    
    print("\n📊 RESULTADOS DA VALIDAÇÃO (Erro Médio por Jogo):")
    print(f"   Erro de xG: ±{mae_g:.4f} gols/90")
    print(f"   Erro de xA: ±{mae_a:.4f} assists/90")
    
    importance = dict(zip(X.columns, model_goals.feature_importances_))
    print("\n📈 PESO DAS FEATURES (O que a IA considerou mais importante):")
    max_imp = max(importance.values()) or 1
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp / max_imp * 20)
        print(f"   {feat:<15} {bar} {imp:.0f}")

    # ── SALVAMENTO DO MODELO ──
    payload = {
        "model_goals": model_goals,
        "model_assists": model_assists,
        "features": list(X.columns),
        "device_used": "GPU (OpenCL)" if gpu_used else "CPU",
        "trained_on": pd.Timestamp.now().isoformat()
    }
    
    joblib.dump(payload, MODEL_OUT)
    
    elapsed = time.time() - start_time
    print(f"\n🏆 Modelos Individuais Salvos com Sucesso em: {MODEL_OUT.name}")
    print(f"   Tempo de Treinamento: {elapsed:.1f} segundos.")

if __name__ == "__main__":
    train_player_models()