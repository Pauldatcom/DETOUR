import type {
  Session,
  Config,
  Stats,
  Demande,
  Proposition,
  ChatMessage,
  ChatResult,
  ApiError as ApiErrorType,
} from "../types";

async function request<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
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
  config: () => request<Config>("/api/config"),

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
  changerStatut: (id: string, statut: string) =>
    request<{ demande: Demande }>(`/api/demandes/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ statut }),
    }),

  stats: () => request<Stats>("/api/stats"),
  propositions: () => request<{ propositions: Proposition[] }>("/api/propositions"),
  proposition: (id: string) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}`),
  mesPropositions: () =>
    request<{ propositions: Proposition[] }>("/api/mes-propositions"),
  creerProposition: (demandeId: string, data: Record<string, unknown>) =>
    request<{ proposition: Proposition }>(`/api/demandes/${demandeId}/propositions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  genererProposition: (demandeId: string) =>
    request<{ proposition: Proposition }>(
      `/api/demandes/${demandeId}/propositions/generer`,
      { method: "POST", body: JSON.stringify({}) },
    ),
  patchProposition: (id: string, data: Record<string, unknown>) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  changerStatutProposition: (id: string, statut: string) =>
    request<{ proposition: Proposition }>(`/api/propositions/${id}/statut`, {
      method: "PATCH",
      body: JSON.stringify({ statut }),
    }),

  chat: (messages: ChatMessage[], demandeId?: string) =>
    request<ChatResult>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ messages, demande_id: demandeId }),
    }),
};