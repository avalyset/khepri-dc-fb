# KHEPRI-DC-FB v1.0

**Data-centre queues against flow-based import limits in the Norwegian bidding zones: a preregistered descriptive analysis**

Eirik Botten Nicolaysen, EcoDeco AS (ORCID 0009-0001-9188-6788). Zenodo: https://doi.org/10.5281/zenodo.24100435

Kode: Apache-2.0 (`LICENSE`). Tekst, figurer og egne tabeller: CC BY 4.0 (`LICENSE-DATA`). Verdier avledet fra JAO-data er fortsatt underlagt JAOs bruksvilkår (klausul 4).

## Hva som er målt
For hvert budområde NO1–NO5 og hver markedstidsenhet (MTU) fra 2024-10-30 til 2026-10-31 regner vi importheadroom H = NP − minNP. NP er realisert day-ahead nettoposisjon. minNP er minste nettoposisjon fra den nordiske flytbaserte kapasitetsberegningen (JAO Nordic Publication Tool). En MTU regnes som en hendelse når datasenterkøen, lagt på som last etter v1-formelen med andelen f av køen, er større enn H. Sekundærmålet legger regulerbar vannkraft som ikke produserte (installert minus faktisk, ENTSO-E) til H. Det er en optimistisk øvre grense.

Utfall: timer med hendelse, andel hendelsestimer og andel hendelses-MTU per sone, f, år og delperiode før og etter JAO-MTU-skiftet. De er regnet for hovedscenarioet og to sensitiviteter (brukstid 1,0 og køavlesningen 09.11). Resultatene er deskriptive. De sier ingenting om faktisk forsyningssikkerhet, priser eller tilknytningskapasitet.

## Preregistrering og avvik
- Metoden ble låst i den signerte taggen `prereg-v1` (commit `7f6a98b`) før noe utfall ble regnet ut.
- Preregistreringen er innsendt til OSF Registries med embargo til 31.12.2027 valgt: https://osf.io/vd9np. Publiseringen venter ikke på OSF (avvik A3).
- Preregistreringen, KDF-0001, POSISJONERING.md og taggens git-arkiv er tidsstemplet med OpenTimestamps. Det er også GROUND_TRUTH.md og KILDER_MANIFEST.csv slik de så ut i commit `10b8886`. Alle stemplede filer ligger i `ots/` ved siden av stemplet sitt, unntatt taggens git-arkiv: det inneholder kildearkivet i `kilder/` og publiseres ikke, så det stemplet kan ikke kontrolleres offentlig (sha256 430574eaf8af9279ff8c29ba49e56639cb9cc197791c45a8dc28e1810aabdec6).
- Etter `ots upgrade` 10.11.2026 har alle stemplene Bitcoin-attestasjoner (blokk 975211, 975212, 975221, 975224 og 975226). Vi har ikke kontrollert dem mot blokkhodene, fordi vi ikke har en lokal Bitcoin-node. Det gjør `ots verify` hos den som har det.
- Avvik og tolkninger står i `AVVIK_FRA_PREREG.md`. A1: publisering uten skriftlig samtykke fra JAO; ingen JAO-rådata eller JAO-tidsserier er publisert. A2: realisert nettoposisjon fra JAO `fbDomainShadowPrice` i stedet for `netPos`, som bare har data fra 2026-05-28. A3: publisering uten å vente på OSF; embargoen blir stående.

## Innhold
- `khepri_dc_fb/`, `tools/`, `tests/`: analysekode, henteskript og tester (`python3 -m pytest tests`).
- `resultater/`: utfallstabellene (CSV).
- `manuskript/`: manuskriptet (LaTeX og PDF), genererte tabeller og figurer, og `sources.csv` med alle arkiverte kilder (URL, hentetidspunkt og sha256).
- `GROUND_TRUTH.md` og `gt/`: hver verdi i tekstene med kilde, utdrag og to verifiseringer, én mekanisk og én uavhengig og blind.
- `KHEPRI-DC-FB_PREREG_v1_2026-11-09.md`, `adr/`, `POSISJONERING.md`, `PUBLISERINGSPORT.md`, `AVVIK_FRA_PREREG.md`.
- `kilder/KILDER_MANIFEST.csv` (bare manifestet).
- `ots/`: OpenTimestamps-stemplene og de stemplede filene.

## Ikke med
- Kildekopiene i `kilder/` (tredjepartsdokumenter og egne utskrifter). Manifestet og `manuskript/sources.csv` oppgir URL og sha256 for hver kilde.
- JAO-rådata og JAO-tidsserier, ENTSO-E-data og Elhub-data. De hentes med henteskriptene i `tools/` under kildenes egne vilkår (JAO: General Terms and Conditions for the use of the Information Systems; ENTSO-E krever egen API-token).
- Taggens git-arkiv (tarballen) for `prereg-v1`.

## Kilde for JAO-data
JAO Nordic Publication Tool (https://publicationtool.jao.eu).

## Gjenskaping
1. JAO-data: `tools/hent_jao.py` (maxNetPos) og `tools/hent_jao_fbdsp.py` (fbDomainShadowPrice), med jao-py 0.8.7. Henteskriptene holder nå en fast pause mellom kall og venter ved HTTP 429. Datakjøringen 10.11.2026 gikk uten pause, og JAO svarte da HTTP 429 fire ganger på tre døgn (to ganger for 2025-02-07). Alle døgnene ble hentet ved et senere forsøk.
2. ENTSO-E-data (A68, A75, A11) med egen token. Kildene og prioriteten mellom dem står i `tools/` og `GROUND_TRUTH.md`.
3. `tools/foer_analyse.py` (dekning, MTU-skifte, fortegnskontroll), `tools/kjor_analyse.py` (utfallstabellene), `tools/lag_manus.py` (tabeller og figurer), `tools/check_anchors.py .` (ankersjekk).

## Sitering
Se `CITATION.cff`. KHEPRI-DC v1: https://doi.org/10.5281/zenodo.23887356 (versjons-DOI; konsept-DOI 10.5281/zenodo.23887355).

## KI-verktøy
Analysen er planlagt og utført med Claude Code som verktøy under forfatterens styring; se manuskriptets avsnitt om KI-verktøy. «The author made the methodological choices, had every figure checked against its source, and is responsible for the content.»
