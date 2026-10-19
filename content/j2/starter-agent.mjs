/**
 * DÉTOUR : point de départ pour le TP agentique.
 * Node.js 20+ ; aucune dépendance à installer.
 *
 * Depuis la racine du projet :
 *   OPENROUTER_API_KEY=... OPENROUTER_MODEL=... TRAVEL_TEAM_KEY=demo-key \
 *     node content/j2/starter-agent.mjs
 *
 * Les TODO sont le travail de l'équipe. Ce fichier ne réserve rien.
 */

const openRouterKey = process.env.OPENROUTER_API_KEY;
const model = process.env.OPENROUTER_MODEL;
const teamKey = process.env.TRAVEL_TEAM_KEY;
const supplierBaseUrl = process.env.TRAVEL_API_URL ?? 'http://127.0.0.1:8765';

if (!openRouterKey || !model || !teamKey) {
  console.error('Configurer OPENROUTER_API_KEY, OPENROUTER_MODEL et TRAVEL_TEAM_KEY.');
  process.exit(1);
}

const tool = {
  type: 'function',
  function: {
    name: 'verifier_disponibilite',
    description: 'Consulte la disponibilité et le prix total fictifs d’une prestation DÉTOUR pour une date et un groupe. Ne pose aucune option et ne réserve rien.',
    parameters: {
      type: 'object',
      properties: {
        prestation_id: { type: 'string', description: 'Identifiant de la prestation du catalogue.' },
        date: { type: 'string', description: 'Date au format AAAA-MM-JJ.' },
        participants: { type: 'integer', description: 'Nombre de voyageurs, entier positif.' },
      },
      required: ['prestation_id', 'date', 'participants'],
    },
  },
};

async function askModel(messages) {
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${openRouterKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model, messages, tools: [tool], tool_choice: 'auto' }),
  });
  if (!response.ok) throw new Error(`OpenRouter : HTTP ${response.status}`);
  const data = await response.json();
  const message = data.choices?.[0]?.message;
  if (!message) throw new Error('OpenRouter : réponse sans message.');
  return message;
}

function validateArguments(rawArguments) {
  // TODO 1 : analyser le JSON, contrôler l'identifiant, la date et les participants.
  // Lever une erreur explicite si les arguments sont invalides.
  throw new Error('TODO 1 : valider les arguments proposés par le modèle.');
}

async function checkAvailability(args) {
  // TODO 2 : construire une URL vers GET /api/v1/disponibilites.
  // Ajouter X-Team-Key côté serveur, traiter les statuts non-200 et retourner le JSON.
  // Ne jamais inclure teamKey dans les messages envoyés au modèle ou la trace.
  void supplierBaseUrl;
  void teamKey;
  void args;
  throw new Error('TODO 2 : consulter le serveur de prestations.');
}

async function main() {
  const userRequest = process.argv.slice(2).join(' ') ||
    'Pour deux personnes le 7 novembre 2026, le train train-nantes-01 est-il disponible et combien coûterait-il ?';
  const messages = [
    {
      role: 'system',
      content: 'Tu aides un conseiller de DÉTOUR. Utilise l’outil pour vérifier disponibilité et prix. N’annonce jamais une réservation. Distingue les faits vérifiés des inconnues.',
    },
    { role: 'user', content: userRequest },
  ];

  const first = await askModel(messages);
  const calls = first.tool_calls ?? [];
  if (calls.length === 0) {
    console.log('Aucun appel d’outil : disponibilité non vérifiée.');
    console.log(first.content ?? 'Aucune réponse du modèle.');
    return;
  }

  // TODO 3 : refuser les noms d’outils inconnus et limiter la boucle.
  // Pour chaque appel autorisé, valider les arguments puis consulter le serveur.
  // Ajouter à messages le message assistant contenant tool_calls,
  // puis un message role:'tool' avec tool_call_id et le résultat JSON.
  // Faire un second appel askModel(messages), afficher réponse et trace sans clés.
  console.log('Appels proposés par le modèle :', calls.map((call) => call.function?.name));
  void validateArguments;
  void checkAvailability;
  throw new Error('TODO 3 : exécuter l’outil et rendre le résultat au modèle.');
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
