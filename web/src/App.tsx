import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useSession } from "./hooks/useSession";
import { Accueil } from "./pages/Accueil";
import { Login } from "./pages/Login";
import { InspirationsPage } from "./pages/Inspirations";
import { ConseillersPage } from "./pages/Conseillers";
import { MesPropositions } from "./pages/MesPropositions";
import { PropositionDetail } from "./pages/PropositionDetail";
import { EspaceConseiller } from "./pages/EspaceConseiller";
import { api } from "./lib/api";
import type { Config } from "./types";

/**
 * Routage DÉTOUR.
 *
 * Public : / → /accueil, /inspirations, /conseillers, /login
 * Client authentifié : /mes-propositions, /propositions/:id
 * Conseiller authentifié : /espace-conseiller
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
  const estConseiller = connecte && session?.role === "conseiller";

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
            estConseiller ? (
              <Navigate to="/espace-conseiller" replace />
            ) : (
              <Navigate to="/mes-propositions" replace />
            )
          ) : (
            <Login onSession={refresh} googleOauth={config?.google_oauth ?? false} />
          )
        }
      />

      {/* ── Client authentifié ─────────────────────────────────── */}
      <Route
        path="/mes-propositions"
        element={
          connecte && !estConseiller ? (
            <MesPropositions nom={session?.nom} onLogout={refresh} />
          ) : estConseiller ? (
            <Navigate to="/espace-conseiller" replace />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route
        path="/propositions/:id"
        element={
          connecte && !estConseiller ? <PropositionDetail /> : <Navigate to="/login" replace />
        }
      />

      {/* ── Conseiller authentifié ─────────────────────────────── */}
      <Route
        path="/espace-conseiller"
        element={
          estConseiller ? (
            <EspaceConseiller nom={session?.nom} onLogout={refresh} />
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
