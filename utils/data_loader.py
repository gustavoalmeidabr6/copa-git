"""
utils/data_loader.py — VERSÃO v4 (Correção do Parse de Nomes Internacionais)

CORREÇÕES DESTA VERSÃO:
  - FIM DAS ABERRAÇÕES ("eko", "Golo Kanté", "inac"): O Regex antigo quebrava ao 
    encontrar acentos do Leste Europeu (ž, š, ć) e apóstrofos curvos (’). 
  - A função `_parse_player_names` foi reescrita para fazer um split estrutural 
    (cortando entre vírgulas e parênteses), sendo 100% blindada a qualquer idioma 
    ou caractere especial. Edin Džeko e N'Golo Kanté agora carregarão perfeitamente.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from difflib import get_close_matches

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONVOCADOS_PATH = DATA_DIR / "convocados_2026.txt"
EAFC_CSV_PATH   = DATA_DIR / "EAFC26-Men.csv"
TM_PLAYERS_CSV  = DATA_DIR / "players.csv"
TM_GOALSCORERS_CSV = DATA_DIR / "goalscorers.csv"

# ─────────────────────────────────────────────────────────────────────────────
# MAPEAMENTO EXPLÍCITO: nome-padrão EN → possíveis nomes no arquivo convocados
# ─────────────────────────────────────────────────────────────────────────────
SQUAD_NAME_ALIASES: dict[str, list[str]] = {
    "Argentina":              ["Argentina", "Selección Argentina"],
    "Australia":              ["Australia", "Socceroos"],
    "Austria":                ["Austria", "Áustria"],
    "Belgium":                ["Belgium", "Bélgica", "Belgique"],
    "Bosnia and Herzegovina": ["Bosnia and Herzegovina", "Bosnia-Herzegovina", "Bosnia",
                               "Bosnia & Herzegovina", "Bosnia Herzegovina"],
    "Brazil":                 ["Brazil", "Brasil"],
    "Canada":                 ["Canada", "Canadá"],
    "Cape Verde":             ["Cape Verde", "Cabo Verde"],
    "Colombia":               ["Colombia", "Colômbia"],
    "Croatia":                ["Croatia", "Croácia"],
    "Czechia":                ["Czechia", "Czech Republic", "República Tcheca"],
    "Curaçao":                ["Curaçao", "Curacao"],
    "DR Congo":               ["DR Congo", "Congo DR", "RD Congo", "DRC",
                               "Democratic Republic of the Congo",
                               "Democratic Republic Congo"],
    "Ecuador":                ["Ecuador", "Equador"],
    "Egypt":                  ["Egypt", "Egito"],
    "England":                ["England", "Inglaterra"],
    "France":                 ["France", "França"],
    "Germany":                ["Germany", "Alemanha", "Deutschland"],
    "Ghana":                  ["Ghana", "Gana"],
    "Haiti":                  ["Haiti"],
    "Iran":                   ["Iran", "Irã"],
    "Iraq":                   ["Iraq", "Iraque"],
    "Ivory Coast":            ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire", "Costa do Marfim"],
    "Japan":                  ["Japan", "Japão", "Japon"],
    "Jordan":                 ["Jordan", "Jordânia", "Jordan"],
    "Mexico":                 ["Mexico", "México"],
    "Morocco":                ["Morocco", "Marrocos", "Maroc"],
    "Netherlands":            ["Netherlands", "Holland", "Países Baixos", "Holanda"],
    "New Zealand":            ["New Zealand", "Nova Zelândia"],
    "Norway":                 ["Norway", "Noruega"],
    "Panama":                 ["Panama", "Panamá"],
    "Paraguay":               ["Paraguay", "Paraguai"],
    "Portugal":               ["Portugal"],
    "Qatar":                  ["Qatar", "Catar"],
    "Saudi Arabia":           ["Saudi Arabia", "Arábia Saudita"],
    "Scotland":               ["Scotland", "Escócia"],
    "Senegal":                ["Senegal"],
    "South Africa":           ["South Africa", "África do Sul", "Sudafrica"],
    "South Korea":            ["South Korea", "Korea Republic", "República da Coreia",
                               "Coreia do Sul", "Corea del Sur"],
    "Spain":                  ["Spain", "Espanha", "España"],
    "Sweden":                 ["Sweden", "Suécia"],
    "Switzerland":            ["Switzerland", "Suíça", "Suisse", "Suiza"],
    "Tunisia":                ["Tunisia", "Tunísia"],
    "Turkey":                 ["Turkey", "Turquia", "Türkiye"],
    "Uruguay":                ["Uruguay", "Uruguai"],
    "USA":                    ["USA", "United States", "Estados Unidos", "US"],
    "Uzbekistan":             ["Uzbekistan", "Uzbequistão"],
    "Algeria":                ["Algeria", "Argélia", "Argelia"],
}

_ALIAS_TO_STANDARD: dict[str, str] = {}
for _std, _aliases in SQUAD_NAME_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_TO_STANDARD[_alias.lower().strip()] = _std

# ─────────────────────────────────────────────────────────────────────────────
# MAPEAMENTO EA FC
# ─────────────────────────────────────────────────────────────────────────────
EA_NATION_MAP: dict[str, str] = {
    "Argentina": "Argentina", "Australia": "Australia", "Austria": "Austria",
    "Belgium": "Belgium", "Bosnia and Herzegovina": "Bosnia & Herzegovina",
    "Brazil": "Brazil", "Canada": "Canada", "Cape Verde": "Cape Verde",
    "Colombia": "Colombia", "Croatia": "Croatia", "Czechia": "Czech Republic",
    "Curaçao": "Curaçao", "DR Congo": "DR Congo", "Ecuador": "Ecuador",
    "Egypt": "Egypt", "England": "England", "France": "France",
    "Germany": "Germany", "Ghana": "Ghana", "Haiti": "Haiti",
    "Iran": "IR Iran", "Iraq": "Iraq", "Ivory Coast": "Ivory Coast",
    "Japan": "Japan", "Jordan": "Jordan", "Mexico": "Mexico",
    "Morocco": "Morocco", "Netherlands": "Netherlands", "New Zealand": "New Zealand",
    "Norway": "Norway", "Panama": "Panama", "Paraguay": "Paraguay",
    "Portugal": "Portugal", "Qatar": "Qatar", "Saudi Arabia": "Saudi Arabia",
    "Scotland": "Scotland", "Senegal": "Senegal", "South Africa": "South Africa",
    "South Korea": "Korea Republic", "Spain": "Spain", "Sweden": "Sweden",
    "Switzerland": "Switzerland", "Tunisia": "Tunisia", "Turkey": "Turkey",
    "Uruguay": "Uruguay", "USA": "USA", "Uzbekistan": "Uzbekistan",
    "Algeria": "Algeria",
}

# ─────────────────────────────────────────────────────────────────────────────
# ELENCOS GENÉRICOS DE FALLBACK
# ─────────────────────────────────────────────────────────────────────────────
GENERIC_SQUADS: dict[str, dict] = {
    "France": {
        "Goalkeeper":  [{"name": "Mike Maignan",        "rating": 8.7, "position": "Goalkeeper"}],
        "Defender":    [{"name": "William Saliba",       "rating": 8.5, "position": "Defender"},
                        {"name": "Dayot Upamecano",      "rating": 8.2, "position": "Defender"},
                        {"name": "Theo Hernandez",       "rating": 8.3, "position": "Defender"},
                        {"name": "Jules Koundé",         "rating": 8.4, "position": "Defender"}],
        "Midfielder":  [{"name": "Aurélien Tchouaméni",  "rating": 8.3, "position": "Midfielder"},
                        {"name": "Adrien Rabiot",        "rating": 8.0, "position": "Midfielder"},
                        {"name": "Antoine Griezmann",    "rating": 8.6, "position": "Midfielder"}],
        "Attacker":    [{"name": "Kylian Mbappé",        "rating": 9.3, "position": "Attacker"},
                        {"name": "Ousmane Dembélé",      "rating": 8.5, "position": "Attacker"},
                        {"name": "Marcus Thuram",        "rating": 8.2, "position": "Attacker"}],
    },
    "Portugal": {
        "Goalkeeper":  [{"name": "Diogo Costa",          "rating": 8.5, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Rúben Dias",           "rating": 8.7, "position": "Defender"},
                        {"name": "Pepe",                 "rating": 7.8, "position": "Defender"},
                        {"name": "Nuno Mendes",          "rating": 8.3, "position": "Defender"},
                        {"name": "João Cancelo",         "rating": 8.4, "position": "Defender"}],
        "Midfielder":  [{"name": "Bernardo Silva",       "rating": 8.9, "position": "Midfielder"},
                        {"name": "Bruno Fernandes",      "rating": 8.7, "position": "Midfielder"},
                        {"name": "Vitinha",              "rating": 8.2, "position": "Midfielder"}],
        "Attacker":    [{"name": "Cristiano Ronaldo",    "rating": 8.8, "position": "Attacker"},
                        {"name": "Rafael Leão",          "rating": 8.6, "position": "Attacker"},
                        {"name": "Gonçalo Ramos",        "rating": 8.3, "position": "Attacker"}],
    },
    "Germany": {
        "Goalkeeper":  [{"name": "Manuel Neuer",         "rating": 8.6, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Antonio Rüdiger",      "rating": 8.5, "position": "Defender"},
                        {"name": "Jonathan Tah",         "rating": 8.1, "position": "Defender"},
                        {"name": "David Raum",           "rating": 8.0, "position": "Defender"},
                        {"name": "Joshua Kimmich",       "rating": 8.8, "position": "Defender"}],
        "Midfielder":  [{"name": "Florian Wirtz",        "rating": 8.8, "position": "Midfielder"},
                        {"name": "Jamal Musiala",        "rating": 8.9, "position": "Midfielder"},
                        {"name": "Toni Kroos",           "rating": 8.7, "position": "Midfielder"}],
        "Attacker":    [{"name": "Kai Havertz",          "rating": 8.3, "position": "Attacker"},
                        {"name": "Leroy Sané",           "rating": 8.4, "position": "Attacker"},
                        {"name": "Thomas Müller",        "rating": 8.2, "position": "Attacker"}],
    },
    "Spain": {
        "Goalkeeper":  [{"name": "Unai Simón",           "rating": 8.4, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Dani Carvajal",        "rating": 8.5, "position": "Defender"},
                        {"name": "Aymeric Laporte",      "rating": 8.3, "position": "Defender"},
                        {"name": "Pau Cubarsí",          "rating": 8.2, "position": "Defender"},
                        {"name": "Alejandro Grimaldo",   "rating": 8.4, "position": "Defender"}],
        "Midfielder":  [{"name": "Rodri",                "rating": 9.1, "position": "Midfielder"},
                        {"name": "Pedri",                "rating": 8.9, "position": "Midfielder"},
                        {"name": "Fabián Ruiz",          "rating": 8.6, "position": "Midfielder"}],
        "Attacker":    [{"name": "Lamine Yamal",         "rating": 8.8, "position": "Attacker"},
                        {"name": "Nico Williams",        "rating": 8.6, "position": "Attacker"},
                        {"name": "Álvaro Morata",        "rating": 8.2, "position": "Attacker"}],
    },
    "Argentina": {
        "Goalkeeper":  [{"name": "Emiliano Martínez",   "rating": 9.0, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Cristian Romero",      "rating": 8.5, "position": "Defender"},
                        {"name": "Lisandro Martínez",    "rating": 8.4, "position": "Defender"},
                        {"name": "Nicolás Otamendi",     "rating": 8.0, "position": "Defender"},
                        {"name": "Nahuel Molina",        "rating": 8.1, "position": "Defender"}],
        "Midfielder":  [{"name": "Rodrigo De Paul",      "rating": 8.4, "position": "Midfielder"},
                        {"name": "Enzo Fernández",       "rating": 8.5, "position": "Midfielder"},
                        {"name": "Alexis Mac Allister",  "rating": 8.6, "position": "Midfielder"}],
        "Attacker":    [{"name": "Lionel Messi",         "rating": 9.3, "position": "Attacker"},
                        {"name": "Lautaro Martínez",     "rating": 8.8, "position": "Attacker"},
                        {"name": "Julián Álvarez",       "rating": 8.5, "position": "Attacker"}],
    },
    "England": {
        "Goalkeeper":  [{"name": "Jordan Pickford",      "rating": 8.3, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Kyle Walker",          "rating": 8.2, "position": "Defender"},
                        {"name": "John Stones",          "rating": 8.3, "position": "Defender"},
                        {"name": "Harry Maguire",        "rating": 7.9, "position": "Defender"},
                        {"name": "Luke Shaw",            "rating": 8.0, "position": "Defender"}],
        "Midfielder":  [{"name": "Jude Bellingham",      "rating": 9.0, "position": "Midfielder"},
                        {"name": "Declan Rice",          "rating": 8.7, "position": "Midfielder"},
                        {"name": "Phil Foden",           "rating": 8.8, "position": "Midfielder"}],
        "Attacker":    [{"name": "Harry Kane",           "rating": 9.0, "position": "Attacker"},
                        {"name": "Bukayo Saka",          "rating": 8.8, "position": "Attacker"},
                        {"name": "Marcus Rashford",      "rating": 8.3, "position": "Attacker"}],
    },
    "Netherlands": {
        "Goalkeeper":  [{"name": "Bart Verbruggen",      "rating": 8.0, "position": "Goalkeeper"}],
        "Defender":    [{"name": "Virgil van Dijk",      "rating": 8.9, "position": "Defender"},
                        {"name": "Stefan de Vrij",       "rating": 8.1, "position": "Defender"},
                        {"name": "Denzel Dumfries",      "rating": 8.2, "position": "Defender"},
                        {"name": "Nathan Aké",           "rating": 8.2, "position": "Defender"}],
        "Midfielder":  [{"name": "Frenkie de Jong",      "rating": 8.7, "position": "Midfielder"},
                        {"name": "Tijjani Reijnders",    "rating": 8.5, "position": "Midfielder"},
                        {"name": "Xavi Simons",          "rating": 8.6, "position": "Midfielder"}],
        "Attacker":    [{"name": "Cody Gakpo",           "rating": 8.5, "position": "Attacker"},
                        {"name": "Donyell Malen",        "rating": 8.2, "position": "Attacker"},
                        {"name": "Wout Weghorst",        "rating": 8.0, "position": "Attacker"}],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
WORLD_CUP_2026_TEAMS = {
    "Mexico":                 {"group": "A"}, "South Korea":    {"group": "A"},
    "South Africa":           {"group": "A"}, "Czechia":        {"group": "A"},
    "Canada":                 {"group": "B"}, "Bosnia and Herzegovina": {"group": "B"},
    "Qatar":                  {"group": "B"}, "Switzerland":    {"group": "B"},
    "Brazil":                 {"group": "C"}, "Morocco":        {"group": "C"},
    "Haiti":                  {"group": "C"}, "Scotland":       {"group": "C"},
    "USA":                    {"group": "D"}, "Paraguay":       {"group": "D"},
    "Australia":              {"group": "D"}, "Turkey":         {"group": "D"},
    "Germany":                {"group": "E"}, "Curaçao":        {"group": "E"},
    "Ivory Coast":            {"group": "E"}, "Ecuador":        {"group": "E"},
    "Netherlands":            {"group": "F"}, "Japan":          {"group": "F"},
    "Sweden":                 {"group": "F"}, "Tunisia":        {"group": "F"},
    "Belgium":                {"group": "G"}, "Egypt":          {"group": "G"},
    "Iran":                   {"group": "G"}, "New Zealand":    {"group": "G"},
    "Spain":                  {"group": "H"}, "Cape Verde":     {"group": "H"},
    "Saudi Arabia":           {"group": "H"}, "Uruguay":        {"group": "H"},
    "France":                 {"group": "I"}, "Senegal":        {"group": "I"},
    "Iraq":                   {"group": "I"}, "Norway":         {"group": "I"},
    "Argentina":              {"group": "J"}, "Algeria":        {"group": "J"},
    "Austria":                {"group": "J"}, "Jordan":         {"group": "J"},
    "Portugal":               {"group": "K"}, "DR Congo":       {"group": "K"},
    "Uzbekistan":             {"group": "K"}, "Colombia":       {"group": "K"},
    "England":                {"group": "L"}, "Croatia":        {"group": "L"},
    "Ghana":                  {"group": "L"}, "Panama":         {"group": "L"},
}

ELO_RATINGS_CONFIRMED = {
    "Spain": 2165, "Argentina": 2113, "France": 2081, "England": 2020, "Brazil": 1988,
    "Portugal": 1984, "Colombia": 1977, "Netherlands": 1961, "Ecuador": 1935, "Croatia": 1930,
    "Germany": 1925, "Norway": 1917, "Turkey": 1906, "Japan": 1906, "Switzerland": 1894,
    "Uruguay": 1892, "Denmark": 1870, "Mexico": 1868, "Belgium": 1866, "Senegal": 1866,
    "Italy": 1856, "Paraguay": 1833, "Austria": 1830, "Morocco": 1822, "Canada": 1793,
    "Ukraine": 1785, "Australia": 1775, "Scotland": 1770, "Nigeria": 1769, "Russia": 1766,
    "Iran": 1764, "South Korea": 1756, "Greece": 1752, "Algeria": 1743, "Serbia": 1742,
    "Czechia": 1733, "United States": 1733, "USA": 1733, "Panama": 1733, "Venezuela": 1727,
    "Uzbekistan": 1718, "Sweden": 1714, "Kosovo": 1714, "Poland": 1711, "Chile": 1710,
    "Hungary": 1703, "Egypt": 1699, "Wales": 1698, "Peru": 1695, "Slovenia": 1694,
    "Ireland": 1694, "Jordan": 1685, "Ivory Coast": 1676, "Slovakia": 1674, "DR Congo": 1655,
    "Georgia": 1653, "Albania": 1646, "Bolivia": 1645, "Israel": 1634, "Tunisia": 1633,
    "Romania": 1627, "Cameroon": 1614, "Costa Rica": 1612, "Iraq": 1608, "Northern Ireland": 1601,
    "Mali": 1596, "Bosnia and Herzegovina": 1591, "North Macedonia": 1589, "New Zealand": 1585,
    "Cape Verde": 1576, "Honduras": 1571, "Iceland": 1569, "Saudi Arabia": 1566, "Angola": 1543,
    "Finland": 1540, "United Arab Emirates": 1540, "Haiti": 1532, "Burkina Faso": 1530,
    "Jamaica": 1527, "South Africa": 1517, "Guatemala": 1514, "Belarus": 1513, "Ghana": 1503,
    "Syria": 1491, "Oman": 1490, "Guinea": 1469, "Palestine": 1469, "Bulgaria": 1461,
    "Montenegro": 1453, "Luxembourg": 1436, "Curaçao": 1433, "Suriname": 1431, "Kazakhstan": 1430,
    "Benin": 1429, "China": 1423, "Qatar": 1423, "Libya": 1420, "Bahrain": 1418, "Gambia": 1418,
    "Gabon": 1401, "Uganda": 1394, "Niger": 1393, "Equatorial Guinea": 1390,
    "Trinidad and Tobago": 1388, "Madagascar": 1382, "Armenia": 1379, "Thailand": 1376,
    "North Korea": 1375, "Zimbabwe": 1372, "Mozambique": 1372, "Zambia": 1370, "Comoros": 1362,
    "Togo": 1358, "Kenya": 1356, "Vietnam": 1351, "Sudan": 1350, "Sierra Leone": 1348,
    "El Salvador": 1342, "Azerbaijan": 1340, "Estonia": 1339, "Rwanda": 1336, "Nicaragua": 1334,
    "Lebanon": 1332, "Indonesia": 1331, "Kuwait": 1328, "Tanzania": 1313, "Mauritania": 1311,
    "Namibia": 1303, "Latvia": 1301, "Cyprus": 1301, "Liberia": 1296, "Malaysia": 1293,
    "Lithuania": 1291, "Kyrgyzstan": 1291, "Tajikistan": 1285, "Burundi": 1285, "Ethiopia": 1285,
    "Dominican Republic": 1284, "Botswana": 1267, "Moldova": 1262, "Guinea-Bissau": 1248,
    "Malawi": 1241, "Cuba": 1239, "Central African Republic": 1237, "Malta": 1236,
    "Turkmenistan": 1209, "Congo": 1207, "Lesotho": 1205, "Eritrea": 1201, "Philippines": 1167,
    "Yemen": 1151, "Singapore": 1139, "India": 1128, "Hong Kong": 1120, "South Sudan": 1109,
}

HISTORICAL_GOALS_AVG: dict[str, dict] = {
    "Spain":       {"scored": 2.1, "conceded": 0.7},
    "Argentina":   {"scored": 2.0, "conceded": 0.8},
    "France":      {"scored": 1.9, "conceded": 0.9},
    "England":     {"scored": 1.8, "conceded": 0.8},
    "Brazil":      {"scored": 1.9, "conceded": 0.9},
    "Portugal":    {"scored": 2.0, "conceded": 0.9},
    "Germany":     {"scored": 2.0, "conceded": 1.1},
    "Netherlands": {"scored": 1.9, "conceded": 1.0},
    "Colombia":    {"scored": 1.7, "conceded": 0.9},
    "Croatia":     {"scored": 1.5, "conceded": 0.9},
    "Norway":      {"scored": 2.1, "conceded": 1.1},
    "Belgium":     {"scored": 1.8, "conceded": 1.0},
    "Uruguay":     {"scored": 1.6, "conceded": 0.9},
    "Ecuador":     {"scored": 1.5, "conceded": 1.0},
    "Japan":       {"scored": 1.7, "conceded": 1.1},
    "Mexico":      {"scored": 1.6, "conceded": 1.1},
    "USA":         {"scored": 1.5, "conceded": 1.1},
    "Switzerland": {"scored": 1.6, "conceded": 1.0},
    "Morocco":     {"scored": 1.3, "conceded": 0.8},
    "Senegal":     {"scored": 1.4, "conceded": 1.0},
    "Turkey":      {"scored": 1.6, "conceded": 1.2},
    "Australia":   {"scored": 1.4, "conceded": 1.2},
    "Canada":      {"scored": 1.5, "conceded": 1.1},
    "South Korea": {"scored": 1.5, "conceded": 1.1},
    "Sweden":      {"scored": 1.5, "conceded": 1.1},
    "Scotland":    {"scored": 1.4, "conceded": 1.2},
    "Austria":     {"scored": 1.6, "conceded": 1.1},
    "Algeria":     {"scored": 1.4, "conceded": 1.1},
    "Paraguay":    {"scored": 1.3, "conceded": 1.2},
    "Iran":        {"scored": 1.3, "conceded": 1.1},
}
_DEFAULT_GOALS = {"scored": 1.2, "conceded": 1.2}


def _get_historical_goals(team: str) -> dict:
    return HISTORICAL_GOALS_AVG.get(team, _DEFAULT_GOALS)


class DataLoader:
    def __init__(self):
        self.players_db   = self._load_csv(EAFC_CSV_PATH,      "EA FC 26")
        self.tm_players   = self._load_csv(TM_PLAYERS_CSV,     "Transfermarkt Players")
        self.tm_goals     = self._load_csv(TM_GOALSCORERS_CSV, "Transfermarkt Goalscorers")
        self.recent_goals_dict = self._build_recent_goals_dict()
        self.squads_dict  = self._parse_convocados()
        self.cache: dict  = {}

    def _load_csv(self, path: Path, name: str) -> pd.DataFrame:
        if not path.exists():
            print(f"[DataLoader] AVISO: {name} não encontrado em {path}")
            return pd.DataFrame()
        return pd.read_csv(path, low_memory=False)

    def _build_recent_goals_dict(self) -> dict:
        if self.tm_goals.empty:
            return {}
        try:
            self.tm_goals["date"] = pd.to_datetime(self.tm_goals["date"], errors="coerce")
            recent = self.tm_goals[self.tm_goals["date"].dt.year >= 2024]
            return recent["scorer"].value_counts().to_dict()
        except Exception:
            return {}

    @staticmethod
    def _extract_team_name_from_header(raw_line: str) -> str:
        line = raw_line.strip().strip("'\"«»")
        result = re.sub(
            r"['\u2019]s\b.*$"          
            r"|\bfor\s+the\b.*$"        
            r"|\bWorld\s+Cup\b.*$"      
            r"|\b2026\b.*$"             
            r"|\b(Squad|Roster|Elenco|Convocatoria|Convocados)\b.*$",
            "", line, flags=re.IGNORECASE
        ).strip().strip("'\"").strip()
        return result

    def _parse_convocados(self) -> dict:
        squads: dict = {}
        if not CONVOCADOS_PATH.exists():
            print(f"[DataLoader] AVISO: {CONVOCADOS_PATH} não encontrado.")
            return squads

        with open(CONVOCADOS_PATH, "r", encoding="utf-8") as fh:
            lines = fh.readlines()

        current_team: str | None = None

        HEADER_KEYWORDS = (
            "squad", "roster", "elenco", "convocados", "convocatoria",
            "world cup squad", "world cup roster",
        )

        pos_map = {
            "goalkeeper":     "Goalkeeper",
            "goalkeepers":    "Goalkeeper",
            "defender":       "Defender",
            "defenders":      "Defender",
            "midfielder":     "Midfielder",
            "midfielders":    "Midfielder",
            "centrocampista": "Midfielder",
            "centrocampistas":"Midfielder",
            "forward":        "Attacker",
            "forwards":       "Attacker",
            "attacker":       "Attacker",
            "attackers":      "Attacker",
            "delantero":      "Attacker",
            "delanteros":     "Attacker",
        }

        for raw_line in lines:
            line = raw_line.strip()
            if not line: continue

            line_lower = line.lower()
            is_header = any(kw in line_lower for kw in HEADER_KEYWORDS)
            is_group_line = re.match(r'^group\s+[a-l]$', line_lower.strip())

            if is_group_line: continue

            if is_header:
                raw_name = self._extract_team_name_from_header(line)
                if not raw_name or raw_name.startswith('*') or len(raw_name) < 3:
                    continue

                std_name = _ALIAS_TO_STANDARD.get(raw_name.lower())
                if std_name is None:
                    candidates = list(_ALIAS_TO_STANDARD.keys())
                    fuzzy = get_close_matches(raw_name.lower(), candidates, n=1, cutoff=0.75)
                    std_name = _ALIAS_TO_STANDARD[fuzzy[0]] if fuzzy else raw_name

                current_team = std_name
                if current_team not in squads:
                    squads[current_team] = {
                        "Goalkeeper": [], "Defender": [],
                        "Midfielder": [], "Attacker": [],
                    }
                continue

            if current_team is None: continue

            colon_pos = line.find(":")
            if colon_pos <= 0: continue

            keyword = line[:colon_pos].strip().lower()
            if keyword not in pos_map: continue

            pos_value = pos_map[keyword]
            names_str = line[colon_pos + 1:]

            players = self._parse_player_names(names_str)
            squads[current_team][pos_value].extend(players)

        total = len(squads)
        print(f"[DataLoader] convocados_2026.txt: {total} seleções carregadas.")
        empty = [t for t, d in squads.items() if all(len(v) == 0 for v in d.values())]
        if empty:
            print(f"[DataLoader] AVISO: times sem jogadores detectados: {empty}")
        return squads

    @staticmethod
    def _parse_player_names(names_str: str) -> list[str]:
        """
        Nova Estratégia de Parse (100% blindada a idiomas e caracteres estendidos).
        Corta as vírgulas e "and", e captura tudo o que estiver antes do parêntese.
        Acabou o problema com Džeko e N'Golo Kanté!
        """
        if '(' in names_str:
            parts = re.split(r',|\band\b|\be\b|\by\b', names_str, flags=re.IGNORECASE)
            result = []
            for p in parts:
                idx = p.find('(')
                if idx > 0:
                    n = p[:idx].strip()
                    n = n.rstrip('*').strip()
                    if len(n) > 2 and not n.isdigit():
                        result.append(n)
            if result:
                return result

        # Estratégia 2: sem clube
        no_parens = re.sub(r'\(.*?\)', '', names_str)
        no_parens = re.sub(r'\*[^\,]*', '', no_parens)
        parts = re.split(r',|\band\b|\be\b|\by\b', no_parens, flags=re.IGNORECASE)
        result = []
        for p in parts:
            p = p.strip().strip('.').strip('"\'').strip()
            if len(p) > 2 and not p.isdigit():
                result.append(p)
        return result

    def _get_player_true_rating(self, p_name: str, ea_nation: str) -> float:
        base_rating        = 7.0
        market_value_bonus = 0.0
        goals_bonus        = 0.0

        if not self.players_db.empty:
            nat_col = "Nationality" if "Nationality" in self.players_db.columns else None
            if nat_col:
                nat_df = self.players_db[
                    self.players_db[nat_col].str.contains(ea_nation, case=False, na=False)
                ]
            else:
                nat_df = self.players_db

            if not nat_df.empty:
                ea_names = nat_df["Name"].dropna().tolist()
                match_ea = get_close_matches(p_name, ea_names, n=1, cutoff=0.60)
                if match_ea:
                    row = nat_df[nat_df["Name"] == match_ea[0]].iloc[0]
                    base_rating = float(row.get("OVR", 70)) / 10.0

        if not self.tm_players.empty:
            tm_names = self.tm_players["name"].dropna().astype(str).tolist()
            match_tm = get_close_matches(p_name, tm_names, n=1, cutoff=0.65)
            if match_tm:
                tm_row = self.tm_players[self.tm_players["name"] == match_tm[0]].iloc[0]
                value = tm_row.get("market_value_in_eur", 0)
                if pd.notna(value):
                    v = float(value)
                    if   v >= 80_000_000: market_value_bonus = 0.8
                    elif v >= 50_000_000: market_value_bonus = 0.5
                    elif v >= 20_000_000: market_value_bonus = 0.3
                    elif v >=  5_000_000: market_value_bonus = 0.1

        goals_recentes = 0
        for name_key, gols in self.recent_goals_dict.items():
            if isinstance(name_key, str) and (p_name in name_key or name_key in p_name):
                goals_recentes += gols
        if   goals_recentes >= 10: goals_bonus = 0.6
        elif goals_recentes >=  5: goals_bonus = 0.3
        elif goals_recentes >=  2: goals_bonus = 0.1

        return round(min(9.9, base_rating + market_value_bonus + goals_bonus), 2)

    def get_real_squad_data(self, team_name: str) -> dict:
        if team_name in self.cache:
            return self.cache[team_name]

        base_data = {
            "squad_rating": 7.0, "injured_count": 0, "form_2026": 10,
            "top_players": [], "bench_players": [],
            "data_source": "Lista Oficial Convocados",
        }

        dict_team_name = team_name
        if team_name not in self.squads_dict:
            team_lower = team_name.lower()
            std = _ALIAS_TO_STANDARD.get(team_lower)
            if std and std in self.squads_dict:
                dict_team_name = std
            else:
                keys = list(self.squads_dict.keys())
                fuzzy = get_close_matches(team_name, keys, n=1, cutoff=0.80)
                dict_team_name = fuzzy[0] if fuzzy else None

        ea_nation = EA_NATION_MAP.get(team_name, team_name)
        official_roster: list[dict] = []

        if dict_team_name and dict_team_name in self.squads_dict:
            for pos, players_list in self.squads_dict[dict_team_name].items():
                for p_name in players_list:
                    rating = self._get_player_true_rating(p_name, ea_nation)
                    official_roster.append({"name": p_name, "rating": rating, "position": pos})

        if not official_roster:
            if team_name in GENERIC_SQUADS:
                for pos, players_list in GENERIC_SQUADS[team_name].items():
                    official_roster.extend(players_list)
                base_data["data_source"] = "Elenco Genérico (fallback)"
                print(f"[DataLoader] {team_name}: usando elenco genérico de fallback.")
            else:
                base_data["data_source"] = "Elenco Genérico Mínimo"
                base_data["squad_rating"] = self._elo_to_squad_rating(
                    ELO_RATINGS_CONFIRMED.get(team_name, 1600)
                )
                starters = self._build_minimal_squad(team_name)
                base_data["top_players"] = starters
                self.cache[team_name] = base_data
                return base_data

        official_roster.sort(key=lambda x: x["rating"], reverse=True)

        gks  = [p for p in official_roster if p["position"] == "Goalkeeper"]
        defs = [p for p in official_roster if p["position"] == "Defender"]
        mids = [p for p in official_roster if p["position"] == "Midfielder"]
        atts = [p for p in official_roster if p["position"] == "Attacker"]

        starters = gks[:1] + defs[:4] + mids[:3] + atts[:3]
        if len(starters) < 11:
            used_names = {p["name"] for p in starters}
            for p in official_roster:
                if p["name"] not in used_names:
                    starters.append(p)
                    used_names.add(p["name"])
                    if len(starters) == 11:
                        break

        used_names = {p["name"] for p in starters}
        bench      = [p for p in official_roster if p["name"] not in used_names]
        avg_rating = sum(p["rating"] for p in starters) / len(starters) if starters else 7.0

        base_data["squad_rating"]  = round(avg_rating, 2)
        base_data["top_players"]   = starters
        base_data["bench_players"] = bench
        self.cache[team_name]      = base_data
        return base_data

    @staticmethod
    def _elo_to_squad_rating(elo: float) -> float:
        return round(min(9.5, max(6.5, 6.5 + (elo - 1400) / (2200 - 1400) * 3.0)), 2)

    @staticmethod
    def _build_minimal_squad(team_name: str) -> list[dict]:
        positions = (
            [("Goalkeeper", "GK")] +
            [("Defender",   f"DEF{i}") for i in range(1, 5)] +
            [("Midfielder", f"MID{i}") for i in range(1, 4)] +
            [("Attacker",   f"ATT{i}") for i in range(1, 4)]
        )
        elo  = ELO_RATINGS_CONFIRMED.get(team_name, 1600)
        base = DataLoader._elo_to_squad_rating(elo)
        squad = []
        for pos, suffix in positions:
            r = base - 0.5 if pos == "Goalkeeper" else base
            squad.append({"name": f"{team_name[:3].upper()} {suffix}", "rating": round(r, 2), "position": pos})
        return squad

    def get_all_teams(self) -> dict:
        return WORLD_CUP_2026_TEAMS

    def get_team_elo(self, team_name: str) -> float:
        return float(ELO_RATINGS_CONFIRMED.get(team_name, 1600.0))

    def get_historical_goals(self, team_name: str) -> dict:
        return _get_historical_goals(team_name)

    def get_world_cup_fixtures(self) -> list:
        fixtures = []
        groups = {}
        for team, info in WORLD_CUP_2026_TEAMS.items():
            g = info["group"]
            groups.setdefault(g, []).append(team)

        import itertools
        round_dates = {
            "A": ["2026-06-11", "2026-06-15", "2026-06-19"],
            "B": ["2026-06-12", "2026-06-16", "2026-06-20"],
            "C": ["2026-06-12", "2026-06-16", "2026-06-20"],
            "D": ["2026-06-13", "2026-06-17", "2026-06-21"],
            "E": ["2026-06-13", "2026-06-17", "2026-06-21"],
            "F": ["2026-06-14", "2026-06-18", "2026-06-22"],
            "G": ["2026-06-14", "2026-06-18", "2026-06-22"],
            "H": ["2026-06-15", "2026-06-19", "2026-06-23"],
            "I": ["2026-06-15", "2026-06-19", "2026-06-23"],
            "J": ["2026-06-16", "2026-06-20", "2026-06-24"],
            "K": ["2026-06-16", "2026-06-20", "2026-06-24"],
            "L": ["2026-06-17", "2026-06-21", "2026-06-25"],
        }

        for grp, teams in sorted(groups.items()):
            matchups = list(itertools.combinations(teams, 2))
            dates = round_dates.get(grp, ["2026-06-20"] * 6)
            for idx, (home, away) in enumerate(matchups):
                round_num = min(idx, len(dates) - 1)
                fixtures.append({
                    "utcDate":  dates[round_num] + "T20:00:00Z",
                    "group":    f"Grupo {grp}",
                    "homeTeam": {"name": home},
                    "awayTeam": {"name": away},
                })
        return fixtures
    