import io,os
p=r'C:\Users\HP ZBOOK\DETOUR\web\src\components\traveler\PriceVerification.test.tsx'
s=open(p,encoding='utf-8').read()
# Replace literal \n sequences that broke
old = r'  it(\"says when the total still includes a price copied from the previous version\", () => {\n    const copied = service({\n      id: \"hotel-copie\",\n      nom: \"Hôtel repris\",\n      copie_depuis_v1: true,\n      prix_unitaire_eur: 25,\n      prix_total_eur: 50,\n    });\n    render(<ProposalTotal proposition={proposition([service(), copied])} />);\n\n    expect(screen.getByText(\"Dont 1 prix repris de la proposition précédente.\")).toBeInTheDocument();\n  });\n\n  it(\"warns that the total predates a modified price\", () => {'
new = '''  it("says when the total still includes a price copied from the previous version", () => {
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

  it("warns that the total predates a modified price", () => {'''
if old not in s:
    print('no')
else:
    s=s.replace(old,new)
    open(p,'w',encoding='utf-8').write(s)
    print('yes')
