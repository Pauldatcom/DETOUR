import type {
  Session,
  Account,
  Config,
  Disponibilite,
  Stats,
  Demande,
  Proposition,
  ChatMessage,
  ChatResult,
  ApiError as ApiErrorType,
} from "../types";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  const text = await res.text();
  if (!text) return {} as T;
  const data = JSON.parse(text);
  if (!res.ok) {
    const err = data as ApiErrorType;
    throw new Error(err?.erreur?.message || `Erreur ${res.status}`);
  }
  return data as T;
}

export const api = {
  session: () => request<Session>("/api/session"),
  logout: () => request<{ deconnecte: boolean }>("/api/logout", { method: "POST" }),
  compte: () => request<{ compte: Account }>("/api/account"),
  modifierCompte: (data: { email: string; nom: string; mot_de_passe_actuel?: string }) =>
    request<{ compte: Account }>("/api/account", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  changerMotDePasse: (data: { mot_de_passe_actuel: string; nouveau_mot_de_passe: string }) =>
    request<{ mot_de_passe_modifie: boolean }>("/api/account/password", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  config: () => request<Config>("/api/config"),
  disponibilite: () => request<Disponibilite>("/api/disponibilite"),

  login: (email: string, mot_de_passe: string) =>
    request<{ session: { role: string; nom: string } }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ email, mot_de_passe }),
    }),
  register: (email: string, nom: string, mot_de_passe: string) =>
    request<{ session: { role: string; nom: string } }>("/api/register", {
      method: "POST",
      body: JSON.stringify({ email, nom, mot_de_passe }),
    }),
  loginConseiller: (cle: string) =>
    request<{ session: { role: string; nom: string } }>("/api/login-conseiller", {
      method: "POST",
      body: JSON.stringify({ cle }),
    }),
  googleAuth: () => {
    window.location.href = "/api/auth/google";
  },

  demandes: () => request<{ demandes: Demande[] }>("/api/demandes"),
  demande: (id: string) => request<{ demande: Demande }>(`/api/demandes/${id}`),
  mesDemandes: () => request<{ demandes: Demande[] }>("/api/mes-demandes"),
  creerDemande: (data: Record<string, unknown>) =>
    request<{ demande: Demande }>("/api/demandes", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  rechercher: (id: string) =>
    request<{ recherche: unknown }>(`/api/demandes/${id}/recherche`, { method: "POST" }),
  approveRequest: (id: string, confirmed: boolean) =>
    request<{ demande: Demande }>(`/api/demandes/${id}/approbation`, {
      method: "POST",
      body: JSON.stringify({ confirme: confirmed }),
    }),
  changerStatut: (id: string, statut: string, motif: string) =>
    request<{ demande: Demande }>(`/api/demandes/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ statut, motif }),
    }),
  changerQualification: (id: string, qualification: string, motif: string) =>
    request<{ demande: Demande }>(`/api/demandes/${id}/qualification`, {
      method: "PATCH",
      body: JSON.stringify({ qualification, motif }),
    }),
  corrigerDemande: (id: string, champs: Record<string, unknown>, motif: string) =>
    request<{ demande: Demande }>(`/api/demandes/${id}/correction`, {
      method: "PATCH",
      body: JSON.stringify({ champs, motif }),
    }),

  stats: () => request<Stats>("/api/stats"),
  propositions: () => request<{ propositions: Proposition[] }>("/api/propositions"),
  proposition: (id: string) => request<{ proposition: Proposition }>(`/api/propositions/${id}`),
  mesPropositions: () => request<{ propositions: Proposition[] }>("/api/mes-propositions"),
  creerProposition: (demandeId: string, data: Record<string, unknown>) =>
    request<{ proposition: Proposition }>(`/api/demandes/${demandeId}/propositions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  genererProposition: (demandeId: string) =>
    request<{ proposition: Proposition }>(`/api/demandes/${demandeId}/propositions/generer`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  patchProposition: (id: string, data: Record<string, unknown>) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  changerStatutProposition: (id: string, statut: string, motif: string) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ statut, motif }),
    }),
  deciderProposition: (
    id: string,
    action: "accepter" | "correction" | "refuser",
    motif: string,
    instructions?: string,
  ) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ motif, ...(instructions ? { instructions } : {}) }),
    }),
  decisionsPrestation: (
    id: string,
    prestationId: string,
    choix: "keep" | "replace" | "drop",
    motif: string,
    remplacementId?: string,
  ) =>
    request<{ proposition: Proposition; proposition_v2?: Proposition }>(
      `/api/propositions/${id}/decisions`,
      {
        method: "POST",
        body: JSON.stringify({
          prestation_id: prestationId,
          choix,
          motif,
          ...(remplacementId ? { remplacement_id: remplacementId } : {}),
        }),
      },
    ),

  chat: (messages: ChatMessage[], demandeId?: string) =>
    request<ChatResult>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ messages, demande_id: demandeId }),
    }),
};
