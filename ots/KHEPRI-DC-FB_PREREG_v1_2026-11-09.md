# KHEPRI-DC-FB: preregistrering v1

- Bestilt: 09.11.2026 [GT-178]. Låsedatoen er datoen for den signerte taggen `prereg-v1`.
- Forfatter: Eirik Botten Nicolaysen, EcoDeco AS
- Status: låses med signert tagg `prereg-v1` og OSF-registrering når port A i `PUBLISERINGSPORT.md` er grønn.
- Grunnlag: `adr/KDF-0001-headroom-mot-min-nettoposisjon.md`, `POSISJONERING.md` og `GROUND_TRUTH.md`. Hvert tall og hvert sitat under har en GT-ID med dobbel verifisering.
- Grunnlagsfilene slik de ble OTS-stemplet i steg 6:
  - `GROUND_TRUTH.md` sha256 `9ab057490f94569ea2aaf968bdcaaa848729dc5f3d7178e6d7d75792cd232c58`, stempel `GROUND_TRUTH.md.ots`
  - `KILDER_MANIFEST.csv` sha256 `9c089a024479ca83631a3edb587f3c219e25d80982d32ef2fa9a7665045db7bf`, stempel `kilder/KILDER_MANIFEST.csv.ots`
  - `POSISJONERING.md` sha256 `308bd16355704c3da647e6ea7708b176477ec66cffaecd69423d3df2a1aba17e`, stempel `POSISJONERING.md.ots`
  
  Rader lagt til i GT etter steg 6 er med i tagg-tarballen, som OTS-stemples ved låsing.
- Preregistreringen inneholder ingen JAO-data, bare metadata (antall rader, feltnavn, tidsstempler og feilnavn).
- GT-ID-ene i hakeparentes viser til `GROUND_TRUTH.md` i tagg-tarballen. GT lastes ikke opp til OSF [GT-257]; tarballens sha256 føres i OSF-skjemaet ved låsing [GT-410].

## 1 Posisjonering

Ingen side i kildearkivet slik det var i steg 2 (K-01–K-33) har datasenterord og nettoposisjonsord sammen, utenom v1s egne filer [GT-135]. Nærmest kommer:
- Statnetts svarbrev til NVE: fast realisert kapasitet inn til Område Nord, 1050 MW [GT-130], uten flow-based [GT-133];
- arXiv 2607.00977 [GT-072]: headroom-metoden, men bare for Core [GT-077] og uten nordiske soner [GT-079];
- KHEPRI-DC v1: tester ikke import [GT-031].

Vi påstår ikke at spørsmålet er ubesvart utenfor dette arkivet.

## 2 Forskningsspørsmål

«andel MTU der datasenterkøen lagt på som last i sonen ville kreve mer import enn min nettoposisjon tillater — per NO-sone, som funksjon av andelen f av køen» [GT-179].

## 3 Periode, tidsoppløsning og MTU

**Periode.** 2024-10-30–2026-10-31 [GT-180], i UTC. Grensene er [2024-10-30T00:00Z, 2026-11-01T00:00Z), altså med 31.10.2026, og JAO-MTU utenfor kuttes bort [GT-361, GT-379].

**Tidsoppløsning.** «Alle serier legges på JAO-dataenes MTU med varighetsvekting, uten interpolering av manglende verdier. Delperiodene før og etter MTU-skiftet (dato fra 3a) rapporteres hver for seg og samlet; resultater oppgis per time og per MTU.» [GT-206] Dette erstatter bestillingens opprinnelige formulering [GT-181, GT-207]. «3a» viser til JAO-MTU-skiftet rett under.

