"""
api_clients/football_api.py
Clientes completos e estruturados para todas as APIs de futebol.
Inclui tratamento seguro de cache para Windows.
"""
import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

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

class APIFootball:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "v3.football.api-sports.io"}

    def _get(self, endpoint: str, params: dict = None) -> dict | None:
        cache_key = _build_safe_cache_key("apif", endpoint, params)
        cached = _load_cache(cache_key)
        if cached: return cached

        if not self.api_key or self.api_key == "SUA_CHAVE_AQUI": return None

        try:
            # Usando os dois cabeçalhos possíveis para garantir 100% de compatibilidade
            headers = {
                "x-rapidapi-key": self.api_key, 
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-apisports-key": self.api_key 
            }
            r = requests.get(f"{self.BASE_URL}/{endpoint}", headers=headers, params=params, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                
                # 1. Se o próprio JSON enviar uma lista ou dicionário de erros, aí sim abortamos.
                if data.get('errors') and len(data['errors']) > 0: 
                    print(f"⚠️ API-Football recusou {endpoint}. Motivo: {data['errors']}")
                    return None
                
                # 2. Se a chave 'response' não existir no JSON, algo deu errado.
                # Nota: Se ela existir e for [], significa "zero resultados" (ex: 0 lesões). É válido!
                if 'response' not in data: 
                    print(f"⚠️ API-Football não enviou 'response' para {endpoint}.")
                    return None
                
                _save_cache(cache_key, data)
                time.sleep(1) # Intervalo seguro para não tomar block
                return data
            else:
                print(f"⚠️ Erro de conexão na API: Status {r.status_code} ({endpoint})")
        except requests.RequestException as e:
            print(f"⚠️ Falha de rede ao chamar a API: {e}")
            
        return None
    
    def get_team_statistics(self, team_id: int, season: int) -> dict | None:
        data = self._get("teams/statistics", {"league": 1, "team": team_id, "season": season})
        return data.get("response") if data else None

    def get_injuries(self, team_id: int) -> list | None:
        """Busca a lista de lesionados do time em tempo real."""
        data = self._get("injuries", {"team": team_id})
        return data.get("response") if data else None

    def get_last_match_players(self, team_id: int) -> list | None:
        """Busca os jogadores que entraram em campo no ÚLTIMO JOGO OFICIAL do time."""
        # 1. Pega o ID da última partida real que o time disputou
        fix_data = self._get("fixtures", {"team": team_id, "last": 1})
        if not fix_data or not fix_data.get('response'): return None
        
        fixture_id = fix_data['response'][0]['fixture']['id']
        
        # 2. Pega o elenco, notas e posições exatas dessa partida
        players_data = self._get("fixtures/players", {"fixture": fixture_id, "team": team_id})
        
        if players_data and players_data.get('response'):
            return players_data['response'][0].get('players')
            
        return None

class FootballDataOrg:
    BASE_URL = "https://api.football-data.org/v4"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"X-Auth-Token": api_key}

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

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_world_cup_odds(self) -> list | None:
        cache_key = "odds_wc_outrights"
        cached = _load_cache(cache_key, max_age_hours=1)
        if cached: return cached
        
        if not self.api_key or self.api_key == "SUA_CHAVE_AQUI": return None
        
        params = {"apiKey": self.api_key, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"}
        try:
            r = requests.get(f"{self.BASE_URL}/sports/{self.SOCCER_KEY}/odds", params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                _save_cache(cache_key, data)
                return data
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
    """Classe mantida para compatibilidade com o __init__.py"""
    pass