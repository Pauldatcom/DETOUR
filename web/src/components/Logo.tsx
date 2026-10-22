import { useEffect, useRef, useState } from "react";
import { LOGO_VIEWBOX, MONOGRAMME_VIEWBOX, P_MONOGRAMME_D, P_O, P_REST } from "./logoPaths";

/*
 * Official DÉTOUR logo — rendered from the brand SVG paths (source of truth:
 * brand-2026/logo/*.svg). Never recreate the logo with text, CSS or a font.
 *
 * Variants follow the charte:
 * - encre: ink lettering, yellow O (default, on light backgrounds)
 * - negatif: chalk lettering, yellow O (on ink backgrounds)
 * - mono-encre: all ink (the O included)
 * - mono-blanc: all chalk (the O included)
 *
 * Below 96 px of available width, render the DO monogramme instead.
 */

type LogoVariant = "encre" | "negatif" | "mono-encre" | "mono-blanc";

interface LogoProps {
  variant?: LogoVariant;
  /** Width hint in px; below 96 the monogramme is used. */
  width?: number;
  /** Play the jumping-o animation once (app open / advisor confirmation). */
  play?: boolean;
  className?: string;
  /** Accessible label override. */
  label?: string;
}

/** Full wordmark: five letters on the baseline, the O raised half a capital. */
export function Logo({
  variant = "encre",
  width,
  play = false,
  className,
  label = "DÉTOUR",
}: LogoProps) {
  const useMonogramme = width !== undefined && width < 96;
  const [playing, setPlaying] = useState(play);
  const playedOnce = useRef(false);

  // Play once per mount (or when explicitly re-triggered by a new play prop).
  useEffect(() => {
    if (play && !playedOnce.current) {
      playedOnce.current = true;
      setPlaying(true);
    }
  }, [play]);

  if (useMonogramme) {
    return <Monogramme variant={variant} className={className} label={label} play={play} />;
  }

  const variantClass =
    variant === "encre"
      ? "logo-encre"
      : variant === "negatif"
        ? "logo-negatif"
        : variant === "mono-encre"
          ? "logo-mono-encre"
          : "logo-mono-blanc";

  return (
    <svg
      className={`logo ${variantClass} ${playing ? "play" : ""} ${className ?? ""}`}
      viewBox={LOGO_VIEWBOX}
      role="img"
      aria-label={label}
    >
      <path className="rest" d={P_REST} />
      <g transform="translate(0 -330)">
        <g className="o-move">
          <path className="o-fill" d={P_O} />
        </g>
      </g>
    </svg>
  );
}

/** DO monogramme for narrow placements (< 96 px). */
export function Monogramme({
  variant = "encre",
  className,
  label = "DÉTOUR",
  play = false,
}: {
  variant?: LogoVariant;
  className?: string;
  label?: string;
  play?: boolean;
}) {
  const variantClass =
    variant === "encre"
      ? "logo-encre"
      : variant === "negatif"
        ? "logo-negatif"
        : variant === "mono-encre"
          ? "logo-mono-encre"
          : "logo-mono-blanc";

  return (
    <svg
      className={`logo ${variantClass} ${play ? "play" : ""} ${className ?? ""}`}
      viewBox={MONOGRAMME_VIEWBOX}
      role="img"
      aria-label={label}
    >
      <path className="rest" d={P_MONOGRAMME_D} />
      <g transform="translate(-1085 -330)">
        <g className="o-move">
          <path className="o-fill" d={P_O} />
        </g>
      </g>
    </svg>
  );
}
