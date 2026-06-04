import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";
import { GROUPS, ALL_TEAMS } from "@/lib/teams";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { NeonButton, Panel, SectionTitle, CornerTicks } from "@/components/sim/ui";
import { SimOverlay } from "@/components/sim/SimOverlay";
import { ArrowLeft, Trophy, ChevronRight, Play } from "lucide-react";
import { TeamFlag, PlayerAvatar } from "@/lib/visuals";

export const Route = createFileRoute("/copa")({
  head: () => ({
    meta: [
      { title: "Simular Copa do Mundo · Ultra Simulador 2026" },
      { name: "description", content: "Simule a Copa do Mundo 2026 inteira via Motor Quantitativo XGBoost." },
    ],
  }),
  component: CopaPage,
});

type Step = "groups" | "final";

export type TournamentAPIResult = {
  total_sims: number;
  favorites: { team: string; prob: number }[];
  top_scorers: { player: string; avg_goals: number }[];
  best_attack: { team: string; gf: number }[];
  best_defense: { team: string; ga: number }[];
  biggest_zebra?: { team: string; elo: number; avg_stage_score: number };
};

function CopaPage() {
  const [step, setStep] = useState<Step>("groups");
  const [sim, setSim] = useState(false);
  const [result, setResult] = useState<TournamentAPIResult | null>(null);

  const start = async () => {
    setSim(true);
    try {
      const response = await fetch("http://localhost:8000/api/simulate_tournament", { method: "POST" });
      if (!response.ok) throw new Error("Erro na API");
      const data = await response.json();
      setResult(data);
      setStep("final"); 
    } catch (err) {
      console.error(err);
      alert("Falha ao comunicar com o Motor em Python. Ele está ligado (porta 8000)?");
    } finally {
      setSim(false);
    }
  };

  return (
    <NeonChrome>
      <main className="mx-auto max-w-7xl px-6 py-6">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
          <div className="flex items-center gap-2">
            <Link to="/" className="text-primary/80 hover:text-primary">Menu</Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-foreground/80">Copa do Mundo Monte Carlo</span>
          </div>
          <span className="text-primary/70">Nível 24</span>
        </div>

        <AnimatePresence mode="wait">
          {step === "groups" && (
            <motion.div key="g" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <GroupsStep onSim={start} />
            </motion.div>
          )}
          {step === "final" && result && (
            <motion.div key="f" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <FinalStep result={result} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      {sim && <SimOverlay onDone={() => {}} label="Processando 200 Copas do Mundo no XGBoost..." />}
    </NeonChrome>
  );
}

function GroupsStep({ onSim }: { onSim: () => void }) {
  return (
    <div className="mt-6 space-y-6">
      <div className="text-center">
        <SectionTitle accent="COPA DO MUNDO">Simulador Quântico</SectionTitle>
        <p className="mt-1 text-xs uppercase tracking-[0.3em] text-muted-foreground">Grupos Oficiais 2026</p>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Object.entries(GROUPS).map(([g, teams], gi) => (
          <motion.div
            key={g}
            initial={{ opacity: 0, y: 20, rotateX: -30 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ delay: gi * 0.05, type: "spring", stiffness: 110 }}
          >
            <Panel className="space-y-2 p-3">
              <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-primary">Grupo {g}</div>
              <ul className="space-y-1">
                {teams.map((t) => (
                  <li key={t.id} className="flex items-center gap-2 rounded border border-border/30 bg-background/30 px-2 py-1.5 text-[11px]">
                    <TeamFlag teamId={t.id} className="h-4 w-6" />
                    <span className="flex-1 truncate uppercase tracking-wider text-foreground/85">{t.name}</span>
                  </li>
                ))}
              </ul>
            </Panel>
          </motion.div>
        ))}
      </div>

      <div className="flex flex-col items-center gap-4">
        <NeonButton onClick={onSim} variant="gold" className="animate-pulse-neon px-10 py-4 text-base">
          <Trophy className="h-5 w-5" /> Iniciar Motor Quant (200 Torneios)
        </NeonButton>
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
      </div>
    </div>
  );
}

function FinalStep({ result }: { result: TournamentAPIResult }) {
  
  // Função que nunca mais vai deixar o México ganhar acidentalmente!
  const getTeam = (apiName: string) => {
    const found = ALL_TEAMS.find(t => t.apiName.toLowerCase() === apiName.toLowerCase() || t.name.toLowerCase() === apiName.toLowerCase());
    if (!found) {
        console.warn(`⚠️ ALERTA: O Python retornou a seleção '${apiName}', mas ela não existe no frontend.`);
        return ALL_TEAMS[0]; // Retorna Mexico pra não quebrar a tela
    }
    return found;
  };

  const champ = getTeam(result.favorites[0]?.team || "");

  return (
    <div className="mt-6 space-y-5">
      <SectionTitle accent="CONCLUÍDA">Estatísticas Monte Carlo</SectionTitle>
      <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">O motor processou as probabilidades baseadas em {result.total_sims} torneios massivos</p>

      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
        <Panel glow="gold" className="text-center">
          <CornerTicks />
          <motion.div animate={{ rotate: [0, 5, -5, 0] }} transition={{ duration: 4, repeat: Infinity }} className="mx-auto text-7xl drop-shadow-[0_0_30px_var(--gold)]">🏆</motion.div>
          <div className="mt-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">O Grande Favorito</div>
          <div className="mt-2 flex justify-center"><TeamFlag teamId={champ.id} className="h-16 w-24" /></div>
          <div className="mt-1 font-display text-4xl uppercase tracking-widest text-gold">{champ.name}</div>
          <div className="mt-3 font-display text-3xl text-neon">{result.favorites[0]?.prob.toFixed(1)}%</div>
          <div className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Probabilidade Estatística de Título</div>
        </Panel>

        <Panel>
          <div className="mb-3 font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Top 5 Favoritos</div>
          <ul className="space-y-2">
            {result.favorites.slice(0, 5).map((t, i) => {
              const teamData = getTeam(t.team);
              return (
                <motion.li key={t.team} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-3">
                      <span className="font-display tabular-nums text-gold">{i + 1}</span>
                      <TeamFlag teamId={teamData.id} className="h-5 w-8" />
                      <span className="font-display uppercase tracking-widest">{teamData.name}</span>
                    </div>
                    <span className="font-display text-primary">{t.prob.toFixed(1)}%</span>
                  </div>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${t.prob * 3}%` }} transition={{ delay: 0.2 + i * 0.08, duration: 0.6 }} className="mt-1 h-1 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
                </motion.li>
              );
            })}
          </ul>
        </Panel>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Artilheiro da Copa</div>
          <div className="mt-3 grid place-items-center"><PlayerAvatar name={result.top_scorers[0]?.player || "Desconhecido"} px={72} /></div>
          <div className="mt-2 text-center font-display text-xl uppercase">{result.top_scorers[0]?.player}</div>
          <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{result.top_scorers[0]?.avg_goals.toFixed(2)}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols em média</span></div>
        </Panel>
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Melhor Defesa</div>
          {result.best_defense[0] && (
            <>
              <div className="mt-3 flex justify-center"><TeamFlag teamId={getTeam(result.best_defense[0].team).id} className="h-12 w-20" /></div>
              <div className="mt-1 text-center font-display text-xl uppercase">{getTeam(result.best_defense[0].team).name}</div>
              <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{result.best_defense[0].ga.toFixed(2)}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols sofridos/jogo</span></div>
            </>
          )}
        </Panel>
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Melhor Ataque</div>
          {result.best_attack[0] && (
            <>
              <div className="mt-3 flex justify-center"><TeamFlag teamId={getTeam(result.best_attack[0].team).id} className="h-12 w-20" /></div>
              <div className="mt-1 text-center font-display text-xl uppercase">{getTeam(result.best_attack[0].team).name}</div>
              <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{result.best_attack[0].gf.toFixed(2)}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols marcados/jogo</span></div>
            </>
          )}
        </Panel>
      </div>

      <div className="flex flex-wrap justify-between gap-3">
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
        <Link to="/copa"><NeonButton onClick={() => window.location.reload()}><Play className="h-4 w-4" /> Rodar Novamente</NeonButton></Link>
      </div>
    </div>
  );
}