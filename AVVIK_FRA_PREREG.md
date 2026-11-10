# AVVIK_FRA_PREREG — KHEPRI-DC-FB dataruna

Den bindende teksten er preregistreringen i taggen `prereg-v1` (taggobjekt `d567d764` → commit `7f6a98b`). Dataruna er bestilt i K-84. Hvert avvik føres her med begrunnelse, GT-ID og tidspunkt (UTC), og det føres FØR det gjøres. Tidspunktene og koden står i `kode`.

## Avvik

- **`A1` — port B uten samtykke fra JAO; resultatene publiseres med JAO som kilde.** Ført `2026-11-10T04:36Z`, før endringen i `PUBLISERINGSPORT.md`. Eiriks beslutning (K-92):
  - «JAO-rådata og JAO-tidsserier publiseres ikke.» [GT-546]
  - «Det publiseres resultater (utfallstabeller og tall i manuskriptet), med JAO oppgitt som kilde, og kode med henteskript slik at andre kan hente dataene selv.» [GT-547]
  - «Port B venter ikke på skriftlig samtykke fra JAO.» [GT-548]
  - «Skulle JAO ha innvendinger etter publisering, håndteres det med en rettelse.» [GT-551]
  - «Ingen henvendelse til JAO.» [GT-552]

  **Hva som endres.** Port B i `PUBLISERINGSPORT.md` krevde at «skriftlig samtykke fra JAO foreligger og er arkivert som kilde i GT» [GT-251]. Kravet fjernes i en egen commit [GT-549]. `PUBLISERINGSPORT.md` ligger også i OSF-registreringen (`https://osf.io/vd9np`), og derfor føres endringen her [GT-550]. Den registrerte versjonen står uendret i taggen `prereg-v1`.

  **Forholdet til preregistreringen.** Under Data og lisens sier preregistreringen: «ingen JAO-rådata eller avledede serier publiseres før skriftlig samtykke fra JAO» [GT-190]. Rådata og tidsserier publiseres fortsatt ikke [GT-546], så den delen av regelen står. Avviket gjelder resultatene. JAO-vilkårene regner avledet materiale som innhold [GT-063], og utfallstabellene er avledet av JAO-data. Å publisere dem uten samtykke avviker derfor fra preregistreringens regel under Data og lisens, i den grad tabellene regnes som avledet materiale. Eiriks begrunnelse: kode og henteskript publiseres, så andre kan hente dataene selv [GT-547], og innvendinger fra JAO håndteres med en rettelse [GT-551]. Det åpne punktet om bots står fortsatt [GT-476].

- **`A2` — JAO fbDomainShadowPrice erstatter netPos som kilde for NP.** Ført `2026-11-10T05:14Z`, før noe hentes eller kjøres [GT-603]. Eiriks beslutning (`K-104`):
  - «JAO fbDomainShadowPrice (cnecName NetPosition_<sone>, feltet flowFb) erstatter netPos som kilde for realisert DA-nettoposisjon for hele perioden 2024-10-30–2026-10-31.» [GT-601]
  - Begrunnelse: «netPos-siden bygger på samme datasett (K-25), og de to er identiske i overlappet (75 380 par, 0 avvik).» [GT-602]

  **Hva som endres.** Under Data og roller i preregistreringen er kilden for NP JAO Nordic `netPos` [GT-085]. Den byttes mot verdien `flowFb` for `cnecName` `NetPosition_<sone>` i `fbDomainShadowPrice`. Ifølge JAO-håndboka er det denne verdien netPos-siden publiserer [GT-569]. Datasettet har data fra første leveringsdøgn [GT-572]. I overlappet er det identisk med netPos [GT-577]. Resten av preregistreringen gjelder uendret, også regelen for MTU-skiftet. Den anvendes nå på `fbDomainShadowPrice` og `maxNetPos`, og datoen regnes ut fra de hentede dataene og føres i GT før analysen [GT-605].

  **Presisering** (ført `2026-11-10T06:51Z`, uavhengig gjennomgang før publisering): De 159 døgnene fra reconen var hentet før `A2` ble ført, samme dag, og ble tatt inn uendret [GT-613, GT-676]; overlappssammenligningen mot netPos, som er begrunnelsen for `A2`, var også kjørt før [GT-577]; resten av hentingen og analysekjøringene skjedde etter at `A2` var ført [GT-614, GT-657].

  **Kontroll.** Hentingen følger samme regler som før, med manifest og kontrollstreng [GT-604]. Analysen og den uavhengige celle-for-celle-kontrollen kjøres på nytt [GT-606]. Regresjonskontrollen krever at hendelse/ikke-hendelse per MTU og per time i overlappet er identisk med forrige kjøring [GT-607]. Tabellceller per år og delperiode kan endre seg [GT-608]. Ethvert annet avvik gir STOPP og rapport [GT-609].

- **`A3` — port B venter ikke på OSF; embargoen blir stående.** Ført `2026-11-10T06:37Z`, i samme commit som endringen i `PUBLISERINGSPORT.md` [GT-752]. Eiriks beslutning (`K-117`): «port B venter ikke på OSF, og embargoen blir stående» [GT-751].

  **Hva som endres.** Port B begynte med steget «Be om å avslutte embargoen på OSF-registreringen minst 48 timer før publisering, og bekreft at den er offentlig før Zenodo-publisering.» [GT-266] Det steget utgår [GT-751]. OSF-registreringen er innsendt med embargo til 31.12.2027 valgt [GT-753, GT-268], og embargoen blir stående [GT-751]. Manuskriptet skal ikke kalle embargoen godkjent [GT-754]. Kravet i `M3` om å oppdatere embargo-teksten når embargoen er opphevet, gjelder fortsatt [GT-677]. `PUBLISERINGSPORT.md` ligger i OSF-registreringen, og derfor føres endringen her [GT-550].

