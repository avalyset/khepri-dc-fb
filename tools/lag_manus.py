"""Bygger manuskriptets tabeller, figurer og tallmakroer direkte fra CSV-ene i resultater/ (ingen tall for hånd).

Utdata i <ut> (standard manuskript/generert/):
  tab_hoved_primaer.tex, tab_hoved_sekundaer.tex  primærscenarioet: timer med hendelse per sone og år, utvalgte f
  tab_sensitivitet.tex                            sensitivitetene hver for seg [GT-411], begge mål, hele perioden
  tab_delperiode.tex                              andel hendelses-MTU og -timer før og etter JAO-MTU-skiftet
  tab_manglende.tex                               manglende MTU og timer per sone og mål, MTU med H < 0
  fig_f_kurver.pdf                                timer med hendelse mot f per sone, begge mål, primærscenarioet
  fig_sensitivitet.pdf                            timer med hendelse mot f per sone og scenario, primærmålet
  tall.tex                                        makroer for tall i løpende tekst
Første linje i hver .tex-fil: «% generert av tools/lag_manus.py fra <fil> sha256 <hash> [GT-nnn]; …». Den kontrolleres av
tools/check_anchors.py (vi): hash lik fila i resultater/ og lik verdien til GT-ID-en, og ny kjøring gir like byte.
Figurene lagres uten tidsstempel (metadata CreationDate=None), slik at de også kan gjenskapes byte for byte.
Bruk: /opt/homebrew/bin/python3 -I -B tools/lag_manus.py [<ut>]   (tolken med matplotlib; tools/check_anchors.py bruker samme)
"""
import collections
import csv
import hashlib
import os
import sys
from pathlib import Path

ROT = Path(__file__).resolve().parents[1]
RES = ROT / "resultater"
UT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROT / "manuskript/generert"
UT.mkdir(parents=True, exist_ok=True)
GT_SHA = {"utfall.csv": "GT-647", "h_under_null.csv": "GT-648", "manglende_per_maaned.csv": "GT-649", "L_f.csv": "GT-650"}
SONER = ["NO_1", "NO_2", "NO_3", "NO_4", "NO_5"]
SNAVN = {z: z.replace("_", "") for z in SONER}
F_TAB = ["0.00", "0.25", "0.50", "0.75", "1.00"]
SCEN = {"primaer": "primary", "brukstid_1_0": "utilisation 1.0", "koe_0911": "queue read 09.11"}
MAAL = {"primaer": "primary", "sekundaer": "secondary"}


def sha(f):
    return hashlib.sha256((RES / f).read_bytes()).hexdigest()


def hode(*filer):
    return "% generert av tools/lag_manus.py fra " + "; ".join(f"resultater/{f} sha256 {sha(f)} [{GT_SHA[f]}]" for f in filer) + "\n"


U = list(csv.DictReader(open(RES / "utfall.csv", encoding="utf-8")))
IDX = {(r["scenario"], r["maal"], r["sone"], r["f"], r["aar"], r["delperiode"]): r for r in U}


def u(sc, m, z, f, a, dp):
    return IDX[(sc, m, z, f, a, dp)]


def skriv(navn, tekst):
    (UT / navn).write_text(tekst, encoding="utf-8")


def tab_hoved(maal):
    linjer = [hode("utfall.csv"), "\\begin{tabular}{llrrrrrr}\n\\toprule\n",
              "Zone & Year & \\multicolumn{5}{c}{Hours with event, $f =$} & Valid hours \\\\\n",
              "\\cmidrule(lr){3-7}\n & & " + " & ".join(F_TAB) + " & \\\\\n\\midrule\n"]
    for z in SONER:
        for a in ("2024", "2025", "2026", "alle"):
            r0 = u("primaer", maal, z, "0.00", a, "samlet")
            celler = [u("primaer", maal, z, f, a, "samlet")["timer_med_hendelse"] for f in F_TAB]
            linjer.append(f"{SNAVN[z] if a == '2024' else ''} & {a if a != 'alle' else 'all'} & " + " & ".join(celler)
                          + f" & {r0['timer_gyldige']} \\\\\n")
        if z != SONER[-1]:
            linjer.append("\\addlinespace\n")
    linjer.append("\\bottomrule\n\\end{tabular}\n")
    skriv(f"tab_hoved_{maal}.tex", "".join(linjer))


