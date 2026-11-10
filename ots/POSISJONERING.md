# POSISJONERING — KHEPRI-DC-FB

Spørsmål: hvor ofte ville datasenterkøen i en NO-sone kreve mer import enn TSO-enes publiserte importgrense (flow-based min nettoposisjon) tillater?

Hver celle viser til rader i `GROUND_TRUTH.md`. Ingen celle bruker en verdi som ikke står der. Kildene er K-01–K-34 i `kilder/KILDER_MANIFEST.csv`.

## Hva finnes / hva finnes ikke

| Byggestein | Hva finnes | Hva finnes ikke |
|---|---|---|
| Datasenterkø per NO-sone (MW) | Statnett Power BI per sone 02.11 [GT-016–GT-027] og 09.11 [GT-045–GT-051]. Nasjonale kø- og reservasjonstall varierer med kilde og dato: pressemelding 09.11 [GT-039, GT-040, GT-041], LMA [GT-120], NVE 37/2026 [GT-157, GT-158], Faktaportalen [GT-095]. | Et versjonert Statnett-datasett per sone: 09.11-tallene er en egen avlesning uten skjermbildearkiv [GT-045]. |
| Observert balanse per sone med køen lagt på | KHEPRI-DC v1: timer 2023–2025 [GT-007], flat last [GT-012], brukstid [GT-013, GT-015], fortegnsskifte i årssummen [GT-028, GT-029, GT-030]. | Import testes ikke i v1 [GT-031, GT-032, GT-033]. |
| Publisert importgrense per sone per MTU | JAO Nordic min/maks nettoposisjon per budområde per MTU [GT-082, GT-086], realisert DA-nettoposisjon [GT-085, GT-087], recon-uke med NO1–NO5 [GT-056, GT-057, GT-058, GT-059]. Flow-based fra første levering 30.10.2024 [GT-089, GT-090]; 15-minuttersoppløsning fra våren 2025 [GT-091]. | Samtidig gjennomførbarhet av min/maks garanteres ikke [GT-083, GT-084]. Håndboka oppgir «24 MTUs» per døgn, mot 96 kvarter i recon-dataene [GT-088, GT-058]. |
| Metode: headroom mot min nettoposisjon | arXiv 2607.00977: importheadroom = realisert sonenettoposisjon mot minimum nettoposisjon [GT-071, GT-072, GT-073, GT-074, GT-075, GT-076]. | Bare Core, tyske kraftverk 2022–2024 [GT-077, GT-078]; ingen nordiske soner, ingen ny last [GT-079, GT-080]. |
| Effekt i del av sone mot eksplisitt importkapasitet | Statnett svarbrev 15.06.2026: realisert kapasitet inn til Område Nord [GT-130], varighet av utkobling [GT-131], grense for forbruksvekst [GT-132], nabopåvirkning [GT-052]. Områdeplan Nord: Ofoten ved intakt nett [GT-126]. | Ikke flow-based [GT-133]; Område Nord og reservert forbruk totalt, ikke datasenterkøen per sone [GT-130, GT-132]. |
| Sonevis effektbalanse (NVE) | Importbehov per budområde i én topplasttime [GT-140, GT-142]; observert nettoposisjon og flytbasert 2025 [GT-149, GT-150]. | Bare nasjonal vurdering og forenklet budområdebilde [GT-138, GT-139]; effektbalanse uten import [GT-148]; ingen importgrense/min nettoposisjon [GT-151, GT-141]; importmuligheter ikke analysert [GT-144, GT-145]. |
| Nasjonal import og datasenterscenarioer | LMA: full nettoimport ikke nok når alt reservert realiseres [GT-121], effekt for hele Norge [GT-122]. NVE 37/2026: netto import i 17 av 30 værår [GT-159], jevn datasenterprofil [GT-156]. KMA: ikke nok importkapasitet i ett scenario [GT-118]. Menon: priser per prisområde [GT-102]. | Ingen nettoposisjon i KMA/LMA [GT-117, GT-123]; ingen flytbasert i NVE 37/2026 [GT-160]; Menon antar nettbegrensninger løst [GT-100, GT-101]; NVE-metoden uten import og sone [GT-163]. |
| Adekvans med flow-based i Norden | ACER 06/2026: Nordic CCR med sju FB-domener per målår [GT-108, GT-110, GT-112]. ERAA Annex 6: adekvansproblemer i NOS1 2030–2035 [GT-103], Statnett uenig [GT-104], flow-based-modellering som mulig årsak [GT-105]. | Norge nevnes ikke i ACER-vedtaket [GT-111]; ingen pålitelighetsstandard eller LOLE/EENS for norske soner i arkivet [GT-106, GT-136]; standard bare for SE03/SE04 [GT-107]. |
| Datasenterkø × flow-based importgrense per NO-sone | — | Ingen side i arkivet har datasenter- og nettoposisjonsord sammen, utenom v1s egne filer [GT-135]. Nullbelegg per kilde: [GT-093, GT-094, GT-097, GT-101, GT-117, GT-123, GT-133, GT-141, GT-145, GT-151, GT-160, GT-163, GT-079, GT-080]. |

## Konklusjon for steg 2

Ingen kilde i arkivet besvarer spørsmålet [GT-135]. De nærmeste er svarbrevet fra Statnett (fast snittkapasitet inn til Område Nord, ikke flow-based) [GT-130, GT-133] og arXiv 2607.00977 (headroom-metoden, men Core/Tyskland) [GT-073, GT-077]. Ingen STOPP.
