Analiza błędów w SWOT_ANALYSIS.md
Po dokładnym przeglądzie pliku SWOT_ANALYSIS.md w kontekście SEED_IDEA.md i HARDWARE_PUSH_CATALOG.md zidentyfikowałem kilka nieścisłości, błędów merytorycznych i logicznych. Poniżej znajduje się ich zestawienie wraz z uzasadnieniem i propozycjami poprawek.

🔴 Błąd 1 – Terminologiczny / merytoryczny (TDA)
Fragment:

"Topologiczna sygnatura zmienia się 'lokalnie', ale przekład na konkretne numerical findings ('liczba 23 zaczęła być częstsza') wymaga osobnej analizy eigenvectors filtration."

Problem:
W Topological Data Analysis (TDA) nie występuje pojęcie „eigenvectors filtration”. Eigenvectors są związane z algebra liniową (PCA, RMT), a nie z homologią trwałą. Autor najprawdopodobniej miał na myśli reprezentatywne cykle (representative cycles) lub generatory trwałych cech topologicznych, które pozwalają wskazać, które punkty (liczby) tworzą znaczące pętle (1-wymiarowa homologia) lub składowe spójności (0-wymiarowa). W przypadku łańcucha Markowa o skończonym stanie (50 liczb) można by analizować tzw. persistence landscapes lub heatmaps of persistence, ale nie „eigenvectors”.

Propozycja poprawy:
Zamienić na:

„…wymaga osobnej analizy reprezentatywnych cykli (representative cycles) w diagramie persystencji, co pozwala zidentyfikować, które liczby są zaangażowane w topologiczną strukturę.”

🟡 Błąd 2 – Niejasność / brak precyzji (konsensus LLM)
Fragment:

*„Konsensus 5/6 zewnętrznych LLM-ów.”*

Problem:
W kontekście pliku SEED_IDEA.md nie ma wyraźnej informacji, które 6 LLM-ów brało udział w cross-review, ani które z nich wskazywały TDA. W tekscie SWOT_ANALYSIS.md (nagłówek) wspomniano o „6 LLM-ach + 3 Claude” – ale to daje 9 opinii, a nie 6. Liczba 5/6 jest więc nieuzasadniona i wprowadza zamieszanie. Jest to błąd w referencji do źródła konsensusu.

Propozycja poprawy:
Usunąć stwierdzenie lub zastąpić je bardziej precyzyjnym:

*„Większość zewnętrznych LLM-ów (5 z 6, które bezpośrednio oceniały TDA) wskazała TDA jako najsilniejszą hipotezę H5.”*
Albo dodać stopkę z wyjaśnieniem, które modele brały udział i jak liczony był konsensus.

🟠 Błąd 3 – Niespójność z SEED_IDEA.md (rozmiary modeli)
Fragment (SWOT, punkt 1.6 G3):

„Jedyny finalista w Balanced tier (1–2GB FP16) […]”

Kontekst z SEED_IDEA (§10.1):

„Wszystkie kandydaci modeli są <1GB FP16”

Problem:
W SEED_IDEA autor deklarował, że wszystkie rozważane modele mieszczą się w <1 GB w FP16. Tymczasem G3 (Entropy Auditor) został sklasyfikowany jako 1–2 GB, co jest sprzeczne z tamtym założeniem. Nie jest to błędem samego SWOT, bo SWOT mógł zaktualizować wiedzę, ale brak jest komentarza o tej rozbieżności. Może to wprowadzić w błąd, jeśli czytelnik nie zauważy zmiany.

Propozycja poprawy:
Dodać w SWOT adnotację (np. w sekcji 1.6 lub w przypisie):

„Uwaga: W SEED_IDEA zakładano <1GB, ale dalsza analiza wykazała, że transformer z 5–10M parametrów w FP16 zajmuje ~1–2 GB, co kwalifikuje go do tieru Balanced według HARDWARE_PUSH_CATALOG.”

🟢 Błąd 4 – Potencjalny błąd logiczny w hybrydzie K2+K4 (zmiana reżimu)
Fragment (HYBRYDA-1):

„K4 trenowany tylko w obrębie wykrytego reżimu – daje honest predyktor warunkowy bez globalnego overfittingu.”

