import { useCallback, useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useSession } from "./hooks/useSession";
import { Accueil } from "./pages/Accueil";
import { Login } from "./pages/Login";
import { InspirationsPage } from "./pages/Inspirations";
import { ConseillersPage } from "./pages/Conseillers";
import { CompteLayout } from "./pages/CompteLayout";
import { MesDemandes } from "./pages/MesDemandes";
import { MesPropositions } from "./pages/MesPropositions";
import { PropositionDetail } from "./pages/PropositionDetail";
import { DemandeDetail } from "./pages/DemandeDetail";
import { ParametresCompte } from "./pages/ParametresCompte";
import { api } from "./lib/api";
import type { Config } from "./types";

/**
 * Routage DÉTOUR — pas de dashboard.
 *
 * Public : / → /accueil, /inspirations, /conseillers, /login
 * Voyageur connecté : /mon-compte/*
 */
export default function App() {
  const { session, loading, refresh } = useSession();
  const [config, setConfig] = useState<Config | null>(null);
  const deconnecter = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      await refresh();
    }
  }, [refresh]);

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
  const clientConnecte = connecte && session?.role === "client";

  return (
    <Routes>
      {/* ── Public ─────────────────────────────────────────────── */}
      <Route path="/" element={<Navigate to="/accueil" replace />} />
      <Route
        path="/accueil"
        element={<Accueil isLoggedIn={clientConnecte} session={session} onLogout={deconnecter} />}
      />
      <Route
        path="/inspirations"
        element={
          <InspirationsPage
            onDecrir={() => {}}
            isLoggedIn={clientConnecte}
            session={session}
            onLogout={deconnecter}
          />
        }
      />
      <Route
        path="/conseillers"
        element={
          <ConseillersPage isLoggedIn={clientConnecte} session={session} onLogout={deconnecter} />
        }
      />
      <Route
        path="/login"
        element={
          connecte ? (
            <Navigate to={clientConnecte ? "/mon-compte" : "/accueil"} replace />
          ) : (
            <Login onSession={refresh} googleOauth={config?.google_oauth ?? false} />
          )
        }
      />

      {/* ── Espace personnel voyageur ───────────────────────────── */}
      <Route
        element={
          clientConnecte && session ? (
            <CompteLayout session={session} onLogout={deconnecter} onProfileUpdated={refresh} />
          ) : (
            <Navigate to={connecte ? "/accueil" : "/login"} replace />
          )
        }
      >
        <Route path="/mon-compte" element={<Navigate to="/mon-compte/demandes" replace />} />
        <Route path="/mon-compte/demandes" element={<MesDemandes />} />
        <Route path="/mon-compte/demandes/:id" element={<DemandeDetail />} />
        <Route path="/mon-compte/propositions" element={<MesPropositions />} />
        <Route path="/mon-compte/propositions/:id" element={<PropositionDetail />} />
        <Route path="/mon-compte/parametres" element={<ParametresCompte />} />
        <Route path="/mes-demandes" element={<Navigate to="/mon-compte/demandes" replace />} />
        <Route
          path="/mes-propositions"
          element={<Navigate to="/mon-compte/propositions" replace />}
        />
        <Route path="/propositions/:id" element={<PropositionDetail />} />
      </Route>

      {/* ── 404 → accueil ──────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/accueil" replace />} />
    </Routes>
  );
}
