// src/lib/teams.ts
import titularesCsv from './titulares.txt?raw';

export type Team = {
  id: string;
  name: string;
  apiName: string;
  flag: string;
  rating: number;
  group: string;
};

// ─── COPA DO MUNDO 2026 — 48 SELEÇÕES OFICIAIS ───────────────────────────────
// Grupos A–L com 4 times cada (total: 48)
// apiName deve bater EXATAMENTE com as chaves usadas no backend (data_loader.py)
export const GROUPS: Record<string, Team[]> = {
  A: [
    { id: "MEX", name: "México",        apiName: "Mexico",       flag: "https://flagcdn.com/w40/mx.png", rating: 76, group: "A" },
    { id: "RSA", name: "África do Sul", apiName: "South Africa", flag: "https://flagcdn.com/w40/za.png", rating: 68, group: "A" },
    { id: "KOR", name: "Coreia do Sul", apiName: "South Korea",  flag: "https://flagcdn.com/w40/kr.png", rating: 74, group: "A" },
    { id: "CZE", name: "Rep. Tcheca",   apiName: "Czechia",      flag: "https://flagcdn.com/w40/cz.png", rating: 72, group: "A" },
  ],
  B: [
    { id: "CAN", name: "Canadá",        apiName: "Canada",                  flag: "https://flagcdn.com/w40/ca.png", rating: 73, group: "B" },
    { id: "BIH", name: "Bósnia-Herz.",  apiName: "Bosnia and Herzegovina",  flag: "https://flagcdn.com/w40/ba.png", rating: 69, group: "B" },
    { id: "QAT", name: "Catar",         apiName: "Qatar",                   flag: "https://flagcdn.com/w40/qa.png", rating: 65, group: "B" },
    { id: "SUI", name: "Suíça",         apiName: "Switzerland",             flag: "https://flagcdn.com/w40/ch.png", rating: 78, group: "B" },
  ],
  C: [
    { id: "BRA", name: "Brasil",   apiName: "Brazil",   flag: "https://flagcdn.com/w40/br.png", rating: 88, group: "C" },
    { id: "MAR", name: "Marrocos", apiName: "Morocco",  flag: "https://flagcdn.com/w40/ma.png", rating: 78, group: "C" },
    { id: "HAI", name: "Haiti",    apiName: "Haiti",    flag: "https://flagcdn.com/w40/ht.png", rating: 62, group: "C" },
    { id: "SCO", name: "Escócia",  apiName: "Scotland", flag: "https://flagcdn.com/w40/gb-sct.png", rating: 71, group: "C" },
  ],
  D: [
    { id: "USA", name: "EUA",       apiName: "USA",       flag: "https://flagcdn.com/w40/us.png", rating: 75, group: "D" },
    { id: "PAR", name: "Paraguai",  apiName: "Paraguay",  flag: "https://flagcdn.com/w40/py.png", rating: 70, group: "D" },
    { id: "AUS", name: "Austrália", apiName: "Australia", flag: "https://flagcdn.com/w40/au.png", rating: 72, group: "D" },
    { id: "TUR", name: "Turquia",   apiName: "Turkey",    flag: "https://flagcdn.com/w40/tr.png", rating: 77, group: "D" },
  ],
  E: [
    { id: "GER", name: "Alemanha",        apiName: "Germany",      flag: "https://flagcdn.com/w40/de.png", rating: 85, group: "E" },
    { id: "CUW", name: "Curaçao",         apiName: "Curacao",      flag: "https://flagcdn.com/w40/cw.png", rating: 62, group: "E" },
    { id: "CIV", name: "Costa do Marfim", apiName: "Ivory Coast",  flag: "https://flagcdn.com/w40/ci.png", rating: 73, group: "E" },
    { id: "ECU", name: "Equador",         apiName: "Ecuador",      flag: "https://flagcdn.com/w40/ec.png", rating: 74, group: "E" },
  ],
  F: [
    { id: "NED", name: "Holanda",  apiName: "Netherlands", flag: "https://flagcdn.com/w40/nl.png", rating: 84, group: "F" },
    { id: "JPN", name: "Japão",    apiName: "Japan",       flag: "https://flagcdn.com/w40/jp.png", rating: 78, group: "F" },
    { id: "SWE", name: "Suécia",   apiName: "Sweden",      flag: "https://flagcdn.com/w40/se.png", rating: 75, group: "F" },
    { id: "TUN", name: "Tunísia",  apiName: "Tunisia",     flag: "https://flagcdn.com/w40/tn.png", rating: 68, group: "F" },
  ],
  G: [
    { id: "BEL", name: "Bélgica",       apiName: "Belgium",     flag: "https://flagcdn.com/w40/be.png", rating: 83, group: "G" },
    { id: "EGY", name: "Egito",         apiName: "Egypt",       flag: "https://flagcdn.com/w40/eg.png", rating: 71, group: "G" },
    { id: "IRN", name: "Irã",           apiName: "Iran",        flag: "https://flagcdn.com/w40/ir.png", rating: 71, group: "G" },
    { id: "NZL", name: "Nova Zelândia", apiName: "New Zealand", flag: "https://flagcdn.com/w40/nz.png", rating: 64, group: "G" },
  ],
  H: [
    { id: "ESP", name: "Espanha",   apiName: "Spain",         flag: "https://flagcdn.com/w40/es.png", rating: 89, group: "H" },
    { id: "CPV", name: "Cabo Verde", apiName: "Cape Verde",   flag: "https://flagcdn.com/w40/cv.png", rating: 63, group: "H" },
    { id: "KSA", name: "Ar. Saudita", apiName: "Saudi Arabia", flag: "https://flagcdn.com/w40/sa.png", rating: 67, group: "H" },
    { id: "URU", name: "Uruguai",   apiName: "Uruguay",       flag: "https://flagcdn.com/w40/uy.png", rating: 82, group: "H" },
  ],
  I: [
    { id: "FRA", name: "França",   apiName: "France",  flag: "https://flagcdn.com/w40/fr.png", rating: 89, group: "I" },
    { id: "SEN", name: "Senegal",  apiName: "Senegal", flag: "https://flagcdn.com/w40/sn.png", rating: 77, group: "I" },
    { id: "IRQ", name: "Iraque",   apiName: "Iraq",    flag: "https://flagcdn.com/w40/iq.png", rating: 63, group: "I" },
    { id: "NOR", name: "Noruega",  apiName: "Norway",  flag: "https://flagcdn.com/w40/no.png", rating: 80, group: "I" },
  ],
  J: [
    { id: "ARG", name: "Argentina", apiName: "Argentina", flag: "https://flagcdn.com/w40/ar.png", rating: 90, group: "J" },
    { id: "ALG", name: "Argélia",   apiName: "Algeria",   flag: "https://flagcdn.com/w40/dz.png", rating: 72, group: "J" },
    { id: "AUT", name: "Áustria",   apiName: "Austria",   flag: "https://flagcdn.com/w40/at.png", rating: 77, group: "J" },
    { id: "JOR", name: "Jordânia",  apiName: "Jordan",    flag: "https://flagcdn.com/w40/jo.png", rating: 64, group: "J" },
  ],
  K: [
    { id: "POR", name: "Portugal",  apiName: "Portugal",  flag: "https://flagcdn.com/w40/pt.png", rating: 86, group: "K" },
    { id: "COD", name: "RD Congo",  apiName: "DR Congo",  flag: "https://flagcdn.com/w40/cd.png", rating: 65, group: "K" },
    { id: "UZB", name: "Uzbequistão", apiName: "Uzbekistan", flag: "https://flagcdn.com/w40/uz.png", rating: 67, group: "K" },
    { id: "COL", name: "Colômbia",  apiName: "Colombia",  flag: "https://flagcdn.com/w40/co.png", rating: 81, group: "K" },
  ],
  L: [
    { id: "ENG", name: "Inglaterra", apiName: "England",  flag: "https://flagcdn.com/w40/gb-eng.png", rating: 87, group: "L" },
    { id: "CRO", name: "Croácia",    apiName: "Croatia",  flag: "https://flagcdn.com/w40/hr.png", rating: 82, group: "L" },
    { id: "GHA", name: "Gana",       apiName: "Ghana",    flag: "https://flagcdn.com/w40/gh.png", rating: 67, group: "L" },
    { id: "PAN", name: "Panamá",     apiName: "Panama",   flag: "https://flagcdn.com/w40/pa.png", rating: 66, group: "L" },
  ],
};

