export type Team = {
  id: string;
  name: string;
  apiName: string; // <-- A ponte vital entre o Frontend e o Backend Python
  flag: string;
  rating: number;
  group: string;
};

export const GROUPS: Record<string, Team[]> = {
  A: [
    { id: "MEX", name: "México", apiName: "Mexico", flag: "🇲🇽", rating: 76, group: "A" },
    { id: "RSA", name: "África do Sul", apiName: "South Africa", flag: "🇿🇦", rating: 70, group: "A" },
    { id: "KOR", name: "Coreia do Sul", apiName: "South Korea", flag: "🇰🇷", rating: 74, group: "A" },
    { id: "CZE", name: "Rep. Tcheca", apiName: "Czech Republic", flag: "🇨🇿", rating: 72, group: "A" },
  ],
  B: [
    { id: "CAN", name: "Canadá", apiName: "Canada", flag: "🇨🇦", rating: 73, group: "B" },
    { id: "AUS", name: "Austrália", apiName: "Australia", flag: "🇦🇺", rating: 72, group: "B" },
    { id: "NOR", name: "Noruega", apiName: "Norway", flag: "🇳🇴", rating: 80, group: "B" },
    { id: "SUI", name: "Suíça", apiName: "Switzerland", flag: "🇨🇭", rating: 78, group: "B" },
  ],
  C: [
    { id: "BRA", name: "Brasil", apiName: "Brazil", flag: "🇧🇷", rating: 90, group: "C" },
    { id: "MAR", name: "Marrocos", apiName: "Morocco", flag: "🇲🇦", rating: 78, group: "C" },
    { id: "SCO", name: "Escócia", apiName: "Scotland", flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", rating: 71, group: "C" },
    { id: "HAI", name: "Haiti", apiName: "Haiti", flag: "🇭🇹", rating: 64, group: "C" },
  ],
  D: [
    { id: "USA", name: "EUA", apiName: "USA", flag: "🇺🇸", rating: 75, group: "D" }, 
    { id: "PAR", name: "Paraguai", apiName: "Paraguay", flag: "🇵🇾", rating: 72, group: "D" },
    { id: "TUN", name: "Tunísia", apiName: "Tunisia", flag: "🇹🇳", rating: 71, group: "D" },
    { id: "DEN", name: "Dinamarca", apiName: "Denmark", flag: "🇩🇰", rating: 81, group: "D" },
  ],
  E: [
    { id: "GER", name: "Alemanha", apiName: "Germany", flag: "🇩🇪", rating: 86, group: "E" },
    { id: "ECU", name: "Equador", apiName: "Ecuador", flag: "🇪🇨", rating: 74, group: "E" },
    { id: "CIV", name: "Costa do Marfim", apiName: "Ivory Coast", flag: "🇨🇮", rating: 73, group: "E" },
    { id: "KSA", name: "Arábia Saudita", apiName: "Saudi Arabia", flag: "🇸🇦", rating: 69, group: "E" },
  ],
  F: [
    { id: "NED", name: "Holanda", apiName: "Netherlands", flag: "🇳🇱", rating: 84, group: "F" },
    { id: "JPN", name: "Japão", apiName: "Japan", flag: "🇯🇵", rating: 78, group: "F" },
    { id: "IRN", name: "Irã", apiName: "Iran", flag: "🇮🇷", rating: 73, group: "F" },
    { id: "UKR", name: "Ucrânia", apiName: "Ukraine", flag: "🇺🇦", rating: 75, group: "F" },
  ],
  G: [
    { id: "BEL", name: "Bélgica", apiName: "Belgium", flag: "🇧🇪", rating: 83, group: "G" },
    { id: "EGY", name: "Egito", apiName: "Egypt", flag: "🇪🇬", rating: 73, group: "G" },
    { id: "IRL", name: "Irlanda", apiName: "Ireland", flag: "🇮🇪", rating: 70, group: "G" },
    { id: "NZL", name: "Nova Zelândia", apiName: "New Zealand", flag: "🇳🇿", rating: 66, group: "G" },
  ],
  H: [
    { id: "ESP", name: "Espanha", apiName: "Spain", flag: "🇪🇸", rating: 88, group: "H" },
    { id: "URU", name: "Uruguai", apiName: "Uruguay", flag: "🇺🇾", rating: 82, group: "H" },
    { id: "CMR", name: "Camarões", apiName: "Cameroon", flag: "🇨🇲", rating: 71, group: "H" },
    { id: "AUT", name: "Áustria", apiName: "Austria", flag: "🇦🇹", rating: 77, group: "H" },
  ],
  I: [
    { id: "FRA", name: "França", apiName: "France", flag: "🇫🇷", rating: 89, group: "I" },
    { id: "SEN", name: "Senegal", apiName: "Senegal", flag: "🇸🇳", rating: 77, group: "I" },
    { id: "POL", name: "Polônia", apiName: "Poland", flag: "🇵🇱", rating: 76, group: "I" },
    { id: "QAT", name: "Catar", apiName: "Qatar", flag: "🇶🇦", rating: 67, group: "I" },
  ],
  J: [
    { id: "ARG", name: "Argentina", apiName: "Argentina", flag: "🇦🇷", rating: 89, group: "J" },
    { id: "COL", name: "Colômbia", apiName: "Colombia", flag: "🇨🇴", rating: 81, group: "J" },
    { id: "NGA", name: "Nigéria", apiName: "Nigeria", flag: "🇳🇬", rating: 75, group: "J" },
    { id: "JAM", name: "Jamaica", apiName: "Jamaica", flag: "🇯🇲", rating: 68, group: "J" },
  ],
  K: [
    { id: "POR", name: "Portugal", apiName: "Portugal", flag: "🇵🇹", rating: 86, group: "K" },
    { id: "GHA", name: "Gana", apiName: "Ghana", flag: "🇬🇭", rating: 73, group: "K" },
    { id: "PER", name: "Peru", apiName: "Peru", flag: "🇵🇪", rating: 71, group: "K" },
    { id: "PAN", name: "Panamá", apiName: "Panama", flag: "🇵🇦", rating: 68, group: "K" },
  ],
  L: [
    { id: "ENG", name: "Inglaterra", apiName: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", rating: 87, group: "L" },
    { id: "CRO", name: "Croácia", apiName: "Croatia", flag: "🇭🇷", rating: 82, group: "L" },
    { id: "ALG", name: "Argélia", apiName: "Algeria", flag: "🇩🇿", rating: 73, group: "L" },
    { id: "UZB", name: "Uzbequistão", apiName: "Uzbekistan", flag: "🇺🇿", rating: 69, group: "L" },
  ],
};

export const ALL_TEAMS: Team[] = Object.values(GROUPS).flat();
export const teamById = (id: string) => ALL_TEAMS.find((t) => t.id === id)!;

const GENERIC = ["Silva","García","Müller","Rossi","Smith","Dubois","Petrov","Tanaka","Kim","Hassan","Okafor","Jansen","Andersen","Costa","Lopez","Nguyen","Schmidt","Ivanov"];

// Fallback (caso a API falhe, usa este gerador)
export function rosterFor(teamId: string): string[] {
  return GENERIC.slice(0, 18).map((n, i) => `${n} ${i + 1}`);
}

export const FORMATIONS = {
  "4-2-3-1": [[0.5,0.92],[0.15,0.76],[0.38,0.78],[0.62,0.78],[0.85,0.76],[0.36,0.58],[0.64,0.58],[0.2,0.38],[0.5,0.42],[0.8,0.38],[0.5,0.18]],
  "4-3-3":   [[0.5,0.92],[0.15,0.76],[0.38,0.78],[0.62,0.78],[0.85,0.76],[0.3,0.55],[0.5,0.6],[0.7,0.55],[0.2,0.25],[0.5,0.2],[0.8,0.25]],
  "4-4-2":   [[0.5,0.92],[0.15,0.76],[0.38,0.78],[0.62,0.78],[0.85,0.76],[0.18,0.52],[0.4,0.54],[0.6,0.54],[0.82,0.52],[0.38,0.22],[0.62,0.22]],
  "3-5-2":   [[0.5,0.92],[0.25,0.78],[0.5,0.8],[0.75,0.78],[0.1,0.55],[0.3,0.5],[0.5,0.55],[0.7,0.5],[0.9,0.55],[0.38,0.22],[0.62,0.22]],
} as const;
export type Formation = keyof typeof FORMATIONS;

export const POSITIONS = ["GOL","LD","ZAG","ZAG","LE","VOL","VOL","MEI","PE","PD","ATA"];