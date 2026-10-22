import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FORMULAIRE } from "../../data/detourContent";
import { api } from "../../lib/api";

type Etat = "vide" | "en_cours" | "envoye" | "erreur";

interface TravelRequestFormProps {
  isLoggedIn: boolean;
  onClose: () => void;
}

const TYPES_VOYAGE = [
  ["trek-randonnee", "Trek et randonnée"],
  ["lune-de-miel", "Lune de miel"],
  ["voyage-familial", "Voyage en famille"],
  ["autres", "Autre voyage"],
] as const;

/** Formulaire de demande de voyage persisté sur le compte du voyageur connecté. */
export function TravelRequestForm({ isLoggedIn, onClose }: TravelRequestFormProps) {
  const navigate = useNavigate();
  const [etat, setEtat] = useState<Etat>("vide");
  const [destination, setDestination] = useState("");
  const [dateDepart, setDateDepart] = useState("");
  const [dateRetour, setDateRetour] = useState("");
  const [typeVoyage, setTypeVoyage] = useState<(typeof TYPES_VOYAGE)[number][0] | "">("");
  const [voyageurs, setVoyageurs] = useState("2");
  const [budget, setBudget] = useState("");
  const [niveau, setNiveau] = useState("");
  const [envies, setEnvies] = useState("");
  const [erreur, setErreur] = useState("");
  const [demandeId, setDemandeId] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setErreur("");
    if (!isLoggedIn) {
      onClose();
      navigate("/login");
      return;
    }
    if (dateRetour < dateDepart) {
      setEtat("erreur");
      setErreur("La date de retour doit être égale ou postérieure à la date de départ.");
      return;
    }

    setEtat("en_cours");
    try {
      const { demande } = await api.creerDemande({
        type_voyage: typeVoyage,
        destination,
        date_depart: dateDepart,
        date_retour: dateRetour,
        nombre_voyageurs: Number(voyageurs),
        has_enfants: false,
        nombre_enfants: 0,
        budget_max_par_personne: Number(budget),
        niveau_aventure: niveau,
        besoin_guide: false,
        activites: [],
        contraintes: "",
        conseiller: "",
        souhaits: envies,
      });
      setDemandeId(demande.id);
      setEtat("envoye");
    } catch (err) {
      setErreur(err instanceof Error ? err.message : FORMULAIRE.etatErreur);
      setEtat("erreur");
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="form-titre"
    >
      <div className="absolute inset-0 bg-[#06101c]/75 backdrop-blur-sm" onClick={onClose} />
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-auto rounded-2xl bg-white shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 rounded-full p-2 text-[#4b6480] outline-none hover:bg-[#f2f7fc] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
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
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-[#f0fdf4]">
                <svg
                  className="h-7 w-7 text-[#22c55e]"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </div>
              <h2 id="form-titre" className="text-xl font-bold text-[#0b2447]">
                Demande enregistrée
              </h2>
              <p className="mt-3 leading-relaxed text-[#4b6480]">{FORMULAIRE.messageSucces}</p>
              <button
                onClick={() => {
                  onClose();
                  navigate(`/mon-compte/demandes/${demandeId}`);
                }}
                className="mt-6 rounded-full bg-[#0b2447] px-6 py-2.5 text-sm font-semibold text-white outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8]"
              >
                Voir ma demande
              </button>
            </div>
          ) : (
            <>
              <h2 id="form-titre" className="text-xl font-bold text-[#0b2447]">
                {FORMULAIRE.titre}
              </h2>
              <p className="mt-1 text-sm text-[#4b6480]">{FORMULAIRE.sousTitre}</p>

              {!isLoggedIn && (
                <div className="mt-4 rounded-xl border border-[#e8d5ff] bg-[#f8f0ff] px-4 py-3 text-sm text-[#6b3e9e]">
                  Connectez-vous pour enregistrer votre demande et la retrouver dans votre espace.
                </div>
              )}

              {etat === "erreur" && (
                <p
                  role="alert"
                  className="mt-3 rounded-xl border border-[#fce8e8] bg-[#fff0f0] px-4 py-2 text-sm text-[#b91c1c]"
                >
                  {erreur || FORMULAIRE.etatErreur}
                </p>
              )}

              <form onSubmit={(event) => void handleSubmit(event)} className="mt-5 space-y-4">
                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                    {FORMULAIRE.champDestination} <span className="text-[#b91c1c]">*</span>
                  </span>
                  <input
                    value={destination}
                    onChange={(event) => setDestination(event.target.value)}
                    required
                    placeholder="Ex. : Norvège, côte amalfitaine…"
                    className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                  />
                </label>

                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                    Type de voyage <span className="text-[#b91c1c]">*</span>
                  </span>
                  <select
                    value={typeVoyage}
                    onChange={(event) => setTypeVoyage(event.target.value as typeof typeVoyage)}
                    required
                    className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                  >
                    <option value="">Choisir un type de voyage</option>
                    {TYPES_VOYAGE.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                      Date de départ <span className="text-[#b91c1c]">*</span>
                    </span>
                    <input
                      type="date"
                      value={dateDepart}
                      onChange={(event) => setDateDepart(event.target.value)}
                      required
                      className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                      Date de retour <span className="text-[#b91c1c]">*</span>
                    </span>
                    <input
                      type="date"
                      value={dateRetour}
                      min={dateDepart || undefined}
                      onChange={(event) => setDateRetour(event.target.value)}
                      required
                      className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    />
                  </label>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                      Voyageurs *
                    </span>
                    <select
                      value={voyageurs}
                      onChange={(event) => setVoyageurs(event.target.value)}
                      required
                      className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-3 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    >
                      {[1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20].map((count) => (
                        <option key={count} value={count}>
                          {count}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                      Budget / pers. *
                    </span>
                    <input
                      type="number"
                      min={1}
                      max={100000}
                      step={1}
                      value={budget}
                      onChange={(event) => setBudget(event.target.value)}
                      required
                      placeholder="1500 €"
                      className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-3 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                      Aventure *
                    </span>
                    <select
                      value={niveau}
                      onChange={(event) => setNiveau(event.target.value)}
                      required
                      className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-3 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                    >
                      <option value="">Choisir</option>
                      <option value="calme">Calme</option>
                      <option value="modere">Modéré</option>
                      <option value="intense">Intense</option>
                    </select>
                  </label>
                </div>

                <label className="block">
                  <span className="mb-1 block text-sm font-medium text-[#0b2447]">
                    Vos envies et contraintes
                  </span>
                  <textarea
                    value={envies}
                    onChange={(event) => setEnvies(event.target.value)}
                    rows={3}
                    placeholder="Ex. : montagne, pas de foule, gastronomie locale…"
                    className="w-full resize-none rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm text-[#0b2447] outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
                  />
                </label>

                <p className="text-xs text-[#8ba8c4]">
                  Les champs marqués d’un * sont obligatoires.
                </p>
                <button
                  type="submit"
                  disabled={etat === "en_cours"}
                  className="w-full rounded-full bg-[#0b2447] px-6 py-3 font-semibold text-base text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] disabled:opacity-60"
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
