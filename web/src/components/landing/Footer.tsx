import { Link } from "react-router-dom";
import { Logo } from "../Logo";
import { FOOTER } from "../../data/detourContent";

/** Footer public DÉTOUR — 2026 brand: ink band, negatif wordmark, sky links. */
export function Footer() {
  return (
    <footer className="bg-ink text-sky">
      <div className="mx-auto max-w-6xl px-4 pt-14 pb-8 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr]">
          <div>
            <Link
              to="/accueil"
              className="flex w-32 items-center gap-2"
              aria-label="DÉTOUR, accueil"
            >
              <Logo variant="negatif" width={128} />
              <span className="sr-only">DÉTOUR</span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed">{FOOTER.tagline}</p>
            <div className="mt-4 flex gap-3">
              {["Twitter / X", "Instagram", "LinkedIn"].map((r) => (
                <span
                  key={r}
                  aria-label={r}
                  className="grid h-8 w-8 cursor-not-allowed place-items-center rounded-lg border border-chalk/15 text-xs text-sky opacity-50"
                  title={`${r} — lien désactivé (projet fictif)`}
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={1.5}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244"
                    />
                  </svg>
                </span>
              ))}
            </div>
          </div>

          {FOOTER.colonnes.map((col) => (
            <div key={col.titre}>
              <h3 className="mb-3 font-mono text-xs font-semibold tracking-widest text-chalk uppercase">
                {col.titre}
              </h3>
              <ul className="space-y-2">
                {col.liens.map((lien) => (
                  <li key={lien.label}>
                    <Link to={lien.href} className="text-sm transition hover:text-chalk">
                      {lien.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-chalk/15 pt-6 text-xs sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} DÉTOUR</p>
          <p className="rounded-full border border-chalk/15 bg-chalk/5 px-3 py-1 text-sky">
            {FOOTER.mentions}
          </p>
        </div>
      </div>
    </footer>
  );
}
