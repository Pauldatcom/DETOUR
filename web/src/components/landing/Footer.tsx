import { Link } from "react-router-dom";
import { FOOTER } from "../../data/detourContent";
import { BrandLogo } from "../conseiller/BrandLogo";

/** Footer public DÉTOUR. */
export function Footer() {
  return (
    <footer className="bg-[#06101c] text-[#8ba8c4]">
      <div className="mx-auto max-w-6xl px-4 pt-14 pb-8 sm:px-6">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1fr_1fr]">
          <div>
            <Link to="/accueil" className="flex items-center gap-2">
              <BrandLogo variant="negative" width={105} alt="DÉTOUR" />
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed">{FOOTER.tagline}</p>
            <div className="mt-4 flex gap-3">
              {["Twitter / X", "Instagram", "LinkedIn"].map((r) => (
                <span
                  key={r}
                  aria-label={r}
                  className="grid h-8 w-8 cursor-not-allowed place-items-center rounded-lg border border-white/10 text-xs text-[#8ba8c4] opacity-50"
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
              <h3 className="mb-3 text-xs font-semibold tracking-widest text-white uppercase">
                {col.titre}
              </h3>
              <ul className="space-y-2">
                {col.liens.map((lien) => (
                  <li key={lien.label}>
                    <Link
                      to={lien.href}
                      className="text-sm transition outline-none hover:text-white focus-visible:text-white"
                    >
                      {lien.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-start justify-between gap-3 border-t border-white/10 pt-6 text-xs sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} DÉTOUR</p>
          <p className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[#7fd9d5]">
            {FOOTER.mentions}
          </p>
        </div>
      </div>
    </footer>
  );
}