**JAO-MTU-skiftet.** Regelen er låst, men datoen er ikke fastsatt: «MTU-skiftet = første døgn med 96 MTU i de hentede JAO-dataene; datoen leses ut og føres i GT i dataruna før analysen» [GT-209]. Regelen anvendes på hvert JAO-datasett for seg og på JAOs forretningsdøgn slik det faktisk er avgrenset: norsk døgn, som starter 23:00Z ved normaltid og 22:00Z ved sommertid [GT-373]. Håndboka gir sommertidstilfellet: «2026-04-01 22:00:00 corresponds to the full EDD 2026-04-02» [GT-393]. «96 MTU» leses som at alle MTU i døgnet er 15 minutter, og skifter datasettene på ulike datoer, er den seneste datoen skillet [GT-355, GT-373]. Døgnene mellom de to datoene hører altså til delperioden før skiftet, den med 60-minutters MTU [GT-373, GT-378].
- Første leveringsdøgn hadde 24 rader i `maxNetPos` [GT-167], og døgnet 2026-10-26 hadde 96 rader i `netPos` [GT-166, GT-311].
- Håndboka oppgir «24 MTUs» per døgn [GT-088], mens QPRE-tabellen har siste MTU nr. 96 [GT-211]. Begge føres slik de står.

**Tidsanker.** Alle MTU angis ved intervallstart (UTC), anker A, slik Eirik har bestemt [GT-315]. JAOs `dateTimeUtc` er intervallstart: første tidsstempel i forretningsdøgnet 2024-10-30 (normaltid) er 23:00Z [GT-168]. Håndboka skriver også, om API-svar som følger Core-strukturen: «CET time stamp (yes… CET?!)» [GT-394]. Det føres slik det står. Tidsstemplet 23:00Z for starten av forretningsdøgnet 2024-10-30 [GT-168] er i UTC og svarer til midnatt norsk normaltid; håndbokas sommertidseksempel er også oppgitt i UTC [GT-393]. I ENTSO-E-rådataene er første 15-minutters MTU [GT-312]:
- A65: 2025-03-18T00:00Z [GT-213];
- A75: 2025-04-10T00:00Z [GT-214].

Anker B, første tidsstempel med 15 minutter til forrige, oppgis til sammenligning, bare for NO1: 2025-03-18T00:15Z [GT-220] og 2025-04-10T00:15Z [GT-219]. I rådataene for NO1 er tidsstemplene intervallstart: XML-perioden med kvartersoppløsning starter der timeperioden slutter [GT-216, GT-217], og CSV-verdiene ved samme tidsstempel er identiske med XML-punktene som starter der [GT-221, GT-222].

## 4 Data og roller

- **Realisert DA-nettoposisjon per sone:** JAO Nordic `netPos` [GT-085], felt `hub_<sone>`, for eksempel `hub_NO1` [GT-164].
- **Min nettoposisjon per sone og MTU:** JAO Nordic `maxNetPos` [GT-086], felt `min_<sone>`. Felt finnes for alle fem NO-soner [GT-059].
- **Installert regulerbar vannkraft:** ENTSO-E A68, typene Hydro Water Reservoir og Hydro Pumped Storage [GT-320]. A68-tabellen har kolonner for alle tre år i alle fem soner [GT-169]. Hydro Pumped Storage står som «n/e» i NO1 og NO4 alle tre år [GT-329, GT-332]; der settes pumpekraftleddet til 0 [GT-354, GT-372]. Vilkåret for det er oppfylt: de lagrede A75-dataene har ingen produksjonsserier for pumpekraft i NO1 eller NO4 i perioden (0 serier, 0 verdier, 23 filer per sone [GT-363, GT-364]), mens NO2 har 23 serier og 88340 verdier som positiv kontroll [GT-365]. Hadde A75 hatt slik produksjon, ville regelen vært «STOPP og rapporter» [GT-362]. For hver MTU brukes verdien for kalenderåret MTU-en ligger i [GT-359, GT-377]. Brukes bare i sekundærmålet.
- **Faktisk regulerbar vannkraft per MTU:** ENTSO-E A75, de samme to typene (produksjonssiden) [GT-320]. A75 «Actual Consumption» for Hydro Pumped Storage brukes bare til å avgjøre om et intervall er pumpeintervall [GT-403]. Brukes bare i sekundærmålet, etter regelen for pumpekraft og delvis dekning under Mål [GT-408].
- **Fysisk flyt (A11):** brukes bare til å kontrollere fortegnet på JAO-nettoposisjonen før analysen, og inngår ikke i H(t), L_f eller utfallene [GT-308, GT-321].
- **Last (A65):** inngår ikke i målene. Dekningen er dokumentert under Datagrunnlag, men A65 brukes ikke i analysen [GT-322].
- **Datasenterkø per sone:** Statnett Power BI, «02.11-køen» i primæranalysen [GT-016–GT-027, GT-185].
- **Eksisterende datasenterlast:** E per sone og år fra v1s parameterfil, med referanseår [GT-199] og år med verdier [GT-200]. Kilden er Elhub-fila med sha256 `f03d3098c728c64a846a70c610de52afb6d06ee1cfbee60cc0e8cbc58ec1d79f` [GT-334, GT-335]. Siste starttid i fila er 2026-11-01T22:00:00Z [GT-336], og den har alle 7296 timer i januar–oktober 2026 i hver sone [GT-337, GT-338], så den brukes også for 2026 [GT-319].

