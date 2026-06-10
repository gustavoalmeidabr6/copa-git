import { useState, useEffect, useRef } from "react";

export function FlappyGame() {
  const [gameState, setGameState] = useState<"idle" | "playing" | "gameover">("idle");
  const [score, setScore] = useState(0);
  
  const [birdY, setBirdY] = useState(200);
  const [birdVelocity, setBirdVelocity] = useState(0);
  
  const [obstacles, setObstacles] = useState<{x: number, topH: number, passed: boolean}[]>([]);
  
  const requestRef = useRef<number>();
  const birdYRef = useRef(200);
  const birdVelRef = useRef(0);
  const obstaclesRef = useRef<{x: number, topH: number, passed: boolean}[]>([]);
  const scoreRef = useRef(0);
  const gameStateRef = useRef(gameState);

  // Constants
  const GAME_WIDTH = 500;
  const GAME_HEIGHT = 500;
  const GRAVITY = 0.35;
  const JUMP_STRENGTH = -7.5;
  const PIPE_SPEED = 3;
  const PIPE_WIDTH = 60;
  const PIPE_GAP = 160;
  const BIRD_X = 60;
  const BIRD_SIZE = 40; // Approx visual size of the emoji
  const HITBOX_MARGIN = 10; // Forgiving hitbox

  useEffect(() => {
    gameStateRef.current = gameState;
  }, [gameState]);

  const jump = () => {
    if (gameState === "idle" || gameState === "gameover") {
      // reset
      birdYRef.current = 200;
      birdVelRef.current = JUMP_STRENGTH;
      obstaclesRef.current = [{ x: GAME_WIDTH, topH: 150, passed: false }];
      scoreRef.current = 0;
      
      setBirdY(200);
      setBirdVelocity(JUMP_STRENGTH);
      setObstacles(obstaclesRef.current);
      setScore(0);
      setGameState("playing");
    } else if (gameState === "playing") {
      birdVelRef.current = JUMP_STRENGTH;
    }
  };

  const update = () => {
    if (gameStateRef.current === "playing") {
      // physics
      birdVelRef.current += GRAVITY; 
      birdYRef.current += birdVelRef.current;

      // obstacles
      const newObstacles = [...obstaclesRef.current];
      for (let i = 0; i < newObstacles.length; i++) {
        newObstacles[i].x -= PIPE_SPEED; 
      }

      // remove old
      if (newObstacles[0] && newObstacles[0].x < -PIPE_WIDTH) {
        newObstacles.shift();
      }
      
      // spawn new
      const lastObstacle = newObstacles[newObstacles.length - 1];
      if (!lastObstacle || lastObstacle.x < GAME_WIDTH - 250) {
        newObstacles.push({
          x: GAME_WIDTH,
          topH: 50 + Math.random() * (GAME_HEIGHT - PIPE_GAP - 100), 
          passed: false
        });
      }

      // collisions
      let collided = false;
      // Floor / Ceiling
      if (birdYRef.current > GAME_HEIGHT - BIRD_SIZE + 10 || birdYRef.current < -20) {
        collided = true;
      }

      for (const obs of newObstacles) {
        // Hitbox collision
        // X collision: bird right edge > pipe left edge AND bird left edge < pipe right edge
        const hitX = (BIRD_X + BIRD_SIZE - HITBOX_MARGIN > obs.x) && (BIRD_X + HITBOX_MARGIN < obs.x + PIPE_WIDTH);
        
        // Y collision: bird top < pipe top bottom OR bird bottom > pipe bottom top
        const hitY = (birdYRef.current + HITBOX_MARGIN < obs.topH) || (birdYRef.current + BIRD_SIZE - HITBOX_MARGIN > obs.topH + PIPE_GAP);

        if (hitX && hitY) {
          collided = true;
        }

        // score update
        if (!obs.passed && obs.x + PIPE_WIDTH < BIRD_X) {
            obs.passed = true;
            scoreRef.current += 1;
            setScore(scoreRef.current);
        }
      }

      if (collided) {
        setGameState("gameover");
      } else {
        obstaclesRef.current = newObstacles;
        setBirdY(birdYRef.current);
        setBirdVelocity(birdVelRef.current);
        setObstacles(newObstacles);
      }
    }
    
    requestRef.current = requestAnimationFrame(update);
  };

  useEffect(() => {
    requestRef.current = requestAnimationFrame(update);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, []);

  return (
     <div className="flex flex-col items-center justify-center w-full max-w-lg mx-auto p-2 select-none touch-none">
      
      <div className="mb-4 text-center">
        <h2 className="text-lg sm:text-xl font-display text-primary uppercase tracking-[0.15em] drop-shadow-[0_0_10px_rgba(var(--primary),0.5)]">
          Processando 400 Copas (41.600 jogos)
        </h2>
        <p className="text-xs sm:text-sm text-muted-foreground opacity-80 mt-1">
          Para uma simulação mais rápida seria necessário um servidor pago.
        </p>
      </div>

      <div className="flex justify-between w-full mb-2 px-4 text-neon font-display uppercase tracking-widest text-lg">
        <span>Pontos: {score}</span>
      </div>

      <div className="text-primary font-display mb-2 animate-pulse text-center h-6 text-sm uppercase tracking-widest">
        {gameState === "idle" ? "Toque para voar!" : gameState === "gameover" ? "Fim de jogo! Toque para tentar de novo" : ""}
      </div>

      <div 
        className="relative w-full max-w-[500px] h-[500px] border-b-4 border-primary/30 flex flex-col overflow-hidden bg-background/50 rounded-xl cursor-pointer shadow-[0_0_25px_rgba(0,0,0,0.6)]"
        onPointerDown={jump}
      >
        {/* Background grid */}
        <div 
          className="absolute inset-0 z-0 opacity-20"
          style={{ 
            backgroundImage: "linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "25px 25px"
          }}
        ></div>

        {/* Player (Trophy) */}
        <div 
          className="absolute z-20 flex items-center justify-center drop-shadow-[0_0_15px_rgba(255,215,0,0.8)]"
          style={{ 
            left: `${BIRD_X}px`, 
            top: `${birdY}px`,
            width: `${BIRD_SIZE}px`,
            height: `${BIRD_SIZE}px`,
            transform: `rotate(${Math.min(Math.max(birdVelocity * 4, -30), 90)}deg)`,
            transition: 'transform 0.1s'
          }}
        >
          <img src="/trophy/8861317.png" alt="Trophy" className="w-full h-full object-contain" draggable={false} />
        </div>

        {/* Obstacles */}
        {obstacles.map((obs, i) => (
          <div key={i} className="absolute inset-y-0 z-10" style={{ left: `${obs.x}px`, width: `${PIPE_WIDTH}px` }}>
            <div className="absolute top-0 w-full bg-primary/80 border-4 border-primary rounded-b-lg shadow-[0_0_12px_rgba(var(--primary),0.6)]" style={{ height: `${obs.topH}px` }}></div>
            <div className="absolute bottom-0 w-full bg-primary/80 border-4 border-primary rounded-t-lg shadow-[0_0_12px_rgba(var(--primary),0.6)]" style={{ height: `${GAME_HEIGHT - obs.topH - PIPE_GAP}px` }}></div>
          </div>
        ))}
        
      </div>
    </div>
  );
}
