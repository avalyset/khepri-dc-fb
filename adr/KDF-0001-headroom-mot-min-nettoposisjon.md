# KDF-0001: Datasenterkøen målt mot flow-based importheadroom per NO-sone

- Status: først committet før koden, revidert etter Eiriks beslutninger (K-64, K-70, K-77); låses sammen med preregistreringen (tagg prereg-v1) når port A i `PUBLISERINGSPORT.md` er grønn
- Bestilt: 09.11.2026 [GT-178]
- Grunnlag: `GROUND_TRUTH.md` (alle tall og sitater under har GT-ID), `POSISJONERING.md`

## Spørsmålet

Vi stilte spørsmålet slik bestillingen formulerte det: «andel MTU der datasenterkøen lagt på som last i sonen ville kreve mer import enn min nettoposisjon tillater — per NO-sone, som funksjon av andelen f av køen» [GT-179].

## Hvorfor v1 ikke svarte

KHEPRI-DC v1 la køen på som flat last [GT-012] mot observert produksjon minus last (A75 [GT-008] minus A65 [GT-009]), men skrev selv: «Vi modellerer ikke priser, nett inne i sonene, respons i produksjon eller import, eller effektbalanse.» [GT-031]
Tolkningsreglene behandlet import som normal drift uten å teste noen grense: «Netto import er ikke mangel eller rasjonering.» [GT-032] og «Vannkraft og import er normal drift.» [GT-033]
Fortegnsskiftet i årssummen (NO4 ved f = 0,43 / 0,22 / 0,44 [GT-028], NO2 ved f = 0,50 / 0,63 / 0,58 [GT-029]) sier derfor ingenting om hvorvidt importen fantes i de timene den trengtes.

## Hvorfor kildene ikke svarte

Vi fant ingen side i kildearkivet slik det var i steg 2 (K-01–K-33) der datasenterord og nettoposisjonsord står sammen, utenom v1s egne filer [GT-135].
- Statnetts svarbrev til NVE regnet effekt mot en fast realisert kapasitet inn til Område Nord på 1050 MW [GT-130], men uten flow-based [GT-133], og risikoen gjaldt forbruksvekst «utover 850 MW» i Område Nord samlet [GT-132].
- NVE definerte positiv nasjonal effektbalanse [GT-436] som å dekke eget forbruk «uten å være avhengig av import» [GT-148] og sa at budområdebalansene er svært forenklet [GT-139].
- Statnetts «Langsiktig markedsanalyse 2026-60» [GT-313] viste at norsk produksjon og full nettoimport ikke er nok til å dekke forbruket i tørrår når alt reservert realiseres [GT-121, GT-435], og effektbalansen regnes der for hele Norge [GT-122], ikke per budområde.
- ERAA modellerte Nordic CCR med flow-based-domener [GT-110], men ACER-vedtaket nevner ikke Norge [GT-111], og arkivet har ingen pålitelighetsstandard for norske soner [GT-136].
- Menon antok at prosjektenes lokalisering «tar høyde for begrensninger i nettet» [GT-100].

## Valgt metode

Vi valgte headroom-definisjonen fra arXiv 2607.00977 [GT-072], slik bestillingen krevde: «import-/eksport-headroom = realisert sonenettoposisjon mot min/maks (arXiv 2607.00977)» [GT-192].
Artikkelen definerte importheadroom som «the absolute difference (in GW) between the realized zonal net position in Core» [GT-073] og minimum nettoposisjon, «minimum (for import) net position in Core» [GT-074].
Tre avvik fra artikkelen:
- vi bruker signert differanse, «H(t) = NP(t) − minNP(t)» [GT-182], ikke absoluttverdi, slik at NP under minNP gir H < 0 [GT-357, GT-375];
- vi legger til påslag og hendelse, «hendelse når L_f > H(t)» [GT-182];
- vi anvender definisjonen på Nordic, mens artikkelens data er «only published for the Core FBMC region» [GT-077].
For Norden publiserer JAO både realisert DA-nettoposisjon og min/maks nettoposisjon per budområde [GT-085, GT-086], med flow-based fra første levering: «first trading day for delivery on 30th October 2024» [GT-089].

## Forkastede alternativer

- Fast snittkapasitet som i svarbrevet (1050 MW [GT-130]) eller Områdeplan Nord (ca. 1200 MW [GT-126]): forkastet fordi grensene ikke er per budområde og ikke flow-based.
- Framoverskuende adekvansmodellering som i ERAA (flow-based-domener per målår [GT-110]): forkastet fordi spørsmålet gjelder observerte MTU-er, ikke scenarioer.
- Nasjonal import mot all utvekslingskapasitet (LMA [GT-121]): forkastet fordi forskjellen mellom sonene er poenget.

## Argument mot å gjøre studien

- Min nettoposisjon er et ytterpunkt av domenet og ikke samtidig gjennomførbar med andre ytterpunkter: «simultaneous feasibility of e.g. maximum flow on two borders cannot be guaranteed.» [GT-084] Resultatet blir derfor en optimistisk øvre grense for hvor mye import som fantes, gitt at domenet ikke flytter seg (neste punkt).
- Domenet ville flyttet seg med stor ny last, og systemegenskaper ligger utenfor metoden [GT-193]. Statnett begrunnet stansen nettopp i systemegenskaper: «Det er datasentrenes systemmessige egenskaper som utløser den midlertidige stansen.» [GT-037]
- Køtallene varierer med kilde og dato: 4 200 MW reservert og 9 100 MW i kø i pressemeldingen [GT-040, GT-041], 4 205 og 10 774 i Power BI samme dag [GT-045, GT-046], og ca. 4200 og ca. 8800 i «Langsiktig markedsanalyse 2026-60» [GT-120, GT-313].
- JAO-vilkårene hindrer publisering av rådata og avledede serier uten skriftlig samtykke [GT-061, GT-063].
- Realisert nettoposisjon ga ingen data for første leveringsdøgn [GT-165].

Vi gjør studien likevel fordi ingen side i kildearkivet slik det var i steg 2 (K-01–K-33) har datasenterord og nettoposisjonsord sammen utenom v1s egne filer [GT-135], og fordi svaret, gitt at domenet ikke flytter seg, blir en øvre grense som kan avvise, men ikke bekrefte, at importen var tilstrekkelig.
