# PUBLISERINGSPORT — KHEPRI-DC-FB

Portene som må være grønne før noe låses eller publiseres. Kravene er Eiriks bestillinger og beslutninger (K-50, K-53, K-64, K-70, K-77, K-92, K-115 og K-117), gjengitt via `GROUND_TRUTH.md`. Ingen port hoppes over: «Ingen port hoppes over; ingen publisering «for å rette etterpå».» [GT-253]

## Publiseringsramme for denne runden

- arXiv: «ingen innsending i denne runden» [GT-244].
- OSF: «preregistreringen låses nå, i denne runden, når port A er grønn» [GT-245].
- Zenodo: «KHEPRI-DC-FB får eget konsept» [GT-246], ikke ny versjon av KHEPRI-DC v1 (konsept-DOI 10.5281/zenodo.23887355 [GT-247]). «Ingen Zenodo-publisering i denne runden.» [GT-248]
- «Én publisering per objekt, ingen versjonsrunder.» [GT-249]
- «Ingen push, ingen Zenodo, ingen arXiv i denne runden.» [GT-258]

Rammen over gjaldt låsingsrunden. Publiseringen er bestilt i K-117, og port B under gjelder den.

## Port A — låsing av preregistreringen

Vilkår: «frysregel a–f lest linje for linje fra disk; check_anchors.py grønn; uavhengig gjennomgang av egen Opus-underagent; alle tall VERIFISERT×2» [GT-250].

Frysregelens feilklasser a–f: «intern numerisk selvmotsigelse, påstand mot tabellverdi, metrikk-overclaim, uverifiserte eksterne tall, stale status, tittel/metadata mot innhold» [GT-254].

Gjennomgangsløkka har tak: «Maks 2 runder.» [GT-255] Gjenstår funn etter siste runde, låses ingenting.

Etter andre runde godkjente Eirik en tredje runde som siste innholdsrunde [GT-409]. Finner den feil som kan endre resultatene, gjelder: «STOPP, ingen låsing, rapporter.» [GT-413] Finner den bare ordlyd, rettes den, ankersjekken kjøres, gjennomgåeren verifiserer bare differansen, og deretter låses det [GT-414].

Til OSF: «Last opp preregistreringen, KDF-0001 og PUBLISERINGSPORT.md. GT, kildearkiv og data lastes IKKE opp.» [GT-257]

Oppsett:
- Ikke under Khepri-TSFM: «Ikke registrer under osf.io/dbwvx (Khepri-TSFM).» [GT-267]
- Registreringen startes fra bunnen av, uten eksisterende prosjekt (steg 1: «Select “No”» [GT-273]), fordi «An OSF Project is not required to create a registration.» [GT-275] og registrering uten prosjekt foretrekkes [GT-270]. OSF oppretter likevel et tilknyttet prosjekt: «In both cases, the new registration will have a connected OSF project» [GT-272]. Det får bare de tre filene over.
- Det tilknyttede prosjektet blir skrivebeskyttet «February 19, 2027» [GT-276], mens «Your registration is a separate record and is not affected by the changes to OSF Projects.» [GT-277]
- Som Khepri-TSFM (osf.io/hncz5 [GT-314]): mal «Secondary Data Preregistration» [GT-259] i «OSF Registries» [GT-262], lisens «CC-By Attribution 4.0 International» [GT-261], og fagene «Engineering» og «Physical Sciences and Mathematics» [GT-264].
- Tarballens sha256 føres i OSF-skjemaet ved låsing [GT-410].
- Embargo: «Embargo til 31.12.2027.» [GT-268] Embargo kan være «Maximum 4 years from creation date» [GT-274].

## Port B — publisering av resultater, paper eller data

Første steg var: «Be om å avslutte embargoen på OSF-registreringen minst 48 timer før publisering, og bekreft at den er offentlig før Zenodo-publisering.» [GT-266] Steget utgår etter Eiriks beslutning: «port B venter ikke på OSF, og embargoen blir stående» [GT-751]. Endringen er ført som avvik `A3` i `AVVIK_FRA_PREREG.md` [GT-752]. Registreringen er innsendt med embargo til 31.12.2027 valgt [GT-753].

Hva som publiseres: «JAO-rådata og JAO-tidsserier publiseres ikke.» [GT-546] «Det publiseres resultater (utfallstabeller og tall i manuskriptet), med JAO oppgitt som kilde, og kode med henteskript slik at andre kan hente dataene selv.» [GT-547]

«Port B venter ikke på skriftlig samtykke fra JAO.» [GT-548] Kravet om samtykke [GT-251] er fjernet etter Eiriks beslutning, og endringen er ført som avvik `A1` i `AVVIK_FRA_PREREG.md` [GT-550]. «Skulle JAO ha innvendinger etter publisering, håndteres det med en rettelse.» [GT-551]

Deretter publiseres ingenting før alt dette er oppfylt:
- alle tall VERIFISERT×2 og `check_anchors.py` grønn [GT-250];
- «Oppdater embargo-teksten i metode-kapittelet til faktisk status når embargoen er opphevet.» [GT-677] Ført som merknad `M3` i `AVVIK_FRA_PREREG.md` [GT-550].
- «fullt avhengighetssøk etter gamle verdier i alle artefakter; frysregel a–f; uavhengig gjennomgang; Brevet sist; Zenodo eget konsept, versjon 1.0, .zenodo.json med isSupplementTo til taggen; arXiv tidligst desember som ny innsending, Comments ≤ 400 tegn målt» [GT-252].

## Status

- Port A: rundetellingen startet på den committede endelige versjonen [GT-351], etter at 3c-supplementet med A11 var committet [GT-371], og den tredje runden var den siste [GT-409]. Utfallet av hver runde står i meldingen til den signerte taggen `prereg-v1`. Taggen settes bare når port A er grønn; finnes taggen, var port A grønn ved låsing.
- Port B: lukket; vilkårene under Port B er ikke oppfylt ennå.
