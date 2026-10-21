import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../lib/api";
import type { Account, Session } from "../types";

interface CompteContext {
  session: Session;
  onProfileUpdated: () => Promise<void>;
}

export function ParametresCompte() {
  const { onProfileUpdated } = useOutletContext<CompteContext>();
  const [compte, setCompte] = useState<Account | null>(null);
  const [nom, setNom] = useState("");
  const [email, setEmail] = useState("");
  const [chargement, setChargement] = useState(true);
  const [sauvegardeProfil, setSauvegardeProfil] = useState(false);
  const [erreurProfil, setErreurProfil] = useState("");
  const [succesProfil, setSuccesProfil] = useState("");
  const [motDePasseActuel, setMotDePasseActuel] = useState("");
  const [nouveauMotDePasse, setNouveauMotDePasse] = useState("");
  const [confirmationMotDePasse, setConfirmationMotDePasse] = useState("");
  const [sauvegardeMotDePasse, setSauvegardeMotDePasse] = useState(false);
  const [erreurMotDePasse, setErreurMotDePasse] = useState("");
  const [succesMotDePasse, setSuccesMotDePasse] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .compte()
      .then(({ compte: result }) => {
        if (cancelled) return;
        setCompte(result);
        setNom(result.nom);
        setEmail(result.email);
      })
      .catch((err) => {
        if (!cancelled)
          setErreurProfil(err instanceof Error ? err.message : "Erreur de chargement.");
      })
      .finally(() => {
        if (!cancelled) setChargement(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function sauvegarderProfil(event: React.FormEvent) {
    event.preventDefault();
    setErreurProfil("");
    setSuccesProfil("");
    setSauvegardeProfil(true);
    try {
      const { compte: updated } = await api.modifierCompte({ nom, email });
      setCompte(updated);
      setNom(updated.nom);
      setEmail(updated.email);
      setSuccesProfil("Vos informations ont été mises à jour.");
      await onProfileUpdated();
    } catch (err) {
      setErreurProfil(err instanceof Error ? err.message : "Impossible de modifier votre profil.");
    } finally {
      setSauvegardeProfil(false);
    }
  }

  async function sauvegarderMotDePasse(event: React.FormEvent) {
    event.preventDefault();
    setErreurMotDePasse("");
    setSuccesMotDePasse("");
    if (nouveauMotDePasse !== confirmationMotDePasse) {
      setErreurMotDePasse("Les deux mots de passe ne correspondent pas.");
      return;
    }
    setSauvegardeMotDePasse(true);
    try {
      await api.changerMotDePasse({
        mot_de_passe_actuel: motDePasseActuel,
        nouveau_mot_de_passe: nouveauMotDePasse,
      });
      setMotDePasseActuel("");
      setNouveauMotDePasse("");
      setConfirmationMotDePasse("");
      setSuccesMotDePasse("Votre mot de passe a été modifié.");
      const { compte: updated } = await api.compte();
      setCompte(updated);
    } catch (err) {
      setErreurMotDePasse(
        err instanceof Error ? err.message : "Impossible de modifier votre mot de passe.",
      );
    } finally {
      setSauvegardeMotDePasse(false);
    }
  }

  if (chargement) return <p className="text-sm text-[#4b6480]">Chargement de vos paramètres…</p>;

  return (
    <section aria-labelledby="settings-heading">
      <h2 id="settings-heading" className="text-xl font-bold sm:text-2xl">
        Paramètres du compte
      </h2>
      <p className="mt-1 text-sm text-[#4b6480]">
        Gérez vos informations personnelles et vos identifiants de connexion.
      </p>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <form
          onSubmit={(event) => void sauvegarderProfil(event)}
          className="rounded-2xl border border-[#e8eef6] bg-white p-5 sm:p-6"
        >
          <h3 className="text-lg font-bold">Informations personnelles</h3>
          <label className="mt-5 block">
            <span className="mb-1 block text-sm font-medium">Nom</span>
            <input
              value={nom}
              onChange={(event) => setNom(event.target.value)}
              autoComplete="name"
              maxLength={120}
              required
              className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
            />
          </label>
          <label className="mt-4 block">
            <span className="mb-1 block text-sm font-medium">Adresse e-mail</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
            />
          </label>
          {erreurProfil && (
            <p role="alert" className="mt-4 text-sm text-[#b91c1c]">
              {erreurProfil}
            </p>
          )}
          {succesProfil && (
            <p role="status" className="mt-4 text-sm text-[#147f7c]">
              {succesProfil}
            </p>
          )}
          <button
            type="submit"
            disabled={sauvegardeProfil || !compte}
            className="mt-5 rounded-full bg-[#0b2447] px-5 py-2.5 text-sm font-semibold text-white transition outline-none hover:bg-[#12335e] focus-visible:ring-2 focus-visible:ring-[#38bdb8] disabled:opacity-60"
          >
            {sauvegardeProfil ? "Enregistrement…" : "Enregistrer le profil"}
          </button>
        </form>

        <form
          onSubmit={(event) => void sauvegarderMotDePasse(event)}
          className="rounded-2xl border border-[#e8eef6] bg-white p-5 sm:p-6"
        >
          <h3 className="text-lg font-bold">Mot de passe</h3>
          <p className="mt-1 text-sm text-[#4b6480]">
            {compte?.mot_de_passe_defini
              ? "Choisissez un nouveau mot de passe pour votre compte."
              : "Définissez un mot de passe pour aussi vous connecter avec votre e-mail."}
          </p>
          {compte?.mot_de_passe_defini && (
            <label className="mt-5 block">
              <span className="mb-1 block text-sm font-medium">Mot de passe actuel</span>
              <input
                type="password"
                value={motDePasseActuel}
                onChange={(event) => setMotDePasseActuel(event.target.value)}
                autoComplete="current-password"
                required
                className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
              />
            </label>
          )}
          <label className="mt-4 block">
            <span className="mb-1 block text-sm font-medium">Nouveau mot de passe</span>
            <input
              type="password"
              value={nouveauMotDePasse}
              onChange={(event) => setNouveauMotDePasse(event.target.value)}
              autoComplete="new-password"
              minLength={6}
              maxLength={1024}
              required
              className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
            />
            <span className="mt-1 block text-xs text-[#8ba8c4]">6 caractères minimum.</span>
          </label>
          <label className="mt-4 block">
            <span className="mb-1 block text-sm font-medium">
              Confirmer le nouveau mot de passe
            </span>
            <input
              type="password"
              value={confirmationMotDePasse}
              onChange={(event) => setConfirmationMotDePasse(event.target.value)}
              autoComplete="new-password"
              minLength={6}
              maxLength={1024}
              required
              className="w-full rounded-xl border border-[#d5e0ee] bg-[#f7fafd] px-4 py-2.5 text-sm outline-none focus:border-[#38bdb8] focus:ring-2 focus:ring-[#38bdb8]/30"
            />
          </label>
          {erreurMotDePasse && (
            <p role="alert" className="mt-4 text-sm text-[#b91c1c]">
              {erreurMotDePasse}
            </p>
          )}
          {succesMotDePasse && (
            <p role="status" className="mt-4 text-sm text-[#147f7c]">
              {succesMotDePasse}
            </p>
          )}
          <button
            type="submit"
            disabled={sauvegardeMotDePasse || !compte}
            className="mt-5 rounded-full border border-[#d5e0ee] px-5 py-2.5 text-sm font-semibold text-[#0b2447] transition outline-none hover:border-[#38bdb8] focus-visible:ring-2 focus-visible:ring-[#38bdb8] disabled:opacity-60"
          >
            {sauvegardeMotDePasse ? "Enregistrement…" : "Modifier le mot de passe"}
          </button>
        </form>
      </div>
    </section>
  );
}
