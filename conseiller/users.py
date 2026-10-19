"""Comptes utilisateurs de l'application conseiller DÉTOUR.

Les mots de passe sont hachés avec PBKDF2-HMAC-SHA256 (stdlib) et un sel
aléatoire par compte. Ils ne sont jamais stockés ni journalisés en clair.
"""

import hashlib
import json
import re
import secrets
import threading
from pathlib import Path

from utils import EMAIL_RE, ITERATIONS, USER_ID_PREFIX


class UserError(ValueError):
    """Erreur de validation ou d'authentification d'un compte."""

    def __init__(self, message, status=400, code="user_error"):
        super().__init__(message)
        self.status = status
        self.code = code


class UserStore:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.lock = threading.RLock()
        self.users = {}
        if self.path and self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.users = data.get("users", {})
            except (json.JSONDecodeError, OSError):
                self.users = {}

    def save(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"users": self.users}, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        tmp.replace(self.path)

    @staticmethod
    def _hasher(mot_de_passe, sel):
        return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"),
                                   bytes.fromhex(sel), ITERATIONS).hex()

    @staticmethod
    def _valider_identifiants(email, mot_de_passe):
        email = (email or "").strip().lower()
        if not EMAIL_RE.fullmatch(email):
            raise UserError("Adresse e-mail invalide.", 400, "email_invalide")
        if not isinstance(mot_de_passe, str) or len(mot_de_passe) < 6:
            raise UserError("Le mot de passe doit contenir au moins 6 caractères.",
                            400, "mot_de_passe_trop_court")
        return email

    def creer(self, email, nom, mot_de_passe):
        """Crée un compte voyageur. Lève UserError si e-mail déjà utilisé."""
        email = self._valider_identifiants(email, mot_de_passe)
        nom = (nom or "").strip() or email.split("@", 1)[0]
        with self.lock:
            if email in {u.get("email", "").lower() for u in self.users.values()}:
                raise UserError("Un compte existe déjà avec cette adresse e-mail.",
                                409, "compte_existant")
            user_id = USER_ID_PREFIX + secrets.token_hex(6)
            sel = secrets.token_hex(16)
            self.users[user_id] = {
                "id": user_id,
                "email": email,
                "nom": nom,
                "sel": sel,
                "hash": self._hasher(mot_de_passe, sel),
            }
            self.save()
            return {"id": user_id, "email": email, "nom": nom}

    def authentifier(self, email, mot_de_passe):
        """Retourne le compte si les identifiants correspondent, sinon None.

        Lève UserError si le mot de passe est vide (jamais de devinette)."""
        if not isinstance(mot_de_passe, str) or not mot_de_passe:
            raise UserError("Mot de passe requis.", 400, "mot_de_passe_requis")
        email = (email or "").strip().lower()
        with self.lock:
            compte = next((u for u in self.users.values()
                           if u.get("email", "").lower() == email), None)
        if compte is None:
            return None
        attendu = compte["hash"]
        sel = compte["sel"]
        if secrets.compare_digest(self._hasher(mot_de_passe, sel), attendu):
            return {"id": compte["id"], "email": compte["email"], "nom": compte["nom"]}
        return None

    def obtenir(self, user_id):
        with self.lock:
            compte = self.users.get(user_id)
            if not compte:
                return None
            return {"id": compte["id"], "email": compte["email"], "nom": compte["nom"]}