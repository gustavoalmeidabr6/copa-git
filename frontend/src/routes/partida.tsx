// src/routes/partida.tsx
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useEffect, useMemo, useState, useRef } from "react";
import { ALL_TEAMS, FORMATIONS, POSITION_WEIGHT, Team, rosterFor, formationFor, getPlayerPosition, type Formation, KNOWN_PLAYER_POSITIONS, normalizeName, POS_MAP } from "@/lib/teams";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { NeonButton, Panel, SectionTitle, CornerTicks } from "@/components/sim/ui";
import { SimOverlay } from "@/components/sim/SimOverlay";
import { SimulationTransition } from "@/components/sim/SimulationTransition";
import { ArrowLeft, Play, Trash2, ChevronRight, BarChart3 } from "lucide-react";
import { TeamFlag, PlayerAvatar } from "@/lib/visuals";

const API_BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

export const Route = createFileRoute("/partida")({
  head: () => ({
    meta: [
      { title: "Simular Partida · Ultra Simulador 2026" },
      { name: "description", content: "Escolha duas seleções, monte a escalação e simule 400 partidas no Motor Quant." },
    ],
  }),
  component: PartidaPage,
});

type Step = "select" | "lineup" | "result";

const WC2026_TEAM_IDS = new Set([
  "MEX", "RSA", "KOR", "CZE", "CAN", "BIH", "QAT", "SUI",
  "BRA", "MAR", "HAI", "SCO", "USA", "PAR", "AUS", "TUR",
  "GER", "CUW", "CIV", "ECU", "NED", "JPN", "SWE", "TUN",
  "BEL", "EGY", "IRN", "NZL", "ESP", "CPV", "KSA", "URU",
  "FRA", "SEN", "IRQ", "NOR", "ARG", "ALG", "AUT", "JOR",
  "POR", "COD", "UZB", "COL", "ENG", "CRO", "GHA", "PAN",
]);

const PLAYER_PICS = [
  "/cristiano-ronaldo-473-390x509.png",
  "/jude-bellingham-48-284x540.png",
  "/julian-alvarez.png",
  "/harry-kane-66-390x494.png",
  "/kylian-mbappe-153-318x540.png",
  "/lamine-yamal-4-284x540.png",
  "/lionel-messi-392-390x381.png",
  "/luis-diaz-15-366x540.png",
  "/neymar-193-390x535.png",
  "/Memphis-Depay-NL-390x407.png",
  "/erling-braut-haland-51-390x500.png",
  "/vinicius-junior-92-390x472.png"
];

export type APIResult = {
  aWinPct: number;
  drawPct: number;
  bWinPct: number;
  expectedScore: string;
  topScorers: { player: string; team: string; goals: number }[];
  topAssists: { player: string; team: string; assists: number }[];
  avgGoals: { a: number; b: number };
  scoreCounts: Record<string, number>;
  sim_logs: string[];
  hasVegasOdds?: boolean;
  vegasData?: { over_2_5?: number; under_2_5?: number; btts_yes?: number; btts_no?: number } | null;
  fezinhaData?: { source: string; expectedCorners: number; expectedCards: number; bttsPct: number; over25Pct: number } | null;
};

function smartSort(roster: string[]) {
  if (!roster || roster.length === 0) return [];
  const starters = roster.slice(0, 11);
  const bench = roster.slice(11);

  const pool = starters.map((name, idx) => {
    const pos = getPlayerPosition(name);
    // Se a posição for conhecida, usa o peso oficial da matriz tática.
    // Se for um jogador desconhecido da API, usamos a ordem original (que vem Defesa -> Ataque).
    // Multiplicamos o índice por 1.4 para mapear de 0-10 perfeitamente para a escala de pesos 1-15.
    const weight = pos && POSITION_WEIGHT[pos] ? POSITION_WEIGHT[pos] : (idx === 0 ? 1 : idx * 1.4);
    return { name, weight };
  });

  pool.sort((a, b) => a.weight - b.weight);

  return [...pool.map(p => p.name), ...bench];
}

