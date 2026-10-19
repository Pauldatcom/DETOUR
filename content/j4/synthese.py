#!/usr/bin/env python3
"""Compte les verdicts d'une campagne; ne juge ni traces, ni effets, ni sécurité."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

MODES = ("unitaire", "integration_http", "rejeu", "agent_direct")
FAMILIES = ("nominal", "ambigu", "erreur", "adversarial")


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def load_report(cases_path, results_path):
    manifest = json.loads(Path(cases_path).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not nonempty_string(manifest.get("version")):
        raise ValueError("Version non vide du jeu requise.")
    cases = manifest.get("cas")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Le jeu doit contenir une liste de cas non vide.")
    planned = {}
    for case in cases:
        if not isinstance(case, dict) or not nonempty_string(case.get("id")):
            raise ValueError("Chaque cas doit porter un identifiant non vide.")
        if case["id"] in planned:
            raise ValueError("Les identifiants du jeu doivent être uniques.")
        if case.get("famille") not in FAMILIES:
            raise ValueError(f"{case['id']}: famille invalide.")
        count = case.get("essais_prevus", 1)
        if type(count) is not int or count < 1:
            raise ValueError(f"{case['id']}: essais_prevus doit être un entier positif.")
        if case.get("mode_prevu") not in MODES:
            raise ValueError(f"{case['id']}: mode_prevu requis et valide.")
        planned[case["id"]] = {"case": case, "count": count}

    results = {}
    campaign = programme_version = None
    for line_no, line in enumerate(Path(results_path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"Ligne {line_no}: objet JSON requis.")
        case_id = row.get("cas_id")
        if not nonempty_string(case_id) or case_id not in planned:
            raise ValueError(f"Ligne {line_no}: cas inconnu.")
        for field in ("campagne", "version_programme", "jeu_version"):
            if not nonempty_string(row.get(field)):
                raise ValueError(f"Ligne {line_no}: {field} non vide requis.")
        if row["jeu_version"] != manifest["version"]:
            raise ValueError(f"Ligne {line_no}: version du jeu différente du manifeste.")
        if campaign is None:
            campaign, programme_version = row["campagne"], row["version_programme"]
        if row["campagne"] != campaign or row["version_programme"] != programme_version:
            raise ValueError(f"Ligne {line_no}: campagnes ou versions de programme mélangées; séparer les fichiers.")
        attempt = row.get("essai")
        if type(attempt) is not int or not 1 <= attempt <= planned[case_id]["count"]:
            raise ValueError(f"Ligne {line_no}: essai hors du manifeste 1..essais_prevus.")
        key = (case_id, attempt)
        if key in results:
            raise ValueError(f"Ligne {line_no}: essai dupliqué.")
        if row.get("verdict") not in ("reussite", "echec", "non_execute"):
            raise ValueError(f"Ligne {line_no}: verdict invalide.")
        if row.get("mode") != planned[case_id]["case"]["mode_prevu"]:
            raise ValueError(f"Ligne {line_no}: mode incompatible avec le cas prévu; un rejeu ne remplace pas un essai direct.")
        for field in ("violation_executee", "tentative_bloquee"):
            if type(row.get(field)) is not bool:
                raise ValueError(f"Ligne {line_no}: {field} booléen requis.")
        if row["verdict"] == "non_execute" and (row["violation_executee"] or row["tentative_bloquee"]):
            raise ValueError(f"Ligne {line_no}: effet impossible sur un essai non exécuté.")
        if row["verdict"] == "reussite" and row["violation_executee"]:
            raise ValueError(f"Ligne {line_no}: une violation exécutée ne peut être une réussite.")
        results[key] = row

    by_family = defaultdict(lambda: {"cas_prevus": 0, "cas_executes": 0, "cas_reussis_tous_essais_prevus": 0, "cas_incomplets": 0})
    by_mode = defaultdict(lambda: {"essais_prevus": 0, "essais_executes": 0, "essais_reussis": 0, "essais_non_executes": 0, "essais_absents": 0})
    successful_cases = executed_cases = violations = blocked = success_attempts = executed_attempts = expected_attempts = 0
    missing_cases, missing_attempts = [], []
    for case in cases:
        case_id, count, mode = case["id"], planned[case["id"]]["count"], case["mode_prevu"]
        rows = [results.get((case_id, attempt)) for attempt in range(1, count + 1)]
        executions = [row for row in rows if row and row["verdict"] != "non_execute"]
        family = by_family[case["famille"]]
        family["cas_prevus"] += 1
        expected_attempts += count
        by_mode[mode]["essais_prevus"] += count
        if executions:
            executed_cases += 1
            family["cas_executes"] += 1
        if any(row is None or row["verdict"] == "non_execute" for row in rows):
            missing_cases.append(case_id)
            family["cas_incomplets"] += 1
        if all(row and row["verdict"] == "reussite" for row in rows):
            successful_cases += 1
            family["cas_reussis_tous_essais_prevus"] += 1
        for attempt, row in enumerate(rows, 1):
            if row is None or row["verdict"] == "non_execute":
                status = "absent" if row is None else "non_execute"
                missing_attempts.append({"cas_id": case_id, "essai": attempt, "mode_prevu": mode, "statut": status})
                by_mode[mode]["essais_absents" if row is None else "essais_non_executes"] += 1
                continue
            executed_attempts += 1
            success_attempts += row["verdict"] == "reussite"
            violations += row["violation_executee"]
            blocked += row["tentative_bloquee"]
            by_mode[mode]["essais_executes"] += 1
            by_mode[mode]["essais_reussis"] += row["verdict"] == "reussite"
    return {
        "portee": "Verdicts humains déclarés pour un manifeste et une version; preuves non vérifiées par cet outil.",
        "campagne": campaign,
        "version_programme": programme_version,
        "jeu_version": manifest["version"],
        "regle_reussite_cas": "Tous les essais prévus de ce cas sont présents et déclarés réussis.",
        "cas_prevus": len(cases),
        "cas_executes_au_moins_une_fois": executed_cases,
        "cas_reussis_sur_tous_essais_prevus": successful_cases,
        "cas_avec_essai_manquant_ou_absents": missing_cases,
        "essais_manquants": missing_attempts,
        "taux_cas_prevus": f"{successful_cases}/{len(cases)}",
        "taux_cas_executes": f"{successful_cases}/{executed_cases}" if executed_cases else "non calculable",
        "essais_prevus": expected_attempts,
        "essais_executes": executed_attempts,
        "essais_reussis": success_attempts,
        "taux_essais_prevus": f"{success_attempts}/{expected_attempts}",
        "taux_essais_executes": f"{success_attempts}/{executed_attempts}" if executed_attempts else "non calculable",
        "violations_executees_declarees": violations,
        "tentatives_bloquees_declarees": blocked,
        "par_famille": dict(by_family),
        "par_mode": dict(by_mode),
        "decision_usage": "À prendre par une personne, après lecture des preuves, des essais manquants et des limites.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jeu", help="Manifeste JSON figé avec essais_prevus et mode_prevu par cas")
    parser.add_argument("resultats", help="JSONL d'une seule campagne et version de programme")
    args = parser.parse_args()
    try:
        print(json.dumps(load_report(args.jeu, args.resultats), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Entrée invalide : {exc}\n")


if __name__ == "__main__":
    main()