## 5 Mål

**Primærmål.** «H(t) = NP(t) − minNP(t); hendelse når L_f > H(t)» [GT-182].
- NP er nettoeksport: «Net position denotes net export» [GT-075].
- Fortegnet tas fra definisjonen [GT-317]. Nordic CCM definerer: «a positive net position is equivalent to export from, and a negative net position is equivalent to import into, the particular bidding zone» [GT-325]. Definisjonen står i Nordic CCMs endringsforslag fra 2026 (K-66), ikke i den godkjente 2020-teksten (K-65), som bare sier «the net value of generation and consumption in a bidding zone» [GT-327, GT-368]. Derfor kjøres A11-kontrollen før analysen [GT-368]. JAO-håndboka definerer fortegnet bare for virtuelle budområder: «positive when power is flowing from the virtual bidding zone to the adjacent real bidding zone and negative otherwise» [GT-328].
- Før analysen kontrolleres fortegnet mot A11: Pearson-korrelasjon mellom JAO-nettoposisjonen og A11-nettoeksport (sum flyt ut minus sum flyt inn over sonens grenseretninger med data), per MTU på JAO-oppløsning, alle NO-soner samlet [GT-356, GT-374]. Er korrelasjonen negativ, motsier A11 definisjonen, og da gjelder «STOPP og rapporter» [GT-345]. Korrelasjonen rapporteres i tillegg per sone, beskrivende, uten at den avgjør noe [GT-366].

**Påslag.** L_f følger v1-formelen, «L = (E_ref − E_y) + 0,70 × (w × R_new + q × Q)» [GT-197], med w = q = f [GT-196] og R_new = max(0, R − E_ref / 0,70) [GT-198]. «R = reservert, Q = kapasitetskø.» [GT-395] R og Q er Statnetts tall for sonen [GT-018–GT-027], og f er andelen av dem som legges på.
- Primær brukstid: «som v1 (flat, brukstid 0,70, 02.11-køen)» [GT-185]. Brukstiden står to steder i formelen, i R_new og i påslaget [GT-197, GT-198]. I sensitiviteten med «brukstid 1,0» [GT-186] byttes begge [GT-316].
- f-rutenettet er v1s [GT-201].
- E_ref er E for referanseåret i parameterfila [GT-199]. E_y tas fra parameterfila for de årene som finnes der [GT-200].
- For siste år i perioden [GT-180] brukes E_2026 fra Elhub-fila [GT-369]: E_y regnes fra den samme fila med v1s regel (energi delt på antall timer), over januar–oktober (7296 timer) [GT-337]. Regelen gjenskaper v1s verdier for referanseåret [GT-199, GT-340]. Verdiene for NO1–NO5 er 106.676 62.196 109.066 77.291 0.039 MW [GT-339].