def tab_sens():
    fs = ["0.25", "0.50", "0.75", "1.00"]
    linjer = [hode("utfall.csv"), "\\begin{tabular}{lllrrrrr}\n\\toprule\n",
              "Measure & Scenario & Zone & \\multicolumn{4}{c}{Hours with event, $f =$} & Valid hours \\\\\n",
              "\\cmidrule(lr){4-7}\n & & & " + " & ".join(fs) + " & \\\\\n\\midrule\n"]
    for m in MAAL:
        for sc in SCEN:
            for z in SONER:
                celler = [u(sc, m, z, f, "alle", "samlet")["timer_med_hendelse"] for f in fs]
                linjer.append(f"{MAAL[m] if sc == 'primaer' and z == 'NO_1' else ''} & {SCEN[sc] if z == 'NO_1' else ''} & {SNAVN[z]} & "
                              + " & ".join(celler) + f" & {u(sc, m, z, '0.00', 'alle', 'samlet')['timer_gyldige']} \\\\\n")
            linjer.append("\\addlinespace\n")
    linjer[-1] = "\\bottomrule\n\\end{tabular}\n"
    skriv("tab_sensitivitet.tex", "".join(linjer))


def andel(x):
    return "" if x == "" else f"{100 * float(x):.2f}"


def tab_delperiode():
    linjer = [hode("utfall.csv"), "\\begin{tabular}{llrrrrrr}\n\\toprule\n",
              "Measure & Zone & \\multicolumn{3}{c}{Before the MTU shift (60-min MTU)} & \\multicolumn{3}{c}{After the MTU shift (15-min MTU)} \\\\\n",
              "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}\n & & valid MTU & \\% MTU & \\% hours & valid MTU & \\% MTU & \\% hours \\\\\n\\midrule\n"]
    for m in MAAL:
        for f in ("0.50", "1.00"):
            linjer.append(f"\\multicolumn{{8}}{{l}}{{\\emph{{{MAAL[m]} measure, primary scenario, $f = {f}$}}}} \\\\\n")
            for z in SONER:
                c = []
                for dp in ("foer", "etter"):
                    r = u("primaer", m, z, f, "alle", dp)
                    c += [r["mtu_gyldige"], andel(r["andel_mtu_med_hendelse"]), andel(r["andel_timer_med_hendelse"])]
                linjer.append(f" & {SNAVN[z]} & " + " & ".join(c) + " \\\\\n")
    linjer.append("\\bottomrule\n\\end{tabular}\n")
    skriv("tab_delperiode.tex", "".join(linjer))


def tab_manglende():
    M = list(csv.DictReader(open(RES / "manglende_per_maaned.csv", encoding="utf-8")))
    H = {(r["sone"], r["delperiode"]): r for r in csv.DictReader(open(RES / "h_under_null.csv", encoding="utf-8"))}
    s = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in M:
        x = s[(r["maal"], r["sone"])]
        x[0] += int(r["mtu_i_rutenett"])
        x[1] += int(r["mtu_manglende"])
        x[2] += int(r["timer_i_rutenett"])
        x[3] += int(r["timer_manglende"])
    linjer = [hode("manglende_per_maaned.csv", "h_under_null.csv"), "\\begin{tabular}{lrrrrrrr}\n\\toprule\n",
              "Zone & MTU in grid & \\multicolumn{2}{c}{Missing MTU} & Hours in grid & \\multicolumn{2}{c}{Missing hours} & MTU with $H<0$ \\\\\n",
              "\\cmidrule(lr){3-4}\\cmidrule(lr){6-7}\n & & primary & secondary & & primary & secondary & (primary) \\\\\n\\midrule\n"]
    for z in SONER:
        p, q = s[("primaer", z)], s[("sekundaer", z)]
        linjer.append(f"{SNAVN[z]} & {p[0]} & {p[1]} & {q[1]} & {p[2]} & {p[3]} & {q[3]} & {H[(z, 'samlet')]['mtu_H_under_null']} \\\\\n")
    linjer.append("\\bottomrule\n\\end{tabular}\n")
    skriv("tab_manglende.tex", "".join(linjer))


