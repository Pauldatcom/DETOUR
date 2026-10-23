/**
 * Contenu DÉTOUR — données locales fictives, séparées de la présentation.
 * Aucune donnée réelle : toutes les destinations, images et prix sont fictifs.
 */

export interface Destination {
  id: string;
  titre: string;
  region: string;
  description: string;
  prixIndicatif: string;
  image: string;
  alt: string;
  ambiance: string;
}

export interface Etape {
  id: string;
  numero: string;
  titre: string;
  texte: string;
}

export const NAVIGATION = [
  { label: "Accueil", href: "/accueil" },
  { label: "Inspirations", href: "/inspirations" },
  { label: "Conseillers", href: "/conseillers" },
  { label: "Comment ça marche", href: "/accueil#comment-ca-marche" },
] as const;

export const HERO = {
  surtitre: "Agence de voyages sur mesure",
  titre: "Partez avec un conseiller, pas avec un algorithme.",
  texte:
    "Décrivez le voyage dont vous rêvez. Un conseiller DÉTOUR compose un itinéraire unique, adapte chaque étape et vous accompagne jusqu'au départ.",
  ctaPrincipal: "Décrire mon voyage",
  ctaSecondaire: "Découvrir nos inspirations",
  image: "/brand-2026/photo/train.png",
  imageAlt: "Train à grande vitesse traversant la campagne française",
} as const;

export const INSPIRATIONS = {
  surtitre: "Inspirations du moment",
  titre: "Quelques idées de voyages rêvés avec nos conseillers",
  texte:
    "Ces exemples sont entièrement fictifs. Ils illustrent le niveau de personnalisation que vous pouvez attendre d'une demande DÉTOUR.",
  destinations: [
    {
      id: "dest-nantes",
      titre: "Nantes & la Loire",
      region: "France",
      description:
        "Machines de l'île au lever du jour, balade sur les quais, puis une nuit dans un hôtel de charme au bord de l'Erdre.",
      prixIndicatif: "Exemple fictif · 3 jours",
      image: "/brand-2026/photo/nantes.png",
      alt: "Quais de la Loire et machines de Nantes",
      ambiance: "Culture & fluvial",
    },
    {
      id: "dest-lyon",
      titre: "Lyon entre deux fleuves",
      region: "France",
      description:
        "Traboules de Vieux-Lyon le matin, marché des Halles Paul Bocuse à midi, dîner dans une table lyonnaise le soir.",
      prixIndicatif: "Exemple fictif · 4 jours",
      image: "/brand-2026/photo/lyon.png",
      alt: "Rives de la Saône et toits de Lyon au crépuscule",
      ambiance: "Gastronomie & patrimoine",
    },
    {
      id: "dest-lille",
      titre: "Lille & la Grand-Place",
      region: "France",
      description:
        "Grand Place et façades flamandes, une gaufre tiède en main, puis une escapade à la citadelle et au vieux Lille.",
      prixIndicatif: "Exemple fictif · 2 jours",
      image: "/brand-2026/photo/lille.png",
      alt: "Grand Place et façades flamandes de Lille",
      ambiance: "Ville & nord",
    },
  ] as const satisfies readonly Destination[],
} as const;

export const COMMENT_CA_MARCHE = {
  surtitre: "Comment ça marche",
  titre: "Quatre étapes, un seul interlocuteur",
  texte:
    "DÉTOUR ne réserve rien pour vous. Un conseiller prépare votre projet, puis vous décidez ce qui vous convient.",
  etapes: [
    {
      id: "etape-1",
      numero: "01",
      titre: "Vous décrivez votre voyage",
      texte:
        "Destination approximative, dates souples, envies, niveau de confort. Cinq minutes suffisent pour poser votre projet.",
    },
    {
      id: "etape-2",
      numero: "02",
      titre: "Un conseiller analyse votre demande",
      texte:
        "Il identifie les prestations fiables — transport, hébergement, activités — et les assemble dans un itinéraire cohérent.",
    },
    {
      id: "etape-3",
      numero: "03",
      titre: "Vous recevez une proposition",
      texte:
        "Un document détaillé : programme jour par jour, sélection de prestations et budget estimatif. Rien n'est figé.",
    },
    {
      id: "etape-4",
      numero: "04",
      titre: "Vous ajustez ou vous validez",
      texte:
        "Demandez des modifications, comparez des variantes. Vous gardez la main jusqu'à la proposition finale.",
    },
  ] as const satisfies readonly Etape[],
} as const;

