import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState } from "react";
import { GROUPS, teamById } from "@/lib/teams";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { NeonButton, Panel, SectionTitle, CornerTicks } from "@/components/sim/ui";
import { SimOverlay } from "@/components/sim/SimOverlay";
import { simulateWC200 } from "@/lib/sim";
import { ArrowLeft, Trophy, ChevronRight, Play } from "lucide-react";
import { TeamFlag, PlayerAvatar } from "@/lib/visuals";

export const Route = createFileRoute("/copa")({
  head: () => ({
    meta: [
      { title: "Simular Copa do Mundo · Ultra Simulador 2026" },
      { name: "description", content: "Simule a Copa do Mundo 2026 inteira — fase de grupos, mata-mata e estatísticas finais." },
    ],
  }),
  component: CopaPage,
});

type Step = "groups" | "bracket" | "final";
type Result = ReturnType<typeof simulateWC200>;

function CopaPage() {
  const [step, setStep] = useState<Step>("groups");
  const [sim, setSim] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  const start = () => {
    setSim(true);
    setTimeout(() => {
      setResult(simulateWC200());
      setSim(false);
      setStep("bracket");
    }, 2200);
  };

  return (
    <NeonChrome>
      <main className="mx-auto max-w-7xl px-6 py-6">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
          <div className="flex items-center gap-2">
            <Link to="/" className="text-primary/80 hover:text-primary">Menu</Link>
            <ChevronRight className="h-3 w-3" />
            <span className="text-foreground/80">Simular Copa do Mundo</span>
          </div>
          <span className="text-primary/70">Nível 24</span>
        </div>

        <AnimatePresence mode="wait">
          {step === "groups" && (
            <motion.div key="g" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <GroupsStep onSim={start} />
            </motion.div>
          )}
          {step === "bracket" && result && (
            <motion.div key="b" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <BracketStep result={result} onNext={() => setStep("final")} />
            </motion.div>
          )}
          {step === "final" && result && (
            <motion.div key="f" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <FinalStep result={result} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      {sim && <SimOverlay onDone={() => {}} label="Simulando Copa do Mundo" />}
    </NeonChrome>
  );
}

function GroupsStep({ onSim }: { onSim: () => void }) {
  return (
    <div className="mt-6 space-y-6">
      <div className="text-center">
        <SectionTitle accent="COPA DO MUNDO">Simular</SectionTitle>
        <p className="mt-1 text-xs uppercase tracking-[0.3em] text-muted-foreground">Fase de Grupos</p>
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
          <Trophy className="h-5 w-5" /> Simular Copa do Mundo
        </NeonButton>
        <div className="flex items-center gap-4 text-xs uppercase tracking-widest text-muted-foreground">
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" /> Classificados</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-destructive" /> Eliminados</span>
        </div>
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
      </div>
    </div>
  );
}

function MatchPill({ m, delay }: { m: any; delay: number }) {
  const winnerHome = m.hs > m.as;
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="glass-card flex items-center justify-between rounded-lg px-3 py-2 text-xs"
    >
      <div className={`flex items-center gap-2 ${winnerHome ? "text-primary" : "text-muted-foreground line-through opacity-60"}`}>
        <TeamFlag teamId={m.home.id} className="h-4 w-6" /><span className="font-display uppercase">{m.home.name}</span>
      </div>
      <div className="font-display tabular-nums">
        <span className={winnerHome ? "text-primary" : ""}>{m.hs}</span>
        <span className="px-1 text-muted-foreground">–</span>
        <span className={!winnerHome ? "text-primary" : ""}>{m.as}</span>
      </div>
      <div className={`flex items-center gap-2 ${!winnerHome ? "text-primary" : "text-muted-foreground line-through opacity-60"}`}>
        <span className="font-display uppercase">{m.away.name}</span><TeamFlag teamId={m.away.id} className="h-4 w-6" />
      </div>
    </motion.div>
  );
}

function BracketStep({ result, onNext }: { result: Result; onNext: () => void }) {
  const { ko } = result.example;
  return (
    <div className="mt-6 space-y-5">
      <SectionTitle accent="MATA-MATA">Chaveamento</SectionTitle>
      <div className="grid gap-4 lg:grid-cols-4">
        {ko.map((round, ri) => (
          <div key={ri} className="space-y-2">
            <div className="font-display text-xs uppercase tracking-[0.3em] text-gold">{round.round}</div>
            {round.matches.map((m, mi) => (
              <MatchPill key={mi} m={m} delay={ri * 0.2 + mi * 0.06} />
            ))}
          </div>
        ))}
      </div>

      {/* Champion plinth */}
      <motion.div initial={{ scale: 0.7, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 1.2, type: "spring" }} className="relative mx-auto mt-6 max-w-md">
        <Panel glow="gold" className="text-center">
          <CornerTicks />
          <div className="font-display text-xs uppercase tracking-[0.4em] text-muted-foreground">Campeão simulado</div>
          <motion.div animate={{ y: [0, -6, 0] }} transition={{ duration: 3, repeat: Infinity }} className="mt-3 text-7xl drop-shadow-[0_0_30px_var(--gold)]">🏆</motion.div>
          <div className="mt-2 flex justify-center"><TeamFlag teamId={result.example.champion.id} className="h-14 w-20" /></div>
          <div className="mt-1 font-display text-3xl uppercase tracking-widest text-gold">{result.example.champion.name}</div>
        </Panel>
      </motion.div>

      <div className="flex justify-center">
        <NeonButton onClick={onNext} variant="gold"><Trophy className="h-4 w-4" /> Ver Estatísticas Finais</NeonButton>
      </div>
    </div>
  );
}

function FinalStep({ result }: { result: Result }) {
  const champ = result.example.champion;
  const r = result.example;
  return (
    <div className="mt-6 space-y-5">
      <SectionTitle accent="CONCLUÍDA">Simulação</SectionTitle>
      <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">A Copa do Mundo 2026 foi simulada com sucesso — média de {result.totalRuns} torneios</p>

      <div className="grid gap-5 lg:grid-cols-[1.2fr_1fr]">
        <Panel glow="gold" className="text-center">
          <CornerTicks />
          <motion.div animate={{ rotate: [0, 5, -5, 0] }} transition={{ duration: 4, repeat: Infinity }} className="mx-auto text-7xl drop-shadow-[0_0_30px_var(--gold)]">🏆</motion.div>
          <div className="mt-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">Campeão das simulações</div>
          <div className="mt-2 flex justify-center"><TeamFlag teamId={champ.id} className="h-16 w-24" /></div>
          <div className="mt-1 font-display text-4xl uppercase tracking-widest text-gold">{champ.name}</div>
          <div className="mt-3 font-display text-3xl text-neon">{result.top5[0]?.pct.toFixed(1)}%</div>
          <div className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Probabilidade de título</div>
        </Panel>

        <Panel>
          <div className="mb-3 font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Top 5 Favoritos</div>
          <ul className="space-y-2">
            {result.top5.map((t, i) => (
              <motion.li key={t.team.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span className="font-display tabular-nums text-gold">{i + 1}</span>
                    <TeamFlag teamId={t.team.id} className="h-5 w-8" />
                    <span className="font-display uppercase tracking-widest">{t.team.name}</span>
                  </div>
                  <span className="font-display text-primary">{t.pct.toFixed(1)}%</span>
                </div>
                <motion.div initial={{ width: 0 }} animate={{ width: `${t.pct * 3}%` }} transition={{ delay: 0.2 + i * 0.08, duration: 0.6 }} className="mt-1 h-1 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
              </motion.li>
            ))}
          </ul>
        </Panel>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Artilheiro da Copa</div>
          <div className="mt-3 grid place-items-center"><PlayerAvatar name={r.topScorer.player} px={72} /></div>
          <div className="mt-2 text-center font-display text-xl uppercase">{r.topScorer.player}</div>
          <div className="mt-1 flex items-center justify-center gap-1 text-xs text-muted-foreground">
            <TeamFlag teamId={r.topScorer.team} className="h-3 w-5" /> {teamById(r.topScorer.team)?.name}
          </div>
          <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{r.topScorer.goals}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols</span></div>
        </Panel>
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Melhor Defesa</div>
          <div className="mt-3 flex justify-center"><TeamFlag teamId={r.bestDefense.id} className="h-12 w-20" /></div>
          <div className="mt-1 text-center font-display text-xl uppercase">{r.bestDefense.name}</div>
          <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{r.bestDefenseGoalsAgainst}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols sofridos</span></div>
        </Panel>
        <Panel>
          <div className="text-center font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">Melhor Ataque</div>
          <div className="mt-3 flex justify-center"><TeamFlag teamId={r.bestAttack.id} className="h-12 w-20" /></div>
          <div className="mt-1 text-center font-display text-xl uppercase">{r.bestAttack.name}</div>
          <div className="mt-3 text-center"><span className="font-display text-4xl text-neon">{r.bestAttackGoals}</span> <span className="text-xs uppercase tracking-widest text-muted-foreground">gols marcados</span></div>
        </Panel>
      </div>

      <Panel glow="gold">
        <div className="mb-3 font-display text-xs uppercase tracking-[0.3em]">Artilheiros — média de {result.totalRuns} torneios</div>
        <ul className="grid gap-2 md:grid-cols-2">
          {result.topGoalers.map((s, i) => (
            <motion.li key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded border border-border/30 bg-background/30 px-3 py-2 text-sm">
              <div className="flex items-center gap-3">
                <span className="font-display text-gold tabular-nums">{i + 1}</span>
                <PlayerAvatar name={s.player} px={28} />
                <span>{s.player}</span>
                <span className="flex items-center gap-1 text-xs text-muted-foreground">
                  <TeamFlag teamId={s.team} className="h-3 w-5" /> {teamById(s.team)?.name}
                </span>
              </div>
              <span className="font-display text-primary">{(s.goals / result.totalRuns).toFixed(1)} g/torneio</span>
            </motion.li>
          ))}
        </ul>
      </Panel>

      <div className="flex flex-wrap justify-between gap-3">
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar ao Menu</NeonButton></Link>
        <Link to="/copa"><NeonButton><Play className="h-4 w-4" /> Simular Novamente</NeonButton></Link>
      </div>
    </div>
  );
}
