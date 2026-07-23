"""Streamlit demo — DriftScope audit explorer (W9+ stretch, off-stack).

Usage:  streamlit run demo/app.py   (requires: pip install -e ".[demo]")

Zero new methodology — a presentation layer reusing the audit battery
(`reporting.prng_benchmark`) and the information-theoretic supplement
(`reporting.information_theory`). Three tabs:

  1. Detection matrix — battery of 4 detectors over PRNGs (good/crypto/DEFECT) + real
     EuroJackpot; FLAG vs clear (sensitivity/specificity live).
  2. Entropy lens — Lempel-Ziv 1976 complexity histogram (order-shuffle null) vs the
     observed value per source + bz2 ratio. The IT supplement's money shot.
  3. Turing test — mini-game: which of two sequences is the real EuroJackpot, and which
     is uniform? (wow option #5, the intuition of a random string's incompressibility).

The data/figure builder functions are PURE (testable without the Streamlit runtime); the
whole `st.*` layer lives in `render()` under `__main__`, so importing the module does not
launch the UI.
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
# Pure data / figure builders (testable without Streamlit)
# ---------------------------------------------------------------------------

def detection_rows(
    n_draws: int, n_perm: int, seed: int, *, with_real: bool = True
) -> list[BenchmarkRow]:
    """Detection matrix rows (battery over PRNGs + optionally the real EuroJackpot)."""
    seed_csv = (_ROOT / settings.data_seed_path) if with_real else Path("___none___")
    return run_benchmark(n_draws=n_draws, n_perm=n_perm, seed=seed, seed_csv=seed_csv)


def detection_table(rows: list[BenchmarkRow]) -> list[dict[str, object]]:
    """List of rows for `st.dataframe` — detection matrix with the FLAG/clear verdict."""
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
    """LZ76 complexity histogram under the order-shuffle null + observed-value line.

    Structure (period/autocorr) → c_obs in the LEFT tail of the null (compressible sequence).
    A clean null → c_obs in the bulk of the distribution (incompressible).
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
        annotation_text=f"observed c={c_obs}",
        annotation_position="top",
    )
    fig.update_layout(
        title=title or f"Lempel-Ziv 1976 — obs vs null (left-tail p={p_left:.3f})",
        xaxis_title="LZ76 complexity (lower = more compressible / structured)",
        yaxis_title="permutation count",
        bargap=0.02,
        showlegend=False,
        height=420,
    )
    return fig


