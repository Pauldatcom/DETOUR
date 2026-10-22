import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api } from "../lib/api";

interface LoginProps {
  onSession: () => Promise<void>;
  googleOauth: boolean;
}

/** Page Login — même design que la landing (clair, night blue, accents turquoise). */
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
      let role: string;
      if (tab === "login") {
        role = (await api.login(email, password)).session.role;
      } else if (tab === "register") {
        role = (await api.register(email, nom, password)).session.role;
      } else {
        role = (await api.loginConseiller(cle)).session.role;
      }
      await onSession();
      navigate(role === "client" ? "/mon-compte" : "/accueil");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-white text-[#0b2447]">
      {/* Mini-nav */}
      <header className="sticky top-0 z-40 border-b border-[#e8eef6] bg-white/90 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Link to="/accueil" className="flex items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-[#0b2447] text-lg font-bold text-white">
              D
            </span>
            <span className="text-lg font-bold tracking-wide">DÉTOUR</span>
          </Link>
          <Link
            to="/accueil"
            className="rounded-full border border-[#d5e0ee] px-4 py-1.5 text-sm font-semibold text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
          >
            ← Retour à l'accueil
          </Link>
        </nav>
      </header>

      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-[#e8eef6] bg-white p-8 shadow-lg">
          <h1 className="text-2xl font-bold">Bienvenue</h1>
          <p className="mt-1 text-sm text-[#4b6480]">
            Connectez-vous pour accéder à vos demandes et gérer votre compte.
          </p>

          {/* Onglets */}
          <div className="mt-6 flex gap-1 rounded-xl border border-[#e8eef6] bg-[#f7fafd] p-1">
            {(
              [
                ["login", "Connexion"],
                ["register", "Inscription"],
                ["conseiller", "Conseiller"],
              ] as const
            ).map(([t, label]) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition outline-none ${
                  tab === t
                    ? "bg-[#0b2447] text-white shadow"
                    : "text-[#4b6480] hover:text-[#0b2447]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4">
            {tab === "register" && (
              <div>
                <label className="mb-1 block text-sm font-medium text-[#0b2447]">Nom</label>
                <input
                  value={nom}
                  onChange={(e) => setNom(e.target.value)}
                  className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm transition outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                  required
                />
              </div>
            )}

            {tab !== "conseiller" ? (
              <>
                <div>
                  <label className="mb-1 block text-sm font-medium text-[#0b2447]">E-mail</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm transition outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-[#0b2447]">
                    Mot de passe
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm transition outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    required
                    minLength={6}
                  />
                </div>
              </>
            ) : (
              <div>
                <label className="mb-1 block text-sm font-medium text-[#0b2447]">
                  Clé d'accès conseiller
                </label>
                <input
                  type="password"
                  value={cle}
                  onChange={(e) => setCle(e.target.value)}
                  className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm transition outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                  required
                />
              </div>
            )}

            {error && (
              <p role="alert" className="rounded-xl bg-[#fff0f0] px-4 py-2 text-sm text-[#b91c1c]">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-[#0b2447] px-6 py-3 font-semibold text-base text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] focus-visible:ring-offset-2 disabled:opacity-60"
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
              <div className="my-4 flex items-center gap-3 text-xs text-[#8ba8c4]">
                <div className="h-px flex-1 bg-[#e8eef6]" />
                ou
                <div className="h-px flex-1 bg-[#e8eef6]" />
              </div>
              <button
                onClick={() => api.googleAuth()}
                className="w-full rounded-full border border-[#d5e0ee] px-4 py-2.5 text-sm font-medium text-[#0b2447] transition outline-none hover:bg-[#f2f7fc] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                Continuer avec Google
              </button>
            </>
          )}

          <p className="mt-6 rounded-xl bg-[#f0eefe] px-4 py-3 text-xs text-[#6b3e9e]">
            Projet fictif — aucune réservation réelle. Les comptes servent à accéder au chatbot et à
            vos propositions.
          </p>
        </div>
      </div>
    </div>
  );
}
