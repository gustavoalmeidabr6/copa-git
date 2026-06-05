// src/lib/teams.ts
export type Team = {
  id: string;
  name: string;
  apiName: string;
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

export function rosterFor(teamId: string): string[] {
  return GENERIC.slice(0, 18).map((n, i) => `${n} ${i + 1}`);
}

// === DICIONÁRIO DE INTELIGÊNCIA TÁTICA ===
// Os pesos determinam a ordem correta na renderização baseada na Formação escolhida
export const POSITION_WEIGHT: Record<string, number> = {
  "GOL": 1,
  "LD": 2, 
  "ZAG": 3,
  "LE": 4, 
  "AD": 5, // Ala Direito (3 zagueiros)
  "AE": 6, // Ala Esquerdo (3 zagueiros)
  "VOL": 7,
  "MC": 8,
  "MD": 9, 
  "ME": 10,
  "MEI": 11,
  "PD": 12, 
  "PE": 13,
  "ATA": 15
};

export const KNOWN_PLAYER_POSITIONS: Record<string, string> = {
  // Algeria
  "Zidane": "GOL", "Belghali": "LD", "Belaid": "ZAG", "Bensebaini": "ZAG", "Ait-Nouri": "LE", "Zerrouki": "VOL", "Boudaoui": "VOL", "Mahrez": "PD", "Aouar": "MEI", "Chaibi": "PE", "Gouiri": "ATA",
  // Saudi Arabia
  "Al-Aqidi": "GOL", "Boushal": "LD", "Tambakti": "ZAG", "Al-Amri": "ZAG", "Al-Harbi": "LE", "Kanno": "VOL", "Al-Khaibari": "MC", "N. Al-Dawsari": "MC", "Mandash": "PD", "S. Al-Dawsari": "PE", "Al-Buraikan": "ATA",
  // Argentina
  "Martinez": "GOL", "Molina": "LD", "Otamendi": "ZAG", "Romero": "ZAG", "Tagliafico": "LE", "Mac Allister": "MC", "Paredes": "VOL", "Fernandez": "MC", "Messi": "PD", "Almada": "PE", "Alvarez": "ATA",
  // Australia
  "Ryan": "GOL", "Italiano": "LD", "Degenek": "ZAG", "Souttar": "ZAG", "Circati": "ZAG", "Bos": "LE", "Metcalfe": "MD", "Devlin": "VOL", "O'Neill": "VOL", "Irankunda": "ME", "Touré": "ATA",
  // Austria
  "A. Schlager": "GOL", "Laimer": "LD", "Lienhart": "ZAG", "Alaba": "ZAG", "Mwene": "LE", "X. Schlager": "VOL", "Seiwald": "VOL", "Wimmer": "PD", "Baumgartner": "MEI", "Sabitzer": "PE", "Arnautovic": "ATA",
  // Belgium
  "Courtois": "GOL", "Castagne": "LD", "Debast": "ZAG", "Theate": "ZAG", "De Cuyper": "LE", "Tielemans": "VOL", "Onana": "VOL", "Doku": "PD", "De Bruyne": "MEI", "Trossard": "PE", "De Ketelaere": "ATA",
  // Bosnia
  "Vasilj": "GOL", "Dedic": "LD", "Katic": "ZAG", "Muharemovic": "ZAG", "Kolasinac": "LE", "Bajraktarevic": "MD", "Sunjic": "VOL", "Tahirovic": "VOL", "Memic": "ME", "Demirovic": "ATA", "Dzeko": "ATA",
  // Brazil
  "Alisson": "GOL", "Wesley": "LD", "Marquinhos": "ZAG", "Gabriel": "ZAG", "Douglas Santos": "LE", "Luis Henrique": "MD", "Casemiro": "VOL", "Bruno Guimaraes": "VOL", "Raphinha": "ME", "Vinicius": "ATA", "Cunha": "ATA",
  // Canada
  "Crepeau": "GOL", "Sigur": "LD", "Bombito": "ZAG", "Jones": "ZAG", "Laryea": "LE", "Buchanan": "MD", "Koné": "VOL", "Eustaquio": "VOL", "Davies": "ME", "Oluwaseyi": "ATA", "David": "ATA",
  // Cape Verde
  "Voziha": "GOL", "Moreira": "LD", "Lopes": "ZAG", "Borges": "ZAG", "Lopes Cabral": "LE", "Lenini": "VOL", "Duarte": "VOL", "Rodrigues": "PD", "Monteiro": "MEI", "Cabral": "PE", "Livramento": "ATA",
  // Colombia
  "Montero": "GOL", "Munoz": "LD", "Sanchez": "ZAG", "Mina": "ZAG", "Mojica": "LE", "Lerma": "VOL", "Rios": "VOL", "Arias": "PD", "James": "MEI", "Diaz": "PE", "Suarez": "ATA",
  // South Korea
  "Seung-gyu Kim": "GOL", "Seol": "LD", "Min-jae Kim": "ZAG", "Han-beom Lee": "ZAG", "Tae-seok Lee": "LE", "Wang": "VOL", "Castrop": "VOL", "Kang-in Lee": "PD", "Jae-sung Lee": "MEI", "Bae": "PE", "Son": "ATA",
  // Ivory Coast
  "Fofana": "GOL", "Doué": "LD", "Koussonou": "ZAG", "Ndicka": "ZAG", "Konan": "LE", "Kessié": "VOL", "Sangaré": "VOL", "Oulai": "MC", "Pepé": "PD", "Diomandé": "PE", "Guessand": "ATA",
  // Curacao
  "Room": "GOL", "Sambo": "LD", "Van Ejma": "ZAG", "Obispo": "ZAG", "Floranus": "LE", "J. Bacuna": "MC", "Comenancia": "VOL", "L. Bacuna": "MC", "Chong": "PD", "Gorré": "PE", "Locadia": "ATA",
  // Croatia
  "Livakovic": "GOL", "Stanisic": "LD", "Sutalo": "ZAG", "Caleta-Car": "ZAG", "Gvardiol": "LE", "Sucic": "VOL", "Modric": "VOL", "Pasalic": "PD", "Kramaric": "MEI", "Perisic": "PE", "Budimir": "ATA",
  // Ecuador
  "Galindez": "GOL", "Preciado": "LD", "Ordonez": "ZAG", "Pacho": "ZAG", "HIncapié": "LE", "Vite": "MC", "Caicedo": "VOL", "Castillo": "MC", "Yeboah": "PD", "Angulo": "PE", "Valencia": "ATA",
  // Egypt (Convertido para alinhar em 3-5-2)
  "El Shenawy": "GOL", "Ibrahim": "ZAG", "Abdelmaguif": "ZAG", "Rabia": "ZAG", "Hany": "AD", "Fatouh": "AE", "Ateya": "VOL", "Lasheen": "MC", "Ashour": "MC", "Salah": "ATA", "Marmoush": "ATA",
  // France
  "Maignan": "GOL", "Koundé": "LD", "Saliba": "ZAG", "Upamecano": "ZAG", "Hernandez": "LE", "Rabiot": "VOL", "Tchouameni": "VOL", "Dembelé": "PD", "Olise": "MEI", "Doué": "PE", "Mbappé": "ATA",
  // Germany
  "Neuer": "GOL", "Kimmich": "LD", "Tah": "ZAG", "Schlotterbeck": "ZAG", "Raum": "LE", "Pavlovic": "VOL", "Goreztka": "VOL", "Sané": "PD", "Musiala": "MEI", "Wirtz": "PE", "Havertz": "ATA",
  // Ghana
  "Asare": "GOL", "Adjetei": "ZAG", "Seidu": "ZAG", "Oppong": "ZAG", "Yirenkyi": "AD", "Mensah": "AE", "Sibo": "VOL", "Partey": "VOL", "Sulemana": "PD", "Semenyo": "PE", "Ayew": "ATA",
  // Japan
  "Suzuki": "GOL", "Tomiyasu": "ZAG", "Taniguchi": "ZAG", "Itakura": "ZAG", "Doan": "AD", "Nakamura": "AE", "Endo": "VOL", "Tanaka": "VOL", "Kubo": "MEI", "Ito": "MEI", "Ueda": "ATA",
  // Jordan
  "Abulaila": "GOL", "Abu Dahab": "ZAG", "Nasib": "ZAG", "Al-Arab": "ZAG", "Haddad": "AD", "Abu Taha": "AE", "Al-Rawahbdeh": "VOL", "Al-Rashdan": "VOL", "Tamari": "PD", "Olwan": "PE", "Al-Mardi": "ATA",
  // Haiti
  "Placide": "GOL", "Arcus": "LD", "Adé": "ZAG", "Duverne": "ZAG", "Expérience": "LE", "Deedson": "MC", "Bellegarde": "VOL", "Pierre": "MC", "Isidor": "PD", "Providence": "PE", "Nazon": "ATA",
  // England
  "Pickford": "GOL", "James": "LD", "Guehi": "ZAG", "Konsa": "ZAG", "O'Reilly": "LE", "Anderson": "VOL", "Rice": "VOL", "Saka": "PD", "Bellingham": "MEI", "Eze": "PE", "Kane": "ATA",
  // Iran
  "Beyranvand": "GOL", "Yousefi": "LD", "Kanaani": "ZAG", "Khalilzadeh": "ZAG", "Mohammadi": "LE", "Ezatolahi": "VOL", "Ghoddos": "VOL", "Jahanbakhsh": "PD", "Ghayedi": "MEI", "Mohebi": "PE", "Taremi": "ATA",
  // Iraq
  "Hassan": "GOL", "Hussein Ali": "LD", "Sulaka": "ZAG", "Tahseen": "ZAG", "Doski": "LE", "Al-Ammari": "VOL", "Bayesh": "VOL", "Ali Jasim": "PD", "Iqbal": "MEI", "Amyn": "PE", "Aymen Hussein": "ATA",
  // Morocco
  "Bono": "GOL", "Hakimi": "LD", "Diop": "ZAG", "Aguerd": "ZAG", "Salah-Eddine": "LE", "Ounahi": "VOL", "El Aynaoui": "VOL", "Brahim Diaz": "PD", "Saibari": "MEI", "Talbi": "PE", "El Kaabi": "ATA",
  // Mexico
  "Rangel": "GOL", "Sanchez": "LD", "Montes": "ZAG", "Vasquez": "ZAG", "Gallardo": "LE", "Pineda": "MC", "Alvarez": "VOL", "Fidalgo": "MC", "Vega": "PD", "Quinones": "PE", "Jimenez": "ATA",
  // Norway
  "Nyland": "GOL", "Ryerson": "LD", "Heggem": "ZAG", "Ostigard": "ZAG", "Wolfe": "LE", "Thorstvedt": "MC", "Berg": "VOL", "Berge": "MC", "Sorloth": "PD", "Nusa": "PE", "Haaland": "ATA",
  // New Zealand
  "Crocombe": "GOL", "Payne": "LD", "Bindon": "ZAG", "Boxall": "ZAG", "Cacace": "LE", "Samenic": "VOL", "Bell": "VOL", "McCowatt": "PD", "Singh": "MEI", "Garbett": "PE", "Wood": "ATA",
  // Netherlands
  "Verbruggen": "GOL", "Dumfries": "LD", "Van Dijk": "ZAG", "Aké": "ZAG", "Van de Ven": "LE", "De Jong": "VOL", "Gravenberch": "VOL", "Malen": "PD", "Reijnders": "MEI", "Gakpo": "PE", "Depay": "ATA",
  // Panama
  "Mosquera": "GOL", "Farina": "ZAG", "Andrade": "ZAG", "Cordoba": "ZAG", "Murillo": "AD", "Davis": "AE", "Carrasquilla": "VOL", "Godoy": "VOL", "Barcenas": "MEI", "Diaz": "MEI", "Fajardo": "ATA",
  // Paraguay
  "Gill": "GOL", "Caceres": "LD", "G. Gomez": "ZAG", "Alderete": "ZAG", "Alonso": "LE", "D. Gomez": "MD", "Ojeda": "VOL", "Bobadilla": "VOL", "Almiron": "ME", "Enciso": "ATA", "Avalos": "ATA",
  // Portugal
  "Costa": "GOL", "Cancelo": "LD", "Ruben Dias": "ZAG", "Inacio": "ZAG", "Nuno Mendes": "LE", "Joao Neves": "MC", "Vitinha": "VOL", "Bruno Fernandes": "MC", "Bernardo Silva": "PD", "Joao Felix": "PE", "Cristiano Ronaldo": "ATA",
  // Qatar
  "Barsham": "GOL", "Al-Oui": "LD", "Khoukhi": "ZAG", "Pedro Miguel": "ZAG", "Al-Amin": "LE", "Boudiaf": "VOL", "Fathy": "MC", "Laye": "MC", "Edmilson Junior": "PD", "Afif": "PE", "Almoez Ali": "ATA",
  // Czech Republic
  "Hornicek": "GOL", "Chaloupek": "ZAG", "Hranac": "ZAG", "Krejci": "ZAG", "Zeleny": "AD", "Coufal": "AE", "Soucek": "VOL", "Darida": "VOL", "Provod": "MEI", "Sulc": "MEI", "Schick": "ATA",
  // DR Congo
  "Mpasi": "GOL", "Wan-Bissaka": "LD", "Mbemba": "ZAG", "Tuanzebe": "ZAG", "Masuaku": "LE", "Pickel": "VOL", "Moutoussamy": "VOL", "Bongonda": "PD", "Kakuta": "MEI", "Wissa": "PE", "Bakambu": "ATA",
  // Scotland
  "Gordon": "GOL", "Hickey": "LD", "Hanley": "ZAG", "McKenna": "ZAG", "Robertson": "LE", "Ferguson": "VOL", "Gannon-Doak": "MD", "Christie": "MC", "McTominay": "MC", "McGinn": "ME", "Adams": "ATA",
  // Senegal
  "Mendy": "GOL", "Diatta": "LD", "Koulibaly": "ZAG", "Niakhaté": "ZAG", "Jakobs": "LE", "Idrissa Gueye": "VOL", "Pape Gueye": "VOL", "Ismaila Sarr": "PD", "Iliman Ndiaye": "MEI", "Mané": "PE", "Jackson": "ATA",
  // Spain
  "Simon": "GOL", "Llorente": "LD", "Cubarsì": "ZAG", "Laporte": "ZAG", "Cucurella": "LE", "Pedri": "MC", "Rodri": "VOL", "Fabian Ruiz": "MC", "Yamal": "PD", "N. Williams": "PE", "Oyarzabal": "ATA",
  // USA
  "Freese": "GOL", "Freeman": "LD", "Richards": "ZAG", "Trusty": "ZAG", "Antonee Robinson": "LE", "McKennie": "MC", "Berhalter": "VOL", "Adams": "MC", "Weah": "PD", "Pulisic": "PE", "Balogun": "ATA",
  // South Africa
  "Williams": "GOL", "Mudau": "LD", "Sibisi": "ZAG", "Ndamane": "ZAG", "Modiba": "LE", "Sithole": "VOL", "Mokoena": "VOL", "Apollis": "PD", "Zwane": "MEI", "Mofokeng": "PE", "Foster": "ATA",
  // Sweden
  "Nordfeldt": "GOL", "Starfelt": "ZAG", "Lagerbielke": "ZAG", "Lindelof": "ZAG", "Svensson": "AD", "Gudmundsson": "AE", "Karlstrom": "VOL", "Ayari": "VOL", "Nygren": "MEI", "Elanga": "MEI", "Gyokeres": "ATA",
  // Swiss
  "Kobel": "GOL", "Widmer": "LD", "Akanji": "ZAG", "Elvedi": "ZAG", "Rodriguez": "LE", "Freuler": "MC", "Xhaka": "VOL", "Rieder": "MC", "Ndoye": "PD", "Vargas": "PE", "Embolo": "ATA",
  // Tunisia
  "Dahmen": "GOL", "Valery": "LD", "Bronn": "ZAG", "Talbi": "ZAG", "Abdi": "LE", "Gharbi": "MC", "Skhiri": "VOL", "Hannibal": "MC", "Achouri": "PD", "Tounekti": "PE", "Mastouri": "ATA",
  // Turkey
  "Cakir": "GOL", "Demiral": "ZAG", "Kabak": "ZAG", "Bardakci": "ZAG", "Celik": "AD", "Ozer": "AE", "Calhanoglu": "VOL", "Kokcu": "VOL", "Guler": "MEI", "Yildiz": "MEI", "Akturkoglu": "ATA",
  // Uruguay
  "Rochet": "GOL", "Valera": "LD", "Gimenez": "ZAG", "Araujo": "ZAG", "Olivera": "LE", "Valverde": "MC", "Ugarte": "VOL", "Bentancur": "MC", "Canobbio": "PD", "Rodriguez": "PE", "Nunez": "ATA",
  // Uzbekistan
  "Nematov": "GOL", "Abdullaev": "ZAG", "Ashurmatov": "ZAG", "Khusanov": "ZAG", "Sayfiev": "AD", "Nasrullaev": "AE", "Shukurov": "VOL", "Khamrobekov": "VOL", "Ganiev": "MEI", "Urunov": "MEI", "Shomurodov": "ATA"
};

// === ENGINE DE COORDENADAS E FORMAÇÕES ===
// As labels foram alinhadas para mapear ordenadamente conforme o peso (POSITION_WEIGHT)
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
      [0.5, 0.60],   // VOL Central
      [0.75, 0.45],  // MC Dir
      [0.25, 0.45],  // MC Esq
      [0.8, 0.25],   // PD
      [0.2, 0.25],   // PE
      [0.5, 0.20],   // ATA
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
      [0.85, 0.55],  // AD
      [0.15, 0.55],  // AE
      [0.5, 0.60],   // VOL
      [0.65, 0.50],  // MC
      [0.35, 0.50],  // MC
      [0.6, 0.22],   // ATA
      [0.4, 0.22],   // ATA
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "AD", "AE", "VOL", "MC", "MC", "ATA", "ATA"]
  },
  "3-4-2-1": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],  // AD
      [0.15, 0.55],  // AE
      [0.6, 0.60],   // VOL
      [0.4, 0.60],   // VOL
      [0.65, 0.40],  // MEI
      [0.35, 0.40],  // MEI
      [0.5, 0.20],   // ATA
    ],
    positions: ["GOL", "ZAG", "ZAG", "ZAG", "AD", "AE", "VOL", "VOL", "MEI", "MEI", "ATA"]
  },
  "3-4-3": {
    coords: [
      [0.5, 0.92],
      [0.75, 0.78],
      [0.5, 0.80],
      [0.25, 0.78],
      [0.85, 0.55],  // AD
      [0.15, 0.55],  // AE
      [0.6, 0.60],   // VOL
      [0.4, 0.60],   // VOL
      [0.8, 0.25],   // PD
      [0.2, 0.25],   // PE
      [0.5, 0.20],   // ATA
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
      [0.5, 0.65],   // VOL (Âncora)
      [0.65, 0.48],  // MC
      [0.35, 0.48],  // MC
      [0.85, 0.45],  // MD
      [0.15, 0.45],  // ME
      [0.5, 0.20],   // ATA
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "LE", "VOL", "MC", "MC", "MD", "ME", "ATA"]
  },
  "5-4-1": {
    coords: [
      [0.5, 0.92],
      [0.9, 0.72],   // LD (Ala)
      [0.7, 0.78],   // ZAG Dir
      [0.5, 0.80],   // ZAG Cen
      [0.3, 0.78],   // ZAG Esq
      [0.1, 0.72],   // LE (Ala)
      [0.6, 0.55],   // VOL
      [0.4, 0.55],   // VOL
      [0.8, 0.40],   // MD
      [0.2, 0.40],   // ME
      [0.5, 0.20],   // ATA
    ],
    positions: ["GOL", "LD", "ZAG", "ZAG", "ZAG", "LE", "VOL", "VOL", "MD", "ME", "ATA"]
  }
} as const;

export type Formation = keyof typeof FORMATIONS;