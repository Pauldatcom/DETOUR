import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FORMULAIRE } from "../../data/detourContent";

type Etat = "vide" | "en_cours" | "envoye" | "erreur";

interface TravelRequestFormProps {
  isLoggedIn: boolean;
  onClose: () => void;
}

/** Modal formulaire de demande de voyage — états vide / en cours / envoyé / erreur (2026 brand). */
export function TravelRequestForm({ isLoggedIn, onClose }: TravelRequestFormProps) {
  const navigate = useNavigate();
  const [etat, setEtat] = useState<Etat>("vide");
  const [destination, setDestination] = useState("");
  const [dates, setDates] = useState("");
  const [voyageurs, setVoyageurs] = useState("");
  const [envies, setEnvies] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isLoggedIn) {
      onClose();
      navigate("/login");
      return;
    }
    setEtat("en_cours");
    // Simulation locale — aucune API appelée
    setTimeout(() => {
      setEtat("envoye");
    }, 900);
  }

  const champClasse =
    "mt-1 w-full rounded-xl border border-ink/15 bg-card px-4 py-2.5 text-sm text-ink transition focus:border-ink focus:ring-2 focus:ring-sky";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="form-titre"
    >
      <div className="absolute inset-0 bg-ink/70 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-lg overflow-auto rounded-2xl bg-card shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 rounded-full p-2 text-ballast hover:bg-sky/40"
          aria-label="Fermer le formulaire"
        >
          <svg
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="p-6 sm:p-8">
          {etat === "envoye" ? (
            <div className="py-4 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-sky/40">
                <svg
                  className="h-7 w-7 text-ink"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </div>
              <h2 id="form-titre" className="text-xl font-extrabold text-ink">
                Demande enregistrée
              </h2>
              <p className="mt-3 leading-relaxed text-ballast">{FORMULAIRE.messageSucces}</p>
              <button
                onClick={onClose}
                className="mt-6 rounded-full bg-ink px-6 py-2.5 text-sm font-semibold text-chalk hover:bg-ink/85"
              >
                Fermer
              </button>
            </div>
          ) : (
            <>
              <h2 id="form-titre" className="text-xl font-extrabold text-ink">
                {FORMULAIRE.titre}
              </h2>
              <p className="mt-1 text-sm text-ballast">{FORMULAIRE.sousTitre}</p>

              {!isLoggedIn && (
                <div className="mt-4 rounded-xl bg-sky/40 px-4 py-3 text-sm text-ink">
                  Vous n'êtes pas connecté. Un clic sur « Envoyer » vous redirigera vers la page de
                  connexion pour finaliser votre demande.
                </div>
              )}

              {etat === "erreur" && (
                <p
                  role="alert"
                  className="mt-3 rounded-xl border border-brick/30 bg-brick/10 px-4 py-2 text-sm text-brick"
                >
                  {FORMULAIRE.etatErreur}
                </p>
              )}

              <form onSubmit={handleSubmit} noValidate className="mt-5 space-y-4">
                <label className="block">
                  <span className="text-sm font-medium text-ink">
                    {FORMULAIRE.champDestination}{" "}
                    <span aria-hidden="true" className="text-brick">
                      *
                    </span>
                  </span>
                  <input
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    required
                    placeholder="Ex. : Norvège, côte amalfitaine…"
                    className={champClasse}
                  />
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-ink">{FORMULAIRE.champDates}</span>
                  <input
                    value={dates}
                    onChange={(e) => setDates(e.target.value)}
                    placeholder="Ex. : début mai, 10 jours…"
                    className={champClasse}
                  />
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="text-sm font-medium text-ink">
                      {FORMULAIRE.champVoyageurs}
                    </span>
                    <select
                      value={voyageurs}
                      onChange={(e) => setVoyageurs(e.target.value)}
                      className={champClasse}
                    >
                      <option value="">—</option>
                      {[1, 2, 3, 4, 5, "6+"].map((n) => (
                        <option key={n} value={n}>
                          {n} voyageur{Number(n) > 1 ? "s" : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="block">
                  <span className="text-sm font-medium text-ink">
                    {FORMULAIRE.champEnvies}{" "}
                    <span aria-hidden="true" className="text-brick">
                      *
                    </span>
                  </span>
                  <textarea
                    value={envies}
                    onChange={(e) => setEnvies(e.target.value)}
                    required
                    rows={3}
                    placeholder="Ex. : montagne, pas de foule, gastronomie locale, budget ~1 500 €/pers…"
                    className={`${champClasse} resize-none`}
                  />
                </label>

                <p className="text-xs text-ballast">{FORMULAIRE.champsRequis}</p>

                <button
                  type="submit"
                  disabled={etat === "en_cours"}
                  className="w-full rounded-full bg-ink px-6 py-3 font-semibold text-base text-chalk transition hover:bg-ink/85 disabled:opacity-60"
                >
                  {etat === "en_cours"
                    ? FORMULAIRE.boutonEnCours
                    : isLoggedIn
                      ? FORMULAIRE.boutonEnvoyer
                      : "Me connecter pour envoyer"}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
