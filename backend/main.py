"""
main.py — VERSÃO v6 (A Versão Definitiva com Dashboard do Torneio)

MUDANÇAS:
  - Aba de Torneio reconstruída: Agora exibe um Dashboard Estatístico de Monte Carlo.
  - Botão para rodar 200 Copas do Mundo em tempo real.
  - Relatório formatado com Emojis mostrando Favoritos, Artilheiros, Garçons,
    Melhores Ataques/Defesas e a grande Zebra da Copa!
"""

import customtkinter as ctk
import threading
from models.simulator import MatchSimulator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class WorldCupApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("World Cup 2026 — Quant Simulator Pro")
        self.geometry("1200x860")

        try:
            self.simulator = MatchSimulator()
            self.teams     = sorted(self.simulator.teams_info.keys())
            self._check_gpu_info()
        except Exception as e:
            self.teams = []
            print(f"Erro fatal ao inicializar o simulador: {e}")

        self._build_ui()
        self._update_player_menus()  

    def _check_gpu_info(self):
        """Exibe info de GPU no console na inicialização."""
        import joblib
        from pathlib import Path
        model_path = Path(__file__).parent / "data" / "xgboost_model.pkl"
        try:
            payload = joblib.load(model_path)
            backend = payload.get("backend", "desconhecido")
            device  = payload.get("device", "cpu")
            print(f"\n{'='*50}")
            print(f"  Modelo carregado: {backend.upper().replace('_', ' ')}")
            print(f"  Dispositivo de treinamento: {device.upper()}")
            if device == "gpu" or device == "cuda":
                print("  ✅ GPU foi usada no treinamento!")
            else:
                print("  ⚠️  GPU NÃO foi usada. Execute o script de treino com GPU.")
            print(f"{'='*50}\n")
        except Exception:
            pass

    def _build_ui(self):
        ctk.CTkLabel(
            self,
            text="⚽  World Cup 2026 — Quant Simulator  ⚽",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=10)

        self.tabview = ctk.CTkTabview(self, width=1150, height=750)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        self.tabview.add("Partida Única")
        self.tabview.add("Simulação do Torneio (Monte Carlo)")

        self._build_single_match_tab()
        self._build_tournament_tab()

    # =========================================================================
    # ABA 1: PARTIDA ÚNICA (MANTIDA E MELHORADA)
    # =========================================================================
    def _build_single_match_tab(self):
        tab = self.tabview.tab("Partida Única")

        sel_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sel_frame.pack(pady=(12, 5))

        self.home_var = ctk.StringVar(value="Brazil")
        ctk.CTkOptionMenu(
            sel_frame, values=self.teams, variable=self.home_var, width=220,
            command=self._update_player_menus
        ).grid(row=0, column=0, padx=20)

        ctk.CTkLabel(
            sel_frame, text="  VS  ", font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=1)

        self.away_var = ctk.StringVar(value="France")
        ctk.CTkOptionMenu(
            sel_frame, values=self.teams, variable=self.away_var, width=220,
            command=self._update_player_menus
        ).grid(row=0, column=2, padx=20)

        excl_frame = ctk.CTkFrame(tab, fg_color="transparent")
        excl_frame.pack(pady=5)

        self.home_exclude_var = ctk.StringVar(value="Nenhum")
        self.home_excl_menu = ctk.CTkOptionMenu(
            excl_frame, variable=self.home_exclude_var, width=220
        )
        self.home_excl_menu.grid(row=0, column=0, padx=20)

        ctk.CTkLabel(
            excl_frame, text=" Desfalques ", font=ctk.CTkFont(size=13, weight="bold"), text_color="#aaaaaa"
        ).grid(row=0, column=1)

        self.away_exclude_var = ctk.StringVar(value="Nenhum")
        self.away_excl_menu = ctk.CTkOptionMenu(
            excl_frame, variable=self.away_exclude_var, width=220
        )
        self.away_excl_menu.grid(row=0, column=2, padx=20)

        self.sim_btn = ctk.CTkButton(
            tab, text="▶  Executar Simulação de Partida", height=42,
            command=self._start_single_sim,
        )
        self.sim_btn.pack(pady=12)

        self.single_text = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.single_text.pack(pady=5, padx=10, fill="both", expand=True)

    def _update_player_menus(self, *args):
        home_team = self.home_var.get()
        away_team = self.away_var.get()
        
        try:
            home_sq = self.simulator.feature_builder.data_loader.get_real_squad_data(home_team)
            home_names = ["Nenhum"] + sorted([p["name"] for p in home_sq.get("top_players", []) + home_sq.get("bench_players", [])])
        except Exception:
            home_names = ["Nenhum"]
            
        try:
            away_sq = self.simulator.feature_builder.data_loader.get_real_squad_data(away_team)
            away_names = ["Nenhum"] + sorted([p["name"] for p in away_sq.get("top_players", []) + away_sq.get("bench_players", [])])
        except Exception:
            away_names = ["Nenhum"]
            
        self.home_excl_menu.configure(values=home_names)
        self.away_excl_menu.configure(values=away_names)
        
        self.home_exclude_var.set("Nenhum")
        self.away_exclude_var.set("Nenhum")

    def _start_single_sim(self):
        home, away = self.home_var.get(), self.away_var.get()
        if home == away:
            self._write(self.single_text, "⚠️  Selecione times diferentes.")
            return

        home_excl = [self.home_exclude_var.get()] if self.home_exclude_var.get() != "Nenhum" else []
        away_excl = [self.away_exclude_var.get()] if self.away_exclude_var.get() != "Nenhum" else []

        self.sim_btn.configure(state="disabled", text="⏳  Simulando Partida…")
        threading.Thread(
            target=self._run_sim_logic,
            args=(home, away, home_excl, away_excl, self.single_text, self.sim_btn),
            daemon=True,
        ).start()

    def _run_sim_logic(
        self,
        home: str,
        away: str,
        home_excluded: list,
        away_excluded: list,
        textbox: ctk.CTkTextbox,
        btn: ctk.CTkButton,
    ):
        try:
            res = self.simulator.simulate_match(
                home, away, 
                num_simulations=200,
                home_excluded=home_excluded,
                away_excluded=away_excluded
            )

            scores_str = "\n".join(f"      {sc}: {pct:.1f}%" for sc, pct in res.get("most_likely_scores", {}).items())
            scorers_str = "\n".join(f"      {p}: {g} gols em 200 sim" for p, g in res.get("top_scorers", []))
            
            assists_str = "\n".join(f"      {p}: {a} assistências em 200 sim" for p, a in res.get("top_assists", []))
            if not assists_str: assists_str = "      Nenhuma assistência registrada."
            
            ratings_str = "\n".join(f"      {p}: {r:.2f} nota média" for p, r in res.get("top_ratings", []))

            stadium_info = f"{res.get('stadium', 'Miami')} | Temperatura: {res.get('temperature', 25)}°C"

            calib_str = (
                f"   λ (gols esperados): {home[:3].upper()} {res.get('home_lambda', 0):.2f}"
                f" | {away[:3].upper()} {res.get('away_lambda', 0):.2f}\n"
                f"   ELO: {home[:3].upper()} {int(res.get('home_elo', 0))}"
                f" | {away[:3].upper()} {int(res.get('away_elo', 0))}\n"
                f"   Modifier Squad Rating: {home[:3].upper()} ×{res.get('modifier_home', 1):.3f}"
                f" | {away[:3].upper()} ×{res.get('modifier_away', 1):.3f}"
            )

            excl_str = ""
            if home_excluded or away_excluded:
                excl_str = f"🛑 DESFALQUES APLICADOS:\n"
                if home_excluded: excl_str += f"   {home}: {', '.join(home_excluded)}\n"
                if away_excluded: excl_str += f"   {away}: {', '.join(away_excluded)}\n"
                excl_str += "\n"

            output = (
                f"=== RELATÓRIO QUANT (200 SIMULAÇÕES) ===\n"
                f"[{home}] vs [{away}]\n"
                f"🏟️  Sede: {stadium_info}\n\n"
                f"{excl_str}"
                f"🩺 STATUS DO ELENCO:\n"
                f"   {home}: Nota {res.get('home_rating', 0)} | ELO {int(res.get('home_elo', 0))} | Fonte: {res.get('home_data_source', 'N/A')}\n"
                f"   {away}: Nota {res.get('away_rating', 0)} | ELO {int(res.get('away_elo', 0))} | Fonte: {res.get('away_data_source', 'N/A')}\n\n"
                f"📊 CALIBRAÇÃO DO MODELO ML:\n{calib_str}\n\n"
                f"🎯 PROBABILIDADES ANALÍTICAS (sem variância):\n"
                f"   Vitória {home}: {res.get('home_win_prob', 0):.1f}% | Empate: {res.get('draw_prob', 0):.1f}% | Vitória {away}: {res.get('away_win_prob', 0):.1f}%\n\n"
                f"🔥 PLACAR PROVÁVEL MÉDIO (Média exata das 200 simulações):\n   >>> {res.get('expected_score', 'Indisponível')} <<<\n\n"
                f"🎲 PLACARES MAIS FREQUENTES (analítico):\n{scores_str}\n\n"
                f"🌟 ARTILHEIROS (200 simulações Monte Carlo):\n{scorers_str}\n\n"
                f"👟 GARÇONS / ASSISTÊNCIAS (Mais raras que gols):\n{assists_str}\n\n"
                f"⭐ MELHORES EM CAMPO (nota média):\n{ratings_str}\n\n"
                f"{'─'*46}\n"
                f"📋 LOG DAS 200 SIMULAÇÕES:\n"
            )
            output += "\n".join(res.get("sim_logs", []))

            self._write(textbox, output)

        except Exception as exc:
            import traceback
            self._write(textbox, f"❌ Erro:\n{exc}\n\n{traceback.format_exc()}")
        finally:
            try: btn.configure(state="normal", text="▶  Executar Simulação de Partida")
            except Exception: pass

    # =========================================================================
    # ABA 2: NOVO DASHBOARD DO TORNEIO (MONTE CARLO)
    # =========================================================================
    def _build_tournament_tab(self):
        tab = self.tabview.tab("Simulação do Torneio (Monte Carlo)")

        top_frame = ctk.CTkFrame(tab, fg_color="transparent")
        top_frame.pack(pady=15)

        ctk.CTkLabel(
            top_frame, 
            text="Simulação Quântica de 200 Copas do Mundo Simultâneas\n(Considera Zebras, Pênaltis e Cruzamentos Reais da FIFA)",
            font=ctk.CTkFont(size=14),
            justify="center"
        ).pack(pady=(0, 10))

        self.tourn_btn = ctk.CTkButton(
            top_frame, text="🌍  INICIAR MOTOR DE TORNEIOS (Processamento Pesado)", height=50,
            command=self._start_tournament_sim,
            fg_color="#8B0000", hover_color="#A52A2A"  # Um vermelho escuro para dar peso ao botão
        )
        self.tourn_btn.pack(pady=5)

        self.tourn_text = ctk.CTkTextbox(
            tab, font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word"
        )
        self.tourn_text.pack(pady=5, padx=20, fill="both", expand=True)

        instrucoes = (
            "📌 BEM-VINDO AO DASHBOARD DA COPA DO MUNDO\n\n"
            "Ao clicar no botão acima, o simulador fará o seguinte:\n"
            " 1. Criar os grupos oficiais da Copa 2026.\n"
            " 2. Rolar probabilidades para TODAS as 104 partidas do torneio.\n"
            " 3. Aplicar a roleta dos pênaltis nos mata-matas empatados.\n"
            " 4. Repetir esse processo 200 VEZES (simulando 20.800 partidas).\n\n"
            "Resultado esperado:\n"
            " - Você verá os maiores favoritos estatísticos a erguer a taça.\n"
            " - Estatísticas de artilheiros e garçons ao longo do torneio inteiro.\n"
            " - A 'Maior Zebra' matemática que pode chocar o mundo.\n\n"
            "⏳ Aguarde alguns segundos após o clique, a CPU trabalhará em 100%!"
        )
        self._write(self.tourn_text, instrucoes)

    def _start_tournament_sim(self):
        self.tourn_btn.configure(state="disabled", text="⏳  Simulando 200 Universos Paralelos... Aguarde!")
        self._write(self.tourn_text, "🚀 Processando os lambdas e rolando os dados... Isso levará cerca de 10-20 segundos na CPU.")
        
        threading.Thread(
            target=self._run_tournament_logic,
            args=(self.tourn_text, self.tourn_btn),
            daemon=True,
        ).start()

    def _run_tournament_logic(self, textbox: ctk.CTkTextbox, btn: ctk.CTkButton):
        try:
            # Roda as 200 copas chamando o simulador
            res = self.simulator.run_full_tournament(num_tournaments=200)

            out =  f"🌍 =============================================================== 🌍\n"
            out += f"      RELATÓRIO QUANTITATIVO: {res['total_sims']} COPAS DO MUNDO SIMULADAS\n"
            out += f"🌍 =============================================================== 🌍\n\n"
            
            out += "🏆 FAVORITOS AO TÍTULO (Frequência de ser Campeão do Mundo):\n"
            for i, item in enumerate(res["favorites"]):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏅"
                out += f"   {medal} {item['team']:<18} {item['prob']:>5.1f}% das Copas\n"
                
            out += "\n👟 CHUTEIRA DE OURO (Média de Gols marcados durante 1 Torneio):\n"
            out += "   *Jogadores de seleções que chegam longe marcam mais gols*\n"
            for item in res["top_scorers"]:
                out += f"   • {item['player']:<22} {item['avg_goals']:>4.2f} gols / copa\n"
                
            out += "\n🎯 GARÇONS DA COPA (Média de Assistências durante 1 Torneio):\n"
            for item in res["top_assists"]:
                out += f"   • {item['player']:<22} {item['avg_assists']:>4.2f} assistências / copa\n"
                
            out += "\n⚔️ MELHOR ATAQUE (Gols Marcados por Partida Realizada):\n"
            for item in res["best_attack"]:
                out += f"   • {item['team']:<18} {item['gf']:>4.2f} gols/jogo\n"
                
            out += "\n🛡️ MELHOR DEFESA (Gols Sofridos por Partida - Min. Oitavas de Final):\n"
            for item in res["best_defense"]:
                out += f"   • {item['team']:<18} {item['ga']:>4.2f} gols/jogo\n"
                
            if res.get("biggest_zebra"):
                z = res["biggest_zebra"]
                out += f"\n📉 A CINDERELA (A Maior Zebra Matemática do Torneio):\n"
                out += f"   • Seleção: {z['team']} (ELO Baixo: {int(z['elo'])})\n"
                out += f"   • Por que? Nas 200 Copas, essa seleção acumulou em média {z['avg_stage_score']:.1f} pts de avanço\n"
                out += f"     (Conseguindo escapar dos Grupos ou até ir mais longe mesmo sendo considerada 'fraca')\n"

            self._write(textbox, out)

        except Exception as exc:
            import traceback
            self._write(textbox, f"❌ Erro Crítico no Torneio:\n{exc}\n\n{traceback.format_exc()}")
        finally:
            try: 
                btn.configure(state="normal", text="🌍  RODAR NOVAMENTE (Mais 200 Copas)")
            except Exception: pass

    # =========================================================================
    # FUNÇÃO UTILITÁRIA
    # =========================================================================
    def _write(self, textbox: ctk.CTkTextbox, text: str):
        textbox.configure(state="normal")
        textbox.delete("0.0", "end")
        textbox.insert("0.0", text)
        textbox.configure(state="disabled")

    # MANTIDA PARA COMPATIBILIDADE DE TESTE INTERNO, NÃO APAGADA:
    def _run_from_list(self, home: str, away: str):
        pass


if __name__ == "__main__":
    app = WorldCupApp()
    app.mainloop()