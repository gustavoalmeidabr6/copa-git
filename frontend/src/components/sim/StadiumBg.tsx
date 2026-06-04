import { motion } from "motion/react";

export function StadiumBg({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none fixed inset-0 -z-10 overflow-hidden ${className}`}>
      <div className="absolute inset-0 bg-pitch opacity-90" />
      <div className="absolute inset-0 [background:radial-gradient(ellipse_at_top,oklch(0.45_0.2_200/.35),transparent_55%)]" />
      {/* stadium lights */}
      <div className="absolute inset-x-0 top-0 h-1/2 [background:repeating-linear-gradient(180deg,oklch(0.85_0.15_200/.06)_0_2px,transparent_2px_8px)] opacity-40" />
      {/* particles */}
      {Array.from({ length: 28 }).map((_, i) => (
        <motion.span
          key={i}
          className="absolute h-1 w-1 rounded-full bg-primary/70 shadow-[0_0_8px_var(--primary)]"
          style={{ left: `${(i * 37) % 100}%`, top: `${(i * 53) % 100}%` }}
          animate={{ y: [0, -20, 0], opacity: [0.2, 1, 0.2] }}
          transition={{ duration: 4 + (i % 5), repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
      {/* horizon grid */}
      <div className="absolute bottom-0 inset-x-0 h-2/3 opacity-30 [background:linear-gradient(180deg,transparent,oklch(0.4_0.2_160/.4)),repeating-linear-gradient(90deg,oklch(0.82_0.23_152/.25)_0_1px,transparent_1px_60px),repeating-linear-gradient(0deg,oklch(0.82_0.23_152/.25)_0_1px,transparent_1px_60px)] [mask-image:linear-gradient(0deg,black,transparent)]" />
    </div>
  );
}

export function NeonChrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen text-foreground">
      <StadiumBg />
      {children}
    </div>
  );
}
