"""DÉTOUR supplier API routes, organized by business domain."""

from httpd.router import Router

from . import (dashboard, disponibilites, instructor, meta, options,
               prestations, recherche, reservations)


def creer_router():
    router = Router()
    for module in (meta, prestations, disponibilites, recherche, options,
                   reservations, instructor, dashboard):
        module.enregistrer(router)
    return router
