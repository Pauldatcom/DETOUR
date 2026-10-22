import { NavLink, Outlet } from "react-router-dom";
import { Footer } from "../components/landing/Footer";
import { PublicNav } from "../components/landing/PublicNav";
import type { Session } from "../types";

interface CompteLayoutProps {
  session: Session;
  onLogout: () => Promise<void>;
  onProfileUpdated: () => Promise<void>;
}

const tabs = [
  { to: "/mon-compte/demandes", label: "Mes demandes" },
  { to: "/mon-compte/propositions", label: "Mes propositions" },
  { to: "/mon-compte/parametres", label: "Paramètres" },
];

export function CompteLayout({ session, onLogout, onProfileUpdated }: CompteLayoutProps) {
  return (
    <div className="min-h-screen bg-[#f7fafd] text-[#0b2447]">
      <PublicNav session={session} onLogout={onLogout} />
      <main className="mx-auto min-h-[60vh] max-w-5xl px-4 py-10 sm:px-6 lg:py-14">
        <div className="mb-7">
          <p className="text-sm font-semibold tracking-widest text-[#38bdb8] uppercase">
            Espace personnel
          </p>
          <h1 className="mt-1 text-2xl font-bold sm:text-3xl">
            {session.nom ? `Bonjour ${session.nom}` : "Mon espace"}
          </h1>
        </div>
        <nav aria-label="Navigation de l’espace personnel" className="mb-8 overflow-x-auto">
          <div className="flex min-w-max gap-2 border-b border-[#d5e0ee]">
            {tabs.map((tab) => (
              <NavLink
                key={tab.to}
                to={tab.to}
                className={({ isActive }) =>
                  `border-b-2 px-4 py-3 text-sm font-semibold transition outline-none focus-visible:ring-2 focus-visible:ring-[#38bdb8] ${
                    isActive
                      ? "border-[#38bdb8] text-[#0b2447]"
                      : "border-transparent text-[#4b6480] hover:text-[#0b2447]"
                  }`
                }
              >
                {tab.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <Outlet context={{ session, onProfileUpdated }} />
      </main>
      <Footer />
    </div>
  );
}
