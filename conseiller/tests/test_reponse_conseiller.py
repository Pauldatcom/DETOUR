#!/usr/bin/env python3
"""Tests de l'enregistrement de la réponse du conseiller à une demande (#52).

Critères d'acceptation :
- le conseiller peut rédiger et envoyer une réponse ;
- la réponse enregistre le conseiller, la date et l'heure ;
- la demande passe au statut « Répondue » ;
- le système calcule le temps de réponse réel ;
- le conseiller voit si la réponse est partie dans les 24 h ou après le
  délai maximal de 48 h.
"""
import secrets
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import make_handler
from horaires import (ECHEANCE_APPROCHE, ECHEANCE_DANS_DELAI, ECHEANCE_DEPASSEE,
                      fuseau_metier)
from propositions import PropositionStore
from store import DemandStore, ValidationError
from test_conseiller import VALIDE
from test_decision_flow import ClientHTTP, demarrer
from users import UserStore
from utils import (REPONSE_MAX_CARACTERES, STATUT_A_ANALYSER, STATUT_A_REVOIR,
                   STATUT_NOUVELLE, STATUT_PROPOSE, STATUT_REFUSE, STATUT_REPONDUE,
                   STATUT_VALIDE)

CONSEILLER = "Alice Martin"
MESSAGE = "Bonjour, nous avons bien reçu votre demande et revenons vers vous avec une proposition."


def metier(*args):
    """Build a datetime in the business timezone (Europe/Paris)."""
    return datetime(*args, tzinfo=fuseau_metier())


def demande_soumise_le(store, soumis_le):
    """Create a request, then backdate its submission to a known instant."""
    dem_id = store.creer(dict(VALIDE))["id"]
    store.demandes[dem_id]["cree_le"] = soumis_le.isoformat()
    return dem_id


