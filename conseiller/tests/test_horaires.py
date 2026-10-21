#!/usr/bin/env python3
"""Tests for the advisor working-hours configuration and response deadlines (#48, #51, #53)."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import horaires
from horaires import (
    DELAI_CIBLE_HEURES_OUVREES,
    DELAI_MAX_HEURES_OUVREES,
    ECHEANCE_APPROCHE,
    ECHEANCE_DANS_DELAI,
    ECHEANCE_DEPASSEE,
    FUSEAU_METIER,
    HEURE_FERMETURE,
    HEURE_OUVERTURE,
    JOURS_OUVRES,
    avancer_heures_ouvrees,
    est_ouvert,
    echeance_reponse,
    fenetre_reponse,
    fuseau_metier,
    marquer_echeances,
    prochaine_ouverture,
    vers_metier,
)


def metier(*args):
    """Build a datetime in the business timezone (Europe/Paris)."""
    return datetime(*args, tzinfo=fuseau_metier())


class TestConfiguration(unittest.TestCase):
    """The working-hours configuration lives in one place (#48)."""

    def test_jours_ouvres_lundi_a_vendredi(self):
        self.assertEqual(JOURS_OUVRES, frozenset({0, 1, 2, 3, 4}))

    def test_heures_d_ouverture(self):
        self.assertEqual(HEURE_OUVERTURE, metier(2026, 1, 5, 9).time().replace(tzinfo=None))
        self.assertEqual(HEURE_FERMETURE, metier(2026, 1, 5, 18).time().replace(tzinfo=None))

    def test_fuseau_metier_defini(self):
        self.assertEqual(FUSEAU_METIER, "Europe/Paris")
        self.assertEqual(str(fuseau_metier()), FUSEAU_METIER)

    def test_delais_de_reponse(self):
        self.assertEqual(DELAI_CIBLE_HEURES_OUVREES, 24)
        self.assertEqual(DELAI_MAX_HEURES_OUVREES, 48)


class TestVersMetier(unittest.TestCase):
    def test_naif_assume_utc(self):
        naive = datetime(2026, 1, 5, 12, 0)
        converti = vers_metier(naive)
        self.assertEqual(converti.utcoffset(), fuseau_metier().utcoffset(converti))

    def test_aware_conserve_l_instant(self):
        utc = datetime(2026, 1, 5, 11, 0, tzinfo=timezone.utc)
        self.assertEqual(vers_metier(utc).timestamp(), utc.timestamp())

    def test_non_datetime_refuse(self):
        with self.assertRaises(ValueError):
            vers_metier("2026-01-05T12:00:00")


class TestEstOuvert(unittest.TestCase):
    """The application can determine whether the service is open or closed (#48)."""

    def test_ouvert_en_semaine(self):
        self.assertTrue(est_ouvert(metier(2026, 1, 5, 10, 0)))   # lundi 10h
        self.assertTrue(est_ouvert(metier(2026, 1, 9, 17, 59)))  # vendredi 17h59

    def test_ferme_avant_ouverture(self):
        self.assertFalse(est_ouvert(metier(2026, 1, 5, 8, 59)))

    def test_ouvert_des_9h(self):
        self.assertTrue(est_ouvert(metier(2026, 1, 5, 9, 0)))

    def test_ferme_apres_fermeture(self):
        self.assertFalse(est_ouvert(metier(2026, 1, 5, 18, 0)))
        self.assertFalse(est_ouvert(metier(2026, 1, 5, 20, 0)))

    def test_weekend_non_ouvrable(self):
        self.assertFalse(est_ouvert(metier(2026, 1, 10, 12, 0)))  # samedi
        self.assertFalse(est_ouvert(metier(2026, 1, 11, 12, 0)))  # dimanche

    def test_sans_argument_renvoie_un_bool(self):
        self.assertIsInstance(est_ouvert(), bool)


class TestProchaineOuverture(unittest.TestCase):
    def test_pendant_l_ouverture_renvoie_le_meme_instant(self):
        moment = metier(2026, 1, 5, 14, 30)
        self.assertEqual(prochaine_ouverture(moment), moment)

    def test_avant_ouverture_le_meme_jour(self):
        moment = metier(2026, 1, 5, 7, 30)  # lundi 7h30
        attendu = metier(2026, 1, 5, 9, 0)
        self.assertEqual(prochaine_ouverture(moment), attendu)

    def test_apres_fermeture_le_jour_suivant(self):
        moment = metier(2026, 1, 6, 20, 0)  # mardi 20h
        attendu = metier(2026, 1, 7, 9, 0)
        self.assertEqual(prochaine_ouverture(moment), attendu)

    def test_vendredi_soir_saute_le_weekend(self):
        moment = metier(2026, 1, 9, 18, 30)  # vendredi 18h30
        attendu = metier(2026, 1, 12, 9, 0)  # lundi 9h
        self.assertEqual(prochaine_ouverture(moment), attendu)

    def test_samedi_renvoie_lundi(self):
        moment = metier(2026, 1, 10, 10, 0)  # samedi
        attendu = metier(2026, 1, 12, 9, 0)
        self.assertEqual(prochaine_ouverture(moment), attendu)

    def test_dimanche_soir_renvoie_lundi(self):
        moment = metier(2026, 1, 11, 23, 0)  # dimanche
        attendu = metier(2026, 1, 12, 9, 0)
        self.assertEqual(prochaine_ouverture(moment), attendu)


class TestAvancerHeuresOuvrees(unittest.TestCase):
    def test_saut_par_dessus_la_nuit(self):
        # Mardi 16h + 4h ouvrées = mercredi 11h (2h mardi, 2h mercredi).
        depart = metier(2026, 1, 6, 16, 0)
        attendu = metier(2026, 1, 7, 11, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 4), attendu)

    def test_hors_ouverture_le_compte_demarre_a_l_ouverture(self):
        # Lundi 7h + 1h ouvrée = lundi 10h (le compte démarre à 9h).
        depart = metier(2026, 1, 5, 7, 0)
        attendu = metier(2026, 1, 5, 10, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 1), attendu)

    def test_weekend_non_compte(self):
        # Samedi 10h + 1h ouvrée = lundi 10h.
        depart = metier(2026, 1, 10, 10, 0)
        attendu = metier(2026, 1, 12, 10, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 1), attendu)

    def test_vendredi_soir_le_compte_reprend_lundi(self):
        # Vendredi 17h + 2h ouvrées = lundi 10h (1h vendredi, 1h lundi).
        depart = metier(2026, 1, 9, 17, 0)
        attendu = metier(2026, 1, 12, 10, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 2), attendu)

    def test_echeance_exacte_a_la_fermeture(self):
        # Mardi 9h + 9h ouvrées = mardi 18h (fin de journée).
        depart = metier(2026, 1, 6, 9, 0)
        attendu = metier(2026, 1, 6, 18, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 9), attendu)

    def test_24_heures_ouvrees_depuis_mardi_10h(self):
        # Mardi 10h : 8h restantes mardi, 9h mercredi, 7h jeudi -> jeudi 16h.
        depart = metier(2026, 1, 6, 10, 0)
        attendu = metier(2026, 1, 8, 16, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 24), attendu)

    def test_48_heures_ouvrees_depuis_mardi_10h(self):
        # Mardi 10h : 8h + 9h (mer) + 9h (jeu) + 9h (ven) = 35h ; reste 13h.
        # Lundi 9h : 9h ; reste 4h -> mardi 13h la semaine suivante.
        depart = metier(2026, 1, 6, 10, 0)
        attendu = metier(2026, 1, 13, 13, 0)
        self.assertEqual(avancer_heures_ouvrees(depart, 48), attendu)

    def test_heures_invalides_refusees(self):
        depart = metier(2026, 1, 6, 10, 0)
        with self.assertRaises(ValueError):
            avancer_heures_ouvrees(depart, 0)
        with self.assertRaises(ValueError):
            avancer_heures_ouvrees(depart, -5)


