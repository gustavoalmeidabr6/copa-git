import { GROUPS, Team, teamById, rosterFor } from "./teams";

function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

export type MatchResult = {
  home: Team; away: Team;
  hs: number; as: number;
  scorers: { team: string; player: string; minute: number }[];
};

export function simulateMatch(a: Team, b: Team, seed = Math.random() * 1e9): MatchResult {
  const r = rng(Math.floor(seed));
  const diff = (a.rating - b.rating) / 10;
  const lambdaA = Math.max(0.2, 1.3 + diff * 0.45 + (r() - 0.5) * 0.6);
  const lambdaB = Math.max(0.2, 1.3 - diff * 0.45 + (r() - 0.5) * 0.6);
  const poisson = (l: number) => {
    let k = 0, p = 1, L = Math.exp(-l);
    do { k++; p *= r(); } while (p > L);
    return k - 1;
  };
  const hs = Math.min(7, poisson(lambdaA));
  const as = Math.min(7, poisson(lambdaB));
  const rosterA = rosterFor(a.id);
  const rosterB = rosterFor(b.id);
  const scorers: MatchResult["scorers"] = [];
  for (let i = 0; i < hs; i++)
    scorers.push({ team: a.id, player: rosterA[Math.floor(r() * 11) + 5] ?? rosterA[8], minute: Math.floor(r() * 90) + 1 });
  for (let i = 0; i < as; i++)
    scorers.push({ team: b.id, player: rosterB[Math.floor(r() * 11) + 5] ?? rosterB[8], minute: Math.floor(r() * 90) + 1 });
  scorers.sort((x, y) => x.minute - y.minute);
  return { home: a, away: b, hs, as, scorers };
}

// Decide KO match (no draws)
export function simulateKO(a: Team, b: Team, seed = Math.random() * 1e9) {
  let m = simulateMatch(a, b, seed);
  if (m.hs === m.as) {
    // penalties / extra
    const r = rng(Math.floor(seed * 7));
    if (r() < a.rating / (a.rating + b.rating)) m = { ...m, hs: m.hs + 1 };
    else m = { ...m, as: m.as + 1 };
  }
  return m;
}

export type N200 = {
  results: MatchResult[];
  scoreCounts: Record<string, number>; // "3-1" -> n
  aWinPct: number; drawPct: number; bWinPct: number;
  topScorers: { player: string; team: string; goals: number }[];
  avgGoals: { a: number; b: number };
};

export function simulate200(a: Team, b: Team): N200 {
  const results: MatchResult[] = [];
  const scoreCounts: Record<string, number> = {};
  const scorers: Record<string, { team: string; goals: number }> = {};
  let aW = 0, bW = 0, d = 0, ga = 0, gb = 0;
  for (let i = 0; i < 200; i++) {
    const m = simulateMatch(a, b, i * 911 + 7);
    results.push(m);
    const k = `${m.hs}-${m.as}`;
    scoreCounts[k] = (scoreCounts[k] ?? 0) + 1;
    ga += m.hs; gb += m.as;
    if (m.hs > m.as) aW++;
    else if (m.hs < m.as) bW++;
    else d++;
    for (const s of m.scorers) {
      const key = `${s.team}|${s.player}`;
      scorers[key] = { team: s.team, goals: (scorers[key]?.goals ?? 0) + 1 };
      scorers[key].team = s.team;
      (scorers[key] as any).player = s.player;
    }
  }
  const top = Object.entries(scorers)
    .map(([k, v]) => ({ player: k.split("|")[1], team: v.team, goals: v.goals }))
    .sort((x, y) => y.goals - x.goals)
    .slice(0, 5);
  return {
    results,
    scoreCounts,
    aWinPct: (aW / 200) * 100,
    drawPct: (d / 200) * 100,
    bWinPct: (bW / 200) * 100,
    topScorers: top,
    avgGoals: { a: ga / 200, b: gb / 200 },
  };
}

// ---- World Cup ----
export type GroupTable = { team: Team; pts: number; gd: number; gf: number }[];
export type WCResult = {
  groupTables: Record<string, GroupTable>;
  ko: { round: string; matches: MatchResult[] }[];
  champion: Team;
  runnerUp: Team;
  thirdPlace: Team;
  topScorer: { player: string; team: string; goals: number };
  bestAttack: Team; bestDefense: Team;
  bestAttackGoals: number; bestDefenseGoalsAgainst: number;
};

function playGroups(): { tables: Record<string, GroupTable>; advance: Team[] } {
  const tables: Record<string, GroupTable> = {};
  const advance: Team[] = [];
  for (const [g, teams] of Object.entries(GROUPS)) {
    const stats: Record<string, { team: Team; pts: number; gd: number; gf: number }> = {};
    teams.forEach((t) => (stats[t.id] = { team: t, pts: 0, gd: 0, gf: 0 }));
    for (let i = 0; i < teams.length; i++)
      for (let j = i + 1; j < teams.length; j++) {
        const m = simulateMatch(teams[i], teams[j]);
        stats[teams[i].id].gf += m.hs; stats[teams[j].id].gf += m.as;
        stats[teams[i].id].gd += m.hs - m.as;
        stats[teams[j].id].gd += m.as - m.hs;
        if (m.hs > m.as) stats[teams[i].id].pts += 3;
        else if (m.hs < m.as) stats[teams[j].id].pts += 3;
        else { stats[teams[i].id].pts++; stats[teams[j].id].pts++; }
      }
    const table = Object.values(stats).sort((a, b) => b.pts - a.pts || b.gd - a.gd || b.gf - a.gf);
    tables[g] = table;
    advance.push(table[0].team, table[1].team);
  }
  return { tables, advance };
}

