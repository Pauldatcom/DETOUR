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
 * The O rises half a capital (group translate(0 -330)) and stays yellow in the
 * encre / negatif variants; the O lift is the official kit geometry.
 *
 * 96 px rule (#198): once the slot — the real rendered width — falls under
 * 96 px, the DO monogramme replaces the wordmark. The decision is a CSS
 * container query (no JS), driven by `container-type: inline-size` on
 * .logo-slot, so it reacts to squeezes at runtime AND back when space returns.
 * Pass `width` to size the slot exactly (nav 112, footer 128…) — it must stay
 * >= 96 px for the wordmark; a compressed slot swaps automatically.
 */

type LogoVariant = "encre" | "negatif" | "mono-encre" | "mono-blanc";

interface LogoProps {
  variant?: LogoVariant;
  /** Slot width in px; below 96 the DO monogramme is rendered. */
  width?: number;
  /** Play the jumping-o animation once (app open / advisor confirmation). */
  play?: boolean;
  className?: string;
  /** Accessible label override. */
  label?: string;
}

function variantClassOf(variant: LogoVariant): string {
  return variant === "encre"
    ? "logo-encre"
    : variant === "negatif"
      ? "logo-negatif"
      : variant === "mono-encre"
        ? "logo-mono-encre"
        : "logo-mono-blanc";
}

/** Full wordmark: five letters on the baseline, the O raised half a capital. */
export function Logo({
  variant = "encre",
  width,
  play = false,
  className,
  label = "DÉTOUR",
}: LogoProps) {
  const [playing, setPlaying] = useState(play);
  const playedOnce = useRef(false);

  // Play once per mount (or when explicitly re-triggered by a new play prop).
  useEffect(() => {
    if (play && !playedOnce.current) {
      playedOnce.current = true;
      setPlaying(true);
    }
  }, [play]);

  // Static decision: an explicit width under 96 px means DO monogramme only.
  if (width !== undefined && width < 96) {
    return <Monogramme variant={variant} className={className} label={label} play={play} />;
  }

  const variantClass = variantClassOf(variant);
  const playClass = playing ? "play" : "";
  const slotStyle = width !== undefined ? { width } : undefined;

  return (
    <span className={`logo-slot ${className ?? ""}`} style={slotStyle}>
      <svg
        className={`logo logo-wordmark ${variantClass} ${playClass}`}
        viewBox={LOGO_VIEWBOX}
        role="img"
        aria-label={label}
        data-logo="wordmark"
      >
        <path className="rest" d={P_REST} />
        <g transform="translate(0 -330)">
          <g className="o-move">
            <path className="o-fill" d={P_O} />
          </g>
        </g>
      </svg>
      {/*
        DO monogramme of the same conversation: hidden while the wordmark fits
        (>= 96 px), swapped in by the .logo-slot container query when squeezed.
        Kept out of the accessibility tree here — the wordmark carries the label.
      */}
      <svg
        className={`logo logo-do ${variantClass} ${playClass}`}
        viewBox={MONOGRAMME_VIEWBOX}
        aria-hidden="true"
        data-logo="do"
      >
        <path className="rest" d={P_MONOGRAMME_D} />
        <g transform="translate(-1085 -330)">
          <g className="o-move">
            <path className="o-fill" d={P_O} />
          </g>
        </g>
      </svg>
    </span>
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
  return (
    <svg
      className={`logo ${variantClassOf(variant)} ${play ? "play" : ""} ${className ?? ""}`}
      viewBox={MONOGRAMME_VIEWBOX}
      role="img"
      aria-label={label}
      data-logo="monogram"
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
