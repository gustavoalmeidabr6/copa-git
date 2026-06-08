// src/components/sim/SimulationTransition.tsx
import { motion, AnimatePresence } from "motion/react";
import { useEffect, useRef } from "react";

export interface SimulationTransitionProps {
  isActive: boolean;
  playerImageUrl: string;
  onBlindSpot?: () => void;
  onComplete?: () => void;
}

// Configuração do efeito "Sandevistan" (Rastros do jogador)
const GHOST_TRAILS = [
  // Magenta/Rosa
  { delay: 0.13, opacity: 0.6, filter: "hue-rotate(290deg) saturate(4) brightness(1.3) drop-shadow(10px 0 15px rgba(255,0,255,0.8))" },
  // Ciano
  { delay: 0.16, opacity: 0.4, filter: "hue-rotate(180deg) saturate(4) brightness(1.3) drop-shadow(-10px 0 15px rgba(0,255,255,0.8))" },
  // Verde Limão
  { delay: 0.19, opacity: 0.2, filter: "hue-rotate(90deg) saturate(4) brightness(1.3) drop-shadow(10px 0 15px rgba(0,255,100,0.8))" },
  // Amarelo
  { delay: 0.22, opacity: 0.1, filter: "hue-rotate(45deg) saturate(4) brightness(1.5) drop-shadow(-10px 0 15px rgba(255,255,0,0.8))" },
];

