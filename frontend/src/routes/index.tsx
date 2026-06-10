// src/routes/index.tsx
import { createFileRoute, Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "motion/react";
import { useState, useEffect } from "react";
import { ALL_TEAMS } from "@/lib/teams";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { NeonButton, Panel, CornerTicks } from "@/components/sim/ui";
import { ChevronLeft, ChevronRight, Settings, Trophy, Swords } from "lucide-react";
import { TeamFlag } from "@/lib/visuals";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Ultra Simulador Copa do Mundo 2026" },
      { name: "description", content: "Simulador de alta fidelidade da Copa do Mundo 2026 — simule a Copa inteira ou partidas específicas com estatísticas detalhadas." },
      { property: "og:title", content: "Ultra Simulador Copa do Mundo 2026" },
      { property: "og:description", content: "Simulador premium da Copa do Mundo com chaveamento, escalações e 200 simulações por partida." },
    ],
  }),
  component: Index,
});

const FAVS = ["BRA", "ARG", "FRA", "ESP", "ENG", "GER", "POR", "NED"];

function Index() {
  const [active, setActive] = useState(0);
  const teams = FAVS.map((id) => ALL_TEAMS.find((t) => t.id === id)!);
  const team = teams[active];

  useEffect(() => {
    const timer = setInterval(() => {
      setActive((prev) => (prev + 1) % teams.length);
    }, 2000);
    return () => clearInterval(timer);
  }, [teams.length]);

  return (
    <NeonChrome>
      <main className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-6 py-8">
        <header className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
          <span>v1.0.0 · Ultra Simulador 2026</span>
          <span className="flex items-center gap-2">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
            Servidores online
          </span>
        </header>

        <section className="relative mt-10 flex flex-col items-center text-center">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="font-display"
          >
            <p className="text-sm uppercase tracking-[0.5em] text-primary/80">Ultra</p>
            <h1 className="mt-1 text-6xl font-bold uppercase leading-none md:text-8xl">
              <span className="block">Simulador</span>
              <span
                className="mt-1 block"
                style={{
                  background: 'linear-gradient(90deg, #fff 0%, #ffe566 12%, #ffb347 28%, #ff6b35 45%, #ff4081 62%, #e040fb 76%, #ffb347 88%, #fff 100%)',
                  backgroundSize: '200% auto',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  animation: 'gradientShift 4s linear infinite',
                }}
              >
                Copa do Mundo 2026
              </span>
            </h1>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, type: "spring", stiffness: 150 }}
            className="mt-10"
          >
            <p className="text-xs uppercase tracking-[0.4em] text-muted-foreground">Seleção ativa</p>
            <div className="mt-3 flex items-center gap-6">
              <button
                onClick={() => setActive((a) => (a - 1 + teams.length) % teams.length)}
                className="text-primary/70 transition hover:text-primary"
              >
                <ChevronLeft className="h-7 w-7" />
              </button>
              <AnimatePresence mode="wait">
                <motion.div
                  key={team.id}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  transition={{ duration: 0.35 }}
                  className="flex items-center gap-4"
                >
                  <TeamFlag teamId={team.id} className="h-12 w-20" />
                  <span className="font-display text-3xl font-semibold uppercase tracking-[0.2em]">{team.name}</span>
                </motion.div>
              </AnimatePresence>
              <button
                onClick={() => setActive((a) => (a + 1) % teams.length)}
                className="text-primary/70 transition hover:text-primary"
              >
                <ChevronRight className="h-7 w-7" />
              </button>
            </div>
            <div className="mt-4 flex justify-center gap-2">
              {teams.map((_, i) => (
                <span key={i} className={`h-1.5 rounded-full transition-all ${i === active ? "w-6 bg-primary shadow-[0_0_8px_var(--primary)]" : "w-1.5 bg-muted"}`} />
              ))}
            </div>
          </motion.div>
        </section>

        <section className="mx-auto mt-14 grid w-full max-w-3xl grid-cols-1 gap-5 md:grid-cols-2">
          {[
            { to: "/copa", title: "Simular", sub: "Copa do Mundo", glow: "gold" as const, icon: <Trophy className="h-20 w-20 text-gold drop-shadow-[0_0_24px_var(--gold)]" /> },
            { to: "/partida", title: "Partida Amistosa", sub: "1 vs 1 Simulador", glow: "gold" as const, icon: <Swords className="h-20 w-20 text-gold/80 drop-shadow-[0_0_15px_var(--gold)]" /> },
          ].map((c, i) => (
            <motion.div
              key={c.to}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + i * 0.12, type: "spring", stiffness: 120 }}
            >
              <Link to={c.to}>
                <motion.div
                  whileHover={{ y: -6, scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="group relative flex aspect-[4/3] flex-col items-center justify-between overflow-hidden rounded-xl p-6 transition-all"
                  style={{ background: "linear-gradient(180deg, oklch(0.22 0.05 215 / .85), oklch(0.13 0.04 210 / .9))" }}
                >
                  <CornerTicks />
                  <div className={`absolute -inset-px rounded-xl opacity-60 transition group-hover:opacity-100 ${c.glow === "gold" ? "gold-border" : "neon-border"}`} />
                  <div className="relative flex flex-1 items-center justify-center">{c.icon}</div>
                  <div className="relative text-center font-display uppercase tracking-[0.2em]">
                    {c.title && <div className="text-xs text-muted-foreground">{c.title}</div>}
                    <div className={`text-xl ${c.glow === "gold" ? "text-gold" : "text-neon"}`}>{c.sub}</div>
                  </div>
                  <div className="absolute bottom-3 right-3 text-primary/60 transition group-hover:text-primary">→</div>
                </motion.div>
              </Link>
            </motion.div>
          ))}
        </section>
      </main>
    </NeonChrome>
  );
}