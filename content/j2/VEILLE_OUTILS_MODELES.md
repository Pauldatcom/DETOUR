# Outils, modèles et coûts : fiche de veille

**État vérifié le 14 octobre 2026.** Les modèles, les quotas et les tarifs changent. Le formateur vérifie les fiches liées ci-dessous avant chaque séance. Les usages proposés servent à formuler des hypothèses de test, pas un classement universel.

## Trois choix différents

1. **Le client** est l'interface dans laquelle on travaille : terminal, éditeur ou application graphique. Elle détermine les accès au dépôt, les outils proposés et la manière de relire les changements.
2. **Le modèle** produit des propositions. Ses performances dépendent de la tâche, du contexte, du réglage et des outils disponibles.
3. **L'accès** détermine les limites et la facture : usage inclus dans une application, crédit complémentaire ou clé API facturée selon la consommation.

| Client | Surface principale | À vérifier avant une tâche de code |
|---|---|---|
| [Claude Desktop et Claude Code](https://claude.com/product/claude-code) | Application graphique et agent de code en terminal ou IDE | Quel produit a accès au dépôt, au terminal et aux outils ? Quel plan ou quelle clé est utilisé ? |
| [ChatGPT app et Codex](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan) | Application, terminal, IDE et tâches Codex | La connexion au compte et la clé API sont deux modes d'accès différents. Vérifier les limites du plan. |
| [Cursor](https://cursor.com/docs/models-and-pricing) | Éditeur avec agent intégré | Le modèle choisi change la consommation de l'usage inclus. Vérifier le tableau de bord et les achats additionnels. |
| [OpenCode](https://opencode.ai/docs) | Terminal, bureau et IDE | Choisir le fournisseur et le modèle ; vérifier si la connexion utilise un abonnement ou une clé de fournisseur. |

Dans une démonstration, on peut dire : « Claude explore volontiers plusieurs pistes ; Codex avance souvent plus méthodiquement et vérifie ses étapes. » C'est une observation de style à éprouver sur une même tâche, jamais une propriété fixe du modèle ou une garantie de qualité.

## Deux formats d'API, plusieurs fournisseurs

« Compatible OpenAI » ou « compatible Anthropic » décrit un **format d'échange**, pas le modèle qui répond ni une équivalence complète entre fournisseurs. Il faut vérifier la route utilisée, les champs acceptés et la forme réelle des appels d'outils. Un client qui utilise OpenAI **Responses** ne fonctionne pas forcément avec un serveur qui n'implémente que **Chat Completions**.

| Format utilisé en cours | Route courante | Demande d'outil | Retour de l'application | Serveurs documentés |
|---|---|---|---|---|
| [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat) | `POST /v1/chat/completions` | `tool_calls` avec nom et arguments | message `role: tool` lié à l'appel | [OpenRouter](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request), [Ollama](https://docs.ollama.com/api/openai-compatibility), [LM Studio](https://lmstudio.ai/docs/developer/openai-compat) |
| [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create) | `POST /v1/messages` | outil défini avec `input_schema`, puis bloc `tool_use` | bloc `tool_result` lié à l'appel | Anthropic, [OpenRouter](https://openrouter.ai/docs/api/api-reference/anthropic-messages/create-messages), [Ollama](https://docs.ollama.com/api/anthropic-compatibility), [LM Studio](https://lmstudio.ai/docs/developer/anthropic-compat) |

La `base URL` désigne le serveur. Le **modèle** est un autre choix. Changer seulement l'URL ne suffit pas si le client attend une route ou une fonction que le serveur n'implémente pas. Le contrôle métier reste dans notre programme : quel que soit le format, le modèle propose l'appel, le code valide les arguments et consulte le serveur DÉTOUR.

[Ollama](https://docs.ollama.com/api/openai-compatibility) sert des modèles locaux sur `localhost:11434` et documente une compatibilité partielle avec les deux formats. [LM Studio](https://lmstudio.ai/docs/developer/core/server) propose une interface graphique, un serveur local habituellement sur `localhost:1234`, et les deux familles de routes. Le modèle doit être installé ou chargé, et sa qualité d'appel d'outils doit être éprouvée : [LM Studio distingue différents niveaux de prise en charge](https://lmstudio.ai/docs/developer/openai-compat/tools). Une exécution réellement locale évite une facture d'API distante par appel, mais consomme du stockage, de la mémoire et du calcul. Les offres cloud éventuelles suivent d'autres règles.

Pour le TP DÉTOUR, le parcours de référence reste **OpenRouter avec Chat Completions OpenAI-compatible**. Il ne demande ni installation d'un modèle local ni adaptation au format Anthropic. Les deux formats et les deux serveurs locaux sont présentés pour savoir choisir un environnement de développement et préparer une autre architecture.

## Modèles à mettre à l'épreuve

| Modèle | Usage à essayer | Limite ou question à vérifier |
|---|---|---|
| [Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5) | Travail complexe et longues tâches avec jugement | Coût supérieur à un modèle plus léger ; l'action produite doit être relue. |
| [GPT-6 Astra](https://openai.com/index/gpt-6-astra/) | Problème exigeant où la profondeur compte | À 10 $ / million de tokens d'entrée et 50 $ / million de sortie dans l'[exemple tarifaire officiel](https://openai.com/index/practical-guide-building-gpt-6/), les boucles répétées coûtent vite. |
| [GPT-6.1 Sol](https://openai.com/index/introducing-gpt-6-1-sol/) | Code, recherche et usage agentique courant | Le coût et la fiabilité des appels d'outils se mesurent sur le parcours réel. Tarif d'exemple : 2 $ / million en entrée et 10 $ / million en sortie. |
| [Gemini 4 Argon](https://ai.google.dev/gemini-api/docs/latest-model) | Raisonnement long, code et flux complexes | API payante. Tarif introductif annoncé jusqu'au 30 novembre 2026, puis hausse annoncée ; revalider avant usage. |
| [Grok 4.1 et 4.1 Fast](https://x.ai/news/grok-4-1-fast) | Conversation avec Grok 4.1 ; appels d'outils avec la variante Fast | Les variantes ne sont pas interchangeables. Vérifier l'identifiant API, le budget des outils et la source des faits. |

Les fiches des éditeurs décrivent leurs propres évaluations. Pour DÉTOUR, comparer les modèles sur la **même** demande, avec les **mêmes** outils et critères : arguments valides, prix et disponibilité issus du serveur, réaction à une erreur, nombre de tours, coût et capacité à expliquer la trace.

## OpenRouter pour le TP

[OpenRouter](https://openrouter.ai/docs/quickstart) est une passerelle vers plusieurs modèles, pas un modèle. Dans la [collection gratuite](https://openrouter.ai/collections/free-models/) consultée le 14 octobre 2026, **Nemotron 3 Ultra (free)** et **Nemotron 3.5 Lightning (free)** apparaissent parmi les modèles les plus utilisés. Le routeur `openrouter/free` choisit automatiquement un modèle gratuit adapté aux capacités demandées ; ce choix peut changer. La popularité affichée ne mesure pas la qualité. Avant le cours, sélectionner un modèle gratuit qui [accepte les appels d'outils](https://openrouter.ai/docs/guides/features/tool-calling), faire un essai réel, puis vérifier [quota et disponibilité](https://openrouter.ai/pricing). Le TP n'active pas de route payante de secours.

Le modèle peut demander un outil. Dans le TP, **le programme exécute les outils de DÉTOUR**, valide leurs arguments et renvoie le résultat. OpenRouter propose aussi des outils exécutés de son côté ; ils ne font pas partie du parcours DÉTOUR.

## Abonnement et API : calcul de contrôle

Le forfait Claude Code sert au **travail du développeur** dans le terminal, l'IDE ou l'application, selon les limites du plan. Quand les voyageurs utilisent DÉTOUR, c'est **l'application** qui appelle un modèle avec sa clé API : il faut un accès API, des quotas, un suivi d'usage et un budget propres au produit. [Anthropic distingue l'abonnement et la facturation API](https://support.claude.com/en/articles/9876003-i-have-a-paid-claude-subscription-pro-max-team-or-enterprise-plans-why-is-claude-api-usage-billed-separately-from-my-paid-claude-plan). Certains forfaits Max et Team proposent des [crédits API mensuels](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-and-team-plans) via une organisation Console liée : ils restent séparés de l'usage Claude Code et ne dispensent pas de suivre la consommation. Cursor décrit aussi un usage inclus qui dépend du modèle, puis des possibilités d'achat supplémentaire.

De la même façon, payer ChatGPT Plus ne crédite pas son compte OpenRouter. Les [crédits d'usage ChatGPT et Codex](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-personal-plans) sont distincts des crédits API OpenAI, et la clé OpenRouter du programme suit ses propres règles.

Avec le tarif indicatif vérifié de **GPT-6.1 Sol**, un appel consommant 100 000 tokens d'entrée et 20 000 tokens de sortie coûte `(100 000 × 2 + 20 000 × 10) / 1 000 000 = 0,40 $`. Deux cents appels identiques coûtent **80 $**, hors outils et frais éventuels. Dans une boucle agentique, l'historique répété, les réponses longues, les reprises sur erreur et les branches parallèles peuvent augmenter le total. Les tokens de raisonnement et les résultats d'outils peuvent aussi peser sur la consommation selon le fournisseur.

Avant d'activer une clé API payante : fixer un budget, borner le nombre de tours et d'appels, suivre l'usage réel et définir les modèles autorisés. OpenRouter documente des [garde-fous de budget et de modèles](https://openrouter.ai/docs/guides/features/guardrails/overview). Pour ce cours, on reste sur les modèles gratuits annoncés, avec un rejeu local si nécessaire.

## Veille continue

Une annonce repérée sur X peut être un signal rapide, avec du bruit autour. Ouvrir ensuite la fiche officielle du fournisseur, relever le modèle exact, la date, les capacités d'outils, les limites et la tarification. Enfin, refaire le petit banc d'essai DÉTOUR avant de changer le choix du cours ou du produit. Conserver la date et les résultats du test : une capture d'annonce ne démontre ni la qualité, ni la compatibilité, ni le coût réel.
