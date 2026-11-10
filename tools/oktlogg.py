"""Verktøy, modeller og underagentformål i denne Claude Code-økta, lest fra øktloggene (JSONL + meta.json).

Leser bare feltene version, timestamp, type, message.model og, for underagenter, meta.json-feltene description og model.
Formålskategori per underagent fra description (oppgavenavnet hovedøkta ga underagenten):
  «Les …»                                  -> kildelesing (steg 2)
  inneholder «verifisering» eller «blindrunde» -> blind GT-verifisering
  begynner med «Port A»                    -> uavhengig gjennomgang i port A
  inneholder «blind gt round»              -> blind GT-verifisering (engelske oppgavenavn i dataruna 10.11)
  begynner med «Independent recomputation» -> uavhengig omregning av utfallene
Bruk: python3 -I -B tools/oktlogg.py <øktlogg.jsonl>
"""
import collections
import json
import sys
from pathlib import Path

hoved = Path(sys.argv[1]).expanduser()
sub = hoved.with_suffix("") / "subagents"


def les(p):
    for linje in open(p, encoding="utf-8"):
        try:
            yield json.loads(linje)
        except json.JSONDecodeError:
            continue


def modeller(p):
    n, tid = collections.Counter(), collections.defaultdict(list)
    for x in les(p):
        if x.get("type") == "assistant":
            m = (x.get("message") or {}).get("model")
            if m and not m.startswith("<"):
                n[m] += 1
                tid[m].append(x["timestamp"])
    return n, tid


versjoner = sorted({x["version"] for x in les(hoved) if x.get("version")})
n, tid = modeller(hoved)
print("Claude Code-versjon(er) i hovedloggen:", " ".join(versjoner))
print("Hovedøkt, assistentsvar per modell:", "; ".join(f"{m}: {k}" for m, k in sorted(n.items())))
for m in sorted(tid):
    print(f"Hovedøkt, tidsrom for {m}: {min(tid[m])} – {max(tid[m])}")


def kategori(d):
    if d.startswith("Les "):
        return "kildelesing (steg 2)"
    if "verifisering" in d.lower() or "blindrunde" in d.lower() or "blind gt round" in d.lower():
        return "blind GT-verifisering"
    if d.startswith("Independent recomputation"):
        return "uavhengig omregning av utfallene"
    if d.startswith("Port A"):
        return "uavhengig gjennomgang i port A"
    return "annet"


rader = []
for meta in sorted(sub.glob("*.meta.json")):
    d = json.load(open(meta, encoding="utf-8"))
    nm, tm = modeller(meta.with_name(meta.name.replace(".meta.json", ".jsonl")))
    alle = [t for v in tm.values() for t in v]
    rader.append((min(alle) if alle else "", kategori(d.get("description", "")), d.get("description", ""), "/".join(sorted(nm))))
rader.sort()
print("Underagentlogger:", len(rader))
per = collections.defaultdict(list)
for r in rader:
    per[r[1]].append(r)
for k in ("kildelesing (steg 2)", "blind GT-verifisering", "uavhengig gjennomgang i port A", "uavhengig omregning av utfallene", "annet"):
    if per[k]:
        mod = sorted({r[3] for r in per[k]})
        print(f"Underagenter, {k}: {len(per[k])}; modell: {', '.join(mod)}; første start: {per[k][0][0]}")
print("Underagenter, per logg (første svar, kategori, oppgavenavn, modell):")
for r in rader:
    print(" ", r[0], "|", r[1], "|", r[2], "|", r[3])
