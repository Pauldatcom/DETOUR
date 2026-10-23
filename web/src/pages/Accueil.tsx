import { useState } from "react";
import { PublicNav } from "../components/landing/PublicNav";
import { Hero } from "../components/landing/Hero";
import { Inspirations } from "../components/landing/Inspirations";
import { HowItWorks } from "../components/landing/HowItWorks";
import { AdvisorAvailability } from "../components/landing/AdvisorAvailability";
import { Footer } from "../components/landing/Footer";
import { TravelRequestForm } from "../components/landing/TravelRequestForm";
import { ChatWidget } from "../components/landing/ChatWidget";
import type { Session } from "../types";

interface AccueilProps {
  isLoggedIn: boolean;
  session: Session | null;
  onLogout: () => Promise<void>;
}

/** Page d'accueil publique DÉTOUR — visible sans connexion. */
export function Accueil({ isLoggedIn, session, onLogout }: AccueilProps) {
  const [formOuvert, setFormOuvert] = useState(false);

  return (
    <div className="min-h-screen bg-chalk text-ink">
      <PublicNav session={session} onLogout={onLogout} />
      <main id="contenu-principal">
        <Hero onDecrir={() => setFormOuvert(true)} />
        <Inspirations onDecrir={() => setFormOuvert(true)} />
        <HowItWorks />
        <AdvisorAvailability onDecrir={() => setFormOuvert(true)} />
      </main>
      <Footer />

      {formOuvert && (
        <TravelRequestForm isLoggedIn={isLoggedIn} onClose={() => setFormOuvert(false)} />
      )}

      <ChatWidget isLoggedIn={isLoggedIn} />
    </div>
  );
}