## Tolkninger (ikke avvik)

Her står valg der preregistreringen ikke gir én lesning. Hvert valg følger teksten, og hvert er ført før det ble brukt.

- **`T1` — utfallsrader per år og delperiode.** Ført `2026-11-10T04:16Z`. Under Utfall skal resultatene oppgis per kalenderår og for delperiodene før og etter JAO-MTU-skiftet, hver for seg og samlet [GT-206]. Utfallene rapporteres i krysset av år (`2024`, `2025`, `2026`, `alle`) og delperiode (`foer`, `etter`, `samlet`). Kombinasjoner uten MTU utelates. Andel hendelses-MTU står tom for `samlet` [GT-360, GT-378]. Krysset dekker begge lesningene.
- **`T2` — døgn mellom datasettenes skiftedatoer.** Ført `2026-11-10T04:16Z`. Disse døgnene hører til delperioden med 60-minutters MTU [GT-373, GT-378]. Har ett datasett 15-minutters MTU der, legges det på timen med varighetsvekting [GT-206, GT-378]. Det krever verdi i alle fire kvarter. Ellers er MTU-en manglende, uten interpolering.
- **`T3` — A11-nettoeksport per MTU.** Ført `2026-11-10T04:16Z`. Retningene er sonens grenseretninger i hentesettet, i alt 30 [GT-388]. En MTU tas med i korrelasjonen bare når alle sonens retninger har verdi i alle kvarter av MTU-en. Verdien er det varighetsvektede middelet av sum flyt ut minus sum flyt inn [GT-374].
- **`T4` — forventet rutenett.** Ført `2026-11-10T04:16Z`. Perioden er [2024-10-30T00:00Z, 2026-11-01T00:00Z) [GT-379]. Rutenettet har 60-minutters MTU fram til starten av skiftedøgnet og 15-minutters MTU derfra [GT-373, GT-378, GT-379]. En MTU i rutenettet uten NP eller minNP er manglende og telles per sone og måned (Mål, Manglende data).
- **`T5` — lengden på en CSV-rad.** Ført `2026-11-10T04:16Z`. Preregistreringen sier når et CSV-intervall har verdi, men ikke hvor lenge intervallet varer. Lengden settes til den minste avstanden til nabo-radenes tidsstempel, høyst 60 minutter. Rader med en annen lengde enn 15 eller 60 minutter telles i dekningstellingen [GT-378]. Det fantes 0 slike rader [GT-545].
- **`T6` — terskel for avvik i overlappet.** Ført `2026-11-10T04:16Z`. Terskelen er `|Δ| > 1e-9 MW`, som i revisjonskontrollen for A65 NO1 [GT-231].
- **`T7` — kalenderår.** Ført `2026-11-10T04:16Z`. Kalenderåret regnes i UTC ut fra starten på MTU-en, som for A68 [GT-377]. Det samme gjelder E_y og årsradene.

## Merknader fra dataruna (ikke avvik)

Merknadene følger av at preregistreringen er anvendt slik den står. Ingen regel er endret.

- **`M1` — netPos dekker bare slutten av perioden.** Ført `2026-11-10T04:28Z`. JAO Nordic `netPos` ga NoMatchingDataError for 575 forretningsdøgn og data for 158 [GT-488].
  - Første døgn med data er 2026-05-28 [GT-489].
  - Fraværet for første forretningsdøgn, 2024-10-30, var kjent før preregistreringen [GT-165, GT-483]. Nytt er at det varer helt til skiftedøgnet, som starter 2026-05-27T22:00:00+00:00 [GT-556].
  - `maxNetPos` har data i alle 733 døgn [GT-490].
  - Uten NP er MTU-en manglende for begge mål (Mål, Manglende data). Begge målene kan derfor bare regnes fra 2026-05-28 [GT-489].
- **`M2` — datoen for MTU-skiftet.** Ført `2026-11-10T04:28Z`. Regelen gir 2025-10-01 for maxNetPos og 2026-05-28 for netPos [GT-553, GT-554].
  - Datoen for netPos er første døgn med data i det hele tatt (`M1`).
  - Etter regelen er den seneste datoen skillet [GT-355, GT-373]. Det gir 2026-05-28, med skillet 2026-05-27T22:00:00+00:00 [GT-555, GT-556].
  - Døgnene fra 2025-10-01 til skillet hører dermed til delperioden med 60-minutters MTU, der maxNetPos har 15-minutters MTU og legges på timen (`T2`) [GT-378, GT-554].
  - netPos mangler i hele dette tidsrommet, så valget endrer ingen hendelsestall. Det endrer bare hvilken delperiode de manglende MTU-ene telles i.
  - Presisering ført `2026-11-10T06:41Z` (avhengighetssøk før publisering): `M1` og `M2` gjelder kjøringen før `A2`. Etter `A2` skifter `fbDomainShadowPrice` og `maxNetPos` begge 2025-10-01, og skillet er 2025-09-30T22:00:00+00:00 [GT-617, GT-618, GT-620].
- **`M3` — tilleggskrav i port B.** Ført `2026-11-10T06:17Z`, før endringen i `PUBLISERINGSPORT.md`. Eiriks krav (`K-115`): «Oppdater embargo-teksten i metode-kapittelet til faktisk status når embargoen er opphevet.» [GT-677] `PUBLISERINGSPORT.md` ligger i OSF-registreringen, og endringer i den føres derfor her [GT-550]. Kravet gjør port B strengere og endrer ingen metode.