**Sekundærmål.** «H(t) + regulerbar vannkraft (installert minus faktisk) som øvre grense» [GT-183]. Regulerbar vannkraft er Hydro Water Reservoir og Hydro Pumped Storage, installert fra A68 minus faktisk fra A75 [GT-320]; «Hydro Run-of-river and pondage holdes utenfor.» [GT-348] «Utfall og driftsstans er ikke trukket fra; grensen er derfor optimistisk, og det deklareres.» [GT-350] «Begge rapporteres; ingen velges i ettertid.» [GT-184]

**Pumpekraft og delvis dekning (bare sekundærmålet).** Den opprinnelige regelen for pumpetimer [GT-349] er presisert av Eirik etter andre runde i port A (K-77). Den gjelder hvert A75-intervall, time eller kvarter [GT-402]; A75 har timeoppløsning til 2025-04-10T00:00Z [GT-214].
- «Et intervall der A75 mangler produksjonsverdi for Hydro Pumped Storage regnes som pumpeintervall og settes til 0 FØR varighetsvektingen — bare hvis A75 «Actual Consumption» for Hydro Pumped Storage er > 0 i samme intervall og sone.» [GT-403]
- «Mangler produksjonsverdien uten registrert pumping i intervallet, er intervallet et datahull: MTU-en regnes som manglende for sekundærmålet.» [GT-404]
- «Mangler et intervall for Hydro Water Reservoir, regnes MTU-en som manglende for sekundærmålet.» [GT-405]
- «Mangler feltet i en kilde, blir intervaller uten produksjonsverdi der datahull etter regelen over» [GT-406]. Hvilke kilder som har feltet, står under.
- Om et intervall har produksjons- eller forbruksverdi, avgjøres etter dekodingen av kurvetype A03 [GT-352]: intervallet har verdi når en serie av riktig type dekker det. I CSV-kildene (flowtracing, entsoe-rest) har intervallet verdi når cellen for intervallstarten er ikke-tom og ikke NaN; verdien null teller som verdi.
- Har flere lagrede kilder samme intervall, tas produksjonsverdien, for hver produksjonstype for seg, fra kilden med høyest prioritet som har verdi [GT-376]. Har ingen kilde produksjonsverdi, avgjøres pumpeintervall av forbruksverdien i kilden med høyest prioritet som har forbruksverdi i intervallet [GT-376].
- Faktisk regulerbar vannkraft for en JAO-MTU er det varighetsvektede middelet over A75-intervallene i MTU-en [GT-206], med 0 for pumpekraft i pumpeintervall [GT-403]. Primærmålet påvirkes ikke [GT-408].
- NO1 og NO4 har ikke pumpekraftledd (A68 «n/e» [GT-329, GT-332], se Data og roller) og er uberørt [GT-408]. Der telles verken pumpeintervall eller datahull for pumpekraft, slik at tellingen skiller soner uten pumpeserie fra soner med [GT-412].
- «Antall intervaller i hver kategori (produksjon, pumpeintervall, datahull) rapporteres per sone, kilde og måned.» [GT-407] Hver kilde telles for seg. For den sammenslåtte serien rapporteres i tillegg, per sone og måned, antall MTU som er manglende for sekundærmålet og antall MTU med minst ett pumpeintervall.

**Forbruksfeltet per kilde** (antall forbruksserier eller -kolonner for Hydro Pumped Storage i NO1–NO5, K-78) [GT-406]:
- ny API-henting: 0 5 5 0 5 [GT-415], i alle månedsfilene for NO2, NO3 og NO5 [GT-419];
- v1-XML: 0 1 1 0 1 [GT-416], bare i fila for 2025, ikke i fila for året før [GT-420];
- flowtracing-CSV: 0 4 4 0 4 [GT-417], bare i månedsfilene september–desember 2025 [GT-421];
- entsoe-rest-CSV: 0 0 0 0 0 [GT-418]; ingen fil har feltet [GT-422].