function PartidaPage() {
  const [step, setStep] = useState<Step>("select");
  const [home, setHome] = useState<Team | null>(null);
  const [away, setAway] = useState<Team | null>(null);
  const [formA, setFormA] = useState<Formation>("4-2-3-1");
  const [formB, setFormB] = useState<Formation>("4-3-3");

  const [excludedA, setExcludedA] = useState<string[]>([]);
  const [excludedB, setExcludedB] = useState<string[]>([]);
  const [stadium, setStadium] = useState<string>("");

  const [simState, setSimState] = useState<"idle" | "simulating" | "transitioning" | "finishing_transition">("idle");
  const [transitionPlayerImg, setTransitionPlayerImg] = useState(PLAYER_PICS[0]);

  const [result, setResult] = useState<APIResult | null>(null);
  const [rosterA, setRosterA] = useState<string[]>([]);
  const [rosterB, setRosterB] = useState<string[]>([]);

  useEffect(() => {
    setExcludedA([]);
    if (home) {
      setFormA(formationFor(home.id));
      fetch(`${API_BASE_URL}/api/roster/${home.apiName}`)
        .then(res => res.json())
        .then(data => {
          if (data.positions) {
            for (const [name, pos] of Object.entries(data.positions)) {
              KNOWN_PLAYER_POSITIONS[normalizeName(name as string)] = POS_MAP[pos as string] || (pos as string);
            }
          }
          const arr = [...(data.starters || []), ...(data.bench || [])];
          if (arr.length > 0) setRosterA(smartSort(arr.slice(0, 26)));
        })
        .catch(() => setRosterA(smartSort(rosterFor(home.id).slice(0, 26))));
    }
  }, [home]);

  useEffect(() => {
    setExcludedB([]);
    if (away) {
      setFormB(formationFor(away.id));
      fetch(`${API_BASE_URL}/api/roster/${away.apiName}`)
        .then(res => res.json())
        .then(data => {
          if (data.positions) {
            for (const [name, pos] of Object.entries(data.positions)) {
              KNOWN_PLAYER_POSITIONS[normalizeName(name as string)] = POS_MAP[pos as string] || (pos as string);
            }
          }
          const arr = [...(data.starters || []), ...(data.bench || [])];
          if (arr.length > 0) setRosterB(smartSort(arr.slice(0, 26)));
        })
        .catch(() => setRosterB(smartSort(rosterFor(away.id).slice(0, 26))));
    }
  }, [away]);

  return (
    <NeonChrome>
      <main className="mx-auto max-w-7xl px-6 py-6 relative z-10">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
          <div className="flex items-center gap-2">
            <Link to="/" className="text-primary/80 hover:text-primary">Menu</Link>
            <ChevronRight className="h-3 w-3" />
            <span>Simular Partida Específica</span>
            <ChevronRight className="h-3 w-3" />
            <span className="text-foreground/80">
              {step === "select" ? "Selecionar Times" : step === "lineup" ? "Escalações" : "Resultados"}
            </span>
          </div>
        </div>
        <AnimatePresence mode="wait">
          {step === "select" && (
            <motion.div key="sel" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
              <SelectStep home={home} away={away} setHome={setHome} setAway={setAway} onAdvance={() => setStep("lineup")} />
            </motion.div>
          )}
          {step === "lineup" && home && away && (
            <motion.div key="line" initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.97 }}>
              <LineupStep
                home={home} away={away}
                formA={formA} formB={formB}
                setFormA={setFormA} setFormB={setFormB}
                rosterA={rosterA} rosterB={rosterB}
                setRosterA={setRosterA} setRosterB={setRosterB}
                excludedA={excludedA} setExcludedA={setExcludedA}
                excludedB={excludedB} setExcludedB={setExcludedB}
                stadium={stadium} setStadium={setStadium}
                onBack={() => setStep("select")}
                onSimulate={async () => {
                  const randomPic = PLAYER_PICS[Math.floor(Math.random() * PLAYER_PICS.length)];
                  setTransitionPlayerImg(randomPic);

                  setSimState("simulating");

                  try {
                    const responsePromise = fetch(`${API_BASE_URL}/api/simulate_match`, {
                      method: "POST",
                      headers: { "Content-Type": "application/json" },
                      body: JSON.stringify({
                        home: home.apiName,
                        away: away.apiName,
                        num_simulations: 400,
                        home_excluded: excludedA,
                        away_excluded: excludedB,
                        stadium: stadium || undefined,
                        home_starters: rosterA.slice(0, 11),
                        away_starters: rosterB.slice(0, 11)
                      })
                    });

                    const [response] = await Promise.all([
                      responsePromise,
                      new Promise(res => setTimeout(res, 2000))
                    ]);

                    if (!response.ok) throw new Error("Erro na API");
                    const data = await response.json();

                    const scoreCounts: Record<string, number> = {};
                    Object.entries(data.most_likely_scores || {}).forEach(([score, pct]) => {
                      scoreCounts[score] = Math.round(((pct as number) / 100) * 400);
                    });

                    const mappedResult = {
                      aWinPct: data.home_win_prob || 0,
                      drawPct: data.draw_prob || 0,
                      bWinPct: data.away_win_prob || 0,
                      expectedScore: data.expected_score || "N/A",
                      topScorers: (data.top_scorers || []).map((s: any) => ({ player: s[0], team: home.id, goals: s[1] })),
                      topAssists: (data.top_assists || []).map((s: any) => ({ player: s[0], team: home.id, assists: s[1] })),
                      avgGoals: { a: data.home_lambda || 0, b: data.away_lambda || 0 },
                      scoreCounts: scoreCounts,
                      sim_logs: data.sim_logs || [],
                      hasVegasOdds: data.has_vegas_odds || false,
                      vegasData: data.vegas_data || null,
                      fezinhaData: data.fezinha_data || null
                    };

                    setResult(mappedResult);
                    setSimState("transitioning");

                  } catch (err) {
                    console.error(err);
                    alert("Erro ao conectar ao servidor FastAPI.");
                    setSimState("idle");
                  }
                }}
              />
            </motion.div>
          )}
          {step === "result" && result && home && away && (
            <motion.div key="res" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}>
              <ResultStep home={home} away={away} result={result} onBack={() => setStep("lineup")} onMenu={() => { setStep("select"); setHome(null); setAway(null); setResult(null); }} />
            </motion.div>
          )}
        </AnimatePresence>

        {(simState === "simulating" || simState === "transitioning") && (
          <SimOverlay label="SIMULANDO PARTIDA" />
        )}

        <SimulationTransition
          isActive={simState === "transitioning" || simState === "finishing_transition"}
          playerImageUrl={transitionPlayerImg}
          onBlindSpot={() => {
            setStep("result");
            setSimState("finishing_transition");
          }}
          onComplete={() => {
            setSimState("idle");
          }}
        />
      </main>
    </NeonChrome>
  );
}

