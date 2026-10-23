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
    """Le fournisseur est injoignable ou a répondu par une erreur.

    #6: `status` carries the HTTP code (or 502/503 when the server is down /
    misconfigured) so the agent can tell auth, not-found, conflict and
    unreachable apart.
    """

    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def _detail_http(err):
    try:
        return json.loads(err.read())["erreur"]["message"]
    except Exception:
        return f"HTTP {err.code}"


def erreur_depuis_http(action, err):
    """Map a fictional-server HTTPError to a typed SupplierError (#6)."""
    detail = _detail_http(err)
    code = err.code
    if code in (401, 403):
        return SupplierError(
            f"Authentification ou permission refusée auprès du serveur fictif "
            f"({action}) : {detail}",
            status=code,
        )
    if code == 404:
        return SupplierError(
            f"Prestation ou ressource introuvable sur le serveur fictif "
            f"({action}) : {detail}",
            status=404,
        )
    if code == 409:
        return SupplierError(
            f"Prestation indisponible ou inutilisable sur le serveur fictif "
            f"({action}) : {detail}",
            status=409,
        )
    return SupplierError(
        f"Le serveur fictif a refusé {action} : {detail}",
        status=code if isinstance(code, int) else 502,
    )


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
        # Optional criteria left empty by the advisor search are not sent (#115).
        params = {k: v for k, v in params.items() if v is not None}
        if criteres.get("activites"):
            params["activites"] = ",".join(criteres["activites"])
        url = f"{self.base_url}/api/v1/recherche?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"X-Team-Key": self._team_key})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as err:
            raise erreur_depuis_http("la recherche", err) from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise SupplierError(
                f"Serveur fictif injoignable ({self.base_url}). Lancez : python3 server/app.py --demo",
                status=502,
            ) from err
        except json.JSONDecodeError as err:
            raise SupplierError("Réponse illisible du serveur fictif.", status=502) from err
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
            raise erreur_depuis_http("le catalogue", err) from err
        except (urllib.error.URLError, TimeoutError, OSError) as err:
            raise SupplierError(
                f"Serveur fictif injoignable ({self.base_url}). Lancez : python3 server/app.py --demo",
                status=502,
            ) from err
        except json.JSONDecodeError as err:
            raise SupplierError("Réponse illisible du serveur fictif.", status=502) from err
        return payload.get("prestations", [])