For NO2, NO3 og NO5 dekkes A75 fra periodestart og ut 2024 bare av v1-XML og entsoe-rest-CSV [GT-180, GT-423], og i januar–mai 2026 bare av entsoe-rest-CSV [GT-180, GT-425]. Ingen av disse har feltet i de månedene [GT-420, GT-422]. Der blir derfor hvert intervall uten produksjonsverdi for Hydro Pumped Storage et datahull, og MTU-en er manglende for sekundærmålet. I 2025 dekker v1-XML hele året [GT-424], og fila har feltet [GT-420]; hvor stor del av året forbruksserien dekker, rapporteres i kategoritellingen. I juni–oktober 2026 dekker den nye API-hentingen alt [GT-426], og filene har feltet [GT-419].

**H under null.** MTU der NP ligger under minNP (H(t) < 0) beholdes og vurderes som andre MTU; antallet rapporteres per sone og delperiode [GT-357, GT-375]. Hendelse er L_f > H(t) også når H(t) < 0. L_0 = E_ref − E_y [GT-197] kan være negativ, og raden f = 0 viser derfor hendelser uten datasenterkø, med bare justeringsleddet for eksisterende last [GT-367].

**Manglende data.** MTU uten NP, minNP eller nødvendig ENTSO-E-verdi for det aktuelle målet utelates fra det målet og telles som manglende per sone og måned. Ingen imputering [GT-206]. For sekundærmålet gjelder i tillegg regelen for pumpekraft og delvis dekning over [GT-404, GT-405]. ENTSO-E-XML med kurvetype A03 dekodes som i v1, med «hold forrige verdi» (A03) [GT-352]; det er formatets koding, ikke imputering.

**Per time.** «En time er hendelse hvis minst én MTU i timen er hendelse.» [GT-318] «Mangler en MTU i timen, regnes timen som manglende.» [GT-346]

## 6 Sensitiviteter

- Brukstid: «brukstid 1,0» [GT-186].
- Køavlesning: «09.11-køen» [GT-187], med verdiene per sone fra Power BI 09.11 [GT-045, GT-046, GT-047, GT-048, GT-049, GT-050, GT-051, GT-177, GT-202, GT-203, GT-204, GT-205].
- Sensitivitetene kjøres hver for seg [GT-411]: én endring om gangen, med alt annet som i primæranalysen. Begge mål rapporteres for hver av dem, slik som for primæranalysen [GT-184].

## 7 Utfall

Utfallene er «timer per år med hendelse og minste f der referansen fra 3d passeres; uten referanse deskriptivt, ingen egen terskel» [GT-188]. «3d» viser til en pålitelighetsstandard eller ERAA-referanse for Norge, se referansen nedenfor.
- Per sone, per f og per kalenderår (delår i start- og sluttåret), og for delperiodene før og etter JAO-MTU-skiftet hver for seg og samlet [GT-206]:
  - timer med hendelse etter timeregelen [GT-318];
  - andel hendelsestimer og andel hendelses-MTU, begge [GT-347]. Andel hendelses-MTU rapporteres per delperiode og ikke samlet, fordi MTU-lengden skifter; andel hendelsestimer rapporteres også samlet [GT-360, GT-378];
  - antall manglende MTU og manglende timer.
- Delår rapporteres uskalert, som timer i delåret [GT-360, GT-378].
- Referanse: kildearkivet har ingen pålitelighetsstandard eller LOLE/EENS for norske soner [GT-136, GT-106]. ERAA nevner adekvansproblemer i NOS1 for 2030–2035 [GT-103], men det er en prognose og ingen terskel for observerte MTU. Utfallene rapporteres derfor beskrivende, uten terskel og uten «minste f» [GT-188].

