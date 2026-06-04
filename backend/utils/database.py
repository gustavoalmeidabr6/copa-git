"""
utils/database.py
Gerenciador do banco de dados SQLite local.
Salva o histórico de jogos e faz cache das métricas raspadas da internet.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "worldcup_data.db"

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        
        # Tabela para cachear as métricas de hoje (Fadiga, Lesões, SoFIFA, Clima)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_features_cache (
                team_name TEXT PRIMARY KEY,
                xg_avg REAL,
                xga_avg REAL,
                attack_rating INTEGER,
                midfield_rating INTEGER,
                defense_rating INTEGER,
                fatigue_index REAL,
                last_updated TIMESTAMP
            )
        ''')
        
        self.conn.commit()

    def save_team_features(self, team_name: str, features: dict):
        """Salva as métricas no banco para não ter que raspar a internet toda hora."""
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT OR REPLACE INTO team_features_cache 
            (team_name, xg_avg, xga_avg, attack_rating, midfield_rating, defense_rating, fatigue_index, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            team_name, 
            features.get('xg_avg', 1.2), 
            features.get('xga_avg', 1.2),
            features.get('attack', 75),
            features.get('midfield', 75),
            features.get('defense', 75),
            features.get('fatigue_index', 1.0),
            now
        ))
        self.conn.commit()

    def get_cached_features(self, team_name: str):
        """Busca do cache local. Só vai para a internet se o dado for velho."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM team_features_cache WHERE team_name = ?", (team_name,))
        row = cursor.fetchone()
        
        if row:
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        return None