export const ALL_TEAMS: Team[] = Object.values(GROUPS).flat();
export const teamById = (id: string) => ALL_TEAMS.find((t) => t.id === id)!;

export const POSITION_WEIGHT: Record<string, number> = {
  "GOL": 1,
  "LD": 2,
  "ZAG": 3,
  "LE": 4,
  "AD": 5,
  "AE": 6,
  "VOL": 7,
  "MC": 8,
  "MD": 9,
  "ME": 10,
  "MEI": 11,
  "PD": 12,
  "PE": 13,
  "ATA": 15
};

export const FORMATIONS = {
  "4-2-3-1": {
    coords: [
      [0.5, 0.92],   // 0: GOL
      [0.85, 0.76],  // 1: LD (Dir)
      [0.65, 0.78],  // 2: ZAG (Dir)
      [0.35, 0.78],  // 3: ZAG (Esq)
      [0.15, 0.76],  // 4: LE (Esq)
      [0.65, 0.58],  // 5: VOL (Dir)
      [0.35, 0.58],  // 6: VOL (Esq)
      [0.5, 0.42],   // 7: MEI
      [0.85, 0.35],  // 8: PD
      [0.15, 0.35],  // 9: PE
      [0.5, 0.18],   // 10: ATA
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "LE", "VOL", "VOL", "MEI", "PD", "PE", "ATA"]
  },
  "4-3-3": {
    coords: [
      [0.5, 0.92],
      [0.85, 0.76],
      [0.65, 0.78],
      [0.35, 0.78],
      [0.15, 0.76],
      [0.5, 0.60],
      [0.75, 0.45],
      [0.25, 0.45],
      [0.8, 0.25],
      [0.2, 0.25],
      [0.5, 0.20],
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "LE", "VOL", "MC", "MC", "PD", "PE", "ATA"]
  },
  "4-4-2": {
    coords: [
      [0.5, 0.92],
      [0.85, 0.76],
      [0.65, 0.78],
      [0.35, 0.78],
      [0.15, 0.76],
      [0.65, 0.55],
      [0.35, 0.55],
      [0.85, 0.45],
      [0.15, 0.45],
      [0.6, 0.22],
      [0.4, 0.22],
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "LE", "VOL", "VOL", "MD", "ME", "ATA", "ATA"]
  },
  "3-5-2": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],
      [0.15, 0.55],
      [0.5, 0.60],
      [0.65, 0.50],
      [0.35, 0.50],
      [0.6, 0.22],
      [0.4, 0.22],
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "AD", "AE", "VOL", "MC", "MC", "ATA", "ATA"]
  },
  "3-4-2-1": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],
      [0.15, 0.55],
      [0.6, 0.60],
      [0.4, 0.60],
      [0.65, 0.40],
      [0.35, 0.40],
      [0.5, 0.20],
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "AD", "AE", "VOL", "VOL", "MEI", "MEI", "ATA"]
  },
  "3-4-3": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],
      [0.15, 0.55],
      [0.6, 0.60],
      [0.4, 0.60],
      [0.8, 0.25],
      [0.2, 0.25],
      [0.5, 0.20],
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "AD", "AE", "VOL", "VOL", "PD", "PE", "ATA"]
  },
  "4-1-4-1": {
    coords: [
      [0.5, 0.92],
      [0.85, 0.76],
      [0.65, 0.78],
      [0.35, 0.78],
      [0.15, 0.76],
      [0.5, 0.65],
      [0.65, 0.48],
      [0.35, 0.48],
      [0.85, 0.45],
      [0.15, 0.45],
      [0.5, 0.20],
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "LE", "VOL", "MC", "MC", "MD", "ME", "ATA"]
  },
  "5-4-1": {
    coords: [
      [0.5, 0.92],
      [0.9, 0.72],
      [0.7, 0.78],
      [0.5, 0.80],
      [0.3, 0.78],
      [0.1, 0.72],
      [0.6, 0.55],
      [0.4, 0.55],
      [0.8, 0.40],
      [0.2, 0.40],
      [0.5, 0.20],
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "ZAG", "LE", "VOL", "VOL", "MD", "ME", "ATA"]
  },
  "3-4-1-2": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],
      [0.15, 0.55],
      [0.6, 0.60],
      [0.4, 0.60],
      [0.5, 0.40],
      [0.65, 0.20],
      [0.35, 0.20]
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "MD", "ME", "MC", "MC", "MEI", "ATA", "ATA"]
  }
} as const;