## 8 Datagrunnlag: dekning, hull, revisjoner og hentetidspunkt

**Dekning av ENTSO-E-data.** For A65 og A75 er perioden fullt dekket i 243 kombinasjoner av dokumenttype, sone og måned, mens 7 har hull [GT-297]. For A75 har 0 kombinasjoner hull [GT-298], men da regnes et kvarter som dekket når minst én produksjonstype har verdi. Dekningen for Hydro Water Reservoir og Hydro Pumped Storage måles og deklareres per sone og måned i dataruna før analysen. Hullene er deklarert og interpoleres ikke [GT-195]:
- A65 NO1, september 2026: 3 manglende kvarter: 2026-09-18T06:00Z 2026-09-19T06:00Z 2026-09-22T06:15Z [GT-299]
- A65 NO1, oktober 2026: 1 manglende kvarter: 2026-10-26T10:15Z [GT-300]
- A65 NO2, september 2026: 4 manglende kvarter: 2026-09-11T06:00Z 2026-09-18T06:00Z 2026-09-20T06:00Z 2026-09-22T06:15Z [GT-301]
- A65 NO2, oktober 2026: 1 manglende kvarter: 2026-10-26T10:15Z [GT-302]
- A65 NO3, september 2026: 3 manglende kvarter: 2026-09-18T06:00Z 2026-09-19T06:00Z 2026-09-22T06:15Z [GT-303]
- A65 NO4, september 2026: 3 manglende kvarter: 2026-09-18T06:00Z 2026-09-19T06:00Z 2026-09-22T06:15Z [GT-304]
- A65 NO5, september 2026: 3 manglende kvarter: 2026-09-11T06:00Z 2026-09-19T06:00Z 2026-09-22T06:15Z [GT-305]

For A11 gjelder: «A11-dekningen for 2026 måles og deklareres i dataruna før analysen» [GT-307]. Etter hullhentingen er A11 fullt dekket i alle 30 grenseretninger i hentesettet [GT-388]: 750 / 750 kombinasjoner av retning og måned [GT-389], og 125 / 125 per sone og måned [GT-390]. A75 har 125 / 125 [GT-391] og A65 118 / 125 [GT-392].

**Hullhentingen.** 374 vinduer [GT-381], fordelt på 300 / 49 / 25 for A11 / A65 / A75, alle med status OK [GT-380]; 0 endelig feilet [GT-382]. 4 vinduer trengte til sammen 5 nye forsøk [GT-383], etter 5 tidsavbrudd fra ENTSO-E, ført i henteloggen [GT-384]. Alle vinduer har kurvetype og oppløsning A03 PT15M [GT-387]. JAO-dataene hentes i dataruna. Dekningen deres måles og deklareres på samme måte, før analysen.

**Revisjoner hos ENTSO-E.** Analysen bruker rådataene slik de ble lagret ved henting. Senere revisjoner tas ikke inn. Har flere lagrede kilder samme MTU, går ny API-henting foran v1-XML, som går foran flowtracing-CSV, som går foran entsoe-rest-CSV; avvik i overlappet rapporteres per sone og måned [GT-358, GT-376]. Revisjonskontrollen for A65 NO1, ny henting mot v1-rådata:
- 31080 parrede MTU der begge sider har verdi [GT-228];
- 0 avvikende MTU [GT-231], med største avvik 0.000 MW [GT-232];
- 2976 MTU finnes bare i ny henting [GT-229], og 0 bare i v1 [GT-230];
- begge filsettene er lest, 16 / 25 filer [GT-233];
- den positive kontrollen ga resultatet BESTÅTT [GT-238].

Kontrollen gjelder A65 NO1, som ikke inngår i analysen [GT-322]. Den sier ingenting om A75 eller A11 før kontrollen under er kjørt.

Tilsvarende kontroll gjøres i dataruna for overlapp mellom nye og lagrede filer, og avvik rapporteres per sone og måned.

