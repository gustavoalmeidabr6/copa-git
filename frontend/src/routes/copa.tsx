// src/routes/copa.tsx
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect, useRef } from "react";
import { GROUPS, ALL_TEAMS } from "@/lib/teams";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { NeonButton, Panel, SectionTitle, CornerTicks } from "@/components/sim/ui";
import { SimOverlay } from "@/components/sim/SimOverlay";
import { SimulationTransition } from "@/components/sim/SimulationTransition";
import { ArrowLeft, Trophy, ChevronRight, Play } from "lucide-react";
import { TeamFlag, PlayerAvatar } from "@/lib/visuals";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

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

// ARQUIVOS EXATAMENTE COMO ESTÃO NA SUA PASTA "PUBLIC"
const PLAYER_PICS = [
  "/cristiano-ronaldo-473-390x509.png",
  "/harry-kane-66-390x494.png",
  "/julian-alvarez.png",
  "/julian-alvarez-3-390x395.png",
  "/kylian-mbappe-153-318x540.png",
  "/lamine-yamal-4-284x540.png",
  "/lionel-messi-392-390x381.png",
  "/luis-diaz-15-366x540.png",
  "/neymar-193-390x535.png",
  "/Memphis-Depay-NL-390x407.png",
  "/erling-braut-haland-51-390x500.png",
  "/vinicius-junior-92-390x472.png"
];

export type TournamentAPIResult = {
  total_sims: number;
  favorites: { team: string; prob: number }[];
  top_scorers: { player: string; avg_goals: number }[];
  top_assists: { player: string; avg_assists: number }[]; 
  best_attack: { team: string; gf: number }[];
  best_defense: { team: string; ga: number }[];
  biggest_zebra?: { team: string; elo: number; avg_stage_score: number };
};

function CopaPage() {
  const [step, setStep] = useState<Step>("groups");
  const [simState, setSimState] = useState<"idle" | "simulating" | "transitioning" | "finishing_transition">("idle");
  const [transitionPlayerImg, setTransitionPlayerImg] = useState(PLAYER_PICS[0]);
  const [result, setResult] = useState<TournamentAPIResult | null>(null);

  const start = async () => {
    // SORTEIO DO JOGADOR AQUI
    const randomPic = PLAYER_PICS[Math.floor(Math.random() * PLAYER_PICS.length)];
    setTransitionPlayerImg(randomPic);

    setSimState("simulating");

    try {
      const responsePromise = fetch(`${API_BASE_URL}/api/simulate_tournament`, { method: "POST" });
      
      const [response] = await Promise.all([
        responsePromise,
        new Promise(res => setTimeout(res, 10000))
      ]);

      if (!response.ok) throw new Error("Erro na API");
      const data = await response.json();
      
      setResult(data);
      setSimState("transitioning");
    } catch (err) {
      console.error(err);
      alert("Falha ao comunicar com o Motor em Python. Ele está ligado (porta 8000)?");
      setSimState("idle");
    }
  };

  return (
    <NeonChrome>
      <main className="mx-auto max-w-7xl px-6 py-6 relative z-10">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
          <div className="flex items-center gap-2">
            <Link to="/" className="text-primary/80 hover:text-primary">Menu</Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-foreground/80">Copa do Mundo Monte Carlo</span>
          </div>
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
      
      {(simState === "simulating" || simState === "transitioning") && (
        <SimOverlay label="SIMULANDO TORNEIO" />
      )}

      <SimulationTransition 
        isActive={simState === "transitioning" || simState === "finishing_transition"} 
        playerImageUrl={transitionPlayerImg}
        onBlindSpot={() => {
          setStep("final");
          setSimState("finishing_transition");
        }}
        onComplete={() => {
          setSimState("idle");
        }}
      />
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
          <Trophy className="h-5 w-5" /> Iniciar Motor Quant (400 Torneios)
        </NeonButton>
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
      </div>
    </div>
  );
}

