import { useState } from "react";
import { Link } from "react-router-dom";
import { NAVIGATION } from "../../data/detourContent";

/** Navigation publique DÉTOUR — palette nuit bleu / blanc / accents turquoise-violet. */
export function PublicNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-[#e8eef6] bg-white/90 backdrop-blur">
      <nav
        aria-label="Navigation principale"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <Link to="/accueil" className="flex items-center gap-2" onClick={() => setOpen(false)}>
          <span
            aria-hidden="true"
            className="grid h-9 w-9 place-items-center rounded-xl bg-[#0b2447] text-lg font-bold text-white"
          >
            D
          </span>
          <span className="text-lg font-bold tracking-wide text-[#0b2447]">DÉTOUR</span>
          <span className="hidden rounded-full bg-[#f0eefe] px-2 py-0.5 text-xs font-semibold text-[#7a5cd6] sm:inline">
            Projet fictif
          </span>
        </Link>

        <ul className="hidden items-center gap-6 lg:flex">
          {NAVIGATION.map((item) => (
            <li key={item.label}>
              <Link
                to={item.href}
                className="rounded-lg px-2 py-1 text-sm font-medium text-[#334d6b] outline-none transition hover:text-[#0b2447] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="hidden items-center gap-3 lg:flex">
          <Link
            to="/login"
            className="rounded-full border border-[#d5e0ee] px-4 py-2 text-sm font-semibold text-[#0b2447] outline-none transition hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
          >
            Se connecter
          </Link>
        </div>

        <button
          className="rounded-lg p-2 text-[#0b2447] outline-none focus-visible:ring-2 focus-visible:ring-[#38bdb8] lg:hidden"
          aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
            {open ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            )}
          </svg>
        </button>
      </nav>

      {open && (
        <div className="border-t border-[#e8eef6] bg-white px-4 py-4 lg:hidden">
          <ul className="flex flex-col gap-1">
            {NAVIGATION.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
                  onClick={() => setOpen(false)}
                >
                  {item.label}
                </Link>
              </li>
            ))}
            <li>
              <Link
                to="/login"
                className="block rounded-lg px-3 py-2 text-sm font-semibold text-[#0b2447] hover:bg-[#f2f7fc]"
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
