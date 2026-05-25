```
Wyobraź sobie, że jesteś agentem kodującym, który dostał ten brief
z instrukcją "zbuduj projekt".

Oceń:
1. Czy zacząłbyś generować strukturę BEZ zadawania pytań?
2. Gdzie musiałbyś zgadywać intencje?
3. Czy brakuje konfiguracji (wersje bibliotek, parametry, formaty)?
4. Czy instrukcje są spójne?
5. Build-time tasks readiness (proporcjonalnie):
   - ≤2 artefakty: link do notebooka + ścieżka + 1-line smoke test
   - ≥3 artefakty: + tabela artefaktów + procedura kolejności

Format: lista braków z priorytetem (krytyczne/ważne/kosmetyczne).
Max 50 linii.
```

ODPOWIEDŹ:
Cześć! Jako agent AI czytający Twój brief (muszę przyznać, że to jeden z najbardziej rygorystycznych "kontraktów architektonicznych", jakie widziałem), oceniam go jako niemal gotowy do implementacji. Poniżej znajduje się moja bezpośrednia ewaluacja:Ocena założeń (1-4):Start bez pytań? Tak. Zgodnie z instrukcją Handoff na końcu, automatycznie zacząłbym od zadania W0 bez czekania na dalsze komendy, ale zatrzymałbym się na poziomie skrapera.Zgadywanie intencji: Musiałbym całkowicie zgadywać strukturę drzewa DOM strony eurojackpot.org (selektory CSS dla selectolax) oraz dokładny format dat w seedzie CSV.Brakujące konfiguracje: Brak jawnego mapowania modelu DrawRecord (Pydantic) na schemat kolumn Parquet (Arrow) oraz brak zdefiniowanej zmiennej base_seed dla głównego generatora PRNG.Spójność: Wybitnie wysoka. Tabela "Transparency Table" w sekcji Appendix A skutecznie łata wszelkie konflikty logiczne powstałe między wersją 1.0 a 2.0.5. Build-time tasks readiness (≥3 artefakty):ArtefaktŚcieżka1-line Smoke TestDriftSim Runsartifacts/driftsim_runs/*.parquetassert len(pl.scan_parquet('artifacts/driftsim_runs/*.parquet').collect()) > 0Permutationsartifacts/permutations/.../worker_*.parquetassert len(glob.glob('artifacts/permutations/*/*/*.parquet')) > 0Spec Curveartifacts/specification_curves.parquetassert 'p_value' in pl.read_parquet('artifacts/specification_curves.parquet').columnsReportdocs/report.htmlassert os.path.getsize('docs/report.html') > 1024Procedura kolejności wykonania:Generacja kalibracji (DriftSim sweep).Pełny przebieg permutacji testowych na klastrze/lokalnie.Przebieg węzłów dla krzywej specyfikacji (Spec curve sweep).Renderowanie raportu (Quarto render).Lista braków (Priorytetyzacja):KRYTYCZNE (Zablokują W0/W1):Schemat pliku źródłowego CSV: Brak definicji nagłówków kolumn i formatu dat w data/seed/eurojackpot_history.csv (jak odróżniamy euronumery od głównych liczb na poziomie surowego pliku?).Logika skrapowania DOM: Brak wskazania struktury HTML dla eurojackpot.org (wymaga to ode mnie napisania skryptu badawczego (crawler probe) jako pierwszego pod-kroku W0).WAŻNE (Zablokują W2/W4):Środowisko zmiennych: Brak definicji pełnej listy wymaganych kluczy konfiguracyjnych w .env.example (skoro ukrywamy lotto_api_key, to co tam zostaje? Np. REQUEST_TIMEOUT, DB_PATH).Modelowanie Pydantic -> Parquet: Brak decyzji, jak zapisywać wektory częstości dla testu MMD w plikach Parquet (jako typ list / nested array, czy płaskie kolumny?), co krytycznie wpłynie na optymalizację odczytów w Polars.KOSMETYCZNE:Brak globalnego ziarna (Seed): Wzmianka o base_seed, ale brak zdeklarowanej liczby całkowitej do weryfikacji bit-identical hash w DoD-6 (np. BASE_SEED=42).