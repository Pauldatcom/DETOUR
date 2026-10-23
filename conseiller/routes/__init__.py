"""DÉTOUR portal routes, organized by business domain.

Each module registers its routes on the shared Router, mirroring
the feature folders of a Next.js app (App Router).
"""

from httpd.router import Router

from . import (account, auth, catalogue, chat, demandes, meta, pages,
               propositions, stats)


def creer_router():
    router = Router()
    for module in (pages, meta, auth, account, demandes, propositions,
                   chat, stats, catalogue):
        module.enregistrer(router)
    return router
