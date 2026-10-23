import { useEffect, useRef, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";
import { Logo } from "../components/Logo";

interface LoginProps {
  onSession: () => void;
  googleOauth: boolean;
}

/** Page Login — 2026 brand: chalk background, card panel, ink accents. Accessible forms (#131). */
export function Login({ onSession, googleOauth }: LoginProps) {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"login" | "register" | "conseiller">("login");
  const [email, setEmail] = useState("");
  const [nom, setNom] = useState("");
  const [password, setPassword] = useState("");
  const [cle, setCle] = useState("");
  const [prenom, setPrenom] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<null | { titre: string; destination: string }>(null);
  const redirection = useRef<number | undefined>(undefined);

  // The success banner stays visible until the deferred navigation fires.
  useEffect(() => () => window.clearTimeout(redirection.current), []);

  function deferNavigation(destination: string) {
    redirection.current = window.setTimeout(() => navigate(destination), 900);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await api.login(email, password);
        onSession();
        setSuccess({ titre: "Connexion réussie", destination: "/mes-propositions" });
        deferNavigation("/mes-propositions");
      } else if (tab === "register") {
        await api.register(email, nom, password);
        onSession();
        setSuccess({ titre: "Compte créé", destination: "/mes-propositions" });
        deferNavigation("/mes-propositions");
      } else {
        // #112: the first name signs the advisor's proposals for the traveler.
        if (!prenom.trim()) {
          setError("Indiquez votre prénom : il signe vos propositions.");
          return;
        }
        await api.loginConseiller(cle, prenom.trim());
        onSession();
        setSuccess({ titre: "Espace conseiller ouvert", destination: "/espace-conseiller" });
        deferNavigation("/espace-conseiller");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  const champClasse =
    "mt-1 w-full rounded-xl border border-ink/15 bg-card px-4 py-2.5 text-sm text-ink outline-none transition focus:border-ink focus:ring-2 focus:ring-sky";
  const errorId = "login-error";

  return (
    <div className="flex min-h-screen flex-col bg-chalk text-ink">
      <a href="#contenu-connexion" className="skip-link">
        Aller au formulaire
      </a>
      <header className="sticky top-0 z-40 border-b border-line bg-chalk/90 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/accueil" className="flex w-28 items-center gap-2" aria-label="DÉTOUR, accueil">
            <Logo variant="encre" width={112} />
            <span className="sr-only">DÉTOUR</span>
          </Link>
          <Link
            to="/accueil"
            className="rounded-full border border-ink/20 px-4 py-1.5 text-sm font-semibold text-ink transition outline-none hover:border-ink"
          >
            ← Retour à l'accueil
          </Link>
        </nav>
      </header>

      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <div
          id="contenu-connexion"
          className="w-full max-w-md rounded-2xl border border-line bg-card p-8 shadow-lg"
        >
          <h1 className="font-display text-2xl font-extrabold tracking-tight">Bienvenue</h1>
          <p className="mt-1 text-sm text-ballast">
            Connectez-vous pour accéder à vos demandes et gérer votre compte.
          </p>

          <div
            className="mt-6 flex gap-1 rounded-xl border border-line bg-chalk p-1"
            role="tablist"
            aria-label="Mode de connexion"
          >
            {(
              [
                ["login", "Connexion"],
                ["register", "Inscription"],
                ["conseiller", "Conseiller"],
              ] as const
            ).map(([t, label]) => (
              <button
                key={t}
                type="button"
                role="tab"
                aria-selected={tab === t}
                onClick={() => {
                  setTab(t);
                  setError("");
                }}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition outline-none ${
                  tab === t ? "bg-ink text-chalk shadow" : "text-ballast hover:text-ink"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {success ? (
            <div className="mt-6 text-center" role="status" aria-live="polite">
              <div
                className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-sky/40"
                aria-hidden="true"
              >
                <svg
                  className="h-7 w-7 text-ink"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </div>
              <h2 className="font-display text-xl font-extrabold text-ink">{success.titre}</h2>
              <p className="mt-3 text-sm text-ballast">Redirection en cours…</p>
            </div>
          ) : (
            <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
              {tab === "register" && (
                <div>
                  <label htmlFor="login-nom" className="mb-1 block text-sm font-medium text-ink">
                    Nom
                  </label>
                  <input
                    id="login-nom"
                    value={nom}
                    onChange={(e) => setNom(e.target.value)}
                    autoComplete="name"
                    aria-describedby={error ? errorId : undefined}
                    className={champClasse}
                    required
                  />
                </div>
              )}

              {tab !== "conseiller" ? (
                <>
                  <div>
                    <label
                      htmlFor="login-email"
                      className="mb-1 block text-sm font-medium text-ink"
                    >
                      E-mail
                    </label>
                    <input
                      id="login-email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      autoComplete="email"
                      aria-invalid={Boolean(error)}
                      aria-describedby={error ? errorId : undefined}
                      className={champClasse}
                      required
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="login-password"
                      className="mb-1 block text-sm font-medium text-ink"
                    >
                      Mot de passe
                    </label>
                    <input
                      id="login-password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete={tab === "login" ? "current-password" : "new-password"}
                      aria-invalid={Boolean(error)}
                      aria-describedby={error ? errorId : undefined}
                      className={champClasse}
                      required
                      minLength={6}
                    />
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <label
                      htmlFor="login-prenom"
                      className="mb-1 block text-sm font-medium text-ink"
                    >
                      Votre prénom
                    </label>
                    <input
                      id="login-prenom"
                      value={prenom}
                      onChange={(e) => setPrenom(e.target.value)}
                      autoComplete="given-name"
                      aria-invalid={Boolean(error)}
                      aria-describedby={error ? errorId : "login-prenom-aide"}
                      className={champClasse}
                      required
                    />
                    <p id="login-prenom-aide" className="mt-1 text-xs text-ballast">
                      Les voyageurs le verront en signature de vos propositions.
                    </p>
                  </div>
                  <div>
                    <label htmlFor="login-cle" className="mb-1 block text-sm font-medium text-ink">
                      Clé d'accès conseiller
                    </label>
                    <input
                      id="login-cle"
                      type="password"
                      value={cle}
                      onChange={(e) => setCle(e.target.value)}
                      autoComplete="current-password"
                      aria-invalid={Boolean(error)}
                      aria-describedby={error ? errorId : undefined}
                      className={champClasse}
                      required
                    />
                  </div>
                </>
              )}

              {error && (
                <p
                  id={errorId}
                  role="alert"
                  className="rounded-xl border border-brick/30 bg-brick/10 px-4 py-2 text-sm text-brick"
                >
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-full bg-ink px-6 py-3 font-semibold text-base text-chalk transition outline-none hover:bg-ink/90 disabled:opacity-60"
              >
                {loading
                  ? "…"
                  : tab === "login"
                    ? "Se connecter"
                    : tab === "register"
                      ? "Créer un compte"
                      : "Accéder"}
              </button>
            </form>
          )}

          {googleOauth && tab !== "conseiller" && (
            <>
              <div className="my-4 flex items-center gap-3 text-xs text-ballast">
                <div className="h-px flex-1 bg-line" />
                ou
                <div className="h-px flex-1 bg-line" />
              </div>
              <button
                type="button"
                onClick={() => api.googleAuth()}
                className="w-full rounded-full border border-ink/20 px-4 py-2.5 text-sm font-medium text-ink transition outline-none hover:bg-sky/40"
              >
                Continuer avec Google
              </button>
            </>
          )}

          <p className="mt-6 rounded-xl bg-sky/40 px-4 py-3 text-xs text-ink">
            Projet fictif — aucune réservation réelle. Les comptes servent à accéder au chatbot et à
            vos propositions.
          </p>
        </div>
      </div>
    </div>
  );
}
