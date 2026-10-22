import { useState } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../Logo";
import { NAVIGATION } from "../../data/detourContent";
import type { Session } from "../../types";

interface PublicNavProps {
  session: Session | null;
  onLogout: () => Promise<void>;
}

/** Navigation DÉTOUR — session-aware, skip-link + DO monogram (#131). */
export function PublicNav({ session, onLogout }: PublicNavProps) {
  const [open, setOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const connecte = session?.connecte ?? false;
  const conseiller = session?.role === "conseiller";
  const destinationCompte = conseiller ? "/espace-conseiller" : "/mon-compte";

  async function deconnecter() {
    setOpen(false);
    setProfileOpen(false);
    await onLogout();
  }

  const lienCompte = (
    <Link
      to={destinationCompte}
      className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
      onClick={() => {
        setOpen(false);
        setProfileOpen(false);
      }}
    >
      {conseiller ? "Espace conseiller" : "Mon espace"}
    </Link>
  );

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-chalk/90 backdrop-blur">
      <a href="#contenu-principal" className="skip-link">
        Aller au contenu
      </a>
      <nav
        aria-label="Navigation principale"
        className="relative mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <Link
          to="/accueil"
          className="flex min-w-0 items-center gap-2"
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
                className="rounded-lg px-2 py-1 text-sm font-medium text-ballast transition outline-none hover:text-ink"
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
                className="rounded-full border border-ink/15 px-4 py-2 text-sm font-semibold text-ink transition outline-none hover:border-ink/40"
              >
                Se connecter
              </Link>
            )}
          </div>

          {connecte && (
            <button
              type="button"
              onClick={() => setProfileOpen((value) => !value)}
              className="grid h-10 w-10 place-items-center rounded-full border border-ink/15 bg-card text-ink transition outline-none hover:border-ink/40"
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
            type="button"
            className="rounded-lg p-2 text-ink outline-none lg:hidden"
            aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
            aria-expanded={open}
            aria-controls="nav-mobile"
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
          className="absolute top-16 right-4 z-50 w-56 rounded-xl border border-line bg-card p-2 shadow-lg sm:right-[max(1.5rem,calc((100vw-72rem)/2))]"
        >
          <p className="px-3 pt-2 text-xs font-medium text-ballast">
            {session?.nom || session?.email || "Compte connecté"}
          </p>
          {lienCompte}
          {!conseiller && (
            <>
              <Link
                to="/mon-compte/demandes"
                className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
                onClick={() => setProfileOpen(false)}
              >
                Mes demandes
              </Link>
              <Link
                to="/mon-compte/parametres"
                className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
                onClick={() => setProfileOpen(false)}
              >
                Paramètres
              </Link>
            </>
          )}
          <button
            type="button"
            onClick={() => void deconnecter()}
            className="mt-1 block w-full rounded-lg px-3 py-2 text-left text-sm font-semibold text-brick outline-none hover:bg-brick/10"
          >
            Déconnexion
          </button>
        </div>
      )}

      {open && (
        <div id="nav-mobile" className="border-t border-line bg-chalk px-4 py-4 lg:hidden">
          <ul className="flex flex-col gap-1">
            {NAVIGATION.map((item) => (
              <li key={item.label}>
                <Link
                  to={item.href}
                  className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
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
                        className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
                        onClick={() => setOpen(false)}
                      >
                        Mes demandes
                      </Link>
                    </li>
                    <li>
                      <Link
                        to="/mon-compte/parametres"
                        className="block rounded-lg px-3 py-2 text-sm font-medium text-ballast outline-none hover:bg-card hover:text-ink"
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
                    className="block w-full rounded-lg px-3 py-2 text-left text-sm font-semibold text-brick outline-none hover:bg-brick/10"
                  >
                    Déconnexion
                  </button>
                </li>
              </>
            ) : (
              <li>
                <Link
                  to="/login"
                  className="block rounded-lg px-3 py-2 text-sm font-semibold text-ink outline-none hover:bg-card"
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
