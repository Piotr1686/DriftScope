```
Druga (ostatnia) runda. Skup się na:
1. Czy zmiany z R1 są spójne i nie tworzą konfliktów?
2. Czy coś źle zaimplementowane (np. zmieniono model,
   ale nie zaktualizowano VRAM budgetu)?
3. Czy szacunki czasowe nadal realistyczne po zmianach?

NIE powtarzaj zarzutów z R1. NIE proponuj fundamentalnych zmian.
Format: zwięzły raport (max 100 linii).
```


ODPOWIEDŹ:
Raport końcowy – spójność zmian R1
1. Spójność zmian – brak konfliktów systemowych
Wszystkie modyfikacje z Appendix A (v1.0→v2.0) są spójne wewnętrznie i nie tworzą sprzeczności:

Usunięcie mapie – konsekwentnie wycofane z §3, §5 (Krok 8), §6.4, §8. Brak pozostałości.

Hook .webm + 3 panele – §2, §7.1, §6.5 (ffmpeg) zgodne. GitHub <video> vs Plotly iframe – rozwiązane.

Parquet shards zamiast SQLite dla permutacji – wszędzie spójne: §3 (stack), §4.1 (struktura), §5 (Krok 6), §6.2 (caching), §6.3 (fallback A), §6.5 (composability). SQLite pozostał tylko dla regime_meta (single writer) – brak kolizji.

DVC → git-lfs + archive.py – §3, §4.1, §8 (R12 usunięte), §10 (DoD-6). Determinizm przez ORDER BY CSV, nie binarkę.

Numba realistic speedup (2.7× simple, 10–30× MMD) – §3, §6.2, §6.5, §12 PoC – spójne. @njit(cache=True) selektywnie, nie globalnie.

KPSS przywrócone – §3 (statsmodels), §5 Krok 3, §11 – komplementarność z ADF zachowana.

Family‑aware FDR – §5 Krok 7 (Family A: 12 global, Family B: 300 per‑number), §10 DoD‑3 – osobne korekcje, bez mieszania.

Within‑draw permutations usunięte – §5 Krok 6, §11 – uzasadnione (tożsamość dla frequency vector).

MMD input space: frequency vectors per window – §3, §5 Krok 4 – RBF na sympleksie, nie na raw draws.

Complementary pillars + Disagreement Protocol – §1, §5 Krok 9.1, §10 DoD‑4 – operacjonalizuje 2/3 zgodność.

MMD bandwidth z training‑window only – §5 Krok 4 – anti‑leakage, zgodne z streaming setting.

BCPD: Dirichlet‑Multinomial conjugate – §3, §5 Krok 3, preregistration.md – specyfikacja dodana.

Seedy: SeedSequence – §4.1 (core/seeds.py), §5 Krok 6 – unikanie skorelowanych strumieni.

DrawRecord z Pydantic Field(ge=, le=) – §3, §4.1, §5 Krok 1 – fail‑fast.

--resume + parquet shards jako checkpoint – §3, §6.4 – naturalny restart.

pytest.approx w conftest – §3, §4.1 – tolerancja dla stochastyki.

core/guards.py – §4.1 – lekki monitoring, bez pełnego psutil.

Scraper + cached CSV – §3, §5 Krok 0‑1, §6.4 – fallback bezpieczny ToS.

Streamlit demoted do W9+ (stretch) – §3, §7.1 – primary demo = static HTML.

schema_validation.py + safe_insert – §4.1 – walidacja przy runtime.

Storey tylko dla Family A; spec curve 9 points – §5 Krok 7‑8 – ograniczone, bez combinatorial explosion.

Szacunki czasowe z W0 (8h) i rewizjami – §7.1, §9 – total MVP 210h (realistyczne). W4 (MMD stability PoC) 24h, W5 Decision Gate 16h.

5 planted signals konkretnie zdefiniowane – §5 Krok 5 – list, nie placeholder.

Negative Result Presentation Plan – §7.2 – osobna sekcja, nie tylko wzmianka.

block_bootstrap.py – §4.1, §5 Krok 6 – uzupełniony.

