import sys
print("\n[START] 1. O Python acordou e começou a ler o arquivo test_apis.py...")

try:
    import os
    import requests
    from dotenv import load_dotenv
    from api_clients.football_api import APIFootball, FootballDataOrg, TheOddsAPI

    print("[START] 2. Bibliotecas importadas com sucesso.")

    load_dotenv()
    print("\n=== INICIANDO DIAGNÓSTICO COMPLETO DAS 3 APIS + CLIMA ===\n")

    # 1. API-Football
    print("1️⃣ Testando API-Football (Estatísticas/Lesões)...")
    api_football_key = os.getenv("API_FOOTBALL_KEY")
    if api_football_key and api_football_key not in ["", "CHAVE REAL", "SUA_CHAVE_AQUI"]:
        api_f = APIFootball(api_football_key)
        stats = api_f.get_team_statistics(team_id=2, season=2022)
        if stats:
            print("   ✅ SUCESSO! Conectado à API-Football e Cache salvo.\n")
        else:
            print("   ❌ ERRO: A chave existe, mas o site recusou.\n")
    else:
        print("   ⚠️ AVISO: Sem chave válida para a API-Football.\n")

    # 2. Football-Data.org
    print("2️⃣ Testando Football-Data.org (Tabelas de Jogos)...")
    fd_key = os.getenv("FOOTBALL_DATA_KEY")
    if fd_key and fd_key not in ["", "CHAVE REAL", "SUA_CHAVE_AQUI"]:
        fd_api = FootballDataOrg(fd_key)
        matches = fd_api.get_competition_matches()
        if matches is not None:
            print(f"   ✅ SUCESSO! Conectado à Football-Data. Jogos lidos: {len(matches)}\n")
        else:
            print("   ❌ ERRO: A chave existe, mas o site recusou.\n")
    else:
        print("   ⚠️ AVISO: Sem chave válida para a Football-Data.\n")

    # 3. The Odds API
    print("3️⃣ Testando The Odds API (Mercado de Apostas)...")
    odds_key = os.getenv("ODDS_API_KEY")
    if odds_key and odds_key not in ["", "CHAVE REAL", "SUA_CHAVE_AQUI"]:
        odds_api = TheOddsAPI(odds_key)
        odds = odds_api.get_world_cup_odds()
        if odds is not None:
            print("   ✅ SUCESSO! Conectado à The Odds API e Cache salvo.\n")
        else:
            print("   ❌ ERRO: A chave existe, mas o site recusou.\n")
    else:
        print("   ⚠️ AVISO: Sem chave válida para a The Odds API.\n")

    # 4. Open-Meteo (Clima)
    print("4️⃣ Testando API de Clima Real (Hard Rock Stadium, Miami)...")
    url = "https://api.open-meteo.com/v1/forecast?latitude=25.9580&longitude=-80.2389&current_weather=true"
    r = requests.get(url, timeout=5)
    if r.status_code == 200:
        temp = r.json().get('current_weather', {}).get('temperature')
        print(f"   ✅ SUCESSO! A temperatura REAL AGORA no estádio em Miami é: {temp}°C\n")
    else:
        print("   ❌ ERRO: Falha ao contatar a API de Clima.\n")

    print("=== DIAGNÓSTICO TOTAL CONCLUÍDO ===")

except Exception as e:
    print(f"\n🚨 ERRO CRÍTICO DURANTE A EXECUÇÃO: {e}")