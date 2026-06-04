export type Team = {
  id: string;
  name: string;
  flag: string;
  rating: number;
  group: string;
};

export const GROUPS: Record<string, Team[]> = {
  A: [
    { id: "MEX", name: "México", flag: "🇲🇽", rating: 76, group: "A" },
    { id: "RSA", name: "África do Sul", flag: "🇿🇦", rating: 70, group: "A" },
    { id: "KOR", name: "Coreia do Sul", flag: "🇰🇷", rating: 74, group: "A" },
    { id: "CZE", name: "Rep. Tcheca", flag: "🇨🇿", rating: 72, group: "A" },
  ],
  B: [
    { id: "CAN", name: "Canadá", flag: "🇨🇦", rating: 73, group: "B" },
    { id: "AUS", name: "Austrália", flag: "🇦🇺", rating: 72, group: "B" },
    { id: "NOR", name: "Noruega", flag: "🇳🇴", rating: 80, group: "B" },
    { id: "SUI", name: "Suíça", flag: "🇨🇭", rating: 78, group: "B" },
  ],
  C: [
    { id: "BRA", name: "Brasil", flag: "🇧🇷", rating: 90, group: "C" },
    { id: "MAR", name: "Marrocos", flag: "🇲🇦", rating: 78, group: "C" },
    { id: "SCO", name: "Escócia", flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿", rating: 71, group: "C" },
    { id: "HAI", name: "Haiti", flag: "🇭🇹", rating: 64, group: "C" },
  ],
  D: [
    { id: "USA", name: "EUA", flag: "🇺🇸", rating: 75, group: "D" },
    { id: "PAR", name: "Paraguai", flag: "🇵🇾", rating: 72, group: "D" },
    { id: "TUN", name: "Tunísia", flag: "🇹🇳", rating: 71, group: "D" },
    { id: "DEN", name: "Dinamarca", flag: "🇩🇰", rating: 81, group: "D" },
  ],
  E: [
    { id: "GER", name: "Alemanha", flag: "🇩🇪", rating: 86, group: "E" },
    { id: "ECU", name: "Equador", flag: "🇪🇨", rating: 74, group: "E" },
    { id: "CIV", name: "Costa do Marfim", flag: "🇨🇮", rating: 73, group: "E" },
    { id: "KSA", name: "Arábia Saudita", flag: "🇸🇦", rating: 69, group: "E" },
  ],
  F: [
    { id: "NED", name: "Holanda", flag: "🇳🇱", rating: 84, group: "F" },
    { id: "JPN", name: "Japão", flag: "🇯🇵", rating: 78, group: "F" },
    { id: "IRN", name: "Irã", flag: "🇮🇷", rating: 73, group: "F" },
    { id: "UKR", name: "Ucrânia", flag: "🇺🇦", rating: 75, group: "F" },
  ],
  G: [
    { id: "BEL", name: "Bélgica", flag: "🇧🇪", rating: 83, group: "G" },
    { id: "EGY", name: "Egito", flag: "🇪🇬", rating: 73, group: "G" },
    { id: "IRL", name: "Irlanda", flag: "🇮🇪", rating: 70, group: "G" },
    { id: "NZL", name: "Nova Zelândia", flag: "🇳🇿", rating: 66, group: "G" },
  ],
  H: [
    { id: "ESP", name: "Espanha", flag: "🇪🇸", rating: 88, group: "H" },
    { id: "URU", name: "Uruguai", flag: "🇺🇾", rating: 82, group: "H" },
    { id: "CMR", name: "Camarões", flag: "🇨🇲", rating: 71, group: "H" },
    { id: "AUT", name: "Áustria", flag: "🇦🇹", rating: 77, group: "H" },
  ],
  I: [
    { id: "FRA", name: "França", flag: "🇫🇷", rating: 89, group: "I" },
    { id: "SEN", name: "Senegal", flag: "🇸🇳", rating: 77, group: "I" },
    { id: "POL", name: "Polônia", flag: "🇵🇱", rating: 76, group: "I" },
    { id: "QAT", name: "Catar", flag: "🇶🇦", rating: 67, group: "I" },
  ],
  J: [
    { id: "ARG", name: "Argentina", flag: "🇦🇷", rating: 89, group: "J" },
    { id: "COL", name: "Colômbia", flag: "🇨🇴", rating: 81, group: "J" },
    { id: "NGA", name: "Nigéria", flag: "🇳🇬", rating: 75, group: "J" },
    { id: "JAM", name: "Jamaica", flag: "🇯🇲", rating: 68, group: "J" },
  ],
  K: [
    { id: "POR", name: "Portugal", flag: "🇵🇹", rating: 86, group: "K" },
    { id: "GHA", name: "Gana", flag: "🇬🇭", rating: 73, group: "K" },
    { id: "PER", name: "Peru", flag: "🇵🇪", rating: 71, group: "K" },
    { id: "PAN", name: "Panamá", flag: "🇵🇦", rating: 68, group: "K" },
  ],
  L: [
    { id: "ENG", name: "Inglaterra", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿", rating: 87, group: "L" },
    { id: "CRO", name: "Croácia", flag: "🇭🇷", rating: 82, group: "L" },
    { id: "ALG", name: "Argélia", flag: "🇩🇿", rating: 73, group: "L" },
    { id: "UZB", name: "Uzbequistão", flag: "🇺🇿", rating: 69, group: "L" },
  ],
};

export const ALL_TEAMS: Team[] = Object.values(GROUPS).flat();
export const teamById = (id: string) => ALL_TEAMS.find((t) => t.id === id)!;

const ROSTERS: Record<string, string[]> = {
  BRA: ["Alisson","Danilo","Marquinhos","Éder Militão","Alex Sandro","Casemiro","Bruno Guimarães","Raphinha","Neymar Jr","Vinícius Jr","Richarlison","Weverton","Bremer","Fabinho","G. Martinelli","Rodrygo","Gabriel Jesus","É. Ribeiro"],
  ARG: ["E. Martínez","Molina","C. Romero","Otamendi","Tagliafico","E. Fernández","De Paul","Messi","Di María","J. Álvarez","L. Martínez","Armani","Pezzella","Paredes","A. Gómez","Mac Allister","Garnacho","Correa"],
  FRA: ["Maignan","Koundé","Saliba","Upamecano","T. Hernández","Tchouaméni","Camavinga","Griezmann","Dembélé","Mbappé","Giroud","Lloris","Pavard","Konaté","Rabiot","Coman","Thuram","Kolo Muani"],
  ESP: ["U. Simón","Carvajal","Le Normand","Laporte","Cucurella","Rodri","Pedri","Gavi","Yamal","Morata","N. Williams","Raya","Navas","Merino","Olmo","F. Torres","Oyarzabal","Joselu"],
  ENG: ["Pickford","Walker","Stones","Maguire","Shaw","Rice","Bellingham","Foden","Saka","Kane","Sterling","Ramsdale","Trippier","Konsa","Mainoo","Gordon","Watkins","Toney"],
  GER: ["Neuer","Kimmich","Rüdiger","Tah","Mittelstädt","Andrich","Groß","Musiala","Wirtz","Havertz","Sané","Ter Stegen","Henrichs","Schlotterbeck","Pavlovic","Füllkrug","Müller","Undav"],
  POR: ["D. Costa","Cancelo","Pepe","R. Dias","Mendes","B. Fernandes","Vitinha","B. Silva","L. Diaz","Ronaldo","J. Félix","Patrício","Dalot","Inácio","R. Neves","Leão","G. Ramos","D. Jota"],
  NED: ["Verbruggen","Dumfries","De Vrij","Van Dijk","Aké","Schouten","Reijnders","X. Simons","Gakpo","Depay","Bergwijn","Flekken","Geertruida","V.d. Ven","Veerman","Malen","Weghorst","Brobbey"],
};

const GENERIC = ["Silva","García","Müller","Rossi","Smith","Dubois","Petrov","Tanaka","Kim","Hassan","Okafor","Jansen","Andersen","Costa","Lopez","Nguyen","Schmidt","Ivanov"];

export function rosterFor(teamId: string): string[] {
  if (ROSTERS[teamId]) return ROSTERS[teamId];
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
