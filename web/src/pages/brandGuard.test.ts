import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Guard test (#126): no old blue/cyan/purple hex values remain in the
 * public-facing React screens and their landing components.
 *
 * The old palette used dark navy (#07101e), cyan (#57c8df, #38bdb8) and
 * purple (#7a5cd6) — none of these should survive in the public screens
 * after the 2026 rebrand.
 */

const OLD_COLORS = ["#07101e", "#57c8df", "#38bdb8", "#7a5cd6"];

const PUBLIC_FILES = [
  "src/pages/Accueil.tsx",
  "src/pages/Login.tsx",
  "src/pages/Inspirations.tsx",
  "src/pages/Conseillers.tsx",
  "src/components/landing/PublicNav.tsx",
  "src/components/landing/Footer.tsx",
  "src/components/landing/Hero.tsx",
  "src/components/landing/Inspirations.tsx",
  "src/components/landing/HowItWorks.tsx",
  "src/components/landing/AdvisorAvailability.tsx",
  "src/components/landing/DestinationCard.tsx",
  "src/components/landing/TravelRequestForm.tsx",
  "src/components/landing/ChatWidget.tsx",
  "src/App.tsx",
];

function readFile(rel: string): string {
  return readFileSync(resolve(process.cwd(), rel), "utf-8");
}

describe("No old color values in public screens (#126)", () => {
  for (const file of PUBLIC_FILES) {
    it(`${file} contains no old palette hex values`, () => {
      const source = readFile(file);
      const lower = source.toLowerCase();
      for (const color of OLD_COLORS) {
        expect(lower, `${file} still contains ${color}`).not.toContain(color);
      }
    });
  }
});