Graf §4.2 – db jako sink (terminal) – poprawiony, brak dwukierunkowości.

preregistration_v{N}.md z revision_reason – §5 Krok 4 – wersjonowanie bez sztywnej blokady.

MMD asymptotic stability at N=200 → UNVERIFIED, W4 PoC – §3, §5 Krok 4, §7.1 W4, §8 R13 – explicit warning.

HARDWARE_PUSH_CATALOG: Oś 0 + Oś 3 aplikują – §0, §6.2 – nie wyłączono całości.

2. Potencjalne nieprawidłowości implementacyjne (drobne, nie krytyczne)
Miejsce	Opis	Ocena
§4.2 vs §4.1 – „db (sink)” w grafie	Moduł src/driftscope/db/ zawiera schema.sql, queries.py itp., ale fizyczny plik artifacts/regime_meta.sqlite leży poza src/. Graf sugeruje, że methodology pisze bezpośrednio do db/ jako sink – w rzeczywistości pisze do artifacts/ przez db/queries.py. To nie jest konflikt, ale nieprecyzyjność.	Niska – nie wpływa na pipeline, jedynie na czytelność.
§6.1 VRAM budget – „N/A”	Zgodne z CPU‑only. W żadnej zmianie nie dodano GPU. Brak błędu.	✅
§6.4 fallbacki – SQLite wymieniony jako usunięty dla permutacji	Fallback C mówi „SQLite – usunięte”. W §3 SQLite pozostaje dla regime_meta. To jest poprawne – nie ma tu konfliktu, bo chodzi o różne tabele.	✅
§8 R13 (MMD instability) – trigger detekcji „False positive rate >10% w shuffled”	Brak zdefiniowanego progu w W4 PoC – zostaje do decyzji implementatora. Nie jest to błąd, tylko niedookreślenie.	Bardzo niska – do uzupełnienia w preregistration_v1.md.
3. Realizm szacunków czasowych po zmianach
W0 (8h) – realny na scraper PoC + cached CSV + power preview. Niezbędny przed W1.

W1 (30h) – 15+ modułów, ADF+KPSS+Bayesian CP, DrawRecord, testy. Optymistyczne, ale możliwe przy focusie.

W2 (32h) + W3 (32h) – 5 planted signals × 4 effect sizes + kalibracja. To największy pakiet. Realistyczny, jeśli sygnały są dobrze zdefiniowane (są).

W4 (24h) – MMD + PoC asymptotic stability. W sam raz.

W5 (16h) – Decision Gate. Realne.

W6 (24h) – Rigor layer (FDR, spec curve 9 points, Storey). Po usunięciu mapie i ograniczeniu spec curve – adekwatne.

W7 (24h) – Reporting + disagreement + adaptive. Rozsądne.

W8 (20h) – Polish MVP (README, hook, static HTML). Wystarczy.

Total MVP (210h) – przy 25–30h/tydzień daje 7–8 tygodni. Brief zakłada 8 tygodni (W0–W8) – realistyczne.

W9 (16h stretch) + W10 (20h optional) – portfolio i OS readiness. Możliwe do odłożenia.

Uwaga: W4 PoC (asymptotic stability MMD) jest ryzykowne – jeśli false positive rate >10% w shuffled, może wymagać redesign (większe N lub inny kernel). Brief to uwzględnia (R13, Plan B §7.3). Szacunki czasowe nie są zawyżone.

4. Ostateczna ocena
Spójność zmian: bardzo wysoka – żadnych konfliktów ani pozostałości po starych decyzjach.

Implementacja w briefie: poprawna – jedynie drobna nieścisłość w roli db/ vs artifacts/, bez wpływu na pipeline.

Szacunki czasowe: realistyczne – uwzględniają nowe elementy (W0, MMD PoC, disagreement) i cięcia (usunięte mapie, ograniczona spec curve).

Brief jest gotowy do handoff. Jedyna rekomendacja (opcjonalna): doprecyzować w §4.2, że db/ to warstwa dostępu, a fizyczny sink to artifacts/regime_meta.sqlite – ale nie blokuje to implementacji.