def turing_pair(
    n_window: int, seed: int
) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    """Two draw sequences (5 numbers): real EuroJackpot vs synthetic uniform.

    Returns (real_rows, fake_rows) as lists of sorted 5-number tuples. The presentation order
    (who is A/B) is decided by the UI layer.
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
# Streamlit UI (only under __main__ — importing does not launch render)
# ---------------------------------------------------------------------------

def render() -> None:  # pragma: no cover - UI layer
    import streamlit as st

    st.set_page_config(page_title="DriftScope — audit explorer", layout="wide")
    st.title("DriftScope — audit explorer")
    st.caption(
        "The same battery that finds nothing in EuroJackpot fires on a PRNG with an "
        "injected defect and stays silent on crypto PRNGs. The information-theoretic "
        "supplement (Lempel-Ziv 1976) adds a sequential lens."
    )

    with st.sidebar:
        st.header("Parameters")
        n_draws = st.slider("Draws per synthetic source", 300, 2000, 800, step=100)
        n_perm = st.slider("Permutations (null)", 49, 499, 199, step=50)
        seed = st.number_input("Seed", value=42, step=1)
        with_real = st.checkbox("Include real EuroJackpot", value=True)

    tab_matrix, tab_entropy, tab_turing = st.tabs(
        ["🔬 Detection matrix", "🧬 Entropy lens", "🎲 Turing test"]
    )

    with tab_matrix:
        st.subheader("Detection matrix — 4 detectors × sources with a ground-truth label")
        rows = _cached_rows(int(n_draws), int(n_perm), int(seed), bool(with_real))
        st.dataframe(detection_table(rows), width="stretch", hide_index=True)
        sens = all(r.flagged for r in rows if r.klass == "DEFECT")
        spec = all(not r.flagged for r in rows if r.klass != "DEFECT")
        c1, c2 = st.columns(2)
        c1.metric("Sensitivity (defect → FLAG)", "✓" if sens else "✗")
        c2.metric("Specificity (good/crypto/real → clear)", "✓" if spec else "✗")
        st.info(
            "IT (LZ) p is deliberately HIGH for `+bias` (marginal — order-shuffle preserves it) "
            "and LOW for `+period` (serial structure). That is its complementary niche — a "
            "supplement, NOT a 4th Disagreement Protocol pillar (which stays 3/3)."
        )

    with tab_entropy:
        st.subheader("Lempel-Ziv 1976 — incompressibility as a signature of randomness")
        sources = build_sources(int(n_draws), int(seed))
        names = [s[0] for s in sources]
        default_idx = names.index("EuroJackpot") if "EuroJackpot" in names else 0
        pick = st.selectbox("Source", names, index=default_idx)
        draws = next(d for nm, _, d in sources if nm == pick)
        st.plotly_chart(
            entropy_lens_figure(draws, int(n_perm), int(seed), title=f"{pick} — LZ76 obs vs null"),
            width="stretch",
        )
        res = information_test(draws, n_perm=int(n_perm), seed=int(seed))
        m1, m2, m3 = st.columns(3)
        m1.metric("LZ76 normalized", f"{res.metadata['lz76_norm']:.3f}")
        m2.metric("p (left tail)", f"{res.p_value:.3f}")
        m3.metric("bz2 ratio", f"{res.metadata['bz2_ratio']:.3f}")

    with tab_turing:
        st.subheader("Which sequence is the real EuroJackpot?")
        st.caption("Intuition: both look random. The audit resolves what the eye cannot see.")
        if "turing_seed" not in st.session_state:
            st.session_state.turing_seed = int(seed)
            st.session_state.turing_score = [0, 0]  # [hits, total]
        real, fake = turing_pair(8, st.session_state.turing_seed)
        flip = st.session_state.turing_seed % 2 == 0
        left, right = (real, fake) if flip else (fake, real)
        def _rows(seq: list[tuple[int, ...]]) -> list[dict[str, object]]:
            return [{"draw": i + 1, "numbers": " ".join(map(str, r))} for i, r in enumerate(seq)]

        col_a, col_b = st.columns(2)
        col_a.write("**Sequence A**")
        col_a.table(_rows(left))
        col_b.write("**Sequence B**")
        col_b.table(_rows(right))
        guess = st.radio("Which one is REAL?", ["A", "B"], horizontal=True)
        if st.button("Check"):
            real_is_a = flip
            correct = (guess == "A") == real_is_a
            st.session_state.turing_score[1] += 1
            if correct:
                st.session_state.turing_score[0] += 1
                st.success("Hit — but it's a guess. Real was: " + ("A" if real_is_a else "B"))
            else:
                st.error("Miss. Real was: " + ("A" if real_is_a else "B"))
            hit, tot = st.session_state.turing_score
            st.write(
                f"Your score: **{hit}/{tot}** ({hit / tot:.0%}) — ~50% expected (indistinguishable)"
            )
            st.session_state.turing_seed += 1


def _cached_rows(
    n_draws: int, n_perm: int, seed: int, with_real: bool
) -> list[BenchmarkRow]:  # pragma: no cover - requires the Streamlit runtime
    import streamlit as st

    @st.cache_data(show_spinner="Computing the detector battery…")
    def _inner(nd: int, npp: int, sd: int, wr: bool) -> list[BenchmarkRow]:
        return detection_rows(nd, npp, sd, with_real=wr)

    result: list[BenchmarkRow] = _inner(n_draws, n_perm, seed, with_real)
    return result


if __name__ == "__main__":
    render()
