import { motion, type HTMLMotionProps } from "motion/react";
import { cn } from "@/lib/utils";
import { forwardRef } from "react";

export const NeonButton = forwardRef<HTMLButtonElement, HTMLMotionProps<"button"> & { variant?: "neon" | "gold" | "ghost" }>(
  ({ className, variant = "neon", children, ...props }, ref) => {
    const styles =
      variant === "gold"
        ? "border-gold/60 text-gold shadow-[0_0_18px_oklch(0.83_0.16_85/.35)] hover:shadow-[0_0_28px_oklch(0.83_0.16_85/.65)]"
        : variant === "ghost"
        ? "border-border/60 text-foreground/80 hover:text-foreground hover:border-primary/60"
        : "border-primary/60 text-primary shadow-[0_0_18px_oklch(0.82_0.23_152/.35)] hover:shadow-[0_0_28px_oklch(0.82_0.23_152/.7)]";
    return (
      <motion.button
        ref={ref}
        whileHover={{ y: -2, scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        className={cn(
          "relative inline-flex items-center justify-center gap-2 rounded-md border bg-card/40 px-5 py-3 font-display text-sm uppercase tracking-widest backdrop-blur-sm transition-all",
          styles,
          className,
        )}
        {...props}
      >
        <span className="absolute inset-0 rounded-md opacity-0 transition-opacity hover:opacity-100 [background:linear-gradient(90deg,transparent,oklch(0.82_0.23_152/.12),transparent)]" />
        {children as React.ReactNode}
      </motion.button>
    );
  },
);
NeonButton.displayName = "NeonButton";

export function Panel({ className, children, glow = "neon" }: { className?: string; children: React.ReactNode; glow?: "neon" | "gold" | "none" }) {
  const g = glow === "gold" ? "gold-border" : glow === "neon" ? "neon-border" : "";
  return <div className={cn("glass-card rounded-xl p-5", g, className)}>{children}</div>;
}

export function CornerTicks() {
  const C = "absolute h-3 w-3 border-primary/70";
  return (
    <>
      <span className={`${C} top-0 left-0 border-t border-l`} />
      <span className={`${C} top-0 right-0 border-t border-r`} />
      <span className={`${C} bottom-0 left-0 border-b border-l`} />
      <span className={`${C} bottom-0 right-0 border-b border-r`} />
    </>
  );
}

export function SectionTitle({ children, accent }: { children: React.ReactNode; accent?: string }) {
  return (
    <h2 className="font-display text-2xl uppercase tracking-[0.2em] text-foreground/90">
      {children}{" "}
      {accent && <span className="text-neon">{accent}</span>}
    </h2>
  );
}