**Hentetidspunkt per datakilde:**
- v1-rådata: 2026-11-02T11:08:39Z 2026-11-02T12:41:45Z [GT-239]
- flowtracing: 2026-09-21T17:59:07Z 2026-09-21T21:27:38Z [GT-240]
- entsoe-rest (filtid): 2026-06-29T09:57:44Z 2026-06-29T16:15:03Z [GT-241]
- egen API-henting av A65/A75: 2026-11-09T17:26:37Z 2026-11-09T18:04:34Z [GT-310]
- A11 for 2026 (hullhentingen): 2026-11-09T18:04:55Z 2026-11-09T19:50:37Z [GT-386]; hentingen ble avsluttet 2026-11-09T19:50:37Z [GT-385]. Tidspunkt og dekning er ført i GT [GT-386, GT-389], slik regelen krever [GT-307].
- JAO hentes i dataruna. Tidspunktene føres i GT før analysen.

## 9 Begrensninger (deklarert)

- Ytterpunktene er ikke samtidig gjennomførbare: «simultaneous feasibility of e.g. maximum flow on two borders cannot be guaranteed.» [GT-084] Hver min nettoposisjon er et eget ytterpunkt av domenet [GT-083]. Resultatet er en optimistisk øvre grense for tilgjengelig import, gitt at domenet ikke flytter seg (neste punkt).
- Domenet ville flyttet seg med stor ny last, og systemegenskaper, spenning og stabilitet ligger utenfor metoden [GT-193]. Statnett begrunnet stansen i systemegenskaper [GT-037], og fos § 14 gjelder godkjenning av anleggsfunksjonalitet [GT-038].
- Andre soners køer holdes utenfor: «andre soners køer utenfor» [GT-194].
- Køtallene varierer med kilde og dato:
  - pressemeldingen: 4 200 MW reservert og 9 100 MW i kø [GT-040, GT-041];
  - Power BI, avlest til «02.11-køen» [GT-185]: 4 190 og 10 109 [GT-016, GT-017], som er primæranalysens kø;
  - Power BI, avlest til «09.11-køen» [GT-187]: 4 205 og 10 774 [GT-045, GT-046]; denne avlesningen er ikke arkivert med skjermbilde [GT-045];
  - «Langsiktig markedsanalyse 2026-60»: ca. 4200 og ca. 8800 [GT-120, GT-313].
- Reservert og tilknyttet kapasitet: når et prosjekt er knyttet til nettet, «endres status fra reservert til tilknyttet i våre systemer» [GT-341]. Men «enkelte kundeprosjekter som er tilknyttet med faktisk effektutveksling står oppført som reservert i våre systemer» [GT-342], fordi sakene oppdateres med «minst én årlig oppdatering» [GT-343]. Statnetts reserverte tall kan derfor inneholde prosjekter som allerede er tilknyttet, slik at samme kapasitet kan telles både i nettoposisjonen og i køen. Effekten er at hendelser kan overvurderes, og omfanget er ukjent [GT-370].
- Siste år i perioden bruker E_y for januar–oktober [GT-180, GT-339], mens 2024 og 2025 bruker helårsverdier fra parameterfila [GT-200].
- Realisert nettoposisjon ga ingen data for første leveringsdøgn [GT-165]. Dekningen i starten av perioden måles i dataruna.

## 10 Deklarasjon av sett data

