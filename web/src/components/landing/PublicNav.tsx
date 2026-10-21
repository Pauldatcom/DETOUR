import { useState } from "react";
import { Link } from "react-router-dom";
import { NAVIGATION } from "../../data/detourContent";
import type { Session } from "../../types";

interface PublicNavProps {
  session: Session | null;
  onLogout: () => Promise<void>;
}

/** Navigation DÉTOUR — lien de connexion ou menu du compte selon la session. */
export function PublicNav({ session, onLogout }: PublicNavProps) {
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const connecte = session?.connecte ?? false;
  const conseiller = session?.role === "conseiller";
  const destinationCompte = conseiller ? "/conseiller" : "/mon-compte";

  async function deconnecter() {
    setOpen(false);
    setProfileOpen(false);
    await onLogout();
  }

  const lienCompte = (
    <Link
      to={destinationCompte}
      className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
      onClick={() => {
        setOpen(false);
        setProfileOpen(false);
      }}
    >
      {conseiller ? "Espace conseiller" : "Mon espace"}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-[#e8eef6] bg-white/90 backdrop-blur">
      <nav
        aria-label="Navigation principale"
        className="relative mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
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
                className="rounded-lg px-2 py-1 text-sm font-medium text-[#334d6b] transition outline-none hover:text-[#0b2447] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-3 lg:flex">
            {!connecte && (
              <Link
                to="/login"
                className="rounded-full border border-[#d5e0ee] px-4 py-2 text-sm font-semibold text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                Se connecter
              </Link>
            )}
          </div>

          {connecte && (
            <button
              type="button"
              onClick={() => setProfileOpen((value) => !value)}
              className="grid h-10 w-10 place-items-center rounded-full border border-[#d5e0ee] bg-[#f7fafd] text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              aria-label="Ouvrir le menu du profil"
              aria-expanded={profileOpen}
              aria-controls="profile-menu"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.6}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 6.75a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.5 20.1a7.5 7.5 0 0 1 15 0 17.9 17.9 0 0 1-7.5 1.65 17.9 17.9 0 0 1-7.5-1.65Z"
                />
              </svg>
            </button>
          )}

          <button
            className="rounded-lg p-2 text-[#0b2447] outline-none focus-visible:ring-2 focus-visible:ring-[#38bdb8] lg:hidden"
            aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
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
        </div>
      </nav>

      {profileOpen && connecte && (
        <div
          id="profile-menu"
          className="absolute top-16 right-4 z-50 w-56 rounded-xl border border-[#e8eef6] bg-white p-2 shadow-lg sm:right-[max(1.5rem,calc((100vw-72rem)/2))]"
        >
          <p className="px-3 pt-2 text-xs font-medium text-[#8ba8c4]">
            {session?.nom || session?.email || "Compte connecté"}
          </p>
          {lienCompte}
          {!conseiller && (
            <>
              <Link
                to="/mon-compte/demandes"
                className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
                onClick={() => setProfileOpen(false)}
              >
                Mes demandes
              </Link>
              <Link
                to="/mon-compte/parametres"
                className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
                onClick={() => setProfileOpen(false)}
              >
                Paramètres
              </Link>
            </>
          )}
          <button
            type="button"
            onClick={() => void deconnecter()}
            className="mt-1 block w-full rounded-lg px-3 py-2 text-left text-sm font-semibold text-[#b91c1c] hover:bg-[#fff0f0]"
          >
            Déconnexion
          </button>
        </div>
      )}

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
            {connecte ? (
              <>
                <li>{lienCompte}</li>
                {!conseiller && (
                  <>
                    <li>
                      <Link
                        to="/mon-compte/demandes"
                        className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
                        onClick={() => setOpen(false)}
                      >
                        Mes demandes
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/mon-compte/parametres"
                        className="block rounded-lg px-3 py-2 text-sm font-medium text-[#334d6b] hover:bg-[#f2f7fc]"
                        onClick={() => setOpen(false)}
                      >
                        Paramètres
                      </Link>
                    </li>
                  </>
                )}
                <li>
                  <button
                    type="button"
                    onClick={() => void deconnecter()}
                    className="block w-full rounded-lg px-3 py-2 text-left text-sm font-semibold text-[#b91c1c] hover:bg-[#fff0f0]"
                  >
                    Déconnexion
                  </button>
                </li>
              </>
            ) : (
              <li>
                <Link
                  to="/login"
                  className="block rounded-lg px-3 py-2 text-sm font-semibold text-[#0b2447] hover:bg-[#f2f7fc]"
                  onClick={() => setOpen(false)}
                >
                  Se connecter
                </Link>
              </li>
            )}
          </ul>
        </div>
      )}
    </header>
  );
}