class TestReponseEnregistree(unittest.TestCase):
    """Le conseiller rédige une réponse ; elle garde auteur, date et heure."""

    def setUp(self):
        self.store = DemandStore(None)
        self.soumis = metier(2026, 1, 6, 10, 0)          # mardi 10h
        self.dem_id = demande_soumise_le(self.store, self.soumis)
        self.maintenant = metier(2026, 1, 7, 10, 0)      # mercredi 10h

    def test_la_reponse_garde_le_texte_le_conseiller_la_date_et_l_heure(self):
        record = self.store.repondre(
            self.dem_id, "  " + MESSAGE + "  ", CONSEILLER, maintenant=self.maintenant)
        reponse = record["reponse"]
        self.assertEqual(reponse["message"], MESSAGE)
        self.assertEqual(reponse["par"], CONSEILLER)
        self.assertEqual(reponse["le"], self.maintenant.isoformat())

    def test_la_date_est_posee_par_defaut_a_l_instant_present(self):
        avant = datetime.now(fuseau_metier())
        record = self.store.repondre(self.dem_id, MESSAGE, CONSEILLER)
        apres = datetime.now(fuseau_metier())
        repondu_le = datetime.fromisoformat(record["reponse"]["le"])
        self.assertTrue(avant <= repondu_le <= apres)

    def test_la_demande_passe_au_statut_repondue(self):
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_NOUVELLE)
        record = self.store.repondre(
            self.dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
        self.assertEqual(record["statut"], STATUT_REPONDUE)
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_REPONDUE)

    def test_la_reponse_est_relue_avec_la_demande(self):
        self.store.repondre(self.dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
        lue = self.store.obtenir(self.dem_id)
        self.assertEqual(lue["reponse"]["par"], CONSEILLER)
        listee = next(d for d in self.store.lister() if d["id"] == self.dem_id)
        self.assertEqual(listee["reponse"]["message"], MESSAGE)

    def test_demande_inconnue(self):
        self.assertIsNone(self.store.repondre("dem_inconnue", MESSAGE, CONSEILLER))

    def test_la_decision_est_journalisee(self):
        record = self.store.repondre(
            self.dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
        entree = record["decisions"][-1]
        self.assertEqual(entree["action"], "reponse")
        self.assertEqual(entree["par"], CONSEILLER)
        self.assertEqual(entree["avant"], STATUT_NOUVELLE)
        self.assertEqual(entree["apres"], STATUT_REPONDUE)
        self.assertTrue(entree["le"])


class TestTempsDeReponseReel(unittest.TestCase):
    """Le système calcule le temps réel et le compare aux 24 h / 48 h."""

    def setUp(self):
        self.store = DemandStore(None)
        self.soumis = metier(2026, 1, 6, 10, 0)  # mardi 10h

    def repondre_le(self, repondu_le):
        dem_id = demande_soumise_le(self.store, self.soumis)
        return self.store.repondre(dem_id, MESSAGE, CONSEILLER, maintenant=repondu_le)

    def test_reponse_dans_les_24_heures(self):
        reponse = self.repondre_le(metier(2026, 1, 7, 10, 0))["reponse"]  # mercredi 10h
        self.assertEqual(reponse["delai_heures_ouvrees"], 9)
        self.assertEqual(reponse["delai_statut"], ECHEANCE_DANS_DELAI)

    def test_reponse_apres_24_heures_mais_avant_48_heures(self):
        reponse = self.repondre_le(metier(2026, 1, 8, 17, 0))["reponse"]  # jeudi 17h
        self.assertEqual(reponse["delai_heures_ouvrees"], 25)
        self.assertEqual(reponse["delai_statut"], ECHEANCE_APPROCHE)

    def test_reponse_apres_le_delai_maximal_de_48_heures(self):
        reponse = self.repondre_le(metier(2026, 1, 13, 14, 0))["reponse"]  # mardi suivant 14h
        self.assertEqual(reponse["delai_heures_ouvrees"], 49)
        self.assertEqual(reponse["delai_statut"], ECHEANCE_DEPASSEE)

    def test_les_nuits_et_le_weekend_ne_comptent_pas(self):
        # Demande du vendredi 17h, réponse du lundi 10h : 2 h ouvrées seulement.
        dem_id = demande_soumise_le(self.store, metier(2026, 1, 9, 17, 0))
        reponse = self.store.repondre(
            dem_id, MESSAGE, CONSEILLER, maintenant=metier(2026, 1, 12, 10, 0))["reponse"]
        self.assertEqual(reponse["delai_heures_ouvrees"], 2)
        self.assertEqual(reponse["delai_statut"], ECHEANCE_DANS_DELAI)

    def test_l_indicateur_d_echeance_reste_celui_du_moment_de_la_reponse(self):
        # Répondue à temps : des semaines plus tard, elle n'est pas « dépassée ».
        dem_id = demande_soumise_le(self.store, self.soumis)
        self.store.repondre(dem_id, MESSAGE, CONSEILLER, maintenant=metier(2026, 1, 7, 10, 0))
        self.assertEqual(self.store.obtenir(dem_id)["echeance_statut"], ECHEANCE_DANS_DELAI)
        liste = next(d for d in self.store.lister() if d["id"] == dem_id)
        self.assertEqual(liste["echeance_statut"], ECHEANCE_DANS_DELAI)

    def test_une_demande_sans_reponse_continue_de_deriver(self):
        dem_id = demande_soumise_le(self.store, self.soumis)  # mardi 10h de janvier
        self.assertEqual(self.store.obtenir(dem_id)["echeance_statut"], ECHEANCE_DEPASSEE)


class TestReponseRefusee(unittest.TestCase):
    """Une réponse invalide ne change rien à la demande."""

    def setUp(self):
        self.store = DemandStore(None)
        self.dem_id = demande_soumise_le(self.store, metier(2026, 1, 6, 10, 0))
        self.maintenant = metier(2026, 1, 7, 10, 0)

    def assert_intacte(self):
        record = self.store.obtenir(self.dem_id)
        self.assertEqual(record["statut"], STATUT_NOUVELLE)
        self.assertNotIn("reponse", record)

    def test_reponse_vide(self):
        for vide in (None, "", "   ", "\n\t", 42, ["texte"]):
            with self.assertRaises(ValidationError):
                self.store.repondre(self.dem_id, vide, CONSEILLER, maintenant=self.maintenant)
        self.assert_intacte()

    def test_reponse_trop_longue(self):
        with self.assertRaises(ValidationError):
            self.store.repondre(
                self.dem_id, "x" * (REPONSE_MAX_CARACTERES + 1), CONSEILLER,
                maintenant=self.maintenant)
        self.assert_intacte()

    def test_reponse_a_la_limite_acceptee(self):
        record = self.store.repondre(
            self.dem_id, "x" * REPONSE_MAX_CARACTERES, CONSEILLER, maintenant=self.maintenant)
        self.assertEqual(len(record["reponse"]["message"]), REPONSE_MAX_CARACTERES)

    def test_conseiller_obligatoire(self):
        for sans_nom in (None, "", "   "):
            with self.assertRaises(ValidationError):
                self.store.repondre(self.dem_id, MESSAGE, sans_nom, maintenant=self.maintenant)
        self.assert_intacte()

    def test_l_agent_ne_repond_pas_a_la_place_du_conseiller(self):
        for agent in ("agent", " Agent "):
            with self.assertRaises(ValidationError):
                self.store.repondre(self.dem_id, MESSAGE, agent, maintenant=self.maintenant)
        self.assert_intacte()

    def test_une_seule_reponse_par_demande(self):
        self.store.repondre(self.dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
        with self.assertRaisesRegex(ValidationError, "déjà reçu une réponse"):
            self.store.repondre(
                self.dem_id, "Autre réponse", "Bob", maintenant=metier(2026, 1, 8, 10, 0))
        reponse = self.store.obtenir(self.dem_id)["reponse"]
        self.assertEqual(reponse["message"], MESSAGE)
        self.assertEqual(reponse["par"], CONSEILLER)

    def test_pas_de_reponse_sur_une_demande_deja_traitee(self):
        for statut in (STATUT_PROPOSE, STATUT_VALIDE, STATUT_REFUSE):
            dem_id = demande_soumise_le(self.store, metier(2026, 1, 6, 10, 0))
            self.store.demandes[dem_id]["statut"] = statut
            with self.assertRaises(ValidationError):
                self.store.repondre(dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
            self.assertNotIn("reponse", self.store.obtenir(dem_id))
            self.assertEqual(self.store.obtenir(dem_id)["statut"], statut)

    def test_reponse_possible_depuis_a_analyser_et_a_revoir(self):
        for statut in (STATUT_A_ANALYSER, STATUT_A_REVOIR):
            dem_id = demande_soumise_le(self.store, metier(2026, 1, 6, 10, 0))
            self.store.demandes[dem_id]["statut"] = statut
            record = self.store.repondre(
                dem_id, MESSAGE, CONSEILLER, maintenant=self.maintenant)
            self.assertEqual(record["statut"], STATUT_REPONDUE)
            self.assertEqual(record["decisions"][-1]["avant"], statut)


class TestStatutRepondueProtege(unittest.TestCase):
    """« Répondue » ne s'obtient qu'en envoyant une vraie réponse."""

    def setUp(self):
        self.store = DemandStore(None)
        self.dem_id = demande_soumise_le(self.store, metier(2026, 1, 6, 10, 0))

    def test_changer_statut_vers_repondue_est_refuse(self):
        with self.assertRaisesRegex(ValidationError, "envoyant une réponse"):
            self.store.changer_statut(self.dem_id, STATUT_REPONDUE, CONSEILLER, "test")
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_NOUVELLE)

    def test_changement_automatique_vers_repondue_est_refuse(self):
        with self.assertRaises(ValidationError):
            self.store.changer_statut_automatique(self.dem_id, STATUT_REPONDUE)
        self.assertEqual(self.store.obtenir(self.dem_id)["statut"], STATUT_NOUVELLE)

    def test_apres_la_reponse_le_traitement_continue_et_la_reponse_reste(self):
        self.store.repondre(
            self.dem_id, MESSAGE, CONSEILLER, maintenant=metier(2026, 1, 7, 10, 0))
        record = self.store.changer_statut(
            self.dem_id, STATUT_A_ANALYSER, CONSEILLER, "analyse après réponse")
        self.assertEqual(record["statut"], STATUT_A_ANALYSER)
        self.assertEqual(record["reponse"]["message"], MESSAGE)
        # Une seule réponse même si le statut a changé depuis.
        with self.assertRaises(ValidationError):
            self.store.repondre(self.dem_id, "Encore", CONSEILLER)

    def test_les_statuts_existants_gardent_leurs_transitions(self):
        record = self.store.changer_statut(
            self.dem_id, STATUT_A_ANALYSER, CONSEILLER, "prise en charge")
        self.assertEqual(record["statut"], STATUT_A_ANALYSER)
        with self.assertRaises(ValidationError):
            self.store.changer_statut(self.dem_id, STATUT_NOUVELLE, CONSEILLER, "retour")

class TestRouteReponse(unittest.TestCase):
    """POST /api/demandes/{id}/reponse : l'API que l'interface conseiller appelle."""

    def setUp(self):
        self.store = DemandStore(None)
        self.users = UserStore(None)
        self.team_key = "cle-" + secrets.token_urlsafe(12)

        handler = make_handler(
            self.store,
            None,
            None,
            users=self.users,
            team_key=self.team_key,
            propositions=PropositionStore(None),
        )

        self.server, self.base = demarrer(handler)
        self.addCleanup(
            lambda: (self.server.shutdown(), self.server.server_close())
        )

        self.dem_id = self.store.creer(dict(VALIDE))["id"]
        self.url = f"/api/demandes/{self.dem_id}/reponse"

    def conseiller(self):
        client = ClientHTTP(self.base)
        status, _ = client.post(
            "/api/login-conseiller",
            {"cle": self.team_key},
        )
        self.assertEqual(status, 200)
        return client

    def test_le_conseiller_envoie_une_reponse(self):
        status, data = self.conseiller().post(
            self.url,
            {"message": MESSAGE},
        )

        self.assertEqual(status, 201)

        demande = data["demande"]
        self.assertEqual(demande["statut"], STATUT_REPONDUE)

        reponse = demande["reponse"]
        self.assertEqual(reponse["message"], MESSAGE)
        self.assertEqual(reponse["par"], "Conseiller DÉTOUR")
        self.assertTrue(datetime.fromisoformat(reponse["le"]).tzinfo)

        self.assertIn(
            reponse["delai_statut"],
            (
                ECHEANCE_DANS_DELAI,
                ECHEANCE_APPROCHE,
                ECHEANCE_DEPASSEE,
            ),
        )

        self.assertIsInstance(
            reponse["delai_heures_ouvrees"],
            (int, float),
        )

    def test_une_reponse_immediate_est_dans_le_delai(self):
        _, data = self.conseiller().post(
            self.url,
            {"message": MESSAGE},
        )

        self.assertEqual(
            data["demande"]["reponse"]["delai_statut"],
            ECHEANCE_DANS_DELAI,
        )
        self.assertLess(
            data["demande"]["reponse"]["delai_heures_ouvrees"],
            1,
        )
        self.assertEqual(
            data["demande"]["echeance_statut"],
            ECHEANCE_DANS_DELAI,
        )

    def test_l_auteur_et_la_date_viennent_du_serveur_pas_du_client(self):
        _, data = self.conseiller().post(
            self.url,
            {
                "message": MESSAGE,
                "par": "Quelqu'un d'autre",
                "le": "2020-01-01T00:00:00+00:00",
                "delai_statut": ECHEANCE_DEPASSEE,
            },
        )

        reponse = data["demande"]["reponse"]
        self.assertEqual(reponse["par"], "Conseiller DÉTOUR")
        self.assertNotEqual(
            reponse["le"],
            "2020-01-01T00:00:00+00:00",
        )
        self.assertEqual(
            reponse["delai_statut"],
            ECHEANCE_DANS_DELAI,
        )

    def test_sans_connexion_acces_refuse(self):
        status, _ = ClientHTTP(self.base).post(
            self.url,
            {"message": MESSAGE},
        )

        self.assertEqual(status, 401)
        self.assertNotIn(
            "reponse",
            self.store.obtenir(self.dem_id),
        )

    def test_un_voyageur_ne_peut_pas_repondre(self):
        voyageur = ClientHTTP(self.base)

        voyageur.post(
            "/api/register",
            {
                "email": "zoe@exemple.fr",
                "nom": "Zoé",
                "mot_de_passe": "motdepasse",
            },
        )

        status, _ = voyageur.post(
            self.url,
            {"message": MESSAGE},
        )

        self.assertEqual(status, 401)
        self.assertEqual(
            self.store.obtenir(self.dem_id)["statut"],
            STATUT_NOUVELLE,
        )

    def test_demande_inconnue(self):
        status, data = self.conseiller().post(
            "/api/demandes/dem_abcdef012345/reponse",
            {"message": MESSAGE},
        )

        self.assertEqual(status, 404)
        self.assertEqual(
            data["erreur"]["code"],
            "demande_not_found",
        )

    def test_reponse_vide_ou_absente_refusee(self):
        conseiller = self.conseiller()

        for corps in (
            {"message": ""},
            {"message": "   "},
            {"message": None},
            {"autre": 1},
        ):
            status, data = conseiller.post(self.url, corps)

            self.assertEqual(status, 400)
            self.assertEqual(
                data["erreur"]["code"],
                "validation_error",
            )

        self.assertEqual(
            self.store.obtenir(self.dem_id)["statut"],
            STATUT_NOUVELLE,
        )

    def test_reponse_trop_longue_refusee(self):
        status, _ = self.conseiller().post(
            self.url,
            {"message": "x" * (REPONSE_MAX_CARACTERES + 1)},
        )

        self.assertEqual(status, 400)

    def test_une_seule_reponse(self):
        conseiller = self.conseiller()

        self.assertEqual(
            conseiller.post(self.url, {"message": MESSAGE})[0],
            201,
        )

        status, data = conseiller.post(
            self.url,
            {"message": "Une autre"},
        )

        self.assertEqual(status, 400)
        self.assertIn(
            "déjà reçu une réponse",
            data["erreur"]["message"],
        )
        self.assertEqual(
            self.store.obtenir(self.dem_id)["reponse"]["message"],
            MESSAGE,
        )

    def test_le_menu_de_statut_ne_peut_pas_poser_repondue(self):
        status, data = self.conseiller().patch(
            f"/api/demandes/{self.dem_id}/statut",
            {"statut": STATUT_REPONDUE, "motif": "test"},
        )

        self.assertEqual(status, 400)
        self.assertIn(
            "envoyant une réponse",
            data["erreur"]["message"],
        )
        self.assertNotIn(
            "reponse",
            self.store.obtenir(self.dem_id),
        )

    def test_le_conseiller_voit_la_reponse_dans_la_file_et_le_detail(self):
        conseiller = self.conseiller()

        conseiller.post(
            self.url,
            {"message": MESSAGE},
        )

        _, liste = conseiller.get("/api/demandes")
        ligne = next(
            d for d in liste["demandes"]
            if d["id"] == self.dem_id
        )

        self.assertEqual(ligne["statut"], STATUT_REPONDUE)
        self.assertEqual(
            ligne["reponse"]["par"],
            "Conseiller DÉTOUR",
        )
        self.assertEqual(
            ligne["reponse"]["delai_statut"],
            ECHEANCE_DANS_DELAI,
        )

        _, detail = conseiller.get(
            f"/api/demandes/{self.dem_id}"
        )

        self.assertEqual(
            detail["demande"]["reponse"]["message"],
            MESSAGE,
        )

    def test_le_voyageur_proprietaire_lit_la_reponse_a_sa_demande(self):
        compte = self.users.creer(
            "zoe@exemple.fr",
            "Zoé",
            "motdepasse",
        )

        self.store.demandes[self.dem_id]["demande"]["user_id"] = compte["id"]

        self.conseiller().post(
            self.url,
            {"message": MESSAGE},
        )

        voyageur = ClientHTTP(self.base)

        voyageur.post(
            "/api/login",
            {
                "email": "zoe@exemple.fr",
                "mot_de_passe": "motdepasse",
            },
        )

        status, detail = voyageur.get(
            f"/api/demandes/{self.dem_id}"
        )

        self.assertEqual(status, 200)
        self.assertEqual(
            detail["demande"]["statut"],
            STATUT_REPONDUE,
        )
        self.assertEqual(
            detail["demande"]["reponse"]["message"],
            MESSAGE,
        )

    def test_mode_developpement_sans_comptes(self):
        # users=None : aucune authentification, le conseiller par défaut signe la réponse.
        handler = make_handler(
            self.store,
            None,
            None,
            users=None,
            propositions=PropositionStore(None),
        )

        server, base = demarrer(handler)

        self.addCleanup(
            lambda: (server.shutdown(), server.server_close())
        )

        status, data = ClientHTTP(base).post(
            self.url,
            {"message": MESSAGE},
        )

        self.assertEqual(status, 201)
        self.assertEqual(
            data["demande"]["reponse"]["par"],
            "Conseiller DÉTOUR",
        )


class TestPersistanceReponse(unittest.TestCase):
    def test_la_reponse_survit_au_redemarrage(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = Path(tmp) / "demandes.json"
            store = DemandStore(chemin)
            dem_id = demande_soumise_le(store, metier(2026, 1, 6, 10, 0))
            store.repondre(dem_id, MESSAGE, CONSEILLER, maintenant=metier(2026, 1, 7, 10, 0))

            relu = DemandStore(chemin).obtenir(dem_id)
            self.assertEqual(relu["statut"], STATUT_REPONDUE)
            self.assertEqual(relu["reponse"]["par"], CONSEILLER)
            self.assertEqual(relu["reponse"]["delai_heures_ouvrees"], 9)
            self.assertEqual(relu["reponse"]["delai_statut"], ECHEANCE_DANS_DELAI)


if __name__ == "__main__":
    unittest.main()
