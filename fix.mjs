import fs from 'fs';
const p = 'web/src/components/traveler/PriceVerification.test.tsx';
let s = fs.readFileSync(p, 'utf8');
const start = s.indexOf('  it(\"says when the total still includes');
const end = s.indexOf('\n  it(\"warns that the total predates');
if (start < 0 || end < 0) { console.log('bad'); process.exit(1); }
const repl = \  it("says when the total still includes a price copied from the previous version", () => {
    const copied = service({
      id: "hotel-copie",
      nom: "Hôtel repris",
      copie_depuis_v1: true,
      prix_unitaire_eur: 25,
      prix_total_eur: 50,
    });
    render(<ProposalTotal proposition={proposition([service(), copied])} />);

    expect(screen.getByText("Dont 1 prix repris de la proposition précédente.")).toBeInTheDocument();
  });

\;
s = s.slice(0,start) + repl + s.slice(end);
fs.writeFileSync(p, s);
console.log('ok');