function TeamSlot({ team, label, onClear }: { team: Team | null; label: string; onClear?: () => void }) {
  return (
    <div className="relative flex flex-1 items-center gap-4 rounded-xl border border-primary/30 bg-card/40 p-4 backdrop-blur-md">
      <CornerTicks />
      <div className="font-display text-xs uppercase tracking-[0.3em] text-primary/70">{label}</div>
      <div className="flex flex-1 items-center justify-center gap-3">
        {team ? (
          <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="flex items-center gap-3">
            <TeamFlag teamId={team.id} className="h-8 w-12" />
            <span className="font-display text-xl uppercase tracking-widest">{team.name}</span>
          </motion.div>
        ) : (
          <span className="font-display text-sm uppercase tracking-[0.3em] text-muted-foreground">Selecione um time</span>
        )}
      </div>
      {team && onClear && (
        <button onClick={onClear} className="text-muted-foreground hover:text-destructive"><Trash2 className="h-4 w-4" /></button>
      )}
    </div>
  );
}

function TeamSelectButton({
  t,
  picked,
  index,
  onPick
}: {
  t: Team;
  picked: boolean;
  index: number;
  onPick: (t: Team) => void;
}) {
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <motion.button
      ref={buttonRef}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.01 }}
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.96 }}
      onClick={() => onPick(t)}
      onMouseMove={handleMouseMove}
      className={`group relative flex flex-col items-center gap-1 overflow-hidden rounded-lg border bg-card/40 p-3 backdrop-blur-sm transition-all ${
        picked
          ? "border-primary shadow-[0_0_18px_oklch(0.82_0.23_152/.5)]"
          : "border-border/40 hover:border-primary/60"
      }`}
    >
      {/* 1. Fundo Fixo com Opacidade Baixa */}
      <div className="pointer-events-none absolute inset-0 z-0 opacity-15 transition-opacity duration-300">
        {/* Adicionamos h-full e w-full aqui para travar o tamanho, e reduzimos o scale para 1.3 */}
        <div className="h-full w-full scale-[1.3]">
          <TeamFlag teamId={t.id} className="h-full w-full object-cover blur-[2px] grayscale-[0.2]" />
        </div>
      </div>

      {/* 2. Fundo 'Spotlight' Revelado pelo Mouse (Opacidade Maior) */}
      <div
        className="pointer-events-none absolute inset-0 z-0 opacity-0 transition-opacity duration-300 group-hover:opacity-50"
        style={{
          maskImage: `radial-gradient(circle 60px at ${mousePos.x}px ${mousePos.y}px, black 0%, transparent 100%)`,
          WebkitMaskImage: `radial-gradient(circle 60px at ${mousePos.x}px ${mousePos.y}px, black 0%, transparent 100%)`,
        }}
      >
        <div className="h-full w-full scale-[1.3]">
          <TeamFlag teamId={t.id} className="h-full w-full object-cover blur-[1px]" />
        </div>
      </div>

      {/* 3. Conteúdo Principal */}
      <div className="relative z-10 flex flex-col items-center gap-1 drop-shadow-md">
        <TeamFlag teamId={t.id} className="h-7 w-10 shadow-[0_4px_12px_rgba(0,0,0,0.5)]" />
        <span className="text-[11px] font-medium uppercase tracking-wider text-foreground/90">
          {t.name}
        </span>
      </div>
    </motion.button>
  );
}

