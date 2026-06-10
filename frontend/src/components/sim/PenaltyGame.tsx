import { useState, useRef, useEffect } from "react";
import { motion, useAnimation } from "motion/react";

export function PenaltyGame() {
  const [score, setScore] = useState(0);
  const [attempts, setAttempts] = useState(0);
  const [message, setMessage] = useState("Chute para o gol!");
  const [gameState, setGameState] = useState<"idle" | "dragging" | "shot" | "result">("idle");
  
  const ballControls = useAnimation();
  const gkControls = useAnimation();
  const goalRef = useRef<HTMLDivElement>(null);

  const resetGame = async () => {
    setGameState("idle");
    setMessage("Chute para o gol!");
    await Promise.all([
      ballControls.start({ x: 0, y: 0, scale: 1, transition: { duration: 0.3 } }),
      gkControls.start({ x: 0, y: 0, rotate: 0, transition: { duration: 0.3 } })
    ]);
  };

  const handleDragStart = () => {
    if (gameState !== "idle") return;
    setGameState("dragging");
    setMessage("Solte para chutar!");
  };

  const handleDragEnd = async (event: any, info: { offset: { x: number, y: number }, velocity: { x: number, y: number } }) => {
    if (gameState !== "dragging") return;
    setGameState("shot");

    // Calcular o destino da bola com base no arraste e na velocidade
    const velocityMultiplier = 0.2;
    const targetX = info.offset.x + info.velocity.x * velocityMultiplier;
    const targetY = info.offset.y + info.velocity.y * velocityMultiplier;

    // Se não jogou pra frente (pra cima), reseta
    if (targetY > -50) {
      resetGame();
      return;
    }

    // Animar bola
    ballControls.start({
      x: targetX,
      y: targetY,
      scale: 0.6,
      transition: { type: "spring", damping: 20, stiffness: 100 }
    });

    // Decisão do goleiro
    const gkMoves = [
      { x: -100, y: -40, rotate: -45 }, // Pula esquerda
      { x: 100, y: -40, rotate: 45 },  // Pula direita
      { x: 0, y: -80, rotate: 0 },     // Pula meio (alto)
      { x: -60, y: 0, rotate: -90 },   // Cai esquerda
      { x: 60, y: 0, rotate: 90 },     // Cai direita
      { x: 0, y: 0, rotate: 0 },       // Fica parado
    ];
    const gkChoice = gkMoves[Math.floor(Math.random() * gkMoves.length)];

    gkControls.start({
      x: gkChoice.x,
      y: gkChoice.y,
      rotate: gkChoice.rotate,
      transition: { type: "spring", damping: 15, stiffness: 120, delay: 0.1 }
    });

    // Esperar a animação "terminar" para ver o resultado
    await new Promise(r => setTimeout(r, 600));

    // Lógica super simples de colisão / acerto
    // O gol (na tela) fica grosso modo de X: -150 a 150, Y: -100 a -300
    // O goleiro cobre uma área perto de gkChoice.x / gkChoice.y
    const isGoalBound = Math.abs(targetX) < 160 && targetY < -120 && targetY > -350;
    
    // Distância bola vs goleiro (chute no meio X = 0, Y do gk original é 0)
    // Coords do gk base é X=0, Y=-220 (centro do gol)
    const gkTargX = gkChoice.x;
    // targetY da bola é relativo ao ponto inicial (chão). O gk também.
    // Vamos simplificar: se a distância no X for pequena, defendeu.
    const distX = Math.abs(targetX - gkTargX);
    
    setGameState("result");
    setAttempts(a => a + 1);

    if (!isGoalBound) {
      setMessage("Para fora! ❌");
    } else if (distX < 60) {
      setMessage("Defendeu o goleiro! 🧤");
    } else {
      setMessage("GOOOOOL! ⚽");
      setScore(s => s + 1);
    }

    setTimeout(resetGame, 2000);
  };

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-md mx-auto p-4 select-none touch-none h-[60vh] sm:h-[400px]">
      
      <div className="flex justify-between w-full mb-4 px-4 text-neon font-display uppercase tracking-widest text-sm">
        <span>Gols: {score}</span>
        <span>Tentativas: {attempts}</span>
      </div>

      <div className="text-primary font-display mb-8 animate-pulse text-center h-6">
        {message}
      </div>

      <div className="relative w-full max-w-[320px] h-[300px] border-b-2 border-primary/30 flex flex-col items-center justify-end overflow-hidden">
        
        {/* Trave do Gol */}
        <div 
          ref={goalRef}
          className="absolute top-[20px] w-[280px] h-[140px] border-4 border-white/80 border-b-0 rounded-t-lg z-0"
          style={{ 
            backgroundImage: "linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "20px 20px"
          }}
        ></div>

        {/* Goleiro */}
        <motion.div 
          animate={gkControls}
          className="absolute top-[80px] w-12 h-20 bg-red-500 rounded-t-full flex items-center justify-center z-10 shadow-[0_0_15px_rgba(239,68,68,0.6)]"
        >
          <div className="text-white text-xs">🧤</div>
        </motion.div>

        {/* Área (apenas visual) */}
        <div className="absolute bottom-0 w-[400px] h-[60px] border-t border-white/20"></div>

        {/* Bola */}
        <motion.div
          drag
          dragSnapToOrigin={false}
          dragMomentum={true}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          animate={ballControls}
          whileTap={{ scale: 0.9 }}
          className="w-12 h-12 bg-white rounded-full z-20 shadow-xl cursor-grab active:cursor-grabbing flex items-center justify-center relative mb-4"
          style={{ touchAction: "none" }}
        >
          {/* Desenho simples de bola de futebol */}
          <div className="absolute inset-0 rounded-full border border-gray-300" 
               style={{ background: "radial-gradient(circle at 30% 30%, #fff, #ccc)" }}></div>
          <div className="w-4 h-4 bg-black/80 rounded-full absolute"></div>
          <div className="w-2 h-2 bg-black/80 rounded-full absolute top-1 left-2"></div>
          <div className="w-2 h-2 bg-black/80 rounded-full absolute bottom-2 right-2"></div>
        </motion.div>

      </div>
      
      <div className="mt-4 text-xs text-muted-foreground uppercase tracking-widest opacity-60 text-center">
        Passe o tempo marcando gols<br/>enquanto o motor roda.
      </div>
    </div>
  );
}
