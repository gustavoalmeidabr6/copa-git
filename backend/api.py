from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.simulator import MatchSimulator

app = FastAPI(title="World Cup Simulator API")

# Habilita o CORS para permitir que o frontend (na porta 5173) consiga acessar a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o seu simulador real pesado apenas uma vez ao ligar o servidor
print("Carregando o motor ML e dados de jogadores...")
simulator = MatchSimulator()

# 1. Rota para pegar a lista de times reais e jogadores
@app.get("/api/teams")
def get_teams():
    teams = sorted(simulator.teams_info.keys())
    return {"teams": teams}

@app.get("/api/roster/{team_name}")
def get_roster(team_name: str):
    # Puxa os dados reais dos elencos do DataLoader
    squad = simulator.feature_builder.data_loader.get_real_squad_data(team_name)
    
    # ─── CORREÇÃO TÁTICA ───
    # NÃO podemos ordenar os titulares por nota, senão destruímos o esquema tático.
    # A ordem que vem do DataLoader (API ou PREFERRED_STARTERS) já é a correta.
    top_players = [p["name"] for p in squad.get("top_players", [])]
    
    # Os reservas sim, podemos ordenar por nota para o banco ficar organizado:
    bench_players_data = sorted(
        squad.get("bench_players", []),
        key=lambda x: -x.get("rating", 7.0)
    )
    bench_players = [p["name"] for p in bench_players_data]
    # Coleta as posições reais para enviar ao frontend
    positions = {}
    for p in squad.get("top_players", []):
        positions[p["name"]] = p.get("position", "CM")
    for p in bench_players_data:
        positions[p["name"]] = p.get("position", "CM")
        
    return {"starters": top_players, "bench": bench_players, "positions": positions}

@app.get("/api/weather")
def get_weather(stadium: str):
    temp = simulator.feature_builder.get_weather(stadium)
    return {"stadium": stadium, "temperature": temp}

# Modelo de dados que o frontend vai enviar
class MatchRequest(BaseModel):
    home: str
    away: str
    home_excluded: list = []
    away_excluded: list = []
    home_starters: list = None
    away_starters: list = None
    stadium: str | None = None  # <-- ADICIONE ISTO
    num_simulations: int = 400  

# 2. Rota para rodar uma Partida Específica
@app.post("/api/simulate_match")
def api_simulate_match(req: MatchRequest):
    resultado = simulator.simulate_match(
        req.home, 
        req.away, 
        num_simulations=req.num_simulations, 
        home_excluded=req.home_excluded,
        away_excluded=req.away_excluded,
        stadium=req.stadium,
        home_starters=req.home_starters,
        away_starters=req.away_starters
    )
    return resultado

@app.on_event("startup")
def startup_event():
    # Removido: O loop agressivo na API no startup foi desligado. 
    # Agora a atualização ocorre magicamente e sob-demanda apenas ao clicar no botão "Última (API)".
    print("🚀 Servidor Quantizado online com motor de API sob-demanda!")

# 3. Rota para simular a Copa Inteira
@app.post("/api/simulate_tournament")
def api_simulate_tournament():
    # BLINDAGEM: Forçamos 400 no motor do torneio.
    resultado = simulator.run_full_tournament(num_tournaments=400) 
    return resultado