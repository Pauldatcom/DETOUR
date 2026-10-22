"""Route for the advisor dashboard statistics."""


def stats(req):
    req.admin_exige()
    store = req.ctx.store
    demandes = store.lister()
    par_statut = {}
    for d in demandes:
        s = d.get("statut", "inconnu")
        par_statut[s] = par_statut.get(s, 0) + 1
    props = req.ctx.propositions.lister()
    req.send_json(200, {
        "demandes_total": len(demandes),
        "propositions_total": len(props),
        "par_statut": par_statut,
        "simulation": True,
    })


def enregistrer(router):
    router.route("GET", r"/api/stats")(stats)