function AutoScrollList({ children, className, as: Component = "ul" }: { children: React.ReactNode, className?: string, as?: any }) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    let direction = 1;
    let isPaused = false;
    let isInteracting = false;
    let animationFrameId: number;
    let pauseTimeout: NodeJS.Timeout;
    let idleTimeout: NodeJS.Timeout;
    let lastTime: number | null = null;
    let exactScrollTop = el.scrollTop;
    
    const speedPerMs = 0.025; 

    const startIdleTimer = () => {
      clearTimeout(idleTimeout);
      idleTimeout = setTimeout(() => {
        isInteracting = false;
        exactScrollTop = el.scrollTop; 
        lastTime = null; 
      }, 3000); 
    };

    const handleInteraction = () => {
      isInteracting = true;
      exactScrollTop = el.scrollTop; 
      clearTimeout(idleTimeout);
    };

    const handleInteractionEnd = () => {
      startIdleTimer();
    };

    el.addEventListener('pointerenter', handleInteraction);
    el.addEventListener('pointerleave', handleInteractionEnd);
    el.addEventListener('touchstart', handleInteraction, { passive: true });
    el.addEventListener('touchend', handleInteractionEnd);

    isInteracting = true;
    startIdleTimer();

    const loop = (timestamp: number) => {
      if (lastTime === null) lastTime = timestamp;
      const dt = timestamp - lastTime;
      lastTime = timestamp;

      if (!isInteracting && !isPaused && el.scrollHeight > el.clientHeight) {
        exactScrollTop += speedPerMs * dt * direction;
        el.scrollTop = exactScrollTop;

        if (Math.abs(el.scrollTop - exactScrollTop) > 2) {
           exactScrollTop = el.scrollTop;
        }

        if (direction === 1 && el.scrollTop + el.clientHeight >= el.scrollHeight - 1) {
          direction = -1; 
          isPaused = true;
          pauseTimeout = setTimeout(() => { isPaused = false; lastTime = null; }, 5000); 
        } 
        else if (direction === -1 && el.scrollTop <= 1) {
          direction = 1; 
          isPaused = true;
          pauseTimeout = setTimeout(() => { isPaused = false; lastTime = null; }, 5000); 
        }
      }
      animationFrameId = requestAnimationFrame(loop);
    };

    animationFrameId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animationFrameId);
      clearTimeout(pauseTimeout);
      clearTimeout(idleTimeout);
      el.removeEventListener('pointerenter', handleInteraction);
      el.removeEventListener('pointerleave', handleInteractionEnd);
      el.removeEventListener('touchstart', handleInteraction);
      el.removeEventListener('touchend', handleInteractionEnd);
    };
  }, []);

  return (
    <Component ref={ref} className={className}>
      {children}
    </Component>
  );
}

