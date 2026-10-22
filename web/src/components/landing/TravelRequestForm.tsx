import { useId, useState } from "react";
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

/** Travel request modal — persisted demande + labelled fields (#131). */
export function TravelRequestForm({ isLoggedIn, onClose }: TravelRequestFormProps) {
  const navigate = useNavigate();
  const baseId = useId();
  const errorId = `${baseId}-erreur`;
  const destId = `${baseId}-destination`;
  const typeId = `${baseId}-type`;
  const departId = `${baseId}-depart`;
  const retourId = `${baseId}-retour`;
  const voyageursId = `${baseId}-voyageurs`;
  const budgetId = `${baseId}-budget`;
  const niveauId = `${baseId}-niveau`;
  const enviesId = `${baseId}-envies`;

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

  const fieldClass =
    "mt-1 w-full rounded-xl border border-ink/15 bg-card px-4 py-2.5 text-sm text-ink outline-none";
  const labelClass = "block text-sm font-medium text-ink";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="form-titre"
    >
      <div
        className="absolute inset-0 bg-ink/75 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-auto rounded-2xl bg-white shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 rounded-full p-2 text-ballast outline-none hover:bg-card"
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
            <div className="py-4 text-center" role="status" aria-live="polite">
              <div
                className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-sky/40"
                aria-hidden="true"
              >
                <svg
                  className="h-7 w-7 text-ink"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </div>
              <h2 id="form-titre" className="font-display text-xl font-extrabold text-ink">
                Demande enregistrée
              </h2>
              {/* Confirmation stays clear without motion (#131 / #113). */}
              <p className="mt-3 leading-relaxed text-ballast">{FORMULAIRE.messageSucces}</p>
              <p className="mt-2 text-sm text-ink">
                Un conseiller vous répondra sous 24 à 48 h ouvrées.
              </p>
              <button
                type="button"
                onClick={() => {
                  onClose();
                  navigate(`/mon-compte/demandes/${demandeId}`);
                }}
                className="mt-6 rounded-full bg-ink px-6 py-2.5 text-sm font-semibold text-chalk outline-none hover:bg-ink/90"
              >
                Voir ma demande
              </button>
            </div>
          ) : (
            <>
              <h2 id="form-titre" className="font-display text-xl font-extrabold text-ink">
                {FORMULAIRE.titre}
              </h2>
              <p className="mt-1 text-sm text-ballast">{FORMULAIRE.sousTitre}</p>

              {!isLoggedIn && (
                <div className="mt-4 rounded-xl border border-sky bg-sky/30 px-4 py-3 text-sm text-ink">
                  Connectez-vous pour enregistrer votre demande et la retrouver dans votre espace.
                </div>
              )}

              {etat === "erreur" && (
                <p
                  id={errorId}
                  role="alert"
                  className="mt-3 rounded-xl border border-brick/30 bg-brick/10 px-4 py-2 text-sm text-brick"
                >
                  {erreur || FORMULAIRE.etatErreur}
                </p>
              )}

              <form
                onSubmit={(event) => void handleSubmit(event)}
                noValidate
                className="mt-5 space-y-4"
              >
                <div>
                  <label htmlFor={destId} className={labelClass}>
                    {FORMULAIRE.champDestination}{" "}
                    <span aria-hidden="true" className="text-brick">
                      *
                    </span>
                  </label>
                  <input
                    id={destId}
                    value={destination}
                    onChange={(event) => setDestination(event.target.value)}
                    required
                    placeholder="Ex. : Norvège, côte amalfitaine…"
                    aria-describedby={etat === "erreur" ? errorId : undefined}
                    className={fieldClass}
                  />
                </div>

                <div>
                  <label htmlFor={typeId} className={labelClass}>
                    Type de voyage{" "}
                    <span aria-hidden="true" className="text-brick">
                      *
                    </span>
                  </label>
                  <select
                    id={typeId}
                    value={typeVoyage}
                    onChange={(event) => setTypeVoyage(event.target.value as typeof typeVoyage)}
                    required
                    aria-describedby={etat === "erreur" ? errorId : undefined}
                    className={fieldClass}
                  >
                    <option value="">Choisir un type de voyage</option>
                    {TYPES_VOYAGE.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor={departId} className={labelClass}>
                      Date de départ{" "}
                      <span aria-hidden="true" className="text-brick">
                        *
                      </span>
                    </label>
                    <input
                      id={departId}
                      type="date"
                      value={dateDepart}
                      onChange={(event) => setDateDepart(event.target.value)}
                      required
                      aria-describedby={etat === "erreur" ? errorId : undefined}
                      className={`meta-nowrap ${fieldClass}`}
                    />
                  </div>
                  <div>
                    <label htmlFor={retourId} className={labelClass}>
                      Date de retour{" "}
                      <span aria-hidden="true" className="text-brick">
                        *
                      </span>
                    </label>
                    <input
                      id={retourId}
                      type="date"
                      value={dateRetour}
                      min={dateDepart || undefined}
                      onChange={(event) => setDateRetour(event.target.value)}
                      required
                      aria-describedby={etat === "erreur" ? errorId : undefined}
                      className={`meta-nowrap ${fieldClass}`}
                    />
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <div>
                    <label htmlFor={voyageursId} className={labelClass}>
                      Voyageurs{" "}
                      <span aria-hidden="true" className="text-brick">
                        *
                      </span>
                    </label>
                    <select
                      id={voyageursId}
                      value={voyageurs}
                      onChange={(event) => setVoyageurs(event.target.value)}
                      required
                      className={fieldClass}
                    >
                      {[1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20].map((count) => (
                        <option key={count} value={count}>
                          {count}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label htmlFor={budgetId} className={labelClass}>
                      Budget / pers.{" "}
                      <span aria-hidden="true" className="text-brick">
                        *
                      </span>
                    </label>
                    <input
                      id={budgetId}
                      type="number"
                      min={1}
                      max={100000}
                      step={1}
                      value={budget}
                      onChange={(event) => setBudget(event.target.value)}
                      required
                      placeholder="1500 €"
                      className={`meta-nowrap ${fieldClass}`}
                    />
                  </div>
                  <div>
                    <label htmlFor={niveauId} className={labelClass}>
                      Aventure{" "}
                      <span aria-hidden="true" className="text-brick">
                        *
                      </span>
                    </label>
                    <select
                      id={niveauId}
                      value={niveau}
                      onChange={(event) => setNiveau(event.target.value)}
                      required
                      className={fieldClass}
                    >
                      <option value="">Choisir</option>
                      <option value="calme">Calme</option>
                      <option value="modere">Modéré</option>
                      <option value="intense">Intense</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor={enviesId} className={labelClass}>
                    Vos envies et contraintes
                  </label>
                  <textarea
                    id={enviesId}
                    value={envies}
                    onChange={(event) => setEnvies(event.target.value)}
                    rows={3}
                    placeholder="Ex. : montagne, pas de foule, gastronomie locale…"
                    aria-describedby={etat === "erreur" ? errorId : undefined}
                    className={`resize-none ${fieldClass}`}
                  />
                </div>

                <p className="text-xs text-ballast">Les champs marqués d’un * sont obligatoires.</p>
                <button
                  type="submit"
                  disabled={etat === "en_cours"}
                  className="w-full rounded-full bg-ink px-6 py-3 font-semibold text-base text-chalk transition outline-none hover:bg-ink/90 disabled:opacity-60"
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
