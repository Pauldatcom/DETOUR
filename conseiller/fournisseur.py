"""Client du serveur de prestations fictives.

La clé d'équipe reste dans ce module (côté serveur de l'application) : elle n'est
ni renvoyée au navigateur, ni écrite dans les journaux ou les recherches stockées.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from utils import DEFAULT_URL, SOURCE_LABEL


class SupplierError(Exception):
    """Le fournisseur est injoignable ou a répondu par une erreur."""

    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


class SupplierClient:
    def __init__(self, base_url=DEFAULT_URL, team_key="", timeout=5):
        self.base_url = base_url.rstrip("/")
        self._team_key = team_key
        self.timeout = timeout

    def rechercher(self, criteres):
        """Appelle GET /api/v1/recherche. Ne simule jamais un résultat en cas d'échec."""
        if not self._team_key:
            raise SupplierError("Clé d'équipe absente : définir TRAVEL_TEAM_KEY.", 503)
        params = {
            "destination": criteres["destination"],
            "date_depart": criteres["date_depart"],
            "date_retour": criteres["date_retour"],
            "participants": criteres["participants"],
            "budget_max": criteres["budget_max"],
            "type_voyage": criteres["type_voyage"],
        }
        if criteres.get("activites"):
            params["activites"] = ",".join(criteres["activites"])
        url = f"{self.base_url}/api/v1/recherche?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"X-Team-Key": self._team_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as err:
            try:
                detail = json.loads(err.read())["erreur"]["message"]
            except Exception:
                detail = f"HTTP {err.code}"
            raise SupplierError(f"Le serveur fictif a refusé la recherche : {detail}") from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise SupplierError(
                f"Serveur fictif injoignable ({self.base_url}). Lancez : python3 server/app.py --demo"
            ) from err
        except json.JSONDecodeError as err:
            raise SupplierError("Réponse illisible du serveur fictif.") from err
        payload["source_url"] = f"{self.base_url}/api/v1/recherche"
        payload["source_label"] = SOURCE_LABEL
        return payload

    def catalogue(self):
        """Appelle GET /api/v1/catalogue. Retourne la liste des prestations (lecture seule)."""
        if not self._team_key:
            raise SupplierError("Clé d'équipe absente : définir TRAVEL_TEAM_KEY.", 503)
        url = f"{self.base_url}/api/v1/catalogue"
        request = urllib.request.Request(url, headers={"X-Team-Key": self._team_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as err:
            try:
                detail = json.loads(err.read())["erreur"]["message"]
            except Exception:
                detail = f"HTTP {err.code}"
            raise SupplierError(f"Le serveur fictif a refusé le catalogue : {detail}") from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise SupplierError(
                f"Serveur fictif injoignable ({self.base_url}). Lancez : python3 server/app.py --demo"
            ) from err
        except json.JSONDecodeError as err:
            raise SupplierError("Réponse illisible du serveur fictif.") from err
        return payload.get("prestations", [])
