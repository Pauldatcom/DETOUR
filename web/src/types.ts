export interface Session {
  connecte: boolean;
  role?: "client" | "conseiller";
  nom?: string;
}

export interface Config {
  simulation: boolean;
  agent_actif: boolean;
  google_oauth: boolean;
  model: string;
}

export interface Stats {
  demandes_total: number;
  propositions_total: number;
  par_statut: Record<string, number>;
  simulation: boolean;
}

export interface Demande {
  id: string;
  statut: string;
  cree_le: string;
  demande: DemandeData;
  client?: ClientInfo;
  recherches?: Recherche[];
  messages?: ChatMessage[];
}

export interface DemandeData {
  type_voyage: string;
  destination: string;
  date_depart: string;
  date_retour: string;
  nombre_voyageurs: number;
  has_enfants: boolean;
  nombre_enfants: number;
  budget_max_par_personne: number;
  niveau_aventure: string;
  besoin_guide: boolean;
  activites: string[];
  contraintes: string;
  conseiller: string;
  souhaits: string;
  user_id: string;
}

export interface ClientInfo {
  id: string;
  email: string;
  nom: string;
}

export interface Recherche {
  id: string;
  source_label: string;
  source_url: string;
  consulte_le: string;
  criteres: Record<string, unknown>;
  resultats: PrestationRecherche[];
}

export interface PrestationRecherche {
  id: string;
  nom: string;
  type: string;
  destination: string;
  prix_unitaire_eur: number;
  prix_total_eur: number;
  disponible: boolean;
  dans_budget: boolean;
}

export interface Proposition {
  id: string;
  demande_id: string;
  statut: string;
  cree_le: string;
  modifiee_le: string;
  conseiller: string;
  titre: string;
  description: string;
  prestations: Prestation[];
  prix_total_eur: number;
}

/** One line in a proposal. Only "verifie" lines carry a real server price. */
export type VerificationPrestation = "verifie" | "manquant";

export interface Prestation {
  id: string;
  nom: string;
  type: string;
  quantite: number;
  verification: VerificationPrestation;
  prix_unitaire_eur: number | null;
  prix_total_eur: number | null;
  disponible: boolean | null;
  source: string | null;
  consulte_le: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  reply: string;
  demande?: Demande | null;
  recherche?: Recherche | null;
  trace: {
    model: string;
    tool_calls: unknown[];
    simulation: boolean;
  };
  simulation: boolean;
}

export interface ApiError {
  erreur: { code: string; message: string };
}
