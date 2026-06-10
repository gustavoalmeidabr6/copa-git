import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { FlappyGame } from "./FlappyGame";

export function SimOverlay({ label = "Simulando", withGame = false }: { label?: string; withGame?: boolean }) {
  const [n, setN] = useState(0);

  useEffect(() => {
    const target = 400;
    const start = Date.now();
    const dur = 1800;
    let raf = 0;

    const tick = () => {
      const t = Math.min(1, (Date.now() - start) / dur);
      setN(Math.floor(target * (1 - Math.pow(1 - t, 3))));
      
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      } else {
        setN(400); 
      }
    };
    
    raf = requestAnimationFrame(tick);
    
    return () => cancelAnimationFrame(raf);
  }, []); 

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="fixed inset-0 z-50 grid place-items-center bg-background/95 backdrop-blur-xl">
      <div className="relative flex flex-col items-center gap-2 w-full">
        <div className="font-display text-[10px] uppercase tracking-[0.5em] text-primary/70 mb-2">{label}</div>
        
        {withGame ? (
          <FlappyGame />
        ) : (
          <div className="relative flex flex-col items-center gap-6 mt-4 mb-4">
            <div className="relative">
              <div className="font-display text-8xl font-bold text-neon tabular-nums">{n.toString().padStart(3, "0")}</div>
              <motion.div className="absolute -inset-8 -z-10 rounded-full" animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 1.2, repeat: Infinity }} style={{ background: "radial-gradient(circle, oklch(0.82 0.23 152 / 0.35), transparent 60%)" }} />
            </div>
            
            <div className="pointer-events-none absolute inset-x-0 -bottom-32 grid grid-cols-12 gap-2 opacity-30">
              {Array.from({ length: 60 }).map((_, i) => (
                <motion.span key={i} className="block h-4 w-full text-center font-mono text-[10px] text-primary" animate={{ y: [-10, 30] }} transition={{ duration: 1 + (i % 5) * 0.2, repeat: Infinity, delay: (i % 7) * 0.1 }}>
                  {"⚽◉⬢"[i % 3]}
                </motion.span>
              ))}
            </div>
          </div>
        )}

        {withGame ? (
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground mt-2 z-10">Processando {n}/400 simulações no motor</div>
        ) : (
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-muted-foreground z-10">processando simulações</div>
        )}

        <div className="relative h-1 w-64 overflow-hidden rounded-full bg-muted z-10 mt-1">
          <motion.div className="absolute inset-y-0 bg-primary shadow-[0_0_12px_var(--primary)]" initial={{ width: 0 }} animate={{ width: "100%" }} transition={{ duration: 2.5, ease: "easeOut" }} />
        </div>
      </div>
    </motion.div>
  );
}