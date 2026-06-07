"""Streamlit demo — DriftScope audit explorer (W9+ stretch, off-stack).

Uruchomienie:  streamlit run demo/app.py   (wymaga: pip install -e ".[demo]")

Zero nowej methodology — warstwa prezentacji reuzywajaca baterie audytu
(`reporting.prng_benchmark`) i suplement informacyjno-teoretyczny
(`reporting.information_theory`). Trzy zakladki:

  1. Detection matrix — bateria 4 detektorow nad PRNG (good/crypto/DEFECT) + realny
     EuroJackpot; FLAG vs clear (sensitivity/specificity na zywo).
  2. Entropy lens — histogram zlozonosci Lempel-Ziv 1976 (order-shuffle null) vs
     wartosc obserwowana per zrodlo + bz2 ratio. Money shot suplementu IT.
  3. Turing test — mini-gra: ktora z dwoch sekwencji to realny EuroJackpot, a ktora
     uniform? (wow opcja #5, intuicja niesciliwosci losowego ciagu).

Funkcje budujace dane/figury sa CZYSTE (testowalne bez runtime Streamlit); cala warstwa
`st.*` zyje w `render()` pod `__main__`, wiec import modulu nie odpala UI.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import plotly.graph_objects as go  # type: ignore[import-untyped]

import driftscope
from driftscope.core.config import settings
from driftscope.core.types import DrawRecord
from driftscope.driftsim.null_uniform import generate_uniform_draws
from driftscope.ingestion.lotto_scraper import load_seed_csv
from driftscope.reporting.information_theory import (
    information_test,
    lz76_null_distribution,
)
from driftscope.reporting.prng_benchmark import BenchmarkRow, build_sources, run_benchmark

_ROOT = Path(driftscope.__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Czyste budowniczowie danych / figur (testowalne bez Streamlit)
# ---------------------------------------------------------------------------

def detection_rows(
    n_draws: int, n_perm: int, seed: int, *, with_real: bool = True
) -> list[BenchmarkRow]:
    """Wiersze macierzy detekcji (bateria nad PRNG + opcjonalnie realny EuroJackpot)."""
    seed_csv = (_ROOT / settings.data_seed_path) if with_real else Path("___none___")
    return run_benchmark(n_draws=n_draws, n_perm=n_perm, seed=seed, seed_csv=seed_csv)


def detection_table(rows: list[BenchmarkRow]) -> list[dict[str, object]]:
    """Lista wierszy do `st.dataframe` — macierz detekcji z werdyktem FLAG/clear."""
    return [
        {
            "Source": r.source,
            "Class": r.klass,
            "n": r.n,
            "Family B": f"{r.family_b_reject}/{r.family_b_size}",
            "MMD p": round(r.mmd_p, 3),
            "Co-occ p": round(r.cooc_p, 3),
            "IT (LZ) p": round(r.it_p, 3),
            "Verdict": r.verdict,
        }
        for r in rows
    ]


def entropy_lens_figure(
    draws: list[DrawRecord], n_perm: int, seed: int, *, title: str = ""
) -> go.Figure:
    """Histogram zlozonosci LZ76 pod order-shuffle nullem + linia wartosci obserwowanej.

    Struktura (period/autocorr) → c_obs w LEWYM ogonie nulla (sekwencja sciliwa). Czysty
    null → c_obs w masie rozkladu (niesciliwy).
    """
    c_obs, null = lz76_null_distribution(draws, n_perm=n_perm, seed=seed)
    p_left = (1 + int(np.sum(null <= c_obs))) / (n_perm + 1)
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(x=null, nbinsx=40, name="null (order-shuffle)", marker_color="#90a4ae")
    )
    fig.add_vline(
        x=c_obs,
        line_color="#c62828",
        line_width=3,
        annotation_text=f"obserwowane c={c_obs}",
        annotation_position="top",
    )
    fig.update_layout(
        title=title or f"Lempel-Ziv 1976 — obs vs null (lewy-ogon p={p_left:.3f})",
        xaxis_title="zlozonosc LZ76 (nizsza = bardziej sciliwy / strukturalny)",
        yaxis_title="liczba permutacji",
        bargap=0.02,
        showlegend=False,
        height=420,
    )
    return fig


def turing_pair(
    n_window: int, seed: int
) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    """Dwie sekwencje losowan (5 liczb): realny EuroJackpot vs uniform syntetyczny.

    Zwraca (real_rows, fake_rows) jako listy posortowanych krotek 5-liczbowych. Kolejnosc
    prezentacji (kto jest A/B) decyduje warstwa UI.
    """
    path = _ROOT / settings.data_seed_path
    real_all = load_seed_csv(path)
    rng = np.random.default_rng(seed)
    start = int(rng.integers(0, max(1, len(real_all) - n_window)))
    real = [tuple(sorted(d.main_numbers)) for d in real_all[start : start + n_window]]
    fake_draws = generate_uniform_draws(n_window, "R3", rng)
    fake = [tuple(sorted(d.main_numbers)) for d in fake_draws]
    return real, fake


# ---------------------------------------------------------------------------
# UI Streamlit (tylko pod __main__ — import nie odpala render)
# ---------------------------------------------------------------------------

def render() -> None:  # pragma: no cover - warstwa UI
    import streamlit as st

    st.set_page_config(page_title="DriftScope — audit explorer", layout="wide")
    st.title("DriftScope — audit explorer")
    st.caption(
        "Ten sam battery, ktory nie znajduje nic w EuroJackpot, zapala sie na PRNG z "
        "wstrzyknietym defektem i milczy na krypto-PRNG. Suplement informacyjno-teoretyczny "
        "(Lempel-Ziv 1976) dodaje sekwencyjny obiektyw."
    )

    with st.sidebar:
        st.header("Parametry")
        n_draws = st.slider("Losowan na syntetyczne zrodlo", 300, 2000, 800, step=100)
        n_perm = st.slider("Permutacje (null)", 49, 499, 199, step=50)
        seed = st.number_input("Seed", value=42, step=1)
        with_real = st.checkbox("Dolacz realny EuroJackpot", value=True)

    tab_matrix, tab_entropy, tab_turing = st.tabs(
        ["🔬 Detection matrix", "🧬 Entropy lens", "🎲 Turing test"]
    )

    with tab_matrix:
        st.subheader("Macierz detekcji — 4 detektory × źródła z ground-truth labelem")
        rows = _cached_rows(int(n_draws), int(n_perm), int(seed), bool(with_real))
        st.dataframe(detection_table(rows), width="stretch", hide_index=True)
        sens = all(r.flagged for r in rows if r.klass == "DEFECT")
        spec = all(not r.flagged for r in rows if r.klass != "DEFECT")
        c1, c2 = st.columns(2)
        c1.metric("Sensitivity (defekt → FLAG)", "✓" if sens else "✗")
        c2.metric("Specificity (good/crypto/real → clear)", "✓" if spec else "✗")
        st.info(
            "IT (LZ) p jest celowo WYSOKIE dla `+bias` (marginal — order-shuffle go zachowuje) "
            "i NISKIE dla `+period` (struktura szeregowa). To jego komplementarna nisza — "
            "suplement, NIE 4. filar Disagreement Protocol (ten pozostaje 3/3)."
        )

    with tab_entropy:
        st.subheader("Lempel-Ziv 1976 — niesciliwosc jako sygnatura losowosci")
        sources = build_sources(int(n_draws), int(seed))
        names = [s[0] for s in sources]
        default_idx = names.index("EuroJackpot") if "EuroJackpot" in names else 0
        pick = st.selectbox("Źródło", names, index=default_idx)
        draws = next(d for nm, _, d in sources if nm == pick)
        st.plotly_chart(
            entropy_lens_figure(draws, int(n_perm), int(seed), title=f"{pick} — LZ76 obs vs null"),
            width="stretch",
        )
        res = information_test(draws, n_perm=int(n_perm), seed=int(seed))
        m1, m2, m3 = st.columns(3)
        m1.metric("LZ76 znormalizowane", f"{res.metadata['lz76_norm']:.3f}")
        m2.metric("p (lewy ogon)", f"{res.p_value:.3f}")
        m3.metric("bz2 ratio", f"{res.metadata['bz2_ratio']:.3f}")

    with tab_turing:
        st.subheader("Która sekwencja to realny EuroJackpot?")
        st.caption("Intuicja: oba wyglądają losowo. Audyt rozstrzyga to, czego oko nie widzi.")
        if "turing_seed" not in st.session_state:
            st.session_state.turing_seed = int(seed)
            st.session_state.turing_score = [0, 0]  # [trafione, wszystkie]
        real, fake = turing_pair(8, st.session_state.turing_seed)
        flip = st.session_state.turing_seed % 2 == 0
        left, right = (real, fake) if flip else (fake, real)
        def _rows(seq: list[tuple[int, ...]]) -> list[dict[str, object]]:
            return [{"draw": i + 1, "numbers": " ".join(map(str, r))} for i, r in enumerate(seq)]

        col_a, col_b = st.columns(2)
        col_a.write("**Sekwencja A**")
        col_a.table(_rows(left))
        col_b.write("**Sekwencja B**")
        col_b.table(_rows(right))
        guess = st.radio("Która jest REALNA?", ["A", "B"], horizontal=True)
        if st.button("Sprawdź"):
            real_is_a = flip
            correct = (guess == "A") == real_is_a
            st.session_state.turing_score[1] += 1
            if correct:
                st.session_state.turing_score[0] += 1
                st.success("Trafione — ale to zgadywanie. Real był: " + ("A" if real_is_a else "B"))
            else:
                st.error("Pudło. Real był: " + ("A" if real_is_a else "B"))
            hit, tot = st.session_state.turing_score
            st.write(
                f"Twój wynik: **{hit}/{tot}** ({hit / tot:.0%}) — oczekiwane ~50% (nieodróżnialne)."
            )
            st.session_state.turing_seed += 1


def _cached_rows(
    n_draws: int, n_perm: int, seed: int, with_real: bool
) -> list[BenchmarkRow]:  # pragma: no cover - wymaga runtime Streamlit
    import streamlit as st

    @st.cache_data(show_spinner="Liczę baterię detektorów…")
    def _inner(nd: int, npp: int, sd: int, wr: bool) -> list[BenchmarkRow]:
        return detection_rows(nd, npp, sd, with_real=wr)

    result: list[BenchmarkRow] = _inner(n_draws, n_perm, seed, with_real)
    return result


if __name__ == "__main__":
    render()
