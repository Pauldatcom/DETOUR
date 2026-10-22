import { Link } from "react-router-dom";
import { Logo } from "../Logo";
import { JumpingTitle } from "../../lib/jumpingO";
import { HERO } from "../../data/detourContent";

interface HeroProps {
  onDecrir: () => void;
}

/** Hero DÉTOUR — 2026 brand: ink band, negatif wordmark, yellow CTA, jumping o in the title. */
export function Hero({ onDecrir }: HeroProps) {
  return (
    <section className="relative overflow-hidden bg-ink text-chalk">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(1100px 480px at 85% -10%, rgba(188,211,234,0.18), transparent 60%), radial-gradient(900px 480px at 5% 110%, rgba(242,183,5,0.10), transparent 60%)",
        }}
      />
      <div className="relative mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-24">
        <div>
          <p className="mb-3 font-mono text-xs tracking-widest text-sky uppercase">
            {HERO.surtitre}
          </p>
          <h1 className="text-4xl leading-tight font-extrabold sm:text-5xl">
            <JumpingTitle text={HERO.titre} targetWord="conseiller" as="h1" />
          </h1>
          <p className="mt-5 max-w-xl text-lg text-sky">{HERO.texte}</p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <button
              onClick={onDecrir}
              className="rounded-full bg-yellow px-7 py-3 font-semibold text-base text-ink shadow-lg transition hover:bg-yellow/90"
            >
              {HERO.ctaPrincipal}
            </button>
            <Link
              to="/accueil#inspirations"
              className="rounded-full border border-chalk/30 px-7 py-3 text-center font-semibold text-base text-chalk transition hover:border-chalk/60"
            >
              {HERO.ctaSecondaire}
            </Link>
          </div>

          <p className="mt-6 inline-flex items-center gap-2 rounded-full border border-chalk/20 bg-chalk/5 px-4 py-2 text-sm text-sky">
            <span aria-hidden="true" className="h-2 w-2 rounded-full bg-yellow" />
            {HERO.badge}
          </p>
        </div>

        <div className="relative">
          <div className="mb-6 w-56">
            <Logo variant="negatif" play />
          </div>
          <div
            role="img"
            aria-label={HERO.imageAlt}
            className="relative aspect-[4/3] w-full overflow-hidden rounded-3xl shadow-2xl"
            style={{
              background:
                "linear-gradient(160deg, #1d2c4c 0%, #16233f 30%, #bcd3ea 75%, #f2b705 100%)",
            }}
          >
            <div
              aria-hidden="true"
              className="absolute inset-x-0 bottom-0 h-1/3"
              style={{ background: "linear-gradient(to top, rgba(22,35,63,0.6), transparent)" }}
            />
            <span className="absolute bottom-4 left-4 rounded-full bg-ink/60 px-3 py-1 font-mono text-xs text-chalk">
              Visuel d'illustration fictif
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
