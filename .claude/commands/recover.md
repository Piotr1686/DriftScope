# /recover — Audyt i naprawa stanu (bezpiecznik przed /end)

Cel: zanim zamkniesz sesję, sprawdź czy to, co faktycznie zostało zmienione, zgadza się
z planem i czy projekt jest w spójnym stanie. To komenda DIAGNOSTYCZNA — domyślnie
NIE modyfikuje kodu ani plików stanu; proponuje naprawy i czeka na decyzję.

Ustal "punkt odniesienia wstecz" (do którego momentu cofamy analizę), w tej kolejności:
   a) pole "Punkt odniesienia (git)" zapisane w last_session.md (HEAD z końca poprzedniej sesji),
   b) jeśli brak — ostatni checkpoint /save / ostatni wspólny commit,
   c) jeśli brak repo — analizuj pliki zmodyfikowane od daty ostatniej sesji.

Wykonaj:

1. ZMIANY FAKTYCZNE — zbierz co realnie zmieniło się od punktu odniesienia:
   - `git status` (niezacommitowane),
   - `git diff --stat <punkt_odniesienia>..HEAD` oraz diff working tree,
   - lista nowych/usuniętych plików.

2. PLAN vs RZECZYWISTOŚĆ — porównaj z "NASTĘPNY KROK" i "Co zostało" z last_session.md:
   - Co z planu zostało zrobione? (✓)
   - Co z planu NIE zostało ruszone? (⟳)
   - Co zostało zmienione, a NIE było w planie? (⚠ — możliwy scope creep / przypadek)

3. KONTROLA SPÓJNOŚCI (lekka, bez ciężkiego uruchamiania):
   - Czy pliki wspomniane w "następnym kroku" istnieją?
   - Ślady niedokończonej pracy: TODO/FIXME/XXX dodane w tej sesji, zakomentowany kod,
     `pass`/stuby, importy nieużywane.
   - Jeśli projekt ma testy/linter (pytest, ruff, mypy) — ZAPROPONUJ ich uruchomienie
     (nie uruchamiaj automatycznie jeśli kosztowne; zapytaj).
   - Zmiany w plikach konfiguracyjnych/zależnościach (pyproject.toml, .env.example)
     wymagające reinstalacji/migracji?
   - DriftScope-specyficzne: jeśli ruszono `methodology/` — czy jest update
     `preregistration_v{N}.md` z `revision_reason`? Jeśli ruszono decyzje z PROJECT_BRIEF.md
     — czy jest commit z rationale?

4. RAPORT NAPRAWCZY:

   🔧 AUDYT STANU (od [punkt_odniesienia] do teraz)

   ✅ Zrobione zgodnie z planem:
      [lista]
   ⟳ Z planu, niezrobione:
      [lista]
   ⚠ Zmiany poza planem / do weryfikacji:
      [lista]
   🩹 Sugerowane naprawy PRZED zamknięciem sesji (priorytetowo):
      1. [konkretna naprawa — plik:linia, co zrobić]
      2. ...
   🧪 Weryfikacja zalecana: [testy/linter do uruchomienia lub "brak"]

5. Zakończ pytaniem: "Naprawić teraz wskazane punkty, przejść do /end, czy kontynuować pracę?"
   Naprawy wykonuj TYLKO po potwierdzeniu.
