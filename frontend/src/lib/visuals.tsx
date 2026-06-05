// Visual helpers: real flag images + deterministic player avatars

import { forwardRef, useState } from "react";

const ISO2: Record<string, string> = {
  MEX: "mx", RSA: "za", KOR: "kr", CZE: "cz",
  CAN: "ca", AUS: "au", NOR: "no", SUI: "ch",
  BRA: "br", MAR: "ma", SCO: "gb-sct", HAI: "ht",
  USA: "us", PAR: "py", TUN: "tn", DEN: "dk",
  GER: "de", ECU: "ec", CIV: "ci", KSA: "sa",
  NED: "nl", JPN: "jp", IRN: "ir", UKR: "ua",
  BEL: "be", EGY: "eg", IRL: "ie", NZL: "nz",
  ESP: "es", URU: "uy", CMR: "cm", AUT: "at",
  FRA: "fr", SEN: "sn", POL: "pl", QAT: "qa",
  ARG: "ar", COL: "co", NGA: "ng", JAM: "jm",
  POR: "pt", GHA: "gh", PER: "pe", PAN: "pa",
  ENG: "gb-eng", CRO: "hr", ALG: "dz", UZB: "uz",
};

export function flagUrl(teamId: string, size: 80 | 160 | 320 = 160): string {
  const code = ISO2[teamId] ?? "un";
  return `https://flagcdn.com/w${size}/${code}.png`;
}

// Busca a foto real do jogador usando o proxy público do Bing Imagens
export function playerPhotoUrl(name: string, size = 96): string {
  const query = encodeURIComponent(`${name} football player face`);
  return `https://tse1.mm.bing.net/th?q=${query}&w=${size}&h=${size}&c=7&rs=1&p=0`;
}

// Fallback caso o Bing não encontre a imagem
export function fallbackPhotoUrl(name: string, size = 96): string {
  const seed = encodeURIComponent(name || "player");
  return `https://api.dicebear.com/9.x/initials/svg?seed=${seed}&backgroundColor=0a3d2b,1b6b4a&size=${size}`;
}

type FlagProps = React.ImgHTMLAttributes<HTMLImageElement> & {
  teamId: string;
  size?: 80 | 160 | 320;
};

export const TeamFlag = forwardRef<HTMLImageElement, FlagProps>(
  ({ teamId, size = 160, className, alt, ...rest }, ref) => (
    <img
      ref={ref}
      src={flagUrl(teamId, size)}
      alt={alt ?? `Bandeira ${teamId}`}
      loading="lazy"
      className={
        "inline-block rounded-sm object-cover shadow-[0_0_10px_oklch(0.82_0.23_152/.35)] ring-1 ring-primary/40 " +
        (className ?? "")
      }
      {...rest}
    />
  ),
);
TeamFlag.displayName = "TeamFlag";

type AvatarProps = React.ImgHTMLAttributes<HTMLImageElement> & {
  name: string;
  px?: number;
};

export const PlayerAvatar = forwardRef<HTMLImageElement, AvatarProps>(
  ({ name, px = 40, className, alt, ...rest }, ref) => {
    const [hasError, setHasError] = useState(false);

    return (
      <img
        ref={ref}
        // Se der erro, troca a source instantaneamente para o fallback das iniciais
        src={hasError ? fallbackPhotoUrl(name, px * 2) : playerPhotoUrl(name, px * 2)}
        onError={() => setHasError(true)}
        alt={alt ?? name}
        loading="lazy"
        draggable={false}
        className={
          "inline-block rounded-full bg-background object-cover ring-1 ring-primary/50 shadow-[0_0_10px_oklch(0.82_0.23_152/.45)] " +
          (className ?? "")
        }
        style={{ width: px, height: px }}
        {...rest}
      />
    );
  }
);
PlayerAvatar.displayName = "PlayerAvatar";