export const CONSEILLERS = {
  surtitre: "Nos conseillers",
  titre: "Des humains, joignables aux vraies heures",
  texte:
    "Pas de chatbot au premier niveau : chaque demande est relue et traitée par un conseiller DÉTOUR.",
  disponibilite: {
    jours: "Du lundi au vendredi",
    heures: "9 h — 18 h",
    precision:
      "En dehors de ces horaires, laissez-nous votre demande : nous la traitons à la première heure ouvrée.",
  },
  engagements: [
    "Une proposition détaillée, jamais un forfait standard.",
    "Des prestations vérifiées, sans commission cachée.",
    "La liberté de refuser ou de réajuster chaque étape.",
  ],
  profils: [
    {
      id: "cons-1",
      prenom: "Camille",
      specialite: "Europe du Sud & Méditerranée",
      bio: "Dix ans à arpenter les côtes portugaises et les villages andalous. Elle connaît chaque crique discrète.",
      disponibilite: "Lundi, mardi, jeudi",
    },
    {
      id: "cons-2",
      prenom: "Thomas",
      specialite: "Montagne & trekking",
      bio: "Guide haute montagne reconverti en conseiller de voyage. Patagonie, Dolomites, il a marché partout.",
      disponibilite: "Mardi, mercredi, vendredi",
    },
    {
      id: "cons-3",
      prenom: "Sarah",
      specialite: "Asie & culture",
      bio: "Ancienne résidente à Kyoto. Elle connaît le Japon hors sentiers battus et l'Asie du Sud-Est confidentielle.",
      disponibilite: "Lundi, jeudi, vendredi",
    },
  ],
} as const;

export const FOOTER = {
  tagline: "L'agence qui ne vend pas des voyages tout faits.",
  colonnes: [
    {
      titre: "DÉTOUR",
      liens: [
        { label: "Notre approche", href: "/accueil#comment-ca-marche" },
        { label: "Inspirations", href: "/inspirations" },
        { label: "Conseillers", href: "/conseillers" },
      ],
    },
    {
      titre: "Votre espace",
      liens: [
        { label: "Mes propositions", href: "/mes-propositions" },
        { label: "Se connecter", href: "/login" },
      ],
    },
    {
      titre: "Informations",
      liens: [{ label: "Horaires : lundi à vendredi, 9 h à 18 h", href: "/conseillers" }],
    },
  ],
  mentions:
    "Site fictif — projet pédagogique. Aucune réservation réelle, aucun paiement accepté. Toutes les destinations et tarifs sont des exemples.",
} as const;

export const FORMULAIRE = {
  titre: "Décrivez votre voyage",
  sousTitre: "Le conseiller a besoin de quelques repères pour préparer une proposition pertinente.",
  champDestination: "Où souhaitez-vous aller ? (pays, ville ou région)",
  champDates: "Quelles dates envisagez-vous ? (indicatif)",
  champVoyageurs: "Combien de voyageurs ?",
  champEnvies: "Vos envies et contraintes (rythme, budget, climats, loisirs…)",
  champsRequis: "Champs marqués d'un * obligatoires.",
  boutonEnvoyer: "Envoyer ma demande",
  boutonEnCours: "Envoi en cours…",
  etatVide: "Aucun détail requis pour commencer, mais le plus vous nous en direz, le mieux.",
  etatErreur: "Impossible d'envoyer votre demande. Vérifiez les champs puis réessayez.",
  messageSucces:
    "Votre demande a bien été enregistrée. Un conseiller vous répondra du lundi au vendredi, de 9 h à 18 h.",
} as const;
