import { Link } from "react-router-dom";
import { HERO } from "../../data/detourContent";

interface HeroProps {
  onDecrir: () => void;
}

/** Hero DÉTOUR — grande visuelle dégradée (fictive), CTA principal + secondaire. */
export function Hero({ onDecrir }: HeroProps) {
  return (
    <section className="relative overflow-hidden bg-[#0b2447] text-white">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(1200px 500px at 80% -10%, rgba(56,189,184,0.35), transparent 60%), radial-gradient(900px 500px at 10% 110%, rgba(122,92,214,0.35), transparent 60%)",
        }}
      />
      <div className="relative mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-24">
        <div>
          <p className="mb-3 text-sm font-semibold tracking-widest text-[#7fd9d5] uppercase">
            {HERO.surtitre}
          </p>
          <h1 className="text-4xl leading-tight font-bold sm:text-5xl">{HERO.titre}</h1>
          <p className="mt-5 max-w-xl text-lg text-[#c9d9ec]">{HERO.texte}</p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              onClick={onDecrir}
              className="rounded-full bg-white px-7 py-3 font-semibold text-[#0b2447] text-base shadow-lg transition outline-none hover:bg-[#eaf4fb] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b2447]"
            >
              {HERO.ctaPrincipal}
            </button>
            <Link
              to="/accueil#inspirations"
              className="rounded-full border border-white/30 px-7 py-3 text-center font-semibold text-base text-white transition outline-none hover:border-white/60 focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2 focus-visible:ring-offset-[#0b2447]"
            >
              {HERO.ctaSecondaire}
            </Link>
          </div>
        </div>

        <div
          role="img"
          aria-label={HERO.imageAlt}
          className="relative aspect-[4/3] w-full overflow-hidden rounded-3xl shadow-2xl"
          style={{
            background:
              "linear-gradient(160deg, #12335e 0%, #1d4f7a 35%, #38bdb8 75%, #7a5cd6 100%)",
          }}
        >
          <div
            aria-hidden="true"
            className="absolute inset-x-0 bottom-0 h-1/3"
            style={{
              background: "linear-gradient(to top, rgba(7,16,30,0.55), transparent)",
            }}
          />
          <span className="absolute bottom-4 left-4 rounded-full bg-black/35 px-3 py-1 text-xs font-medium text-white">
            Visuel d'illustration fictif
          </span>
        </div>
      </div>
    </section>
  );
}
