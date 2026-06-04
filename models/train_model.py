"""
models/train_model.py — v4 TURBO (Pesos de Competição e ELO Avançados)

ESTRATÉGIA DE PERFORMANCE (RX 7600 + Ryzen 5500):
═══════════════════════════════════════════════════════════════════════════════
  FASE 1 (Busca): LightGBM CPU com n_jobs=-1 (paraleliza os 60 fits nos 6 cores).
  FASE 2 (Treino): LightGBM com device_type="gpu" (OpenCL) com 3000 árvores.
  
MELHORIAS MATEMÁTICAS DESTA VERSÃO:
  - ELO K-Factor Dinâmico expandido: Eurocopa e Copa América valem 50 pontos, 
    Eliminatórias valem 40, Amistosos 20. O ELO gerado fica absurdamente preciso.
  - Pesos de Treinamento Granulares: O modelo agora penaliza erros cometidos 
    em jogos de Eurocopa/Copa América/Eliminatórias quase com o mesmo rigor 
    que jogos de Copa do Mundo, impedindo que aprenda apenas com amistosos.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import mean_absolute_error
import time
import multiprocessing
import warnings
warnings.filterwarnings("ignore")

DATA_DIR   = Path(__file__).parent.parent / "data"
CSV_PATH   = DATA_DIR / "results.csv"
MODEL_PATH = DATA_DIR / "xgboost_model.pkl"   # mantém o nome para compatibilidade

# ─────────────────────────────────────────────────────────────────────────────
# Detecção de GPU OpenCL (AMD RX 7600)
# ─────────────────────────────────────────────────────────────────────────────
def _detect_gpu_available() -> bool:
    """Retorna True se GPU OpenCL estiver disponível para LightGBM."""
    try:
        import lightgbm  # noqa
        import pyopencl as cl
        for plat in cl.get_platforms():
            devs = plat.get_devices(cl.device_type.GPU)
            if devs:
                names = [f"{plat.name.strip()} / {d.name.strip()}" for d in devs]
                print(f"  → GPU OpenCL detectada: {', '.join(names)}")
                return True
        print("  → Nenhuma GPU OpenCL detectada.")
    except ImportError as e:
        pkg = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"  → Pacote '{pkg}' não instalado — usando CPU puro.")
    except Exception as e:
        print(f"  → Erro na detecção OpenCL: {e}")
    return False

# ─────────────────────────────────────────────────────────────────────────────
# ELO histórico dinâmico e inteligente
# ─────────────────────────────────────────────────────────────────────────────
def get_k_factor(tournament_name: str) -> int:
    """Retorna o peso da partida para a troca de pontos ELO."""
    t = str(tournament_name)
    if t == "FIFA World Cup":
        return 60
    if t in ["UEFA Euro", "Copa América", "African Cup of Nations", "AFC Asian Cup", "FIFA Confederations Cup"]:
        return 50
    if "qualification" in t.lower() or "nations league" in t.lower():
        return 40
    if t == "Friendly":
        return 20
    return 30  # Outros torneios oficiais menores

def calculate_historical_elo(df: pd.DataFrame) -> pd.DataFrame:
    print("  → Calculando ELO histórico dinâmico (com K-Factor granular)...")
    elo: dict = {}
    home_elos, away_elos = [], []

    for _, row in df.iterrows():
        h, a = row["home_team"], row["away_team"]
        elo.setdefault(h, 1500)
        elo.setdefault(a, 1500)

        eh, ea = elo[h], elo[a]
        home_elos.append(eh)
        away_elos.append(ea)

        # Adiciona 100 pontos virtuais de ELO se for mandante de verdade
        dr = eh - ea + (100 if not row["neutral"] else 0)
        we_h = 1.0 / (10 ** (-dr / 400) + 1)
        we_a = 1.0 - we_h

        if   row["home_score"] > row["away_score"]: wh, wa = 1.0, 0.0
        elif row["home_score"] < row["away_score"]: wh, wa = 0.0, 1.0
        else:                                        wh, wa = 0.5, 0.5

        k = get_k_factor(row.get("tournament", ""))
        elo[h] = eh + k * (wh - we_h)
        elo[a] = ea + k * (wa - we_a)

    df["home_elo_pre_match"] = home_elos
    df["away_elo_pre_match"] = away_elos
    df["elo_diff"]           = df["home_elo_pre_match"] - df["away_elo_pre_match"]
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Médias móveis de gols (últimos 10 jogos)
# ─────────────────────────────────────────────────────────────────────────────
def add_rolling_goals(df: pd.DataFrame) -> pd.DataFrame:
    print("  → Calculando médias móveis de gols...")
    scored:   dict = {}
    conceded: dict = {}
    window = 10

    ha_sc, ha_co, aa_sc, aa_co = [], [], [], []

    for _, row in df.iterrows():
        h, a  = row["home_team"], row["away_team"]
        hs, as_ = row["home_score"], row["away_score"]

        ha_sc.append(np.mean(scored.get(h,   [])[-window:]) if scored.get(h)   else 1.2)
        ha_co.append(np.mean(conceded.get(h,  [])[-window:]) if conceded.get(h)  else 1.2)
        aa_sc.append(np.mean(scored.get(a,   [])[-window:]) if scored.get(a)   else 1.2)
        aa_co.append(np.mean(conceded.get(a,  [])[-window:]) if conceded.get(a)  else 1.2)

        scored.setdefault(h,   []).append(hs)
        conceded.setdefault(h, []).append(as_)
        scored.setdefault(a,   []).append(as_)
        conceded.setdefault(a, []).append(hs)

    df["home_avg_scored"]   = ha_sc
    df["home_avg_conceded"] = ha_co
    df["away_avg_scored"]   = aa_sc
    df["away_avg_conceded"] = aa_co
    return df

# ─────────────────────────────────────────────────────────────────────────────
# Carregamento e pré-processamento
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV não encontrado: {CSV_PATH}")

    print(f"Carregando {CSV_PATH.name}...")
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["home_score", "away_score"])
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year >= 2000].copy()
    df = df.sort_values("date").reset_index(drop=True)
    print(f"  → {len(df):,} partidas (2000-2026)")

    df = calculate_historical_elo(df)
    df = add_rolling_goals(df)

    # ── 1. PESO BASE DO TORNEIO (Hierarquia)
    tournaments = df["tournament"].fillna("")
    
    is_wc = tournaments == "FIFA World Cup"
    is_continental = tournaments.isin([
        "UEFA Euro", "Copa América", "African Cup of Nations", 
        "AFC Asian Cup", "CONCACAF Championship", "Gold Cup", "FIFA Confederations Cup"
    ])
    is_qualif_nl = tournaments.str.contains("qualification|Nations League", case=False, na=False)
    is_friendly = tournaments == "Friendly"
    
    tourn_weights = np.ones(len(df))
    tourn_weights[is_wc] = 3.0              # Copa do Mundo = 3x
    tourn_weights[is_continental] = 2.5     # Copas Continentais = 2.5x
    tourn_weights[is_qualif_nl] = 2.0       # Eliminatórias = 2x
    tourn_weights[is_friendly] = 1.0        # Amistosos = 1x
    # O que sobrar (torneios menores oficiais) fica com 1.5x
    mask_others = ~(is_wc | is_continental | is_qualif_nl | is_friendly)
    tourn_weights[mask_others] = 1.5

    # ── 2. PESO TEMPORAL (Ano)
    year = df["date"].dt.year
    year_weights = np.select(
        [year == 2026, year == 2025, year == 2024, year == 2023, year == 2022],
        [10.0,         7.0,          4.0,          2.5,          2.0],
        default=1.0
    )

    # Multiplica a importância do torneio pela importância temporal
    df["sample_weight"] = tourn_weights * year_weights

    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    
    df["is_friendly"]  = is_friendly.astype(int)
    # is_world_cup atua no modelo como a flag definitiva de "Partida Máxima"
    df["is_world_cup"] = is_wc.astype(int)
    
    # home_adv = 1 apenas para os 3 países-sede da Copa 2026
    WC_HOSTS = {"USA", "Mexico", "Canada"}
    df["home_adv"] = df["home_team"].isin(WC_HOSTS).astype(int)

    # EXATAMENTE as 10 features esperadas pelo feature_builder.py
    features = [
        "home_adv", "is_friendly", "is_world_cup",
        "home_elo_pre_match", "away_elo_pre_match", "elo_diff",
        "home_avg_scored", "home_avg_conceded",
        "away_avg_scored", "away_avg_conceded",
    ]
    return df[features], df["home_score"], df["away_score"], df["sample_weight"]

# ─────────────────────────────────────────────────────────────────────────────
# Treino final na GPU com early stopping (fase 2)
# ─────────────────────────────────────────────────────────────────────────────
def _train_final_gpu(lgb, best_params: dict, X_train, y_train, w_train,
                     X_val, y_val, n_estimators: int = 3000) -> object:
    params = {**best_params,
              "objective":      "poisson",
              "metric":         "poisson",
              "device_type":    "gpu",
              "gpu_platform_id": 0,
              "gpu_device_id":   0,
              "num_threads":     1,          
              "verbose":        -1,
              "n_estimators":    n_estimators,
              "random_state":    42}

    model = lgb.LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        sample_weight=w_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False),
                   lgb.log_evaluation(period=200)],
    )
    return model

# ─────────────────────────────────────────────────────────────────────────────
# Treinamento principal — Pipeline de 2 Fases
# ─────────────────────────────────────────────────────────────────────────────
def train_model():
    start  = time.time()
    n_cpu  = multiprocessing.cpu_count()
    X, y_home, y_away, weights = load_data()

    print(f"\nFeatures ({len(X.columns)}): {list(X.columns)}")
    print(f"CPU cores: {n_cpu}  (Ryzen 5500 = 6 cores / 12 threads)")

    gpu_ok = _detect_gpu_available()
    backend = "lightgbm_gpu" if gpu_ok else "lightgbm_cpu"
    device  = "gpu" if gpu_ok else "cpu"
    print(f"Backend: {backend.upper().replace('_',' ')} | Device: {device.upper()}\n")

    split = int(len(X) * 0.9)
    X_train, X_val     = X.iloc[:split],      X.iloc[split:]
    yh_train, yh_val   = y_home.iloc[:split], y_home.iloc[split:]
    ya_train, ya_val   = y_away.iloc[:split], y_away.iloc[split:]
    w_train            = weights.iloc[:split]

    import lightgbm as lgb
    from sklearn.model_selection import RandomizedSearchCV

    print("═" * 60)
    print(f"FASE 1 — Busca de hiperparâmetros (CPU, {n_cpu} cores em paralelo)")
    print("═" * 60)

    cpu_params = {
        "objective":     "poisson",
        "metric":        "poisson",
        "device_type":   "cpu",
        "num_threads":   -1,          
        "verbose":       -1,
        "n_estimators":  500,         
        "random_state":  42,
    }

    param_dist = {
        "num_leaves":        [31, 63, 127, 255],
        "learning_rate":     [0.01, 0.05, 0.08, 0.12],
        "subsample":         [0.7, 0.8, 0.9],
        "colsample_bytree":  [0.7, 0.8, 1.0],
        "min_child_samples": [5, 10, 20],
        "reg_alpha":         [0.0, 0.05, 0.1],
        "reg_lambda":        [0.0, 0.05, 0.1],
    }

    base_cpu = lgb.LGBMRegressor(**cpu_params)

    t1 = time.time()
    print(f"\n[{time.strftime('%H:%M:%S')}] Buscando hiperparâmetros — MANDANTE...")
    search_home = RandomizedSearchCV(
        base_cpu, param_distributions=param_dist, n_iter=20,
        scoring="neg_mean_poisson_deviance", cv=3,
        verbose=2,
        n_jobs=n_cpu,   
        random_state=42,
    )
    search_home.fit(X_train, yh_train, sample_weight=w_train)
    print(f"   Melhores params Home: {search_home.best_params_}")

    print(f"\n[{time.strftime('%H:%M:%S')}] Buscando hiperparâmetros — VISITANTE...")
    search_away = RandomizedSearchCV(
        base_cpu, param_distributions=param_dist, n_iter=20,
        scoring="neg_mean_poisson_deviance", cv=3,
        verbose=2,
        n_jobs=n_cpu,
        random_state=42,
    )
    search_away.fit(X_train, ya_train, sample_weight=w_train)
    print(f"   Melhores params Away: {search_away.best_params_}")
    print(f"   Fase 1 concluída em {time.time()-t1:.1f}s")

    print("\n" + "═" * 60)
    device_label = "GPU OpenCL (RX 7600)" if gpu_ok else "CPU (sem GPU disponível)"
    print(f"FASE 2 — Treino final ({device_label}, early stopping em 3000 árvores)")
    print("═" * 60)

    t2 = time.time()

    if gpu_ok:
        print(f"\n[{time.strftime('%H:%M:%S')}] Treinando modelo MANDANTE na GPU...")
        model_home = _train_final_gpu(lgb, search_home.best_params_,
                                      X_train, yh_train, w_train, X_val, yh_val)

        print(f"\n[{time.strftime('%H:%M:%S')}] Treinando modelo VISITANTE na GPU...")
        model_away = _train_final_gpu(lgb, search_away.best_params_,
                                      X_train, ya_train, w_train, X_val, ya_val)

        print(f"   ✅ Treino GPU concluído em {time.time()-t2:.1f}s")
        print(f"      Mandante: {model_home.best_iteration_} árvores")
        print(f"      Visitante: {model_away.best_iteration_} árvores")
    else:
        print(f"\n[{time.strftime('%H:%M:%S')}] Treinando modelo MANDANTE na CPU...")
        final_params_h = {**search_home.best_params_,
                         "objective": "poisson", "metric": "poisson",
                         "device_type": "cpu", "num_threads": -1,
                         "verbose": -1, "n_estimators": 3000, "random_state": 42}
        model_home = lgb.LGBMRegressor(**final_params_h)
        model_home.fit(X_train, yh_train, sample_weight=w_train,
                       eval_set=[(X_val, yh_val)],
                       callbacks=[lgb.early_stopping(50, verbose=False),
                                  lgb.log_evaluation(200)])

        print(f"\n[{time.strftime('%H:%M:%S')}] Treinando modelo VISITANTE na CPU...")
        final_params_a = {**search_away.best_params_,
                         "objective": "poisson", "metric": "poisson",
                         "device_type": "cpu", "num_threads": -1,
                         "verbose": -1, "n_estimators": 3000, "random_state": 42}
        model_away = lgb.LGBMRegressor(**final_params_a)
        model_away.fit(X_train, ya_train, sample_weight=w_train,
                       eval_set=[(X_val, ya_val)],
                       callbacks=[lgb.early_stopping(50, verbose=False),
                                  lgb.log_evaluation(200)])

    pred_h = model_home.predict(X_val)
    pred_a = model_away.predict(X_val)
    mae_h  = mean_absolute_error(yh_val, pred_h)
    mae_a  = mean_absolute_error(ya_val, pred_a)

    print(f"\n📊 Validação:")
    print(f"   MAE Mandante:  {mae_h:.4f} gols/jogo")
    print(f"   MAE Visitante: {mae_a:.4f} gols/jogo")
    print(f"   (Referência: MAE < 0.90 é excelente para previsão de gols em seleções)")

    try:
        importance = dict(zip(X.columns, model_home.feature_importances_))
        print("\n📈 Importância das features (modelo mandante):")
        max_imp = max(importance.values()) or 1
        for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(imp / max_imp * 20)
            print(f"   {feat:<25} {bar} {imp:.0f}")
    except Exception:
        pass

    payload = {
        "home":       model_home,
        "away":       model_away,
        "features":   list(X.columns),
        "mae_home":   mae_h,
        "mae_away":   mae_a,
        "backend":    backend,
        "device":     device,
        "trained_on": pd.Timestamp.now().isoformat(),
    }
    joblib.dump(payload, MODEL_PATH)

    elapsed = time.time() - start
    print(f"\n🏆 Modelo salvo em: {MODEL_PATH}")
    print(f"   Backend:    {backend.upper().replace('_',' ')}")
    print(f"   Tempo total: {elapsed:.1f}s")

    if not gpu_ok:
        print("\n💡 Para usar sua AMD RX 7600 e acelerar o Fase 2:")
        print("   pip install lightgbm pyopencl")
        print("   Execute novamente — GPU será detectada automaticamente.")

if __name__ == "__main__":
    train_model()