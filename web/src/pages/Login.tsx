import { useState } from "react";
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
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await api.login(email, password);
        onSession();
        navigate("/mes-propositions");
      } else if (tab === "register") {
        await api.register(email, nom, password);
        onSession();
        navigate("/mes-propositions");
      } else {
        await api.loginConseiller(cle);
        onSession();
        navigate("/espace-conseiller");
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
                  <label htmlFor="login-email" className="mb-1 block text-sm font-medium text-ink">
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
