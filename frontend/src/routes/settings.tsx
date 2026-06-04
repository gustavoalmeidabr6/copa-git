import { createFileRoute, Link } from "@tanstack/react-router";
import { NeonChrome } from "@/components/sim/StadiumBg";
import { Panel, NeonButton, SectionTitle } from "@/components/sim/ui";
import { ArrowLeft } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings · Ultra Simulador 2026" }] }),
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <NeonChrome>
      <main className="mx-auto max-w-3xl px-6 py-10">
        <Link to="/"><NeonButton variant="ghost"><ArrowLeft className="h-4 w-4" /> Voltar</NeonButton></Link>
        <div className="mt-8 space-y-6">
          <SectionTitle accent="SETTINGS">Preferências</SectionTitle>
          <Panel>
            <ul className="divide-y divide-border/40">
              {["Efeitos visuais", "Sons", "Velocidade de simulação", "Idioma", "Modo de exibição"].map((s) => (
                <li key={s} className="flex items-center justify-between py-3 text-sm">
                  <span className="text-foreground/85">{s}</span>
                  <span className="text-xs uppercase tracking-widest text-primary">Ultra</span>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </main>
    </NeonChrome>
  );
}