- «recon-uka 26.10–01.11.2026 (bare min/maks) er sett før prereg» [GT-189].
- I tillegg er dette sett før preregistreringen, bare som metadata (antall rader, feltnavn, tidsstempler og feilnavn, ingen verdier analysert):
  - JAO `netPos` for ett døgn [GT-166] og `maxNetPos` for første leveringsdøgn [GT-167];
  - ENTSO-E-dekningstellinger [GT-297, GT-389];
  - A75-tellingen av pumpekraftserier i NO1, NO4 og NO2 [GT-363, GT-364, GT-365]; tellingen (K-71) viste også antall verdier ulik null for produksjon og forbruk i NO2, altså en telling på verdiene;
  - tellingen av forbruksserier og forbruksverdier (Actual Consumption) for pumpekraft per lagret A75-kilde, sone og fil (K-78) [GT-415, GT-416, GT-417, GT-418];
  - den uavhengige gjennomgåerens telling i port A, andre runde, av timer der produksjonen for pumpekraft dekker 1–3 av 4 kvarter i v1-XML, i vinduet [2025-04-10, 2026-01-01) [GT-434]: 61 timer i NO2 og 58 i NO5 [GT-432, GT-433]. Samme utskrift viste også antall timer der alle 4 kvarter er dekket, og antall timer i vinduet (K-80) [GT-432, GT-433]. Bare dekning er talt, ingen verdier.
- Disse verdiene er også sett før preregistreringen, men de er inndata, ikke analyse:
  - A68-tabellene per sone og år, inkludert Hydro Water Reservoir og Hydro Pumped Storage [GT-169, GT-329–GT-333];
  - A75- og A65-verdier i rådatautdragene (K-42) rundt ENTSO-E-skiftet til 15-minutters MTU for NO1 [GT-312, GT-216, GT-217, GT-221, GT-222];
  - A65-verdiene i revisjonskontrollen [GT-228];
  - E per sone fra Elhub for siste år i perioden [GT-339];
  - v1s analyse av A65, A75 og A11 for 2023–2025 [GT-007, GT-008, GT-009, GT-010], som overlapper perioden [GT-180].
- Ingen headroom, ingen last mot headroom og ingen utfall er beregnet.

## 11 Data og lisens

- «ingen JAO-rådata eller avledede serier publiseres før skriftlig samtykke fra JAO» [GT-190].
- JAO-vilkårene sier at innhold ikke kan gjøres tilgjengelig for tredjepart «unless expressly authorized in advance by JAO in writing.» [GT-061]
- Innhold omfatter avledede data: «materials derived from, based on, generated from or incorporating the Content» [GT-063].

## 12 Kontrollstrenger og fraværsbelegg

Hver henting skriver manifest med `sha256`, kontrollstreng og utfall:
- **JAO:** ikke-tom liste med `dateTimeUtc` og feltet `hub_<sone>` eller `min_<sone>`. Tomt svar føres som fravær med feilnavn, slik som `NoMatchingDataError` [GT-165].
- **ENTSO-E:** kontrollstrengen `TimeSeries`. Svar uten data føres med årsakskode fra Acknowledgement_MarketDocument.
- **Manglende MTU:** telles og rapporteres per sone og måned, og glattes ikke over.

## 13 KI-erklæring

Analysen er planlagt og vil bli utført med Claude Code som verktøy under forfatterens styring. Verktøy og modeller brukt så langt (planlegging og preregistrering), lest fra øktloggene (K-76, K-79):
- Claude Code 2.1.317 [GT-396], hovedøkt på `claude-opus-5-5`; `claude-sonnet-5-5` står for 17 av hovedøktas svar, alle i tidsrommet 2026-11-09T16:27:15.690Z – 2026-11-09T16:27:46.448Z [GT-397, GT-398];
- underagenter i Claude Code, alle på `claude-opus-5-5`, talt 2026-11-09T22:20:20Z [GT-427]: 4 til kildelesing i steg 2 [GT-428], 13 til blind GT-verifisering [GT-429] og 3 til uavhengig gjennomgang i port A [GT-430], i alt 20 [GT-431]. Underagenter startet etter dette tidspunktet føres i GT ved låsing;
- chat-Claude (claude.ai) for Eiriks egen gjennomgang; modell-ID-en for den er ikke registrert i øktloggene [GT-401].

«The author made the methodological choices, had every figure checked against its source, and is responsible for the content.» [GT-191]
