#!/usr/bin/env python3
"""Unit tests for propositions, readings comparison and advisor decisions."""

import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

CONSEILLER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CONSEILLER_ROOT))

from app import make_handler
from lecture import (
    a_des_ecarts,
    comparer_ligne,
    comparer_proposition,
    proposition_avec_changements,
)
from propositions import PropositionStore, PropositionError, aligner_sur_serveur
from store import DemandStore
from test_conseiller import (
    VALIDE,
    FakeAgent,
    FakeSupplier,
    get,
    post,
)

PROPOSITION_VALIDE = {
    "titre": "Week-end à Nantes",
    "description": "Un séjour romantique à Nantes.",
    "prestations": [
        {"id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
         "prix_unitaire_eur": 48, "quantite": 2, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-19T10:42:00+00:00"},
        {"id": "hotel-nantes-01", "nom": "Hôtel Nantes", "type": "hébergement",
         "prix_unitaire_eur": 120, "quantite": 1, "disponible": True,
         "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-19T10:42:00+00:00"},
    ],
}


class TestPropositionStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = Path(self.tmpdir) / "propositions.json"
        self.store = PropositionStore(self.path)
        self.demand_store = DemandStore(Path(self.tmpdir) / "demandes.json")

    def test_creer_et_obtenir(self):
        prop = self.store.creer("dem_abc123", dict(PROPOSITION_VALIDE), conseiller="Alice")
        self.assertTrue(prop["id"].startswith("prop_"))
        self.assertEqual(prop["statut"], "brouillon")
        self.assertEqual(prop["conseiller"], "Alice")
        self.assertEqual(prop["prix_total_eur"], 216)
        fetched = self.store.obtenir(prop["id"])
        assert fetched is not None
        self.assertEqual(fetched["titre"], "Week-end à Nantes")

    def test_persiste_sur_disque(self):
        prop = self.store.creer("dem_abc123", dict(PROPOSITION_VALIDE))
        store2 = PropositionStore(self.path)
        self.assertEqual(len(store2.lister()), 1)
        self.assertEqual(store2.obtenir(prop["id"])["titre"], "Week-end à Nantes")

    def test_lister_par_demande(self):
        self.store.creer("dem_aaa", dict(PROPOSITION_VALIDE))
        self.store.creer("dem_bbb", dict(PROPOSITION_VALIDE))
        self.store.creer("dem_aaa", dict(PROPOSITION_VALIDE, titre="Autre"))
        self.assertEqual(len(self.store.lister_par_demande("dem_aaa")), 2)
        self.assertEqual(len(self.store.lister_par_demande("dem_bbb")), 1)

    def test_lister_par_user(self):
        dem = self.demand_store.creer({**VALIDE, "user_id": "usr_abc"})
        self.store.creer(dem["id"], dict(PROPOSITION_VALIDE))
        self.store.creer("dem_autre", dict(PROPOSITION_VALIDE))
        props = self.store.lister_par_user("usr_abc", self.demand_store)
        self.assertEqual(len(props), 1)

    def test_mettre_a_jour(self):
        prop = self.store.creer("dem_abc", dict(PROPOSITION_VALIDE))
        updated = self.store.mettre_a_jour(prop["id"], {"titre": "Modifié",
             "description": "Nouvelle desc", "prestations": []})
        self.assertEqual(updated["titre"], "Modifié")
        self.assertEqual(updated["prix_total_eur"], 0)

    def test_changer_statut(self):
        prop = self.store.creer("dem_abc", dict(PROPOSITION_VALIDE))
        self.assertEqual(self.store.changer_statut(prop["id"], "envoyee")["statut"], "envoyee")
        with self.assertRaises(PropositionError):
            self.store.changer_statut(prop["id"], "inconnu")
        self.assertIsNone(self.store.changer_statut("prop_inconnu", "envoyee"))

    def test_prestation_invalide(self):
        with self.assertRaises(PropositionError):
            self.store.creer("dem_abc", {"titre": "Test", "prestations": [{"nom": ""}]})

    def test_titre_manquant(self):
        with self.assertRaises(PropositionError):
            self.store.creer("dem_abc", {"titre": "", "prestations": []})


class FakeAgentWithGeneration(FakeAgent):
    def generer_proposition(self, demande_record, recherche):
        return {"titre": "Généré", "description": "Proposition générée",
                "prestations": [{"id": "train-01", "nom": "Train", "type": "transport",
                                 "prix_unitaire_eur": 50, "quantite": 2}]}


class TestPropositionGeneration(unittest.TestCase):
    """Test proposition generation through the agent (no real OpenRouter call)."""

    def test_generer_proposition_retourne_json(self):
        agent = FakeAgentWithGeneration()
        demande = {"demande": {"destination": "Nantes", "date_depart": "2026-11-07",
                               "date_retour": "2026-11-09", "nombre_voyageurs": 2,
                               "budget_max_par_personne": 500, "type_voyage": "trek-randonnee",
                               "niveau_aventure": "modere", "souhaits": ""}}
        recherche = {"resultats": [{"id": "train-nantes-01", "nom": "Train", "type": "transport",
                                    "prix_unitaire_eur": 48, "prix_total_eur": 96}]}
        result = agent.generer_proposition(demande, recherche)
        self.assertEqual(result["titre"], "Généré")
        self.assertIsInstance(result["prestations"], list)
        


class TestAlignerSurServeur(unittest.TestCase):
    """Price and provenance come from the server search, never from the model."""
    RESULTATS = [{"id": "train-lyon-01", "nom": "Train vers Lyon",
                  "type": "transport", "prix_unitaire_eur": 62, "disponible": True}]
    CONSULTE = "2026-10-19T10:42:00+00:00"

    def test_prix_du_serveur_remplace_celui_du_modele(self):
        data = {"titre": "Lyon", "prestations": [
            {"id": "train-lyon-01", "nom": "Train", "type": "transport",
             "prix_unitaire_eur": 26, "quantite": 2}]}
        prestation = aligner_sur_serveur(
            data, self.RESULTATS, source_label="Serveur fictif DÉTOUR",
            consulte_le=self.CONSULTE)["prestations"][0]
        self.assertEqual(prestation["prix_unitaire_eur"], 62)
        self.assertEqual(prestation["nom"], "Train vers Lyon")
        self.assertEqual(prestation["quantite"], 2)
        self.assertEqual(prestation["verification"], "verifie")
        self.assertTrue(prestation["disponible"])
        self.assertEqual(prestation["source"], "Serveur fictif DÉTOUR")
        self.assertEqual(prestation["consulte_le"], self.CONSULTE)

    def test_prestation_inconnue_du_serveur_est_manquante(self):
        data = {"titre": "Lyon", "prestations": [
            {"id": "bateau-lyon-99", "nom": "Croisière", "prix_unitaire_eur": 40}]}
        prestation = aligner_sur_serveur(
            data, self.RESULTATS, source_label="Serveur fictif DÉTOUR",
            consulte_le=self.CONSULTE)["prestations"][0]
        self.assertEqual(prestation["verification"], "manquant")
        self.assertIsNone(prestation["prix_unitaire_eur"])
        self.assertIsNone(prestation["disponible"])
        self.assertIsNone(prestation["source"])
        self.assertIsNone(prestation["consulte_le"])

    def test_sans_heure_de_consultation_reste_manquant(self):
        data = {"titre": "Lyon", "prestations": [
            {"id": "train-lyon-01", "nom": "Train", "prix_unitaire_eur": 26}]}
        prestation = aligner_sur_serveur(data, self.RESULTATS)["prestations"][0]
        self.assertEqual(prestation["verification"], "manquant")
        self.assertIsNone(prestation["prix_unitaire_eur"])


class TestProvenancePrestation(unittest.TestCase):
    """Verified lines keep source and time; incomplete prices stay missing."""

    def test_ligne_verifiee_persistee(self):
        tmp = tempfile.mkdtemp()
        path = Path(tmp) / "propositions.json"
        store = PropositionStore(path)
        prop = store.creer("dem_abc", dict(PROPOSITION_VALIDE))
        train = prop["prestations"][0]
        self.assertEqual(train["verification"], "verifie")
        self.assertEqual(train["source"], "Serveur fictif DÉTOUR")
        self.assertEqual(train["consulte_le"], "2026-10-19T10:42:00+00:00")
        self.assertTrue(train["disponible"])
        self.assertEqual(train["prix_unitaire_eur"], 48)
        # Reopening the stored proposition must keep the same source and time.
        reouvert = PropositionStore(path).obtenir(prop["id"])
        self.assertEqual(reouvert["prestations"][0]["source"], train["source"])
        self.assertEqual(reouvert["prestations"][0]["consulte_le"], train["consulte_le"])

    def test_prix_sans_provenance_devient_manquant(self):
        data = {
            "titre": "Sans preuve",
            "description": "",
            "prestations": [{
                "id": "train-nantes-01", "nom": "Train", "type": "transport",
                "prix_unitaire_eur": 48, "quantite": 2,
            }],
        }
        prop = PropositionStore(None).creer("dem_abc", data)
        ligne = prop["prestations"][0]
        self.assertEqual(ligne["verification"], "manquant")
        self.assertIsNone(ligne["prix_unitaire_eur"])
        self.assertIsNone(ligne["disponible"])
        self.assertEqual(prop["prix_total_eur"], 0)


class TestComparerLectures(unittest.TestCase):
    """Compare proposal v1 with a newer reading without rewriting v1."""

    LIGNE = {
        "id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
        "quantite": 2, "verification": "verifie", "prix_unitaire_eur": 48,
        "prix_total_eur": 96, "disponible": True,
        "source": "Serveur fictif DÉTOUR", "consulte_le": "2026-10-19T10:42:00+00:00",
    }

    def test_prix_change_montre_ancien_et_nouveau(self):
        delta = comparer_ligne(self.LIGNE, {
            "id": "train-nantes-01", "prix_unitaire_eur": 62, "disponible": True,
        })
        self.assertEqual(delta["prix_avant"], 48)
        self.assertEqual(delta["prix_apres"], 62)
        self.assertTrue(delta["prix_change"])
        self.assertFalse(delta["inchange"])

    def test_indisponible_apres_nouvelle_lecture(self):
        delta = comparer_ligne(self.LIGNE, {
            "id": "train-nantes-01", "prix_unitaire_eur": 48, "disponible": False,
        })
        self.assertTrue(delta["disponibilite_change"])
        self.assertFalse(delta["disponible_apres"])
        self.assertFalse(delta["inchange"])

    def test_inchange_quand_meme_prix_et_dispo(self):
        delta = comparer_ligne(self.LIGNE, {
            "id": "train-nantes-01", "prix_unitaire_eur": 48, "disponible": True,
        })
        self.assertTrue(delta["inchange"])
        self.assertFalse(a_des_ecarts([delta]))

    def test_lecture_manquante_n_est_pas_un_changement(self):
        self.assertIsNone(comparer_ligne(self.LIGNE, None))
        self.assertIsNone(comparer_ligne(self.LIGNE, {"id": "train-nantes-01"}))
        self.assertEqual(comparer_proposition(
            {"prestations": [self.LIGNE]}, [{"id": "autre-01", "prix_unitaire_eur": 10,
                                             "disponible": True}]), [])

    def test_v1_reste_lisible_apres_enrichissement(self):
        prop = PropositionStore(None).creer("dem_abc", dict(PROPOSITION_VALIDE))
        recherches = [
            {"consulte_le": "2026-10-19T10:42:00+00:00", "resultats": []},
            {"consulte_le": "2026-10-20T11:00:00+00:00", "resultats": [
                {"id": "train-nantes-01", "prix_unitaire_eur": 62, "disponible": True},
                {"id": "hotel-nantes-01", "prix_unitaire_eur": 120, "disponible": True},
            ]},
        ]
        enrichie = proposition_avec_changements(prop, recherches)
        self.assertEqual(enrichie["prestations"][0]["prix_unitaire_eur"], 48)
        self.assertEqual(enrichie["changements"][0]["prix_apres"], 62)
        # Stored record must still be the original v1 prices.
        self.assertEqual(prop["prestations"][0]["prix_unitaire_eur"], 48)


class SequenceSupplier:
    """Returns successive search payloads for re-read scenarios."""

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = []

    def rechercher(self, criteres):
        self.calls.append(criteres)
        if not self.payloads:
            raise AssertionError("No more supplier payloads")
        return self.payloads.pop(0)


class TestStatutARevoirApresChangement(unittest.TestCase):
    """Request becomes To review when a re-read changes price or availability."""

    def serve(self, supplier, props):
        store = DemandStore(None)
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(store, supplier, propositions=props))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return store, f"http://127.0.0.1:{server.server_port}"

    def test_prix_change_passe_la_demande_a_revoir(self):
        props = PropositionStore(None)
        supplier = SequenceSupplier([
            {"source_label": "Faux", "source_url": "http://faux",
             "consulte_le": "2026-10-19T10:42:00+00:00",
             "criteres": {}, "resultats": [
                 {"id": "train-nantes-01", "nom": "Train", "type": "transport",
                  "prix_unitaire_eur": 48, "disponible": True}]},
            {"source_label": "Faux", "source_url": "http://faux",
             "consulte_le": "2026-10-20T11:00:00+00:00",
             "criteres": {}, "resultats": [
                 {"id": "train-nantes-01", "nom": "Train", "type": "transport",
                  "prix_unitaire_eur": 62, "disponible": True}]},
        ])
        store, base = self.serve(supplier, props)
        dem_id = store.creer(dict(VALIDE))["id"]
        post(f"{base}/api/demandes/{dem_id}/recherche")
        prop = props.creer(dem_id, {
            "titre": "Nantes", "description": "",
            "prestations": [{
                "id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
                "prix_unitaire_eur": 48, "quantite": 2, "disponible": True,
                "source": "Serveur fictif DÉTOUR",
                "consulte_le": "2026-10-19T10:42:00+00:00",
            }],
        })
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 201)
        self.assertEqual(data["demande"]["statut"], "a_revoir")
        self.assertEqual(store.obtenir(dem_id)["statut"], "a_revoir")
        # v1 kept on disk / in store
        self.assertEqual(props.obtenir(prop["id"])["prestations"][0]["prix_unitaire_eur"], 48)
        _, got = get(f"{base}/api/propositions/{prop['id']}")
        self.assertEqual(got["proposition"]["prestations"][0]["prix_unitaire_eur"], 48)
        self.assertEqual(got["proposition"]["changements"][0]["prix_avant"], 48)
        self.assertEqual(got["proposition"]["changements"][0]["prix_apres"], 62)

    def test_lecture_manquante_ne_passe_pas_a_revoir(self):
        props = PropositionStore(None)
        supplier = SequenceSupplier([
            {"source_label": "Faux", "source_url": "http://faux",
             "consulte_le": "2026-10-19T10:42:00+00:00",
             "criteres": {}, "resultats": [
                 {"id": "train-nantes-01", "nom": "Train", "type": "transport",
                  "prix_unitaire_eur": 48, "disponible": True}]},
            {"source_label": "Faux", "source_url": "http://faux",
             "consulte_le": "2026-10-20T11:00:00+00:00",
             "criteres": {}, "resultats": []},
        ])
        store, base = self.serve(supplier, props)
        dem_id = store.creer(dict(VALIDE))["id"]
        post(f"{base}/api/demandes/{dem_id}/recherche")
        props.creer(dem_id, {
            "titre": "Nantes", "description": "",
            "prestations": [{
                "id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
                "prix_unitaire_eur": 48, "quantite": 2, "disponible": True,
                "source": "Serveur fictif DÉTOUR",
                "consulte_le": "2026-10-19T10:42:00+00:00",
            }],
        })
        status, data = post(f"{base}/api/demandes/{dem_id}/recherche")
        self.assertEqual(status, 201)
        self.assertEqual(data["demande"]["statut"], "a_analyser")