function SelectStep({ home, away, setHome, setAway, onAdvance }: { home: Team | null; away: Team | null; setHome: (t: Team | null) => void; setAway: (t: Team | null) => void; onAdvance: () => void }) {
  const pick = (t: Team) => {
    if (home?.id === t.id) return setHome(null);
    if (away?.id === t.id) return setAway(null);
    if (!home) setHome(t);
    else if (!away) setAway(t);
  };
  return (
    <div className="mt-6 space-y-6">
      <div className="flex flex-col gap-3 md:flex-row">
        <TeamSlot team={home} label="Time 1" onClear={() => setHome(null)} />
        <div className="grid place-items-center font-display text-xs uppercase tracking-[0.4em] text-gold">vs</div>
        <TeamSlot team={away} label="Time 2" onClear={() => setAway(null)} />
      </div>

      <SectionTitle accent="48 NAÇÕES">Escolha as seleções</SectionTitle>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
        {ALL_TEAMS.filter((t) => WC2026_TEAM_IDS.has(t.id)).map((t, i) => {
          const picked = home?.id === t.id || away?.id === t.id;
          return (
            <TeamSelectButton
              key={t.id}
              t={t}
              picked={picked}
              index={i}
              onPick={pick}
            />
          );
        })}
      </div>

      <div className="flex justify-between">
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar</NeonButton></Link>
        <NeonButton disabled={!home || !away} onClick={onAdvance} className={!home || !away ? "opacity-40" : ""}>
          Avançar para Gerenciamento <ChevronRight className="h-4 w-4" />
        </NeonButton>
      </div>
    </div>
  );
}

function PlayerNode({ name, pos, x, y, delay = 0, mirrored = false }: { name: string; pos: string; x: number; y: number; delay?: number; mirrored?: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.4 }}
      animate={{ opacity: 1, scale: 1, left: `${x * 100}%`, top: `${y * 100}%` }}
      transition={{ type: "spring", stiffness: 120, damping: 14, delay }}
      className="absolute -translate-x-1/2 -translate-y-1/2 z-10"
    >
      <div className="flex flex-col items-center gap-1">
        <div className="relative h-11 w-11 overflow-visible rounded-full">
          <PlayerAvatar name={name} px={44} className={mirrored ? "ring-gold/60" : ""} />
          <span className="absolute -bottom-1 -right-1 rounded-sm bg-background/90 px-1 text-[8px] font-bold text-primary ring-1 ring-primary/50">{pos}</span>
        </div>
        <div className={`whitespace-nowrap rounded-sm bg-background/90 px-1.5 py-0.5 text-[10px] uppercase tracking-wider shadow-sm ${mirrored ? "text-gold" : "text-primary"}`}>{name}</div>
      </div>
    </motion.div>
  );
}

function Pitch({ teamA, teamB, formA, formB, rosterA, rosterB }: { teamA: Team; teamB: Team; formA: Formation; formB: Formation; rosterA: string[]; rosterB: string[] }) {
  const startersA = rosterA.slice(0, 11);
  const startersB = rosterB.slice(0, 11);

  const posA = FORMATIONS[formA].coords;
  const labelsA = FORMATIONS[formA].positions;
  const posB = FORMATIONS[formB].coords;
  const labelsB = FORMATIONS[formB].positions;

  return (
    <div className="relative aspect-[3/4] w-full overflow-hidden rounded-xl border border-primary/40 bg-pitch shadow-[inset_0_0_120px_oklch(0_0_0/.6)]">
      <div className="pointer-events-none absolute inset-3 rounded-md border border-primary/30" />
      <div className="pointer-events-none absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-primary/30" />
      <div className="pointer-events-none absolute left-3 right-3 top-1/2 h-px bg-primary/30" />
      <div className="pointer-events-none absolute left-1/2 top-3 h-20 w-44 -translate-x-1/2 border-l border-r border-b border-primary/30" />
      <div className="pointer-events-none absolute left-1/2 bottom-3 h-20 w-44 -translate-x-1/2 border-l border-r border-t border-primary/30" />
      <div className="pointer-events-none absolute inset-3 opacity-30 [background:repeating-linear-gradient(0deg,oklch(0.4_0.18_160/.0)_0_28px,oklch(0.45_0.2_160/.18)_28px_56px)]" />

      {posA.map(([x, y], i) => <PlayerNode key={`a${i}-${startersA[i]}`} pos={labelsA[i] ?? ""} name={startersA[i] ?? ""} x={x} y={0.5 + y * 0.5} delay={0.05 * i} />)}
      {posB.map(([x, y], i) => <PlayerNode key={`b${i}-${startersB[i]}`} pos={labelsB[i] ?? ""} name={startersB[i] ?? ""} x={1 - x} y={0.5 - y * 0.5} delay={0.05 * i + 0.3} mirrored />)}
    </div>
  );
}

