"""
api_clients/football_api.py
Clientes completos e estruturados para todas as APIs de futebol.
Inclui tratamento seguro de cache para Windows e leitura do .env.
"""
import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carrega as chaves do arquivo .env automaticamente
load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _load_cache(key: str, max_age_hours: int = 12):
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if age < timedelta(hours=max_age_hours):
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
    return None

def _save_cache(key: str, data):
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _build_safe_cache_key(prefix: str, endpoint: str, params: dict) -> str:
    """Gera um nome de arquivo seguro para Windows (sem dois-pontos ou chaves)."""
    safe_endpoint = endpoint.replace('/', '_')
    if not params: return f"{prefix}_{safe_endpoint}"
    param_parts = []
    for k, v in sorted(params.items()):
        val_str = str(v).replace(',', '-').replace(' ', '').replace(':', '')
        param_parts.append(f"{k}-{val_str}")
    param_str = "_".join(param_parts)
    return f"{prefix}_{safe_endpoint}_{param_str}"



class FootballDataOrg:
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_KEY", "")
        self.headers = {"X-Auth-Token": self.api_key}

    def get_competition_matches(self, status: str = None) -> list | None:
        cache_key = "fdorg_matches_wc"
        cached = _load_cache(cache_key)
        if cached: return cached
        if not self.api_key or self.api_key == "SUA_CHAVE_AQUI": return None
        try:
            r = requests.get(f"{self.BASE_URL}/competitions/WC/matches", headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get("matches")
                _save_cache(cache_key, data)
                time.sleep(6)
                return data
        except requests.RequestException:
            pass
        return None

class TheOddsAPI:
    BASE_URL = "https://api.the-odds-api.com/v4"
    SOCCER_KEY = "soccer_fifa_world_cup"

    def __init__(self, api_key: str = None):
        # Vai ler a chave que você colocou no .env
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")

    def get_world_cup_odds(self) -> list | None:
        cache_key = "odds_wc_outrights"
        cached = _load_cache(cache_key, max_age_hours=10) # Cache de 10h para Odds
        if cached: return cached
        
        if not self.api_key or self.api_key == "SUA_CHAVE_AQUI": 
            print("⚠️  Chave TheOddsAPI não detectada. O simulador rodará sem a sabedoria do mercado.")
            return None
        
        params = {"apiKey": self.api_key, "regions": "eu,us", "markets": "h2h", "oddsFormat": "decimal"}
        try:
            print("🌐 Baixando Odds em tempo real das casas de apostas (The Odds API)...")
            r = requests.get(f"{self.BASE_URL}/sports/{self.SOCCER_KEY}/odds", params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                _save_cache(cache_key, data)
                return data
            else:
                print(f"⚠️ Erro TheOddsAPI: Status {r.status_code}")
        except requests.RequestException:
            pass
        return None

class OpenFootball:
    WC_2026_URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

    def get_world_cup_data(self) -> dict | None:
        cache_key = "openfootball_wc2026"
        cached = _load_cache(cache_key, max_age_hours=24)
        if cached: return cached
        try:
            r = requests.get(self.WC_2026_URL, timeout=15)
            if r.status_code == 200:
                data = r.json()
                _save_cache(cache_key, data)
                return data
        except requests.RequestException:
            pass
        return None

class EloRatings:
    pass
