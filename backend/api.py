from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from models.simulator import MatchSimulator # Importa a sua classe original!

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
    # Puxa os dados reais dos elencos do seu DataLoader
    squad = simulator.feature_builder.data_loader.get_real_squad_data(team_name)
    top_players = [p["name"] for p in squad.get("top_players", [])]
    bench_players = [p["name"] for p in squad.get("bench_players", [])]
    return {"starters": top_players, "bench": bench_players}

# Modelo de dados que o frontend vai enviar
class MatchRequest(BaseModel):
    home: str
    away: str
    home_excluded: list = []
    away_excluded: list = []
    num_simulations: int = 200

# 2. Rota para rodar uma Partida Específica
@app.post("/api/simulate_match")
def api_simulate_match(req: MatchRequest):
    resultado = simulator.simulate_match(
        req.home, req.away, 
        num_simulations=req.num_simulations,
        home_excluded=req.home_excluded,
        away_excluded=req.away_excluded
    )
    return resultado

# 3. Rota para simular a Copa Inteira
@app.post("/api/simulate_tournament")
def api_simulate_tournament():
    resultado = simulator.run_full_tournament(num_tournaments=200)
    return resultado