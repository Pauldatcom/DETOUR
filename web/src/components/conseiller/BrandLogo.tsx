/**
 * Official 2026 SVG logo / DO monogram.
 * Below 96 px wide → monogram only (brand kit rule).
 * Never recreate the wordmark with a font.
 */

export type BrandLogoVariant =
  "color" | "negative" | "negative-transparent" | "mono-ink" | "mono-white" | "monogram";

const SRC: Record<BrandLogoVariant, string> = {
  color: "/brand-2026/logo/detour-logo.svg",
  negative: "/brand-2026/logo/detour-logo-negatif.svg",
  // Négatif officiel sans le fond Encre du kit : surfaces sombres legacy (#07101E, #06101C).
  "negative-transparent": "/brand-2026/logo/detour-logo-negatif-transparent.svg",
  "mono-ink": "/brand-2026/logo/detour-logo-mono-encre.svg",
  "mono-white": "/brand-2026/logo/detour-logo-mono-blanc.svg",
  monogram: "/brand-2026/logo/detour-monogramme.svg",
};

interface BrandLogoProps {
  /** Rendered width in CSS pixels. Below 96 → monogram. */
  width?: number;
  variant?: BrandLogoVariant;
  className?: string;
  alt?: string;
}

export function BrandLogo({
  width = 120,
  variant = "color",
  className = "",
  alt = "Détour Voyages",
}: BrandLogoProps) {
  const useMonogram = width < 96 || variant === "monogram";
  const src = useMonogram ? SRC.monogram : SRC[variant];
  const w = useMonogram ? Math.min(width, 48) : width;

  return (
    <img
      src={src}
      alt={alt}
      width={w}
      height={useMonogram ? w : undefined}
      className={`block h-auto ${className}`}
      style={{ width: w }}
      decoding="async"
    />
  );
}