class TestEcheanceReponse(unittest.TestCase):
    def test_defaut_24_heures_ouvrees(self):
        depart = metier(2026, 1, 6, 10, 0)
        self.assertEqual(echeance_reponse(depart),
                         avancer_heures_ouvrees(depart, DELAI_CIBLE_HEURES_OUVREES))

    def test_heures_personnalisees(self):
        depart = metier(2026, 1, 6, 10, 0)
        self.assertEqual(echeance_reponse(depart, 2),
                         avancer_heures_ouvrees(depart, 2))


class TestFenetreReponse(unittest.TestCase):
    """The chatbot communicates the expected response window (#53)."""

    def test_pendant_l_ouverture(self):
        fenetre = fenetre_reponse(metier(2026, 1, 5, 10, 0))
        self.assertTrue(fenetre["ouvert"])
        self.assertIn("peut être traitée", fenetre["message"])
        self.assertNotIn("ferm", fenetre["message"])

    def test_hors_ouverture_pas_de_reponse_immediate(self):
        fenetre = fenetre_reponse(metier(2026, 1, 10, 15, 0))  # samedi
        self.assertFalse(fenetre["ouvert"])
        self.assertIn("fermé", fenetre["message"])
        self.assertIn("prochaine période d'ouverture", fenetre["message"])
        self.assertNotIn("immédiat", fenetre["message"])

    def test_prochaine_ouverture_communiquee(self):
        fenetre = fenetre_reponse(metier(2026, 1, 10, 15, 0))  # samedi
        self.assertEqual(fenetre["prochaine_ouverture"],
                         metier(2026, 1, 12, 9, 0).isoformat())

    def test_fenetres_d_echeance_presentes(self):
        fenetre = fenetre_reponse(metier(2026, 1, 5, 10, 0))
        self.assertEqual(fenetre["echeance_cible"],
                         avancer_heures_ouvrees(metier(2026, 1, 5, 10, 0), 24).isoformat())
        self.assertEqual(fenetre["echeance_max"],
                         avancer_heures_ouvrees(metier(2026, 1, 5, 10, 0), 48).isoformat())

    def test_promesse_delai_mentionne_les_horaires(self):
        fenetre = fenetre_reponse(metier(2026, 1, 5, 10, 0))
        self.assertIn("lundi", fenetre["promesse_delai"])
        self.assertIn("vendredi", fenetre["promesse_delai"])
        self.assertIn("09:00", fenetre["promesse_delai"])
        self.assertIn("18:00", fenetre["promesse_delai"])
        self.assertIn("24 h ouvrées", fenetre["promesse_delai"])
        self.assertIn(str(DELAI_MAX_HEURES_OUVREES), fenetre["promesse_delai"])


