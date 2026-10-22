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

    def _trouver_par_email(self, email):
        email = (email or "").strip().lower()
        with self.lock:
            return next((u for u in self.users.values()
                         if u.get("email", "").lower() == email), None)

    def trouver_par_google_sub(self, google_sub):
        """Return the account linked to this Google sub, else None."""
        with self.lock:
            return next((u for u in self.users.values()
                         if u.get("google_sub") == google_sub), None)

    def creer_ou_lier_google(self, email, nom, google_sub):
        """Create a traveler account linked to Google, or link an existing one.

        If the e-mail already exists, the google_sub is added to that account.
        """
        email = (email or "").strip().lower()
        if not EMAIL_RE.fullmatch(email):
            raise UserError("Adresse e-mail Google invalide.", 400, "email_invalide")
        if not isinstance(google_sub, str) or not google_sub.strip():
            raise UserError("google_sub requis.", 400, "google_sub_requis")
        nom = (nom or "").strip() or email.split("@", 1)[0]
        with self.lock:
            existant = self._trouver_par_email(email)
            if existant:
                existant["google_sub"] = google_sub
                self.save()
                return {"id": existant["id"], "email": existant["email"],
                        "nom": existant["nom"]}
            deja_lier = self.trouver_par_google_sub(google_sub)
            if deja_lier:
                return {"id": deja_lier["id"], "email": deja_lier["email"],
                        "nom": deja_lier["nom"]}
            user_id = USER_ID_PREFIX + secrets.token_hex(6)
            self.users[user_id] = {
                "id": user_id,
                "email": email,
                "nom": nom,
                "google_sub": google_sub,
                "sel": "",
                "hash": "",
            }
            self.save()
            return {"id": user_id, "email": email, "nom": nom}

    def obtenir(self, user_id):
        with self.lock:
            compte = self.users.get(user_id)
            if not compte:
                return None
            return {"id": compte["id"], "email": compte["email"], "nom": compte["nom"]}

    def mettre_a_jour_profil(self, user_id, email, nom):
        email = email.strip().lower() if isinstance(email, str) else ""
        nom = nom.strip() if isinstance(nom, str) else ""
        if not EMAIL_RE.fullmatch(email):
            raise UserError("Adresse e-mail invalide.", 400, "email_invalide")
        if not nom:
            raise UserError("Le nom est obligatoire.", 400, "nom_requis")
        if len(nom) > 120:
            raise UserError("Le nom ne peut pas dépasser 120 caractères.", 400, "nom_trop_long")

        with self.lock:
            compte = self.users.get(user_id)
            if not compte:
                raise UserError("Compte introuvable.", 404, "compte_introuvable")
            email_utilise = any(
                identifiant != user_id and utilisateur.get("email", "").lower() == email
                for identifiant, utilisateur in self.users.items()
            )
            if email_utilise:
                raise UserError("Un compte existe déjà avec cette adresse e-mail.",
                                409, "compte_existant")
            compte["email"] = email
            compte["nom"] = nom
            self.save()
            return {"id": compte["id"], "email": compte["email"], "nom": compte["nom"]}

    def mot_de_passe_defini(self, user_id):
        with self.lock:
            compte = self.users.get(user_id)
            return bool(compte and compte.get("hash"))

    def verifier_mot_de_passe(self, user_id, mot_de_passe):
        with self.lock:
            compte = self.users.get(user_id)
            if not compte:
                return False
            hash_actuel = compte.get("hash", "")
            if not hash_actuel:
                return True
            if not isinstance(mot_de_passe, str) or not mot_de_passe:
                return False
            return secrets.compare_digest(self._hasher(mot_de_passe, compte["sel"]), hash_actuel)

    def changer_mot_de_passe(self, user_id, mot_de_passe_actuel, nouveau_mot_de_passe):
        if not isinstance(nouveau_mot_de_passe, str) or len(nouveau_mot_de_passe) < 6:
            raise UserError("Le mot de passe doit contenir au moins 6 caractères.",
                            400, "mot_de_passe_trop_court")
        if len(nouveau_mot_de_passe) > 1024:
            raise UserError("Le mot de passe est trop long.", 400, "mot_de_passe_trop_long")

        with self.lock:
            compte = self.users.get(user_id)
            if not compte:
                raise UserError("Compte introuvable.", 404, "compte_introuvable")
            hash_actuel = compte.get("hash", "")
            if hash_actuel:
                if not isinstance(mot_de_passe_actuel, str) or not mot_de_passe_actuel:
                    raise UserError("Mot de passe actuel requis.", 400, "mot_de_passe_actuel_requis")
                candidat = self._hasher(mot_de_passe_actuel, compte["sel"])
                if not secrets.compare_digest(candidat, hash_actuel):
                    raise UserError("Le mot de passe actuel est incorrect.",
                                    401, "mot_de_passe_actuel_invalide")
            sel = secrets.token_hex(16)
            compte["sel"] = sel
            compte["hash"] = self._hasher(nouveau_mot_de_passe, sel)
            self.save()