function TeamColumn({ team, form, setForm, roster, setRoster, excluded, setExcluded }: { team: Team; form: Formation; setForm: (f: Formation) => void; roster: string[]; setRoster: (r: string[]) => void; excluded: string[]; setExcluded: (v: string[]) => void }) {
  const [selected, setSelected] = useState<number | null>(null);

  const swap = (i: number, j: number) => {
    if (i === j) return;
    const next = roster.slice();
    [next[i], next[j]] = [next[j], next[i]];
    setRoster(next);
  };

  const onPick = (idx: number) => {
    if (selected === null) return setSelected(idx);
    if (selected === idx) return setSelected(null);
    swap(selected, idx);
    setSelected(null);
  };

  const onDragStart = (e: React.DragEvent, idx: number) => { e.dataTransfer.setData("text/plain", String(idx)); setSelected(idx); };
  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); };
  const onDrop = (e: React.DragEvent, target: number) => {
    e.preventDefault();
    const src = Number(e.dataTransfer.getData("text/plain"));
    if (!Number.isNaN(src)) swap(src, target);
    setSelected(null);
  };

  const labels = FORMATIONS[form].positions;

  return (
    <Panel className="space-y-3 text-sm h-full overflow-y-auto pr-2 max-h-[80vh] custom-scrollbar">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TeamFlag teamId={team.id} className="h-6 w-9" />
          <div>
            <div className="font-display text-base uppercase tracking-widest">{team.name}</div>
            <select value={form} onChange={(e) => setForm(e.target.value as Formation)} className="mt-0.5 rounded border border-border bg-background/60 px-1.5 py-0.5 text-[11px] uppercase tracking-widest text-primary outline-none">
              {Object.keys(FORMATIONS).map((f) => <option key={f}>{f}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="flex gap-2 mt-1 mb-2">
        <button onClick={() => {
          fetch(`${API_BASE_URL}/api/roster/${team.apiName}`)
            .then(res => res.json())
            .then(data => {
              if (data.positions) {
                for (const [name, pos] of Object.entries(data.positions)) {
                  KNOWN_PLAYER_POSITIONS[normalizeName(name as string)] = POS_MAP[pos as string] || (pos as string);
                }
              }
              const arr = [...(data.starters || []), ...(data.bench || [])];
              if (arr.length > 0) setRoster(smartSort(arr.slice(0, 26)));
              setForm(formationFor(team.id));
            })
            .catch(() => {
              setRoster(smartSort(rosterFor(team.id).slice(0, 26)));
              setForm(formationFor(team.id));
            });
        }} className="w-full rounded border border-primary/30 bg-primary/10 py-1.5 text-[9px] uppercase tracking-wider text-primary hover:bg-primary/20 transition shadow-sm">
          Titulares (Padrão)
        </button>
      </div>
      <div className="mt-1 mb-2">
        <div className="text-[9px] uppercase tracking-[0.2em] text-red-400/80 mb-1">🏥 Desfalques / Lesões</div>

        {excluded.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {excluded.map(ex => (
              <div key={ex} className="flex items-center gap-1 rounded bg-red-900/40 border border-red-500/50 px-1.5 py-0.5 text-[10px] text-red-100">
                <span>{ex}</span>
                <button onClick={() => setExcluded(excluded.filter(e => e !== ex))} className="text-red-400 hover:text-red-100 font-bold">&times;</button>
              </div>
            ))}
          </div>
        )}

        <select
          value=""
          onChange={(e) => {
            const val = e.target.value;
            if (val && !excluded.includes(val)) {
              const newExcluded = [...excluded, val];
              setExcluded(newExcluded);

              const pIdx = roster.indexOf(val);
              if (pIdx > -1 && pIdx < 11) {
                const pos = getPlayerPosition(val) || "Midfielder";
                let newRoster = [...roster];

                let benchIdx = newRoster.findIndex((p, i) => i >= 11 && getPlayerPosition(p) === pos && !newExcluded.includes(p));
                if (benchIdx === -1) {
                  benchIdx = newRoster.findIndex((p, i) => i >= 11 && !newExcluded.includes(p));
                }

                if (benchIdx !== -1) {
                  [newRoster[pIdx], newRoster[benchIdx]] = [newRoster[benchIdx], newRoster[pIdx]];
                  setRoster(newRoster);
                }
              }
            }
          }}
          className="w-full rounded border border-border/50 bg-background px-1.5 py-1 text-[11px] text-foreground outline-none shadow-sm"
        >
          <option value="">+ Adicionar Desfalque</option>
          {roster.filter(p => !excluded.includes(p)).map((p) => <option key={`excl-${p}`} value={p}>{p}</option>)}
        </select>
      </div>

      <div className="text-[9px] uppercase tracking-[0.3em] text-muted-foreground">
        {selected === null ? "Clique para trocar jogador" : <span className="text-gold">Selecionado: {roster[selected]}</span>}
      </div>
      <div>
        <div className="mb-1 text-[10px] uppercase tracking-[0.3em] text-primary/80">Titulares</div>
        <ul className="space-y-1">
          {roster.slice(0, 11).map((n, i) => (
            <li key={`s-${i}-${n}`} draggable onDragStart={(e) => onDragStart(e, i)} onDragOver={onDragOver} onDrop={(e) => onDrop(e, i)} onClick={() => onPick(i)}
              className={`group flex cursor-pointer items-center justify-between gap-2 rounded-md border bg-background/40 px-2 py-1 text-[12px] transition ${selected === i ? "border-gold shadow-[0_0_14px_oklch(0.83_0.16_85/.7)]" : "border-primary/25"} ${excluded.includes(n) ? "opacity-40 grayscale line-through border-red-500/50" : ""}`} style={{ userSelect: "none" }}>
              <span className="flex items-center gap-2"><PlayerAvatar name={n} px={24} /><span className="truncate">{n}</span></span>
              <span className="text-[10px] text-primary">{labels[i]}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <div className="mb-1 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Reservas</div>
        <ul className="space-y-1">
          {roster.slice(11).map((n, i) => {
            const realIdx = i + 11;
            return (
              <li key={`b-${realIdx}-${n}`} draggable onDragStart={(e) => onDragStart(e, realIdx)} onDragOver={onDragOver} onDrop={(e) => onDrop(e, realIdx)} onClick={() => onPick(realIdx)}
                className={`group flex cursor-pointer items-center gap-2 rounded-md border bg-background/20 px-2 py-1 text-[11px] ${selected === realIdx ? "border-gold text-foreground" : "border-border/40"} ${excluded.includes(n) ? "opacity-30 grayscale line-through border-red-500/50" : ""}`} style={{ userSelect: "none" }}>
                <PlayerAvatar name={n} px={22} /><span className="truncate">{n}</span>
              </li>
            );
          })}
        </ul>
      </div>
    </Panel>
  );
}

function LineupStep({ home, away, formA, formB, setFormA, setFormB, rosterA, rosterB, setRosterA, setRosterB, excludedA, setExcludedA, excludedB, setExcludedB, stadium, setStadium, onBack, onSimulate }: any) {
  const STADIUMS = [
    "New York", "Los Angeles", "Dallas", "San Francisco", "Miami",
    "Seattle", "Boston", "Atlanta", "Houston", "Kansas City",
    "Philadelphia", "Vancouver", "Toronto", "Guadalajara",
    "Mexico City", "Monterrey"
  ];

  const [stadiumTemp, setStadiumTemp] = useState<number | null>(null);

  useEffect(() => {
    if (stadium) {
      fetch(`${API_BASE_URL}/api/weather?stadium=${encodeURIComponent(stadium)}`)
        .then(res => res.json())
        .then(data => {
          setStadiumTemp(data.temperature);
        })
        .catch(err => console.error("Erro ao buscar clima:", err));
    } else {
      setStadiumTemp(null);
    }
  }, [stadium]);

  return (
    <div className="mt-6 grid gap-5 lg:grid-cols-[260px_1fr_260px]">
      <TeamColumn team={home} form={formA} setForm={setFormA} roster={rosterA} setRoster={setRosterA} excluded={excludedA} setExcluded={setExcludedA} />

      <div className="flex flex-col gap-4">

        <div className="flex flex-col items-center gap-1.5">
          <span className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">🏟️ Sede da Partida (Clima)</span>
          <select
            value={stadium}
            onChange={e => setStadium(e.target.value)}
            className="rounded-md border border-border/50 bg-background/60 px-3 py-1.5 text-xs text-foreground outline-none text-center shadow-inner"
          >
            <option value="">Automático (Fase de Grupos)</option>
            {STADIUMS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <AnimatePresence>
            {stadium && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mt-2 w-full max-w-[240px] overflow-hidden rounded-md border border-primary/30 relative">
                <img
                  src={`/stadiums/${stadium.toLowerCase().replace(" ", "-")}.jpg`}
                  alt={stadium}
                  className="w-full aspect-[16/9] object-cover bg-background/40"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 16 9" preserveAspectRatio="none"><rect width="16" height="9" fill="%231a1a1a"/></svg>';
                  }}
                />
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent p-2 text-center pt-6">
                  <span className="text-xs font-bold text-white flex items-center justify-center gap-1.5 drop-shadow-md">
                    {stadiumTemp !== null ? (
                      <>
                        {stadiumTemp > 28 ? '🔥' : stadiumTemp < 15 ? '❄️' : '🌡️'}
                        {stadiumTemp}°C
                      </>
                    ) : 'Buscando clima...'}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <Pitch teamA={home} teamB={away} formA={formA} formB={formB} rosterA={rosterA} rosterB={rosterB} />

        <div className="flex items-center justify-between gap-3">
          <NeonButton variant="ghost" onClick={onBack}><ArrowLeft className="h-4 w-4" /> Voltar</NeonButton>
          <NeonButton onClick={onSimulate} className="animate-pulse-neon flex-1"><Play className="h-4 w-4" /> Iniciar Simulação</NeonButton>
        </div>
      </div>

      <TeamColumn team={away} form={formB} setForm={setFormB} roster={rosterB} setRoster={setRosterB} excluded={excludedB} setExcluded={setExcludedB} />
    </div>
  );
}

function ResultStep({ home, away, result, onBack, onMenu }: { home: Team; away: Team; result: APIResult; onBack: () => void; onMenu: () => void }) {
  const [showFezinha, setShowFezinha] = useState(false);

  const topScores = useMemo(() => Object.entries(result.scoreCounts).sort((a, b) => b[1] - a[1]).slice(0, 5), [result]);

  const fezinhaStats = useMemo(() => {
    if (result.fezinhaData) return result.fezinhaData;
    return {
      over25Pct: result.vegasData?.over_2_5 ? result.vegasData.over_2_5 * 100 : 0,
      bttsPct: result.vegasData?.btts_yes ? result.vegasData.btts_yes * 100 : 0,
      expectedCorners: 0,
      expectedCards: 0,
      source: "Indisponível"
    };
  }, [result]);
  return (
    <div className="mt-6 space-y-5">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <SectionTitle accent="400 SIMULAÇÕES">Simulação Concluída (Motor Quant)</SectionTitle>
      </motion.div>

      <div className="grid gap-5 md:grid-cols-3">
        {[
          { team: home, pct: result.aWinPct, label: `Vitória ${home.name}`, color: "neon" as const },
          { label: "Empate", pct: result.drawPct, color: "gold" as const },
          { team: away, pct: result.bWinPct, label: `Vitória ${away.name}`, color: "neon" as const },
        ].map((c, i) => (
          <motion.div key={i} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.1 }}>
            <Panel glow={c.color}>
              <div className="flex flex-col items-center gap-2 text-center">
                {(c as any).team ? <TeamFlag teamId={(c as any).team.id} className="h-8 w-12" /> : <div className="text-3xl">🤝</div>}
                <div className="font-display text-xs uppercase tracking-[0.3em] text-muted-foreground">{c.label}</div>
                <div className={`font-display text-4xl font-bold ${c.color === "gold" ? "text-gold" : "text-neon"}`}>{c.pct.toFixed(1)}%</div>
              </div>
            </Panel>
          </motion.div>
        ))}
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        <Panel className="md:col-span-1">
          {result.hasVegasOdds ? (
            <div className="mb-4 rounded-md border border-gold/50 bg-gold/10 p-3 text-center shadow-[0_0_20px_rgba(255,215,0,0.2)]">
              <div className="font-display text-[10px] uppercase tracking-[0.2em] text-gold/90">🔮 Previsão do Modelo Estatístico</div>
              <div className="mt-1 font-display text-lg text-gold">{result.expectedScore}</div>
            </div>
          ) : (
            <div className="mb-4 rounded-md border border-neon/30 bg-neon/5 p-3 text-center">
              <div className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Placar Exato Médio</div>
              <div className="mt-1 font-display text-lg text-neon">{result.expectedScore}</div>
            </div>
          )}

          <div className="mb-3 flex items-center justify-between">
            <div className="font-display text-sm uppercase tracking-[0.3em] text-foreground/90">Mais prováveis</div>
            <BarChart3 className="h-4 w-4 text-primary" />
          </div>
          <ul className="space-y-2">
            {topScores.map(([s, n], i) => {
              const pct = (n / 400) * 100;
              return (
                <li key={s} className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 font-display tabular-nums text-foreground/90">
                      <TeamFlag teamId={home.id} className="h-4 w-6" /> {s} <TeamFlag teamId={away.id} className="h-4 w-6" />
                    </span>
                    <span className="text-xs text-primary">{pct.toFixed(1)}%</span>
                  </div>
                  <motion.div initial={{ width: 0 }} animate={{ width: `${pct * 2}%` }} transition={{ delay: 0.1 + i * 0.06, duration: 0.7 }} className="mt-1 h-1.5 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
                </li>
              );
            })}
          </ul>
        </Panel>

        <Panel glow="gold" className="md:col-span-1">
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em]">Artilheiros</div>
          <ol className="space-y-2">
            {result.topScorers.slice(0, 5).map((s, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                <div className="flex items-center gap-3">
                  <span className="font-display text-gold tabular-nums">{i + 1}</span>
                  <PlayerAvatar name={s.player} px={28} />
                  <span className="text-sm">{s.player}</span>
                </div>
                <span className="font-display text-primary">{s.goals} G</span>
              </motion.li>
            ))}
          </ol>
        </Panel>

        <Panel glow="neon" className="md:col-span-1">
          <div className="mb-3 font-display text-sm uppercase tracking-[0.3em]">Garçons (Assist.)</div>
          <ol className="space-y-2">
            {result.topAssists.slice(0, 5).map((s, i) => (
              <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }} className="flex items-center justify-between rounded-md border border-border/40 bg-background/30 px-3 py-2">
                <div className="flex items-center gap-3">
                  <span className="font-display text-neon tabular-nums">{i + 1}</span>
                  <PlayerAvatar name={s.player} px={28} />
                  <span className="text-sm">{s.player}</span>
                </div>
                <span className="font-display text-primary">{s.assists} A</span>
              </motion.li>
            ))}
            {result.topAssists.length === 0 && (
              <div className="text-xs text-muted-foreground p-3 text-center">Nenhuma assistência simulada</div>
            )}
          </ol>
        </Panel>
      </div>

      {result.fezinhaData && (
        <div className="rounded-xl border border-gold/40 bg-card/60 backdrop-blur-md overflow-hidden transition-all">
          <button onClick={() => setShowFezinha(!showFezinha)} className="w-full flex items-center justify-between p-4 bg-gold/10 hover:bg-gold/20 transition-colors">
            <div className="flex items-center gap-2">
              <span className="text-xl">📊</span>
              <span className="font-display text-sm uppercase tracking-[0.3em] text-gold font-bold">Projeção Estatística ({fezinhaStats.source.replace('Vegas', 'Modelo')})</span>
            </div>
            <ChevronRight className={`h-5 w-5 text-gold transition-transform ${showFezinha ? "rotate-90" : ""}`} />
          </button>
          
          <AnimatePresence>
            {showFezinha && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="border-t border-gold/20">
                <div className="p-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded border border-primary/20 bg-background/50 p-3 lg:col-span-1">
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Mais de 2.5 Gols</div>
                    <div className="flex items-end justify-between">
                      <span className="text-2xl font-bold text-foreground">{fezinhaStats.over25Pct > 0 ? fezinhaStats.over25Pct.toFixed(1) + '%' : 'Indisponível'}</span>
                    </div>
                    <div className="mt-1 text-[10px] text-primary">{fezinhaStats.over25Pct > 60 ? "🔥 Muito Provável" : fezinhaStats.over25Pct > 0 && fezinhaStats.over25Pct < 40 ? "❄️ Improvável" : "⚖️ Equilibrado"}</div>
                  </div>
                  <div className="rounded border border-primary/20 bg-background/50 p-3 lg:col-span-1">
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Ambas Marcam (BTTS)</div>
                    <div className="flex items-end justify-between">
                      <span className="text-2xl font-bold text-foreground">{fezinhaStats.bttsPct > 0 ? fezinhaStats.bttsPct.toFixed(1) + '%' : 'Indisponível'}</span>
                    </div>
                    <div className="mt-1 text-[10px] text-primary">{fezinhaStats.bttsPct > 60 ? "🔥 Muito Provável" : fezinhaStats.bttsPct > 0 && fezinhaStats.bttsPct < 40 ? "❄️ Improvável" : "⚖️ Equilibrado"}</div>
                  </div>
                  <div className="rounded border border-primary/20 bg-background/50 p-3 lg:col-span-1">
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Escanteios Esperados</div>
                    <div className="flex items-end justify-between">
                      <span className="text-2xl font-bold text-foreground">{fezinhaStats.expectedCorners > 0 ? fezinhaStats.expectedCorners.toFixed(1) : 'Indisponível'}</span>
                    </div>
                    <div className="mt-1 text-[10px] text-primary">Média do confronto (Total)</div>
                  </div>
                  <div className="rounded border border-primary/20 bg-background/50 p-3 lg:col-span-1">
                    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Cartões Esperados</div>
                    <div className="flex items-end justify-between">
                      <span className="text-2xl font-bold text-foreground">{fezinhaStats.expectedCards > 0 ? fezinhaStats.expectedCards.toFixed(1) : 'Indisponível'}</span>
                    </div>
                    <div className="mt-1 text-[10px] text-primary">Atenção ao árbitro!</div>
                  </div>
                  
                  <div className="md:col-span-2 lg:col-span-4 rounded border border-gold/30 bg-gold/5 p-3">
                    <div className="text-[10px] uppercase tracking-widest text-gold/80 mb-2">Análise do Modelo</div>
                    <p className="text-sm text-foreground/90">
                      {fezinhaStats.over25Pct > 65 ? "O modelo espera um jogo recheado de gols! Alta expectativa de mais de 2.5 gols." : 
                       fezinhaStats.bttsPct > 65 ? "Ambas as defesas cedem espaços. Alta probabilidade de ambas as equipes marcarem." :
                       fezinhaStats.expectedCorners > 10.5 ? "As duas equipes exploram muito as linhas de fundo. Alta expectativa de escanteios (mais de 9.5)." :
                       fezinhaStats.expectedCards > 4.5 ? "Jogo promete ser tenso e pegado. Fique de olho na quantidade de cartões e na linha do árbitro." :
                       "O modelo prevê um jogo truncado e tático! Alta probabilidade de poucos gols (menos de 2.5) e jogo equilibrado."}
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      <Panel>
        <div className="mb-3 flex items-center justify-between">
          <div className="font-display text-sm uppercase tracking-[0.3em]">Log Completo das 400 Simulações</div>
          <div className="text-xs text-muted-foreground">Expected Goals: <span className="text-primary">{result.avgGoals.a.toFixed(2)}</span> – <span className="text-primary">{result.avgGoals.b.toFixed(2)}</span></div>
        </div>
        <div className="max-h-96 overflow-y-auto pr-2 text-xs font-mono text-muted-foreground whitespace-pre-line rounded border border-border/30 bg-background/30 p-3 custom-scrollbar">
          {result.sim_logs && result.sim_logs.length > 0 ? result.sim_logs.join("\n") : "Sem log disponível."}
        </div>
      </Panel>

      <div className="flex flex-wrap justify-between gap-3">
        <NeonButton variant="ghost" onClick={onBack}><ArrowLeft className="h-4 w-4" /> Voltar</NeonButton>
        <div className="flex gap-3">
          <Link to="/copa"><NeonButton variant="gold">Ver Torneio Completo</NeonButton></Link>
          <NeonButton onClick={onMenu}>Nova Partida</NeonButton>
        </div>
      </div>
    </div>
  );
}