export function SimulationTransition({
  isActive,
  playerImageUrl,
  onBlindSpot,
  onComplete,
}: SimulationTransitionProps) {
  const blindFired = useRef(false);

  useEffect(() => {
    // Reseta o bloqueio sempre que a transição for iniciada
    if (isActive) {
      blindFired.current = false;
    }
  }, [isActive]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div 
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[999999] flex items-center justify-center pointer-events-none overflow-hidden"
        >
          {/* Camada 1 - Amarelo */}
          <motion.div 
            initial={{ x: "-120%", skewX: -15 }}
            animate={{ x: ["-120%", "-5%", "5%", "120%"] }}
            transition={{ duration: 2.2, times: [0, 0.15, 0.85, 1], ease: ["easeOut", "linear", "easeIn"] }}
            className="absolute inset-0 -left-[20%] w-[140%] bg-yellow-400"
          />
          
          {/* Camada 2 - Verde */}
          <motion.div 
            initial={{ x: "-120%", skewX: -15 }}
            animate={{ x: ["-120%", "-5%", "5%", "120%"] }}
            transition={{ duration: 2.2, times: [0, 0.15, 0.85, 1], ease: ["easeOut", "linear", "easeIn"], delay: 0.05 }}
            className="absolute inset-0 -left-[20%] w-[140%] bg-green-600"
          />

          {/* Camada 3 - Azul Escuro (Principal) */}
          <motion.div 
            initial={{ x: "-120%", skewX: -15 }}
            animate={{ x: ["-120%", "-5%", "5%", "120%"] }}
            transition={{ duration: 2.2, times: [0, 0.15, 0.85, 1], ease: ["easeOut", "linear", "easeIn"], delay: 0.1 }}
            className="absolute inset-0 -left-[20%] w-[140%] bg-blue-900 shadow-[-15px_0_30px_rgba(0,0,0,0.5)] flex items-center justify-center overflow-hidden"
            onUpdate={(latest) => {
               const xStr = latest.x;
               if (typeof xStr === "string" && xStr.includes("%")) {
                   const val = parseFloat(xStr);
                   if (val > -20 && !blindFired.current) {
                       blindFired.current = true;
                       onBlindSpot?.();
                   }
               }
            }}
            onAnimationComplete={() => {
                onComplete?.();
            }}
          >
            <div className="w-screen h-screen flex items-center justify-center relative transform skew-x-[15deg]">
              
              {/* WRAPPER DO GLITCH: Aplica o efeito cibernético em todo o conteúdo (Texto, Cópias e Jogador) no meio da tela */}
              <motion.div
                 className="absolute inset-0 flex items-center justify-center"
                 animate={{
                    x: [0, 0, -30, 40, -20, 10, 0, 0],
                    y: [0, 0, 15, -15, 20, -10, 0, 0],
                    filter: [
                        "none",
                        "none",
                        "contrast(1.5) brightness(1.5) hue-rotate(90deg) saturate(2)",
                        "invert(0.8) drop-shadow(15px 0 0 red)",
                        "contrast(1.2) sepia(1) hue-rotate(-90deg) drop-shadow(-15px 0 0 blue)",
                        "brightness(1.5)",
                        "none",
                        "none"
                    ],
                    opacity: [1, 1, 0.8, 1, 0.9, 1, 1, 1]
                 }}
                 transition={{
                    duration: 2.2,
                    delay: 0.1, // Sincroniza com o fundo azul
                    times: [0, 0.45, 0.47, 0.49, 0.51, 0.53, 0.55, 1], // Fica quieto, pipoca loucamente no meio, e estabiliza
                    ease: "linear"
                 }}
              >
                  {/* TEXTO DE FUNDO */}
                  <motion.div 
                    initial={{ x: "60vw" }}
                    animate={{ x: "-60vw" }}
                    transition={{ duration: 2.2, ease: "linear", delay: 0.1 }}
                    className="absolute font-black text-[12vw] text-white uppercase italic opacity-[0.03] whitespace-nowrap z-0"
                  >
                    SIMULANDO RESULTADO
                  </motion.div>

                  {/* CÓPIAS FANTASMAS (SANDEVISTAN) - Renderizadas por baixo do jogador */}
                  {GHOST_TRAILS.map((ghost, i) => (
                    <motion.img 
                      key={`ghost-${i}`}
                      src={playerImageUrl} 
                      initial={{ x: "-60vw", scale: 1.0, opacity: 0 }}
                      animate={{ 
                         x: ["-60vw", "-5vw", "5vw", "120vw"],
                         scale: [1.05, 1.1, 1.15, 1.2],
                         opacity: [0, ghost.opacity, ghost.opacity, 0],
                         filter: [
                           "brightness(1)", 
                           ghost.filter, 
                           ghost.filter, 
                           "brightness(1)"
                         ]
                      }}
                      transition={{ 
                         duration: 2.2, 
                         times: [0, 0.15, 0.85, 1], 
                         ease: ["easeOut", "linear", "easeIn"], 
                         delay: ghost.delay 
                      }}
                      className="absolute bottom-[-2vh] h-[90vh] object-contain blur-[2px] mix-blend-screen z-10" 
                      onError={(e) => { e.currentTarget.style.display = 'none'; }}
                    />
                  ))}
                  
                  {/* JOGADOR PRINCIPAL - Renderizado por cima */}
                  <motion.img 
                    src={playerImageUrl} 
                    initial={{ x: "-60vw", scale: 1.0, opacity: 0 }}
                    animate={{ 
                       x: ["-60vw", "-5vw", "5vw", "120vw"],
                       scale: [1.05, 1.1, 1.15, 1.2],
                       opacity: [0, 1, 1, 0],
                       filter: [
                         "brightness(1) drop-shadow(0px 0px 0px rgba(0,0,0,0))", 
                         "brightness(1.2) drop-shadow(0px 0px 30px rgba(250,204,21,0.5))", 
                         "brightness(1) drop-shadow(15px 15px 25px rgba(0,0,0,0.6))", 
                         "brightness(1)"
                       ]
                    }}
                    transition={{ 
                       duration: 2.2, 
                       times: [0, 0.15, 0.85, 1], 
                       ease: ["easeOut", "linear", "easeIn"], 
                       delay: 0.1 
                    }}
                    className="absolute bottom-[-2vh] h-[90vh] object-contain z-20" 
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />

              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}