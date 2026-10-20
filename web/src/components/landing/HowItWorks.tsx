import { COMMENT_CA_MARCHE } from "../../data/detourContent";

/** Section « Comment ça marche » — 4 étapes numérotées. */
export function HowItWorks() {
  return (
    <section id="comment-ca-marche" className="scroll-mt-20 bg-white py-16 lg:py-24">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl">
          <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-[#38bdb8]">
            {COMMENT_CA_MARCHE.surtitre}
          </p>
          <h2 className="text-3xl font-bold text-[#0b2447] sm:text-4xl">
            {COMMENT_CA_MARCHE.titre}
          </h2>
          <p className="mt-4 text-[#4b6480]">{COMMENT_CA_MARCHE.texte}</p>
        </div>

        <div className="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {COMMENT_CA_MARCHE.etapes.map((etape) => (
            <div key={etape.id} className="relative">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f0eefe]">
                <span className="text-xl font-bold text-[#7a5cd6]">{etape.numero}</span>
              </div>
              <h3 className="mt-4 text-lg font-bold text-[#0b2447]">{etape.titre}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#4b6480]">{etape.texte}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
