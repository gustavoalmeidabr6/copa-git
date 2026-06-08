"""
models/train_player_models.py — MOTOR DE MACHINE LEARNING INDIVIDUAL (v6 DEFINITIVA)

CORREÇÕES APLICADAS:
  - MATCH INVERTIDO (Fix do Darwin Núñez): A IA agora só contabiliza gols 
    históricos se o nome do jogador estiver contido no nome da base de dados, 
    impedindo que Darwin Núñez roube gols de qualquer "Nunez" genérico.
  - ALIAS SYNC: Sincronizado com o data_loader para reconhecer "Mbappé" e "Dembélé".
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

DATA_DIR      = Path(__file__).parent.parent / "data"
SEASON_2526   = DATA_DIR / "players_data-2025_2026.csv"
SEASON_2425   = DATA_DIR / "players_data-2024_2025.csv"
SEASON_2324   = DATA_DIR / "big_5_players_stats_2023_2024.csv"
EAFC_CSV      = DATA_DIR / "EAFC26-Men.csv"
TM_PLAYERS    = DATA_DIR / "players.csv"
TM_GOALS      = DATA_DIR / "goalscorers.csv"
MODEL_OUT     = DATA_DIR / "player_ml_models.pkl"

# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZAÇÃO E ALIASES (A Base O(1) de Performance)
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

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE FUTEBOL
# ─────────────────────────────────────────────────────────────────────────────
def _get_league_weight(league_name: str, player_name: str = "") -> float:
    base = 0.80
    lname = str(league_name).lower()
    if any(x in lname for x in ['premier', 'england', 'la liga', 'spain', 'champions']): base = 1.00
    elif any(x in lname for x in ['serie a', 'italy', 'bundesliga', 'germany']):          base = 0.92
    elif any(x in lname for x in ['ligue 1', 'france']):                                  base = 0.85
    elif any(x in lname for x in ['portugal', 'primeira']):                               base = 0.78
    elif any(x in lname for x in ['saudi', 'mls', 'brasil', 'argentina', 'eredivisie']): base = 0.65
    vip = ["messi","ronaldo","neymar","darwin","depay","bono","kante","james",
           "kessi","afif","arrascaeta","tillman","yilmaz","paez","hwang"]
    if player_name and any(v in player_name for v in vip):
        return max(base, 0.85)
    return base

def _get_pos_category(pos_str: str) -> str:
    pos_str = str(pos_str).lower()
    if any(x in pos_str for x in ['fw','st','lw','rw','cf','attacker']): return "Attacker"
    if any(x in pos_str for x in ['mf','am','dm','cm','lm','rm','midfielder']): return "Midfielder"
    if any(x in pos_str for x in ['df','cb','lb','rb','lwb','rwb','defender']): return "Defender"
    if any(x in pos_str for x in ['gk','goalkeeper']): return "Goalkeeper"
    return "Unknown"

# ─────────────────────────────────────────────────────────────────────────────
# EXTRATOR UNIVERSAL DE TEMPORADAS
# ─────────────────────────────────────────────────────────────────────────────
def _parse_season_csv(filepath: Path, year_label: str) -> dict:
    if not filepath.exists():
        print(f"  ⚠️  Arquivo não encontrado, ignorando: {filepath.name}")
        return {}
        
    df = pd.read_csv(filepath, low_memory=False)
    
    def col(candidates):
        for c in df.columns:
            cl = str(c).lower().strip()
            if cl in candidates: return c
        return None

    name_c = col(['name', 'player', 'jogador'])
    min_c  = col(['min', 'minutes', 'minutos', 'playing time_min', 'playing_time_min'])
    gls_c  = col(['goals', 'gls', 'gols', 'performance_gls', 'performance_goals'])
    ast_c  = col(['assists', 'ast', 'assistencias', 'performance_ast', 'performance_assists'])
    pos_c  = col(['pos', 'position', 'posicao'])
    age_c  = col(['age', 'idade', 'year_born'])
    comp_c = col(['comp', 'league', 'competition', 'campeonato'])

    if not name_c or not min_c: 
        return {}

    parsed_data = {}
    for _, row in df.iterrows():
        raw_name = str(row[name_c]).strip()
        if raw_name == 'nan' or not raw_name: continue
        
        mins = pd.to_numeric(str(row.get(min_c, 0)).replace(',', ''), errors='coerce')
        if pd.isna(mins) or mins <= 0: continue
        
        gls = pd.to_numeric(row.get(gls_c, 0), errors='coerce')
        ast = pd.to_numeric(row.get(ast_c, 0), errors='coerce')
        age = pd.to_numeric(row.get(age_c, 25), errors='coerce')
        pos = str(row.get(pos_c, "Unknown"))
        comp = str(row.get(comp_c, "Unknown"))
        
        n_norm = _normalize_name(raw_name)
        canonical = _canonical(n_norm)
        
        parsed_data[canonical] = {
            "min": mins, "gls": gls, "ast": ast,
            "age": age, "pos": pos, "comp": comp, "raw_name": raw_name
        }
        
    print(f"  → {year_label} carregada: {len(parsed_data)} jogadores válidos.")
    return parsed_data

# ─────────────────────────────────────────────────────────────────────────────
# PREPARAÇÃO DO DATASET TRI-ANUAL (EMA)
# ─────────────────────────────────────────────────────────────────────────────
def prepare_dataset():
    t0 = time.time()
    print(f"\n[{time.strftime('%H:%M:%S')}] ▶ Extraindo Múltiplas Temporadas...")

    data_2526 = _parse_season_csv(SEASON_2526, "Temporada 25/26")
    data_2425 = _parse_season_csv(SEASON_2425, "Temporada 24/25")
    data_2324 = _parse_season_csv(SEASON_2324, "Temporada 23/24 (Big 5)")

    all_names = set(data_2526.keys()) | set(data_2425.keys()) | set(data_2324.keys())

    ea_raw = {}
    if EAFC_CSV.exists():
        df_ea = pd.read_csv(EAFC_CSV, low_memory=False)
        if "Name" in df_ea.columns and "OVR" in df_ea.columns:
            for _, row in df_ea.iterrows(): ea_raw[_normalize_name(row["Name"])] = float(row["OVR"])
    ea_lookup = _build_lookup(ea_raw)

    tm_raw = {}
    if TM_PLAYERS.exists():
        df_tm = pd.read_csv(TM_PLAYERS, low_memory=False)
        name_c = "name" if "name" in df_tm.columns else "first_name"
        if name_c in df_tm.columns and "market_value_in_eur" in df_tm.columns:
            for _, row in df_tm.iterrows():
                try: tm_raw[_normalize_name(row[name_c])] = float(row["market_value_in_eur"]) / 1_000_000.0
                except: pass
    tm_lookup = _build_lookup(tm_raw)

    nat_raw = {}
    if TM_GOALS.exists():
        df_goals = pd.read_csv(TM_GOALS, low_memory=False)
        if "scorer" in df_goals.columns:
            for k, v in df_goals["scorer"].value_counts().to_dict().items():
                nat_raw[_normalize_name(k)] = v

    PRIOR_90S = 10.0
    PRIORS = {
        "Attacker":   {"G90": 0.35, "A90": 0.15, "Code": 3},
        "Midfielder": {"G90": 0.08, "A90": 0.18, "Code": 2},
        "Defender":   {"G90": 0.03, "A90": 0.05, "Code": 1},
        "Goalkeeper": {"G90": 0.00, "A90": 0.01, "Code": 0},
        "Unknown":    {"G90": 0.10, "A90": 0.10, "Code": 2},
    }

    features = []
    
    for n_norm in all_names:
        w_sum = 0.0
        w_gls = 0.0
        w_ast = 0.0
        total_mins = 0.0
        latest_data = None

        if n_norm in data_2526:
            d = data_2526[n_norm]
            latest_data = d
            w = 0.50
            w_sum += w
            w_gls += d['gls'] * w
            w_ast += d['ast'] * w
            total_mins += d['min']

        if n_norm in data_2425:
            d = data_2425[n_norm]
            if not latest_data: latest_data = d
            w = 0.30
            w_sum += w
            w_gls += d['gls'] * w
            w_ast += d['ast'] * w
            total_mins += d['min']

        if n_norm in data_2324:
            d = data_2324[n_norm]
            if not latest_data: latest_data = d
            w = 0.20
            w_sum += w
            w_gls += d['gls'] * w
            w_ast += d['ast'] * w
            total_mins += d['min']

        if w_sum == 0: continue

        final_gls = w_gls / w_sum
        final_ast = w_ast / w_sum
        
        p_name = latest_data['raw_name']
        p_age  = latest_data['age']
        p_pos  = _get_pos_category(latest_data['pos'])
        league_w = _get_league_weight(latest_data['comp'], n_norm)
        
        pos_code = PRIORS[p_pos]["Code"]
        ovr   = _get_value(ea_lookup,  n_norm, 75.0)
        mv    = _get_value(tm_lookup,  n_norm, 5.0)
        
        # FIX DE FOGO: A IA agora SÓ soma gols se o nome base do jogador
        # FOR ACHADO DENTRO da string do banco de dados, e não o inverso.
        nat_g = 0
        for nk, gols in nat_raw.items():
            if n_norm == nk or (len(n_norm) > 3 and n_norm in nk):
                nat_g += gols

        real_90s = total_mins / 90.0
        adj_gls = final_gls * league_w
        adj_ast = final_ast * league_w

        smoothed_g90 = (adj_gls + PRIORS[p_pos]["G90"] * PRIOR_90S) / (real_90s + PRIOR_90S)
        smoothed_a90 = (adj_ast + PRIORS[p_pos]["A90"] * PRIOR_90S) / (real_90s + PRIOR_90S)

        nat_g_normalized = np.log1p(nat_g)
        target_g90 = smoothed_g90 + (nat_g_normalized * 0.003) + (mv * 0.0005)

        features.append({
            "Player":       p_name,
            "Age":          p_age,
            "Pos_Code":     pos_code,
            "EA_Rating":    ovr,
            "Market_Value": np.log1p(mv),
            "League_Weight":league_w,
            "Target_G90":   target_g90,
            "Target_A90":   smoothed_a90,
            "Sample_Weight":np.log1p(total_mins), 
        })

    df_ml = pd.DataFrame(features)

    df_ml["Target_G90"]    = pd.to_numeric(df_ml["Target_G90"],    errors="coerce")
    df_ml["Target_A90"]    = pd.to_numeric(df_ml["Target_A90"],    errors="coerce")
    df_ml["Market_Value"]  = pd.to_numeric(df_ml["Market_Value"],  errors="coerce").fillna(5.0)
    df_ml["EA_Rating"]     = pd.to_numeric(df_ml["EA_Rating"],     errors="coerce").fillna(75.0)
    df_ml.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_ml.dropna(subset=["Target_G90", "Target_A90", "Age", "EA_Rating"], inplace=True)
    
    df_ml["Target_G90"] = df_ml["Target_G90"].clip(lower=0.0)
    df_ml["Target_A90"] = df_ml["Target_A90"].clip(lower=0.0)

    print(f"  → Matriz Final Construída: {len(df_ml)} jogadores únicos processados  ({time.time()-t0:.1f}s)")
    return df_ml

# ─────────────────────────────────────────────────────────────────────────────
# DETECÇÃO DE GPU
# ─────────────────────────────────────────────────────────────────────────────
def _detect_gpu_params(base_params: dict) -> dict:
    for device, extra in [
        ("gpu",  {"gpu_platform_id": 0, "gpu_device_id": 0}),
        ("gpu",  {"gpu_platform_id": 1, "gpu_device_id": 0}),
        ("cpu",  {"num_threads": -1}),
    ]:
        params = {**base_params, "device_type": device, **extra, "n_estimators": 10}
        try:
            m = lgb.LGBMRegressor(**params)
            X_dummy = np.random.rand(50, 5)
            y_dummy = np.random.rand(50)
            m.fit(X_dummy, y_dummy)
            label = f"GPU (OpenCL — platform {extra.get('gpu_platform_id','?')})" if device == "gpu" else "CPU (Multicore)"
            print(f"  ✅ Dispositivo detectado e ativado: {label}")
            result = {**base_params, "device_type": device, **extra}
            result.pop("n_estimators", None)
            return result, label
        except Exception as e:
            pass
    return {**base_params, "device_type": "cpu", "num_threads": -1}, "CPU (fallback)"

# ─────────────────────────────────────────────────────────────────────────────
# TREINAMENTO DA INTELIGÊNCIA ARTIFICIAL
# ─────────────────────────────────────────────────────────────────────────────
def train_player_models():
    start_time = time.time()

    df = prepare_dataset()

    X        = df[["Age", "Pos_Code", "EA_Rating", "League_Weight", "Market_Value"]]
    y_goals  = df["Target_G90"]
    y_assists= df["Target_A90"]
    weights  = df["Sample_Weight"]

    X_train, X_val, yg_train, yg_val, ya_train, ya_val, w_train, w_val = train_test_split(
        X, y_goals, y_assists, weights, test_size=0.1, random_state=42
    )

    BASE_PARAMS = {
        "objective":    "poisson",
        "metric":       "poisson",
        "learning_rate":0.05,
        "num_leaves":   63,
        "max_depth":    6,
        "verbose":      -1,
        "n_estimators": 1000,
        "random_state": 42,
    }

    print(f"\n[{time.strftime('%H:%M:%S')}] ▶ Validando Arquitetura de Hardware...")
    lgb_params, device_label = _detect_gpu_params(BASE_PARAMS)

    CALLBACKS = [lgb.early_stopping(stopping_rounds=50, verbose=False)]

    print(f"[{time.strftime('%H:%M:%S')}] ▶ Treinando Deep Learning: Expected Goals (xG)...")
    model_goals = lgb.LGBMRegressor(**lgb_params)
    model_goals.fit(
        X_train, yg_train, sample_weight=w_train,
        eval_set=[(X_val, yg_val)],
        callbacks=CALLBACKS,
    )

    print(f"[{time.strftime('%H:%M:%S')}] ▶ Treinando Deep Learning: Expected Assists (xA)...")
    model_assists = lgb.LGBMRegressor(**lgb_params)
    model_assists.fit(
        X_train, ya_train, sample_weight=w_train,
        eval_set=[(X_val, ya_val)],
        callbacks=CALLBACKS,
    )

    val_mask_g = ~np.isnan(yg_val.values)
    val_mask_a = ~np.isnan(ya_val.values)

    pred_g = model_goals.predict(X_val)
    pred_a = model_assists.predict(X_val)

    mae_g = mean_absolute_error(yg_val.values[val_mask_g], pred_g[val_mask_g])
    mae_a = mean_absolute_error(ya_val.values[val_mask_a], pred_a[val_mask_a])

    print(f"\n📊 RESULTADOS DA VALIDAÇÃO (Erro Absoluto Médio):")
    print(f"   Precisão de Gols : ±{mae_g:.4f} gols/90")
    print(f"   Precisão de Asts : ±{mae_a:.4f} assists/90")

    importance = dict(zip(X.columns, model_goals.feature_importances_))
    print(f"\n📈 PESO DAS FEATURES (A IA agora enxerga a consistência e o Preço):")
    max_imp = max(importance.values()) or 1
    for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp / max_imp * 20)
        print(f"   {feat:<15} {bar}  {imp:.0f}")

    payload = {
        "model_goals":   model_goals,
        "model_assists": model_assists,
        "features":      list(X.columns),
        "device_used":   device_label,
        "trained_on":    pd.Timestamp.now().isoformat(),
    }
    joblib.dump(payload, MODEL_OUT)

    elapsed = time.time() - start_time
    print(f"\n🏆 Modelos Individuais salvos em: {MODEL_OUT.name}")
    print(f"   Tempo total da operação: {elapsed:.1f}s")


if __name__ == "__main__":
    train_player_models()