import { useState } from "react";
import { PublicNav } from "../components/landing/PublicNav";
import { Hero } from "../components/landing/Hero";
import { Inspirations } from "../components/landing/Inspirations";
import { HowItWorks } from "../components/landing/HowItWorks";
import { AdvisorAvailability } from "../components/landing/AdvisorAvailability";
import { Footer } from "../components/landing/Footer";
import { TravelRequestForm } from "../components/landing/TravelRequestForm";

interface AccueilProps {
  isLoggedIn: boolean;
}

/** Page d'accueil publique DÉTOUR — visible sans connexion. */
export function Accueil({ isLoggedIn }: AccueilProps) {
  const [formOuvert, setFormOuvert] = useState(false);

  return (
    <div className="min-h-screen bg-white text-[#0b2447]">
      <PublicNav />
      <main>
        <Hero onDecrir={() => setFormOuvert(true)} />
        <Inspirations onDecrir={() => setFormOuvert(true)} />
        <HowItWorks />
        <AdvisorAvailability onDecrir={() => setFormOuvert(true)} />
      </main>
      <Footer />

      {formOuvert && (
        <TravelRequestForm
          isLoggedIn={isLoggedIn}
          onClose={() => setFormOuvert(false)}
        />
      )}
    </div>
  );
}
