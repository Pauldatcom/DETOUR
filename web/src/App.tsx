import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useSession } from "./hooks/useSession";
import { Accueil } from "./pages/Accueil";
import { Login } from "./pages/Login";
import { InspirationsPage } from "./pages/Inspirations";
import { ConseillersPage } from "./pages/Conseillers";
import { MesPropositions } from "./pages/MesPropositions";
import { api } from "./lib/api";
import type { Config } from "./types";

/**
 * Routage DÉTOUR — pas de dashboard.
 *
 * Public : / → /accueil, /inspirations, /conseillers, /login
 * Authentifié : /mes-propositions
 */
export default function App() {
  const { session, loading, refresh } = useSession();
  const [config, setConfig] = useState<Config | null>(null);

  useEffect(() => {
    api
      .config()
      .then(setConfig)
      .catch(() =>
        setConfig({ simulation: true, agent_actif: false, google_oauth: false, model: "" }),
      );
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white">
        <span className="text-sm text-[#4b6480]">Chargement…</span>
      </div>
    );
  }

  const connecte = session?.connecte ?? false;

  return (
    <Routes>
      {/* ── Public ─────────────────────────────────────────────── */}
      <Route path="/" element={<Navigate to="/accueil" replace />} />
      <Route path="/accueil" element={<Accueil isLoggedIn={connecte} />} />
      <Route
        path="/inspirations"
        element={<InspirationsPage onDecrir={() => {}} isLoggedIn={connecte} />}
      />
      <Route path="/conseillers" element={<ConseillersPage isLoggedIn={connecte} />} />
      <Route
        path="/login"
        element={
          connecte ? (
            <Navigate to="/mes-propositions" replace />
          ) : (
            <Login onSession={refresh} googleOauth={config?.google_oauth ?? false} />
          )
        }
      />

      {/* ── Authentifié ────────────────────────────────────────── */}
      <Route
        path="/mes-propositions"
        element={
          connecte ? (
            <MesPropositions nom={session?.nom} onLogout={refresh} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />

      {/* ── 404 → accueil ──────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/accueil" replace />} />
    </Routes>
  );
}