class TestMarquerEcheances(unittest.TestCase):
    def test_record_sans_date_reste_inchange(self):
        self.assertEqual(marquer_echeances({}), {})
        self.assertEqual(marquer_echeances({"cree_le": "pas une date"}),
                         {"cree_le": "pas une date"})
        self.assertEqual(marquer_echeances(None), None)

    def test_demande_recente_dans_delai(self):
        # Soumis mardi 10h, on regarde mercredi 10h : 9h ouvrées écoulées (< 24h).
        record = {"cree_le": metier(2026, 1, 6, 10, 0).isoformat()}
        marque = marquer_echeances(record, maintenant=metier(2026, 1, 7, 10, 0))
        self.assertEqual(marque["echeance_statut"], ECHEANCE_DANS_DELAI)
        self.assertEqual(marque["echeance_cible"],
                         avancer_heures_ouvrees(metier(2026, 1, 6, 10, 0), 24).isoformat())
        self.assertEqual(marque["echeance_max"],
                         avancer_heures_ouvrees(metier(2026, 1, 6, 10, 0), 48).isoformat())

    def test_cible_depassee_marquee_approche(self):
        # Soumis mardi 10h, on regarde jeudi 17h : 25h ouvrées écoulées (> 24h, < 48h).
        record = {"cree_le": metier(2026, 1, 6, 10, 0).isoformat()}
        marque = marquer_echeances(record, maintenant=metier(2026, 1, 8, 17, 0))
        self.assertEqual(marque["echeance_statut"], ECHEANCE_APPROCHE)

    def test_maximum_depasse_marquee_depassee(self):
        # Soumis mardi 10h, on regarde mardi suivant 14h : 49h ouvrées écoulées (> 48h).
        record = {"cree_le": metier(2026, 1, 6, 10, 0).isoformat()}
        marque = marquer_echeances(record, maintenant=metier(2026, 1, 13, 14, 0))
        self.assertEqual(marque["echeance_statut"], ECHEANCE_DEPASSEE)

    def test_exactement_a_la_cible_marquee_approche(self):
        # La cible est atteinte (24h ouvrées) : on considère l'échéance comme « approche ».
        record = {"cree_le": metier(2026, 1, 6, 10, 0).isoformat()}
        marque = marquer_echeances(record, maintenant=metier(2026, 1, 8, 16, 0))
        self.assertEqual(marque["echeance_statut"], ECHEANCE_APPROCHE)

    def test_ne_modifie_pas_les_autres_champs(self):
        record = {"id": "dem_1", "cree_le": metier(2026, 1, 6, 10, 0).isoformat(),
                  "statut": "a_analyser"}
        marque = marquer_echeances(record, maintenant=metier(2026, 1, 7, 10, 0))
        self.assertEqual(marque["id"], "dem_1")
        self.assertEqual(marque["statut"], "a_analyser")


class TestSoumissionHorsHoraires(unittest.TestCase):
    """#49: a request can be submitted when the service is closed."""

    def test_fenetre_samedi_ne_promet_pas_une_reponse_immediate(self):
        fenetre = fenetre_reponse(metier(2026, 1, 10, 15, 0))  # saturday
        self.assertFalse(fenetre["ouvert"])
        self.assertFalse(est_ouvert(metier(2026, 1, 10, 15, 0)))
        self.assertIn("fermé", fenetre["message"])

    def test_creation_reste_nouvelle_avec_horodatage(self):
        from store import DemandStore
        from test_conseiller import VALIDE

        record = DemandStore(None).creer(dict(VALIDE))
        self.assertEqual(record["statut"], "nouvelle")
        self.assertTrue(record["cree_le"])
        # Closed hours must not block persistence (no gate in creer).
        self.assertTrue(record["id"].startswith("dem_"))


if __name__ == "__main__":
    unittest.main()