Problem:
Założenie, że zmiany są nagłe (change-pointy) i że w każdym segmencie proces jest stacjonarny. Jeśli drift jest monotoniczny (wzorzec #1 z SEED_IDEA), to podział na segmenty przez K2 może być sztuczny, a K4 trenowany na takich „kawałkach” nie dostanie pełnego obrazu dryfu. Hybryda może zatem nie wykryć monotonicznego trendu, który nie manifestuje się jako topologiczny change-point. SWOT nie omawia tego ograniczenia, choć dla wzorca #1 (monotonic drift) K2 nie jest optymalne narzędziem. Jest to luka w argumentacji, nie ścisły błąd, ale warto ją wskazać.

Propozycja uzupełnienia:
Dodać w sekcji zagrożeń dla HYBRYDA-1:

*„Ryzyko: Jeśli drift ma charakter monotoniczny (wzorzec #1), TDA może nie wykryć wyraźnych change-pointów, co uniemożliwi warunkowy trening K4. W takim przypadku hybryda nie przewyższy K4 standalone.”*

🔵 Błąd 5 – Niezgodność z HARDWARE_PUSH_CATALOG (liczby osi)
Fragment (G3):

*„wymaga 2 osi z katalogu (FP16 + torch.compile).”*

Problem:
W HARDWARE_PUSH_CATALOG dla tieru Balanced (1–4 GB) zalecane są co najmniej 2 osie, ale sugerowany zestaw to Oś 1 (kwantyzacja) + Oś 7 (runtime engine). Oś 3 (compilation) jest opcjonalna i może nie być konieczna, szczególnie na Windows z ograniczeniami torch.compile. Autor SWOT arbitralnie wybiera FP16 + torch.compile, podczas gdy bezpieczniejszym i bardziej zgodnym z katalogiem wyborem byłoby FP16 + ONNX Runtime (Oś 7). torch.compile na Windows ma status ⚠️ (problematyczny) – katalog wyraźnie ostrzega przed jego używaniem jako domyślnego.

Propozycja poprawy:
Zmienić na:

*„wymaga 2 osi z katalogu (FP16 + runtime engine, np. ONNX Runtime z CUDA EP lub kompilacja za pomocą torch.compile z ostrożnością, zgodnie z Osią 3)”*

🟣 Błąd 6 – Drobna nieścisłość w opisie Wasserstein-2
Fragment (Q2):

*„Wasserstein-2 distance to ciągła metryka driftu”*

Problem:
Wasserstein-2 jest metryką, ale nie jest „ciągła” w sensie topologicznym (metryki są z definicji ciągłe względem własnej topologii). Autor prawdopodobnie chodziło o to, że daje ciągły w czasie skalar (w przeciwieństwie do binarnego p-value). Lepiej mówić o wartości ciągłej lub skalarnej metryce. To raczej kwestia stylu, ale może wprowadzać w błąd matematycznie zorientowanego czytelnika.

Propozycja poprawy:

*„Wasserstein-2 distance to skalar metryczny, który płynnie zmienia się w czasie – daje ciągły pomiar siły driftu zamiast binarnego p-value.”*

Podsumowanie i rekomendowane korekty
#	Typ błędu	Lokalizacja w SWOT_ANALYSIS.md	Proponowana poprawka
1	Merytoryczny (terminologia TDA)	Sekcja 1.1 K2, Threats	Zamień „eigenvectors filtration” na „reprezentatywne cykle (representative cycles)”
2	Brak precyzji / referencji	Rekomendacja nr 1, akapit o konsensusie	Usuń „Konsensus 5/6 zewnętrznych LLM-ów” lub dodaj listę LLM-ów i sposób liczenia
3	Niespójność z SEED_IDEA	Sekcja 1.6 G3 (Balanced tier)	Dodaj przypis wyjaśniający rozbieżność z §10.1 SEED_IDEA
4	Luka logiczna w hybrydzie	HYBRYDA-1, brak omówienia monotonicznego driftu	Dodaj do Threats: ryzyko, że TDA nie wykryje change-pointów przy drifcie monotonicznym
5	Niezgodność z HARDWARE_PUSH_CATALOG	Sekcja 1.6 G3 („2 osie: FP16 + torch.compile”)	Zamień na „FP16 + runtime engine (ONNX Runtime CUDA EP) lub ostrożnie torch.compile”
6	Stylistyczno-matematyczny	Sekcja 1.2 Q2 („ciągła metryka”)	Zmień na „płynnie zmieniający się skalar” lub „ciągły w czasie pomiar”
Po wprowadzeniu powyższych poprawek analiza stanie się bardziej spójna z załączonymi materiałami i ustrzeże przed potencjalnymi nieporozumieniami przy implementacji.


