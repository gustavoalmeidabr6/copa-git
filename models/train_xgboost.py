"""
models/train_xgboost.py — VERSÃO CORRIGIDA v2

CORREÇÕES / MELHORIAS:
  BUG 5 (CRÍTICO): GPU não estava sendo usada.
    - XGBoost usa tree_method="hist" por padrão (CPU).
    - Solução: detecta CUDA automaticamente. Se disponível, usa device="cuda"
      que ativa o acelerador de GPU nativo do XGBoost (HistGPU).
    - Compatível com qualquer GPU NVIDIA com drivers CUDA instalados.
    - Fallback automático para CPU se não houver GPU.

  BUG 8 (mantido da versão anterior): filtra partidas >= 2000.

  MELHORIA: log mostra claramente se GPU ou CPU foi usada.
  MELHORIA: pesos temporais granulares (2026=10, 2025=7, 2024=4, 2023=2.5, resto=1).
  MELHORIA: salva métricas de validação junto com o modelo.

NOTA SOBRE GPU:
  Para usar GPU, você precisa de:
  1. GPU NVIDIA com suporte a CUDA (RTX 2000+, GTX 1660+, etc.)
  2. Drivers NVIDIA atualizados
  3. XGBoost >= 2.0 (já vem com suporte CUDA nativo via pip install xgboost)
  
  Verificação: python -c "import xgboost; print(xgboost.__version__)"
  Para forçar GPU: defina FORCE_GPU=True abaixo.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import mean_absolute_error
import joblib
from pathlib import Path
import time
import multiprocessing

DATA_DIR   = Path(__file__).parent.parent / "data"
CSV_PATH   = DATA_DIR / "results.csv"
MODEL_PATH = DATA_DIR / "xgboost_model.pkl"

FORCE_GPU = False  # True para forçar GPU (erro se não tiver CUDA)


def _detect_device() -> str:
    """
    Detecta se há GPU CUDA disponível para XGBoost.
    XGBoost >= 2.0: device="cuda" ativa GPU automaticamente.
    """
    if FORCE_GPU:
        print("  → GPU forçada (FORCE_GPU=True)")
        return "cuda"
    
    try:
        # Método 1: via pynvml (mais confiável)
        import pynvml
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        if count > 0:
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(handle)
            print(f"  → GPU detectada: {name} — XGBoost usará CUDA")
            return "cuda"
    except Exception:
        pass
    
    try:
        # Método 2: via torch (se PyTorch estiver instalado)
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            print(f"  → GPU detectada via PyTorch: {name} — XGBoost usará CUDA")
            return "cuda"
    except Exception:
        pass
    
    try:
        # Método 3: testa diretamente com XGBoost em um dataset mínimo
        import xgboost as xgb_test
        dtrain = xgb_test.DMatrix(np.array([[1,2],[3,4]]), label=[0,1])
        xgb_test.train({"device": "cuda", "tree_method": "hist", "verbosity": 0}, dtrain, num_boost_round=1)
        print("  → GPU CUDA disponível para XGBoost")
        return "cuda"
    except Exception:
        pass
    
    print("  → Nenhuma GPU detectada. Usando CPU (tree_method=hist).")
    print("     Para usar GPU: instale drivers NVIDIA + XGBoost >= 2.0")
    return "cpu"


def calculate_historical_elo(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula ELO histórico dinâmico linha a linha."""
    print("  → Calculando ELO histórico dinâmico...")
    K = {"Friendly": 20, "FIFA World Cup": 60}
    K_DEFAULT = 40

    elo: dict = {}
    home_elos, away_elos = [], []

    for _, row in df.iterrows():
        h, a = row["home_team"], row["away_team"]
        elo.setdefault(h, 1500)
        elo.setdefault(a, 1500)

        eh, ea = elo[h], elo[a]
        home_elos.append(eh)
        away_elos.append(ea)

        dr  = eh - ea + (100 if not row["neutral"] else 0)
        we_h = 1.0 / (10 ** (-dr / 400) + 1)
        we_a = 1.0 - we_h

        if   row["home_score"] > row["away_score"]: wh, wa = 1.0, 0.0
        elif row["home_score"] < row["away_score"]: wh, wa = 0.0, 1.0
        else:                                        wh, wa = 0.5, 0.5

        k = K.get(row["tournament"], K_DEFAULT)
        elo[h] = eh + k * (wh - we_h)
        elo[a] = ea + k * (wa - we_a)

    df["home_elo_pre_match"] = home_elos
    df["away_elo_pre_match"] = away_elos
    df["elo_diff"]           = df["home_elo_pre_match"] - df["away_elo_pre_match"]
    return df


