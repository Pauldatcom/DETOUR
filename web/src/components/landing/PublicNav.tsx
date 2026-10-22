import { useState } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../Logo";
import { NAVIGATION } from "../../data/detourContent";

/** Navigation publique DÉTOUR — 2026 brand: chalk bar, official wordmark, ink links. */
export function PublicNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-chalk/90 backdrop-blur">
      <nav
        aria-label="Navigation principale"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <Link
          to="/accueil"
          className="flex w-28 items-center gap-2"
          aria-label="DÉTOUR, accueil"
          onClick={() => setOpen(false)}
        >
          <Logo variant="encre" width={112} />
          <span className="sr-only">DÉTOUR</span>
        </Link>

        <ul className="hidden items-center gap-6 lg:flex">
          {NAVIGATION.map((item) => (
            <li key={item.label}>
              <Link
                to={item.href}
                className="rounded-lg px-2 py-1 text-sm font-medium text-ink transition hover:text-ballast"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            to="/login"
            className="rounded-full bg-ink px-4 py-2 text-sm font-semibold text-chalk transition hover:bg-ink/85"
          >
            Se connecter
          </Link>
        </div>

        <button
          className="rounded-lg p-2 text-ink lg:hidden"
          aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            {open ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
              />
            )}
          </svg>
        </button>
      </nav>

      {open && (
        <div className="border-t border-line bg-chalk px-4 py-4 lg:hidden">
          <ul className="flex flex-col gap-1">
            {NAVIGATION.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  className="block rounded-lg px-3 py-2 text-sm font-medium text-ink hover:bg-sky/40"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link
                to="/login"
                className="mt-2 block rounded-full bg-ink px-3 py-2 text-center text-sm font-semibold text-chalk"
                onClick={() => setOpen(false)}
              >
                Se connecter
              </Link>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