def figurer():
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    import matplotlib
    matplotlib.use("pdf")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 8, "pdf.fonttype": 42, "svg.hashsalt": "khepri"})
    fs = [f"{i / 100:.2f}" for i in range(101)]
    x = [float(f) for f in fs]
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    for k, m in enumerate(MAAL):
        for z in SONER:
            ax[k].plot(x, [int(u("primaer", m, z, f, "alle", "samlet")["timer_med_hendelse"]) for f in fs], label=SNAVN[z], lw=1.2)
        ax[k].set_title(f"{MAAL[m].capitalize()} measure (primary scenario)")
        ax[k].set_xlabel("f (share of the zone's queue added as load)")
        ax[k].grid(alpha=0.3)
    ax[0].set_ylabel("Hours with event, whole period")
    ax[1].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(UT / "fig_f_kurver.pdf", metadata={"CreationDate": None, "ModDate": None, "Producer": None, "Creator": None})
    plt.close(fig)
    fig, ax = plt.subplots(1, 5, figsize=(7.0, 2.2), sharey=True)
    for k, z in enumerate(SONER):
        for sc in SCEN:
            ax[k].plot(x, [int(u(sc, "primaer", z, f, "alle", "samlet")["timer_med_hendelse"]) for f in fs], label=SCEN[sc], lw=1.0)
        ax[k].set_title(SNAVN[z])
        ax[k].set_xlabel("f")
        ax[k].grid(alpha=0.3)
    ax[0].set_ylabel("Hours with event")
    ax[-1].legend(frameon=False, fontsize=6)
    fig.tight_layout()
    fig.savefig(UT / "fig_sensitivitet.pdf", metadata={"CreationDate": None, "ModDate": None, "Producer": None, "Creator": None})
    plt.close(fig)
    skriv("fig_kilder.tex", hode("utfall.csv") + "% figurene fig_f_kurver.pdf og fig_sensitivitet.pdf er laget fra samme fil med "
          f"Python {sys.version.split()[0]} og matplotlib {matplotlib.__version__}\n")


def tall():
    ORD = {"NO_1": "NOone", "NO_2": "NOtwo", "NO_3": "NOthree", "NO_4": "NOfour", "NO_5": "NOfive"}
    H = {(r["sone"], r["delperiode"]): r for r in csv.DictReader(open(RES / "h_under_null.csv", encoding="utf-8"))}
    r = u("primaer", "primaer", "NO_1", "0.00", "alle", "samlet")
    m = {"GyldigeTimerPrimaer": r["timer_gyldige"], "TimerIRutenett": str(int(r["timer_gyldige"]) + int(r["timer_manglende"])),
         "ManglendeTimerPrimaer": r["timer_manglende"]}
    for z, o in ORD.items():
        m[f"PrimFull{o}"] = u("primaer", "primaer", z, "1.00", "alle", "samlet")["timer_med_hendelse"]
        m[f"PrimHalf{o}"] = u("primaer", "primaer", z, "0.50", "alle", "samlet")["timer_med_hendelse"]
        m[f"SekFull{o}"] = u("primaer", "sekundaer", z, "1.00", "alle", "samlet")["timer_med_hendelse"]
        m[f"SekGyldige{o}"] = u("primaer", "sekundaer", z, "0.00", "alle", "samlet")["timer_gyldige"]
        m[f"Hneg{o}"] = H[(z, "samlet")]["mtu_H_under_null"]
        m[f"HnegFoer{o}"] = H[(z, "foer")]["mtu_H_under_null"]
    m["PrimNullFoer"] = u("primaer", "primaer", "NO_5", "0.00", "alle", "samlet")["timer_med_hendelse"]
    linjer = [hode("utfall.csv", "h_under_null.csv")] + [f"\\newcommand{{\\res{k}}}{{{v}}}\n" for k, v in m.items()]
    skriv("tall.tex", "".join(linjer))


tab_hoved("primaer")
tab_hoved("sekundaer")
tab_sens()
tab_delperiode()
tab_manglende()
figurer()
tall()
print("skrev", sorted(p.name for p in UT.iterdir()))