def add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona média móvel de gols marcados/sofridos (últimos 10 jogos)."""
    print("  → Calculando médias móveis de gols...")
    team_goals_scored: dict   = {}
    team_goals_conceded: dict = {}
    window = 10

    home_avg_scored, home_avg_conceded = [], []
    away_avg_scored, away_avg_conceded = [], []

    for _, row in df.iterrows():
        h, a = row["home_team"], row["away_team"]
        hs, as_ = row["home_score"], row["away_score"]

        h_sc  = team_goals_scored.get(h, [])
        h_con = team_goals_conceded.get(h, [])
        a_sc  = team_goals_scored.get(a, [])
        a_con = team_goals_conceded.get(a, [])

        home_avg_scored.append(   np.mean(h_sc[-window:])   if h_sc  else 1.2)
        home_avg_conceded.append( np.mean(h_con[-window:])  if h_con else 1.2)
        away_avg_scored.append(   np.mean(a_sc[-window:])   if a_sc  else 1.2)
        away_avg_conceded.append( np.mean(a_con[-window:])  if a_con else 1.2)

        team_goals_scored.setdefault(h, []).append(hs)
        team_goals_conceded.setdefault(h, []).append(as_)
        team_goals_scored.setdefault(a, []).append(as_)
        team_goals_conceded.setdefault(a, []).append(hs)

    df["home_avg_scored"]   = home_avg_scored
    df["home_avg_conceded"] = home_avg_conceded
    df["away_avg_scored"]   = away_avg_scored
    df["away_avg_conceded"] = away_avg_conceded
    return df


def load_and_preprocess_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV não encontrado: {CSV_PATH}")

    print("Carregando results.csv...")
    df = pd.read_csv(CSV_PATH)
    df = df.dropna(subset=["home_score", "away_score"])
    df["date"] = pd.to_datetime(df["date"])

    df = df[df["date"].dt.year >= 2000].copy()
    df = df.sort_values("date").reset_index(drop=True)

    print(f"  → {len(df):,} partidas carregadas (2000–hoje)")

    df = calculate_historical_elo(df)
    df = add_rolling_features(df)

    year = df["date"].dt.year
    conditions = [year == 2026, year == 2025, year == 2024, year == 2023]
    choices    = [10.0,          7.0,          4.0,          2.5]
    df["sample_weight"] = np.select(conditions, choices, default=1.0)

    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["is_friendly"]  = (df["tournament"] == "Friendly").astype(int)
    df["is_world_cup"] = (df["tournament"] == "FIFA World Cup").astype(int)
    df["home_adv"]     = (~df["neutral"]).astype(int)

    features = [
        "home_adv", "is_friendly", "is_world_cup",
        "home_elo_pre_match", "away_elo_pre_match", "elo_diff",
        "home_avg_scored", "home_avg_conceded",
        "away_avg_scored", "away_avg_conceded",
    ]
    return df[features], df["home_score"], df["away_score"], df["sample_weight"]


def train_model():
    start = time.time()
    X, y_home, y_away, weights = load_and_preprocess_data()

    # ── CORREÇÃO BUG 5: detecta GPU automaticamente ────────────────────
    device = _detect_device()
    
    print(f"\nIniciando treinamento com {len(X):,} partidas...")
    print(f"Features utilizadas: {list(X.columns)}")
    print(f"Dispositivo: {'GPU (CUDA)' if device == 'cuda' else 'CPU'}")

    param_dist = {
        "max_depth":        [3, 4, 5, 6],
        "learning_rate":    [0.01, 0.05, 0.1, 0.15],
        "n_estimators":     [200, 400, 600],
        "subsample":        [0.7, 0.8, 0.9],
        "colsample_bytree": [0.7, 0.8, 1.0],
        "min_child_weight": [1, 3, 5],
        "reg_alpha":        [0, 0.1, 0.5],
    }

    cores = multiprocessing.cpu_count()
    print(f"CPU cores disponíveis: {cores}\n")

    # CORREÇÃO: device="cuda" para GPU, mantém tree_method="hist" (compatível)
    base_params = {
        "objective":   "count:poisson",
        "tree_method": "hist",
        "device":      device,          # ← NOVO: GPU se disponível
        "n_jobs":      1 if device == "cuda" else -1,  # GPU não precisa de multithread
        "random_state": 42,
    }
    
    base = xgb.XGBRegressor(**base_params)

    split_idx = int(len(X) * 0.9)
    X_train, X_val     = X.iloc[:split_idx],      X.iloc[split_idx:]
    y_h_train, y_h_val = y_home.iloc[:split_idx], y_home.iloc[split_idx:]
    y_a_train, y_a_val = y_away.iloc[:split_idx], y_away.iloc[split_idx:]
    w_train            = weights.iloc[:split_idx]

    n_jobs_search = 1 if device == "cuda" else -1

    search_home = RandomizedSearchCV(
        base, param_distributions=param_dist, n_iter=20,
        scoring="neg_mean_poisson_deviance", cv=3,
        verbose=1, n_jobs=n_jobs_search, random_state=42,
    )
    search_away = RandomizedSearchCV(
        base, param_distributions=param_dist, n_iter=20,
        scoring="neg_mean_poisson_deviance", cv=3,
        verbose=1, n_jobs=n_jobs_search, random_state=42,
    )

    print("Treinando modelo MANDANTE (home goals)...")
    search_home.fit(X_train, y_h_train, sample_weight=w_train)

    print("\nTreinando modelo VISITANTE (away goals)...")
    search_away.fit(X_train, y_a_train, sample_weight=w_train)

    pred_h = search_home.best_estimator_.predict(X_val)
    pred_a = search_away.best_estimator_.predict(X_val)
    mae_h  = mean_absolute_error(y_h_val, pred_h)
    mae_a  = mean_absolute_error(y_a_val, pred_a)

    print(f"\n✅ Validação — MAE Mandante: {mae_h:.4f} gols | MAE Visitante: {mae_a:.4f} gols")
    print(f"   Melhores hiperparâmetros Home:  {search_home.best_params_}")
    print(f"   Melhores hiperparâmetros Away:  {search_away.best_params_}")

    payload = {
        "home":       search_home.best_estimator_,
        "away":       search_away.best_estimator_,
        "features":   list(X.columns),
        "mae_home":   mae_h,
        "mae_away":   mae_a,
        "device":     device,
        "trained_on": pd.Timestamp.now().isoformat(),
    }
    joblib.dump(payload, MODEL_PATH)

    elapsed = time.time() - start
    device_str = "GPU (CUDA)" if device == "cuda" else "CPU"
    print(f"\n🏆 Modelo salvo em {MODEL_PATH}")
    print(f"   Dispositivo usado: {device_str}")
    print(f"   Tempo total: {elapsed:.1f}s")
    
    if device == "cpu":
        print("\n💡 DICA: Para usar sua GPU e treinar mais rápido:")
        print("   1. Confirme que os drivers NVIDIA estão atualizados")
        print("   2. pip install xgboost --upgrade")
        print("   3. Execute novamente — a GPU será detectada automaticamente")


if __name__ == "__main__":
    train_model()