export type Formation = keyof typeof FORMATIONS;

export const POS_MAP: Record<string, string> = {
  // Goleiro
  "GK": "GOL",
  // Defensores
  "RB": "LD", "RWB": "AD", "CB": "ZAG", "LB": "LE", "LWB": "AE",
  "SW": "ZAG", "WB": "AD",
  // Volantes / Meios defensivos
  "CDM": "VOL", "DM": "VOL",
  // Meias
  "CM": "MC", "RM": "MD", "LM": "ME",
  "CAM": "MEI", "AM": "MEI", "SS": "MEI",
  // Pontas / Extremos
  "RW": "PD", "LW": "PE",
  "RWF": "PD", "LWF": "PE",
  // Atacantes
  "ST": "ATA", "CF": "ATA", "FW": "ATA", "F": "ATA",
};

export const KNOWN_PLAYER_POSITIONS: Record<string, string> = {};
export const TEAM_ROSTERS: Record<string, { name: string, position: string }[]> = {};
export const TEAM_FORMATIONS: Record<string, string> = {};

export function normalizeName(name: string) {
  if (!name) return "";
  return name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function loadTitulares() {
  const lines = titularesCsv.split('\n').filter(l => l.trim().length > 0);

  for (let i = 1; i < lines.length; i++) {
    const parts = lines[i].split(',');
    if (parts.length < 5) continue;

    let [, selecao, formacao, jogador, pos] = parts;
    selecao = selecao?.trim();

    const rawPos = pos?.split('/')[0].trim();
    let cleanPos: string;
    if (!rawPos || rawPos === "N" || rawPos === "NA" || rawPos === "N/A") {
      cleanPos = "MC";
    } else {
      cleanPos = POS_MAP[rawPos] ?? "MC";
    }

    if (jogador) {
      const fullName = jogador.trim();
      const normFull = normalizeName(fullName);
      KNOWN_PLAYER_POSITIONS[normFull] = cleanPos;

      const nameParts = normFull.split(' ');
      if (nameParts.length > 1) {
        const lastTwo = nameParts.slice(-2).join(' ');
        if (!KNOWN_PLAYER_POSITIONS[lastTwo]) KNOWN_PLAYER_POSITIONS[lastTwo] = cleanPos;

        const last = nameParts[nameParts.length - 1];
        if (!KNOWN_PLAYER_POSITIONS[last]) KNOWN_PLAYER_POSITIONS[last] = cleanPos;

        const first = nameParts[0];
        if (!KNOWN_PLAYER_POSITIONS[first]) KNOWN_PLAYER_POSITIONS[first] = cleanPos;
      }
    }

    const team = ALL_TEAMS.find(t => normalizeName(t.name) === normalizeName(selecao));
    if (!team) continue;

    if (!TEAM_ROSTERS[team.id]) {
      TEAM_ROSTERS[team.id] = [];
      TEAM_FORMATIONS[team.id] = formacao?.trim();
    }

    TEAM_ROSTERS[team.id].push({ name: jogador?.trim(), position: cleanPos });
  }
}

loadTitulares();

export function getPlayerPosition(name: string): string | undefined {
  if (!name) return undefined;
  const norm = normalizeName(name);

  if (KNOWN_PLAYER_POSITIONS[norm]) return KNOWN_PLAYER_POSITIONS[norm];

  const parts = norm.split(' ');
  if (parts.length > 1) {
    const lastTwo = parts.slice(-2).join(' ');
    if (KNOWN_PLAYER_POSITIONS[lastTwo]) return KNOWN_PLAYER_POSITIONS[lastTwo];

    const last = parts[parts.length - 1];
    if (KNOWN_PLAYER_POSITIONS[last]) return KNOWN_PLAYER_POSITIONS[last];

    const first = parts[0];
    if (KNOWN_PLAYER_POSITIONS[first]) return KNOWN_PLAYER_POSITIONS[first];
  }
  return undefined;
}

const GENERIC = ["Silva","García","Müller","Rossi","Smith","Dubois","Petrov","Tanaka","Kim","Hassan","Okafor"];

export function formationFor(teamId: string): Formation {
  const f = TEAM_FORMATIONS[teamId];
  if (f && FORMATIONS[f as Formation]) return f as Formation;
  return "4-3-3";
}

export function rosterFor(teamId: string): string[] {
  const players = TEAM_ROSTERS[teamId];
  if (!players || players.length === 0) {
    return GENERIC.map((n, i) => `${n} ${i + 1}`);
  }

  const formId = formationFor(teamId);
  const targetPositions = FORMATIONS[formId].positions;

  const pool = [...players];
  const result: string[] = [];

  for (const targetPos of targetPositions) {
    const idx = pool.findIndex(p => p.position === targetPos);
    if (idx !== -1) {
      result.push(pool[idx].name);
      pool.splice(idx, 1);
    } else {
      result.push(pool.shift()?.name || "Desconhecido");
    }
  }

  for (const remaining of pool) {
    result.push(remaining.name);
  }

  return result;
}