class TestDecisionPrestation(unittest.TestCase):
    """Advisor keep/replace/drop is stored with name, time and reason — no send, no option."""

    def setUp(self):
        self.props = PropositionStore(None)
        self.prop = self.props.creer("dem_abc", dict(PROPOSITION_VALIDE))

    def test_replace_stocke_nom_heure_et_motif(self):
        record = self.props.enregistrer_decision(
            self.prop["id"], "train-nantes-01", "replace", "Nora",
            "budget no longer holds", remplacement_id="train-nantes-02")
        self.assertEqual(len(record["decisions"]), 1)
        d = record["decisions"][0]
        self.assertEqual(d["choix"], "replace")
        self.assertEqual(d["par"], "Nora")
        self.assertEqual(d["motif"], "budget no longer holds")
        self.assertEqual(d["prestation_id"], "train-nantes-01")
        self.assertEqual(d["remplacement_id"], "train-nantes-02")
        self.assertTrue(d["le"])
        self.assertEqual(record["statut"], "brouillon")

    def test_replace_sans_remplacement_id_refuse(self):
        with self.assertRaises(PropositionError):
            self.props.enregistrer_decision(
                self.prop["id"], "train-nantes-01", "replace", "Nora",
                "budget no longer holds")

    def test_sans_nom_conseiller_refuse(self):
        with self.assertRaises(PropositionError):
            self.props.enregistrer_decision(
                self.prop["id"], "train-nantes-01", "keep", "", "ok")
        with self.assertRaises(PropositionError):
            self.props.enregistrer_decision(
                self.prop["id"], "train-nantes-01", "keep", "   ", "ok")
        self.assertEqual(self.props.obtenir(self.prop["id"])["decisions"], [])

    def test_sans_motif_refuse(self):
        with self.assertRaises(PropositionError):
            self.props.enregistrer_decision(
                self.prop["id"], "train-nantes-01", "drop", "Nora", "")

    def test_decision_ne_passe_pas_en_envoyee(self):
        record = self.props.enregistrer_decision(
            self.prop["id"], "train-nantes-01", "keep", "Nora", "prix acceptable")
        self.assertNotEqual(record["statut"], "envoyee")
        self.assertEqual(record["statut"], "brouillon")

    def test_decisions_are_append_only_for_audit(self):
        self.props.enregistrer_decision(
            self.prop["id"], "train-nantes-01", "keep", "Nora", "first look")
        record = self.props.enregistrer_decision(
            self.prop["id"], "train-nantes-01", "drop", "Nora", "changed mind")
        self.assertEqual(len(record["decisions"]), 2)
        self.assertEqual(record["decisions"][0]["choix"], "keep")
        self.assertEqual(record["decisions"][1]["choix"], "drop")

    def test_http_decision_sans_appel_option(self):
        class SpySupplier(FakeSupplier):
            def __init__(self):
                super().__init__()
                self.option_calls = 0

            def creer_option(self, *args, **kwargs):
                self.option_calls += 1
                raise AssertionError("option endpoint must not be called")

        supplier = SpySupplier()
        store = DemandStore(None)
        props = PropositionStore(None)
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_handler(store, supplier, propositions=props))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        base = f"http://127.0.0.1:{server.server_port}"
        dem_id = store.creer(dict(VALIDE))["id"]
        prop = props.creer(dem_id, dict(PROPOSITION_VALIDE))
        status, data = post(f"{base}/api/propositions/{prop['id']}/decisions", {
            "prestation_id": "train-nantes-01",
            "choix": "replace",
            "motif": "budget no longer holds",
            "remplacement_id": "train-nantes-02",
        })
        self.assertEqual(status, 200)
        self.assertEqual(data["proposition"]["decisions"][0]["choix"], "replace")
        self.assertEqual(data["proposition"]["decisions"][0]["par"], "Conseiller DÉTOUR")
        self.assertEqual(data["proposition"]["statut"], "brouillon")
        self.assertEqual(supplier.option_calls, 0)
        self.assertEqual(supplier.calls, [])  # no supplier call at all