export function simulateWorldCup(): WCResult {
  const { tables, advance } = playGroups();
  // simple bracket — pair sequentially
  const ko: WCResult["ko"] = [];
  const goals: Record<string, { player: string; team: string; goals: number }> = {};
  const teamGoalsFor: Record<string, number> = {};
  const teamGoalsAgainst: Record<string, number> = {};
  let current = advance.slice(0, 32); // 24 -> we have 24 advance, pad? we have 24.
  // For simplicity: use top 16 by rating among advance, plus best 16 = 16. Take all 24 -> top 16 by rating.
  current = current.sort((a, b) => b.rating - a.rating).slice(0, 16);
  const roundNames = ["Oitavas", "Quartas", "Semi", "Final"];
  for (let rIdx = 0; current.length > 1; rIdx++) {
    const matches: MatchResult[] = [];
    const next: Team[] = [];
    for (let i = 0; i < current.length; i += 2) {
      const m = simulateKO(current[i], current[i + 1]);
      matches.push(m);
      teamGoalsFor[m.home.id] = (teamGoalsFor[m.home.id] ?? 0) + m.hs;
      teamGoalsFor[m.away.id] = (teamGoalsFor[m.away.id] ?? 0) + m.as;
      teamGoalsAgainst[m.home.id] = (teamGoalsAgainst[m.home.id] ?? 0) + m.as;
      teamGoalsAgainst[m.away.id] = (teamGoalsAgainst[m.away.id] ?? 0) + m.hs;
      for (const s of m.scorers) {
        const k = `${s.team}|${s.player}`;
        goals[k] = { player: s.player, team: s.team, goals: (goals[k]?.goals ?? 0) + 1 };
      }
      next.push(m.hs > m.as ? m.home : m.away);
    }
    ko.push({ round: roundNames[rIdx] ?? `R${rIdx}`, matches });
    current = next;
  }
  const finalMatch = ko[ko.length - 1].matches[0];
  const semiLosers = ko[ko.length - 2]?.matches.map((m) => (m.hs > m.as ? m.away : m.home)) ?? [];
  const champion = finalMatch.hs > finalMatch.as ? finalMatch.home : finalMatch.away;
  const runnerUp = finalMatch.hs > finalMatch.as ? finalMatch.away : finalMatch.home;
  const thirdPlace = semiLosers[0] ?? finalMatch.home;
  const top = Object.values(goals).sort((a, b) => b.goals - a.goals)[0] ?? { player: "—", team: champion.id, goals: 0 };
  const bestAttackId = Object.entries(teamGoalsFor).sort((a, b) => b[1] - a[1])[0]?.[0] ?? champion.id;
  const bestDefenseId = Object.entries(teamGoalsAgainst).sort((a, b) => a[1] - b[1])[0]?.[0] ?? champion.id;
  return {
    groupTables: tables,
    ko,
    champion, runnerUp, thirdPlace,
    topScorer: top,
    bestAttack: teamById(bestAttackId),
    bestDefense: teamById(bestDefenseId),
    bestAttackGoals: teamGoalsFor[bestAttackId] ?? 0,
    bestDefenseGoalsAgainst: teamGoalsAgainst[bestDefenseId] ?? 0,
  };
}

export function simulateWC200() {
  const championCount: Record<string, number> = {};
  const scorerCount: Record<string, { player: string; team: string; goals: number }> = {};
  const attackSum: Record<string, number> = {};
  const defenseSum: Record<string, number> = {};
  let example: WCResult | null = null;
  for (let i = 0; i < 60; i++) { // 60 for perf
    const r = simulateWorldCup();
    if (i === 0) example = r;
    championCount[r.champion.id] = (championCount[r.champion.id] ?? 0) + 1;
    const k = `${r.topScorer.team}|${r.topScorer.player}`;
    scorerCount[k] = { player: r.topScorer.player, team: r.topScorer.team, goals: (scorerCount[k]?.goals ?? 0) + r.topScorer.goals };
    attackSum[r.bestAttack.id] = (attackSum[r.bestAttack.id] ?? 0) + r.bestAttackGoals;
    defenseSum[r.bestDefense.id] = (defenseSum[r.bestDefense.id] ?? 0) + r.bestDefenseGoalsAgainst;
  }
  const total = 60;
  const top5 = Object.entries(championCount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([id, n]) => ({ team: teamById(id), pct: (n / total) * 100 }));
  const topGoalers = Object.values(scorerCount).sort((a, b) => b.goals - a.goals).slice(0, 5);
  return { example: example!, top5, topGoalers, totalRuns: total };
}
