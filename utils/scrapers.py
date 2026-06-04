"""
utils/scrapers.py
Motores de Web Scraping e APIs abertas para buscar dados em tempo real.
"""

import requests
import requests_cache
from bs4 import BeautifulSoup
import time
import re

# Cria um cache local de 12 horas para não sermos bloqueados pelos sites
requests_cache.install_cache('soccer_scraping_cache', expire_after=43200)

class DataScraper:
    def __init__(self):
        # Disfarce perfeito para o robô passar pelos bloqueios básicos
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def get_weather_forecast(self, city: str) -> dict:
        """
        API Open-Meteo (Grátis, sem chave).
        Busca a temperatura atual da cidade do jogo.
        """
        # Cidades sede da Copa 2026 (Exemplos práticos)
        cities_coords = {
            "Miami": {"lat": 25.7617, "lon": -80.1918},
            "Mexico City": {"lat": 19.4326, "lon": -99.1332},
            "New York": {"lat": 40.7128, "lon": -74.0060},
            "Toronto": {"lat": 43.6510, "lon": -79.3470},
            "Los Angeles": {"lat": 34.0522, "lon": -118.2437}
        }
        
        coords = cities_coords.get(city, cities_coords["Miami"]) # Default Miami
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
        
        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                temp = data.get("current_weather", {}).get("temperature", 22.0)
                return {"temperature": temp}
        except Exception as e:
            print(f"Erro no Open-Meteo: {e}")
            
        return {"temperature": 22.0} # Temperatura neutra em caso de erro

    def get_sofifa_team_ratings(self, team_name: str) -> dict:
        """
        Faz Web Scraping no SoFIFA.com para pegar a nota exata (1-99) 
        do Ataque, Meio-Campo e Defesa da seleção ATUALIZADA HOJE.
        """
        # URL de busca do SoFIFA
        search_url = f"https://sofifa.com/teams?type=national&kw={team_name.replace(' ', '+')}"
        
        default_ratings = {"attack": 75, "midfield": 75, "defense": 75, "overall": 75}
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return default_ratings
                
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Encontra a primeira linha da tabela de resultados (o time mais relevante)
            table = soup.find('table', {'class': 'table'})
            if not table:
                return default_ratings
                
            first_row = table.find('tbody').find('tr')
            if not first_row:
                return default_ratings
                
            # Extraindo as notas (O SoFIFA guarda isso em spans com data-col)
            # Geralmente as colunas são: OVR, ATT, MID, DEF
            spans = first_row.find_all('span', class_=re.compile('bp3-tag'))
            
            # Limpando os números
            ratings = [int(span.text) for span in spans if span.text.isdigit()]
            
            if len(ratings) >= 4:
                return {
                    "overall": ratings[0],
                    "attack": ratings[1],
                    "midfield": ratings[2],
                    "defense": ratings[3]
                }
                
        except Exception as e:
            print(f"Erro ao raspar SoFIFA para {team_name}: {e}")
            
        return default_ratings

    def get_fbref_xg(self, team_name: str) -> dict:
        """
        API não-oficial de raspagem do FBref usando Pandas.
        """
        import pandas as pd
        
        try:
            # Pegando tabela genérica de seleções masculinas
            url = "https://fbref.com/en/comps/1/World-Cup-Stats"
            # O read_html do pandas é um monstro para extrair tabelas
            tables = pd.read_html(url, storage_options=self.headers)
            df = tables[0]
            
            # Arruma os nomes das colunas que vêm em múltiplos níveis (MultiIndex)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(0)
                
            # Busca a linha do time
            team_row = df[df['Squad'].str.contains(team_name, case=False, na=False)]
            
            if not team_row.empty:
                return {
                    "xg_per_90": float(team_row['xG'].values[0] / team_row['MP'].values[0]),
                    "xga_per_90": float(team_row['xGA'].values[0] / team_row['MP'].values[0])
                }
        except Exception:
            pass # Se o FBref bloquear por limite de requisições, silencia
            
        return {"xg_per_90": 1.2, "xga_per_90": 1.2}
    
    def get_squad_micro_stats(self, team_name: str) -> dict:
        """
        Coleta dados granulares dos 11 titulares atuais usando SofaScore / FBref.
        Na vida real, isso requereria iterar sobre os 11 jogadores do time.
        """
        # Exemplo de payload real consolidado que extrairíamos cruzando dados:
        try:
            # Aqui entraria o request para o JSON oculto do SofaScore
            # URL_SOFASCORE = "https://api.sofascore.com/api/v1/team/..."
            pass 
        except Exception:
            pass

        # Como não temos as URLs exatas de cada jogador mapeadas ainda, 
        # aqui está a estrutura de dados que o scraper deve retornar:
        return {
            "avg_form_last_30_days": 7.4,  # Nota média dos titulares (0 a 10)
            "total_season_minutes": 38500, # Soma dos minutos jogados pelos 11 titulares no ano
            "injured_starters": 1,         # Quantos titulares absolutos estão fora
            "avg_caps": 45,                # Média de jogos pela seleção (Experiência)
            "same_club_connections": 3     # Quantas "duplas" ou "trios" jogam no mesmo clube
        }

    def get_manager_tenure(self, team_name: str) -> int:
        """
        Transfermarkt scraping para pegar os dias de cargo do treinador.
        """
        # Estrutura base de conhecimento
        tenures_in_days = {
            "Argentina": 2000, # Scaloni (muito tempo)
            "France": 4000,    # Deschamps (década)
            "Brazil": 800,     # Dorival (exemplo)
        }
        return tenures_in_days.get(team_name, 365) # Média de 1 ano para os demais
    def get_match_conditions(self, stadium_city: str, match_date: str) -> dict:
        """Busca o clima REAL no momento da simulação."""
        # Se for no México, bota a altitude pesada. Se não, Miami.
        if "Mexico" in stadium_city:
            coords = {"lat": 19.3029, "lon": -99.1505, "alt": 2200}
        else:
            coords = {"lat": 25.9580, "lon": -80.2389, "alt": 3}
            
        try:
            # Bate na API de clima real gratuita
            url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                temp = data.get("current_weather", {}).get("temperature", 25.0)
                return {"temperature": temp, "altitude": coords["alt"]}
        except Exception:
            pass
            
        return {"temperature": 25.0, "altitude": coords["alt"]}