function FinalStep({ result }: { result: TournamentAPIResult }) {
  const getTeam = (apiName: string) => {
    const found = ALL_TEAMS.find(t => t.apiName.toLowerCase() === apiName.toLowerCase() || t.name.toLowerCase() === apiName.toLowerCase());
    if (!found) {
        console.warn(`⚠️ ALERTA: O Python retornou a seleção '${apiName}', mas ela não existe no frontend.`);
        return ALL_TEAMS[0]; 
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
          <div className="mb-3 font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Top 8 Favoritos</div>
          <AutoScrollList as="ul" className="space-y-2 max-h-[16rem] overflow-y-auto pr-2 custom-scrollbar">
            {result.favorites.slice(0, 8).map((t, i) => {
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
          </AutoScrollList>
        </Panel>
      </div>

      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        
        <Panel glow="gold">
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em] text-gold">Chuteira de Ouro</div>
          <AutoScrollList as="ol" className="space-y-2 max-h-[12rem] overflow-y-auto pr-2 custom-scrollbar">
            {(result.top_scorers || []).slice(0, 5).map((s, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-display text-gold tabular-nums">{i + 1}</span>
                  <PlayerAvatar name={s.player} px={24} />
                  <span className="text-xs truncate w-[85px]" title={s.player}>{s.player}</span>
                </div>
                <span className="font-display text-primary text-[11px] whitespace-nowrap">{s.avg_goals.toFixed(2)} G</span>
              </motion.li>
            ))}
          </AutoScrollList>
        </Panel>

        <Panel glow="neon">
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em] text-neon">Líderes de Assist.</div>
          <AutoScrollList as="ol" className="space-y-2 max-h-[12rem] overflow-y-auto pr-2 custom-scrollbar">
            {(result.top_assists || []).slice(0, 5).map((s, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-display text-neon tabular-nums">{i + 1}</span>
                  <PlayerAvatar name={s.player} px={24} />
                  <span className="text-xs truncate w-[85px]" title={s.player}>{s.player}</span>
                </div>
                <span className="font-display text-primary text-[11px] whitespace-nowrap">{s.avg_assists.toFixed(2)} A</span>
              </motion.li>
            ))}
            {(!result.top_assists || result.top_assists.length === 0) && (
              <div className="text-xs text-muted-foreground p-3 text-center">Nenhuma assistência registrada</div>
            )}
          </AutoScrollList>
        </Panel>

        <Panel>
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em] text-foreground/90">Melhores Ataques</div>
          <AutoScrollList as="ol" className="space-y-2 max-h-[12rem] overflow-y-auto pr-2 custom-scrollbar">
            {(result.best_attack || []).slice(0, 5).map((t, i) => {
              const teamData = getTeam(t.team);
              return (
                <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="font-display tabular-nums text-muted-foreground">{i + 1}</span>
                    <TeamFlag teamId={teamData.id} className="h-4 w-6" />
                    <span className="text-xs uppercase tracking-wider truncate w-[80px]">{teamData.name}</span>
                  </div>
                  <span className="font-display text-primary text-[11px] whitespace-nowrap">{t.gf.toFixed(2)} G/J</span>
                </motion.li>
              );
            })}
          </AutoScrollList>
        </Panel>

        <Panel>
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em] text-foreground/90">Melhores Defesas</div>
          <AutoScrollList as="ol" className="space-y-2 max-h-[12rem] overflow-y-auto pr-2 custom-scrollbar">
            {(result.best_defense || []).slice(0, 5).map((t, i) => {
              const teamData = getTeam(t.team);
              return (
                <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="font-display tabular-nums text-muted-foreground">{i + 1}</span>
                    <TeamFlag teamId={teamData.id} className="h-4 w-6" />
                    <span className="text-xs uppercase tracking-wider truncate w-[80px]">{teamData.name}</span>
                  </div>
                  <span className="font-display text-primary text-[11px] whitespace-nowrap">{t.ga.toFixed(2)} GS/J</span>
                </motion.li>
              );
            })}
          </AutoScrollList>
        </Panel>
      </div>

      {result.biggest_zebra && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Panel glow="neon" className="flex flex-col sm:flex-row items-center justify-between gap-4 border-dashed border-neon/50 bg-neon/5">
             <div className="flex items-center gap-4">
                <div className="text-4xl">📉</div>
                <div>
                   <div className="font-display text-sm uppercase tracking-[0.3em] text-neon">A Grande Zebra Matemática</div>
                   <div className="text-xs text-muted-foreground">A seleção de baixo ELO com a maior propensão estatística a surpreender na Copa.</div>
                </div>
             </div>
             <div className="flex items-center gap-3 bg-background/60 px-4 py-2 rounded-md border border-border/50">
                <TeamFlag teamId={getTeam(result.biggest_zebra.team).id} className="h-6 w-10" />
                <span className="font-display uppercase tracking-widest text-lg">{getTeam(result.biggest_zebra.team).name}</span>
             </div>
          </Panel>
        </motion.div>
      )}

      <div className="flex flex-wrap justify-between gap-3">
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
        <Link to="/copa"><NeonButton onClick={() => window.location.reload()}><Play className="h-4 w-4" /> Rodar Novamente</NeonButton></Link>
      </div>
    </div>
  );
}