class TestPropositionV2(unittest.TestCase):
    """Completed decisions create draft v2; v1 stays readable with original prices."""

    def test_replace_cree_v2_depuis_lecture_serveur(self):
        props = PropositionStore(None)
        v1 = props.creer("dem_abc", dict(PROPOSITION_VALIDE))
        self.assertEqual(v1["version"], 1)
        # Only the train changed → one decision completes the set.
        props.enregistrer_decision(
            v1["id"], "train-nantes-01", "replace", "Nora",
            "budget no longer holds", remplacement_id="train-nantes-02")
        recherche = {
            "source_label": "Serveur fictif DÉTOUR",
            "consulte_le": "2026-10-20T11:05:00+00:00",
            "resultats": [
                {"id": "train-nantes-01", "nom": "Train Nantes", "type": "transport",
                 "prix_unitaire_eur": 62, "disponible": True},
                {"id": "train-nantes-02", "nom": "Train Nantes alt", "type": "transport",
                 "prix_unitaire_eur": 40, "disponible": True},
                {"id": "hotel-nantes-01", "nom": "Hôtel Nantes", "type": "hébergement",
                 "prix_unitaire_eur": 120, "disponible": True},
            ],
        }
        v2 = props.creer_v2_si_complet(v1["id"], recherche, conseiller="Nora")
        self.assertIsNotNone(v2)
        self.assertEqual(v2["version"], 2)
        self.assertEqual(v2["parente_id"], v1["id"])
        self.assertEqual(v2["demande_id"], "dem_abc")
        self.assertEqual(v2["statut"], "brouillon")
        self.assertNotEqual(v2["statut"], "envoyee")
        ids = {p["id"] for p in v2["prestations"]}
        self.assertIn("train-nantes-02", ids)
        self.assertNotIn("train-nantes-01", ids)
        remp = next(p for p in v2["prestations"] if p["id"] == "train-nantes-02")
        self.assertEqual(remp["prix_unitaire_eur"], 40)
        self.assertEqual(remp["source"], "Serveur fictif DÉTOUR")
        self.assertEqual(remp["consulte_le"], "2026-10-20T11:05:00+00:00")
        # v1 untouched
        v1_relue = props.obtenir(v1["id"])
        self.assertEqual(v1_relue["prestations"][0]["id"], "train-nantes-01")
        self.assertEqual(v1_relue["prestations"][0]["prix_unitaire_eur"], 48)

    def test_incomplet_ne_cree_pas_v2(self):
        props = PropositionStore(None)
        v1 = props.creer("dem_abc", dict(PROPOSITION_VALIDE))
        recherche = {
            "consulte_le": "2026-10-20T11:05:00+00:00",
            "resultats": [
                {"id": "train-nantes-01", "prix_unitaire_eur": 62, "disponible": True},
                {"id": "hotel-nantes-01", "prix_unitaire_eur": 150, "disponible": True},
            ],
        }
        # Hotel also changed but no decision yet.
        props.enregistrer_decision(
            v1["id"], "train-nantes-01", "keep", "Nora", "ok")
        self.assertIsNone(props.creer_v2_si_complet(v1["id"], recherche, "Nora"))

