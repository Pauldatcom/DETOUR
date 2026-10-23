# 2026 brand kit: frontend rules

Refs #108 (parent epic: rebrand and redesign the frontend).

This document extracts, from the official brand kit, the rules that affect the
frontend. It must be read before any redesign work. The source of truth stays
[`brand-2026/charte/index.html`](../brand-2026/charte/index.html) (brand kit
1.0, October 2026): if this document and the brand kit disagree, the brand kit
wins.

## 1. Official logo files

The SVG files in `brand-2026/logo/` are authoritative. PNG files are exports.

| File | Use |
|---|---|
| `detour-logo.svg` | Primary logo: ink and yellow on chalk. Default choice. |
| `detour-logo-negatif.svg` | Negative: chalk and yellow on ink. Dark backgrounds. |
| `detour-logo-mono-encre.svg` | Ink monochrome: one-color contexts. |
| `detour-logo-mono-blanc.svg` | White monochrome: on a dark photo or a flat color. |
| `detour-logo-anime.svg` | Animated jump of the O (see [Motion](#4-motion)). |
| `detour-monogramme.svg` | "DO" monogram: favicon and small sizes. |
| `detour-icone-app.svg` | App icon. |
| `detour-avatar.svg` | Avatar (advisor chat, social accounts). |
| `png/icone-32.png`, `png/icone-180.png`, `png/icone-512.png` | Raster icons (favicon fallback, Apple touch icon, PWA). |

The front serves an identical copy of the SVG files from
`web/public/brand-2026/logo/` (byte-for-byte equal to `brand-2026/logo/`).
`web/src/components/conseiller/BrandLogo.tsx` is the component that renders
them. If the kit is updated, both copies must be updated together.

The previous brand assets (`brand/` folder) were removed from `main`
(#136) and must not be reintroduced.

## 2. Logo rules

- The logo is always a file, never typed text. Writing "DÉTOUR" in a font in
  place of the logo is not allowed.
- The O sits half a cap height above the line, at every size. The gap it
  leaves on the line is part of the drawing.
- Minimum width on screen: **96 px**. Below that, or below **24 px** high,
  use the monogram.
- Favicon: monogram only, corners rounded at 22.5 %.
- Keep the protection zone around the logo free.
- Do not:
  - put the O back on the line (except the first frame of the animation);
  - move the O down;
  - change the O color (yellow; white on a yellow background; or the mono
    color);
  - stretch, squash or slant the logo;
  - make another letter jump;
  - add shadows, outlines or gradients.
- On yellow: the O turns white. On a photo: chalk version, on a calm area of
  the image.

## 3. Colors

| Token | Hex | Role |
|---|---|---|
| Encre (ink) | `#16233F` | Text, logo, flat areas |
| Craie (chalk) | `#F6F1E7` | Main background |
| Jaune (yellow) | `#F2B705` | The O. One accent per page. |
| Ciel (sky) | `#BCD3EA` | Secondary backgrounds |
| Brique (brick) | `#C4553A` | Alerts, changed price |
| Ballast | `#6B7385` | Secondary text |

- Typical proportions: chalk 60, ink 28, then 6 and 4 for the rest.
- Yellow is reserved for the O and **one** element per composition.
- **Yellow is never a text color on a light background** (contrast 1.9:1).
- These tokens already exist in `web/src/index.css` (`--color-ink`,
  `--color-chalk`, `--color-yellow`, `--color-sky`, `--color-brick`,
  `--color-ballast`). New code must use them, not raw hex values.

## 4. Motion

- The O leaves the line, jumps above its place, falls back and clicks into
  position.
- Duration **1.15 s**, curve `cubic-bezier(.3, .7, .4, 1)`, transform origin
  at the bottom of the O.

  | Time | Phase | Detail |
  |---|---|---|
  | 0 → 180 ms | Wind-up | O squashed on the line: 108 % × 86 % |
  | 180 → 500 ms | Jump | Overshoots its place and stretches |
  | 500 → 870 ms | Click | Falls too low, squashes, bounces |
  | 870 → 1150 ms | Rest | Settles at half a cap height |

- When: opening the site or the app, and when an advisor confirms a booking
  (the O clicks: it is validated).
- Never: in a loop, on repeated hover, or when the user asked for reduced
  motion (`prefers-reduced-motion: reduce`).

## 5. Typography

Two families only, both SIL OFL 1.1 and loaded from Google Fonts. No third
family.

| Family | Weights | Use |
|---|---|---|
| Bricolage Grotesque | 600, 800 | Titles, prices, taglines. Lowercase, tight tracking (−2.5 %). |
| Instrument Sans | 400, 500, 600 | Body text, interface, proposals sent to travelers. |

- Capitals are reserved for the logo.
- Reference scale: display 96, title 44, subtitle 26, body 17, caption 13
  (px).
- Both fonts are already loaded in `web/index.html` and exposed as
  `--font-display` and `--font-sans` in `web/src/index.css`.

## 6. The typographic jump

- In a title or tagline, **one** "o", and only one, jumps by half its own
  height and turns yellow.
- Pick the "o" of the word that carries the idea (court, dos, détour), never
  a random one.
- One per composition. Two jumps on the same page is noise.
- Only in titles and taglines from **28 px**. Never in body text, a price or
  an address.
- Since the jumping "o" is yellow, it must sit on a background where it stays
  legible (see the yellow rule in [Colors](#3-colors)).

## 7. Tone of voice (UI copy)

User-facing text stays in French (see `AGENT.md`).

- Precise first, playful second, and only at the end of the message.
- A price is always dated: "179 € par personne. Prix vérifié ce matin à
  9 h 40." No "à partir de" with an asterisk.
- An availability always has a time. If it changes, say it first.
- Each proposal is signed by an advisor with their first name. "Nous" for the
  agency, "je" for the advisor.
- At most one touch of humor per message, never about a price or a problem.
- Errors are explained and offer an alternative, for example "L'atelier du
  samedi est complet depuis ce matin. Je vous propose dimanche 10 h, même
  prix ?" and not "Erreur : places insuffisantes".
- No exclamation-mark slogans ("Partez autrement !").

## 8. Photography

- Film grain, natural light, people seen from the back or in profile, busy
  doing something.
- Wide framing with space. One warm color spot.
- Real places of our destinations (Nantes, Lyon, Lille).
- Not allowed: eye contact with the camera, posed smiles, HDR, saturated
  sunsets, suitcases, planes, stock photos.
- Reference images: `brand-2026/photo/` (hotel, Lille, Lyon, Nantes, train).

## 9. Product references

Section 12 of the brand kit shows three reference screens: the home page, the
travel notebook sent to the traveler, and the advisor confirmation screen
("this is where the O clicks"). Every price on those screens shows its check
time and the advisor's first name ("Prix vérifié le 19/10 à 09:40 · Confirmé
par Alice").

## 10. Previous identity still in the code

Audit of `main` at `096fa6b`. These places do not follow the 2026 brand yet
and must be migrated by the redesign tickets.

### React front (`web/`)

| Location | Problem |
|---|---|
| `web/src/index.css` | Legacy aliases kept "for pages not yet rebranded (#126)": `--color-base`, `--color-surface`, `--color-border`, `--color-accent`, `--color-accent-bright`, `--color-muted`, `--color-text`, `--color-danger`, `--color-success`, `--color-warning`. |
| `web/src/lib/format.ts` | Status colors use the legacy tokens (`text-accent`, `text-success`, `text-warning`, `text-danger`, `text-muted`). |
| `web/src/components/StatusBadge.tsx` | Legacy tokens (`border-border`, `bg-surface`, `text-muted`). |
| `web/src/components/DataTable.tsx` | Legacy tokens (`border-border`, `bg-surface`, `text-muted`, `text-text`). |
| `web/src/components/PropositionCard.tsx` | Raw off-brand colors (`#0b2447`, `#4b6480`, `#8ba8c4`, `#e8eef6`). |
| `web/src/App.tsx` | Raw off-brand color (`#4b6480`). |
| `web/src/components/landing/Hero.tsx` | Gradients (`#12335e`, `#1d4f7a`, `#38bdb8`, …) and `text-[#0b2447]`. Gradients are forbidden by the brand kit. |
| `web/src/components/landing/DestinationCard.tsx` | Decorative gradients per destination, and destinations that are not ours (Lisbonne, Kyoto, Patagonie, Italie, Maroc). |
| `web/src/components/landing/Inspirations.tsx` | `bg-[#0b2447]` button. |
| `web/src/components/landing/AdvisorAvailability.tsx` | `text-[#0b2447]` button. |
| `web/src/pages/Conseillers.tsx` | `text-[#0b2447]` button. |
| `web/src/components/landing/Footer.tsx` | Logo typed as text ("DÉTOUR"). |
| `web/src/components/landing/PublicNav.tsx` | Logo typed as text ("DÉTOUR") next to the monogram. |
| `web/src/pages/Login.tsx` | Logo typed as text ("DÉTOUR"). |

### Legacy HTML pages (outside `web/`)

| Location | Problem |
|---|---|
| `conseiller/app.css` (`chat.html`, `conseiller.html`, `login.html`) | Previous dark identity: `#07101e` background, cyan accent `#5acbe2`, Inter font, text "brand mark" instead of the logo file. |
| `server/dashboard.css` (`dashboard.html`) | Same previous identity. |

## 11. Open questions before coding

1. **Scope**: are the legacy HTML pages (`conseiller/*.html`,
   `server/dashboard.html`) part of the redesign, or only the React front in
   `web/`? `server/` is the fictional supplier's tool, not a DÉTOUR screen.
2. **Animated logo**: `detour-logo-anime.svg` loops forever (3.6 s,
   `infinite`), but the brand kit says 1.15 s, once per visit, never in a
   loop. Should we ask for a corrected file, or play the jump once in CSS
   from the static logo?
3. **Status colors**: the palette only defines brick for alerts. Which
   brand colors map to "success", "warning" and "neutral" statuses
   (`format.ts`)?
4. **Destination cards**: should the gradients be replaced by the photos in
   `brand-2026/photo/` and the fictional destinations limited to Nantes, Lyon
   and Lille?
5. **Existing work**: the `rebrand-2026` branch already contains redesign
   commits (#126, #113, #127, #128). Is it the base for the next tickets, or
   is it abandoned?
6. **"Once per visit"**: should the opening animation be remembered per
   browser session (`sessionStorage`) or play on every full page load?
