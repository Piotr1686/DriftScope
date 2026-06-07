# DriftScope

[![CI](https://github.com/Piotr1686/DriftScope/actions/workflows/ci.yml/badge.svg)](https://github.com/Piotr1686/DriftScope/actions/workflows/ci.yml)

**A stationarity audit framework for streaming discrete-valued processes — with calibrated
detector hallucination rates.**

DriftScope audits discrete streams that are *uniform by design* for non-stationarity. The
flagship case study is **EuroJackpot**, a process intended to be uniform-random, with a
**known ground truth**: the euro-number pool changed its rules twice (2014, 2022) while the
main 1–50 pool never did. This makes it a built-in positive/negative control — the right
setting to ask not "did we find an anomaly?" but "does the detector fire on a real signal
*and stay silent where there is none?*"

The project is **methodological**. It neither claims nor seeks to predict lottery outcomes in
any actionable sense; the lottery is a convenient ground-truth benchmark for a reusable audit
framework (NIST RNG, cryptographic PRNGs, and financial random walks are natural stretch
targets).

📊 **Live report:** https://piotr1686.github.io/DriftScope/
📄 **Executive summary (1-page, print → PDF):** https://piotr1686.github.io/DriftScope/executive_summary.html

## The headline

Run on 958 real EuroJackpot draws (2012–2026), the framework delivers an unambiguous verdict:

- **Positive control (euron / BOCPD, full stream):** `reject = True`. Change-points detected
  at **2014-11-28** and **2022-03-29** — the first draws reflecting each rule change (ground
  truth, DoD-1b).
- **Negative control (main 1–50, three pillars, *per regime*):** R1 **0/3**, R2 **1/3**,
  R3 **0/3**. The lone R2 single-pillar flag (one number pair) is classified as
  *"requires power context"* — **not a finding** (P ≈ 14% of one of three regimes flagging by
  chance at α = 0.05).
- **Family B FDR (per-number, Benjamini-Yekutieli over 150 hypotheses):** **0/150** rejections.
- **Honest watchlist (DoD-5):** **None** — an honest null, not an empty list or an extrapolation.

The framework confirms the known signal and does not hallucinate one where there is none.

## How it works — three independent pillars

The verdict rests on **three mutually non-redundant families** of detectors (the *Disagreement
Protocol*). Each sees a different class of deviation; a signal is classified by agreement
(3/3 · 2/3 · 1/3 · 0/3):

| Pillar | Family | Detects | Blind to |
|---|---|---|---|
| **H1** (BOCPD) | temporal / global | change-points in the symbol distribution | pair structure |
| **MMD** | distributional | windowed frequencies departing from uniform | pair structure |
| **Co-occurrence** | joint | over-represented number pairs under uniform margins (`pair_corr`) | marginal signal |

The key property: `pair_corr` is visible **only** to co-occurrence — chi²/MMD are provably blind
to it when the margins are preserved (power ≈ FPR). Every planted signal class has at least one
champion pillar, and the families do not overlap.

## Reusability — the same audit on PRNGs

A null result on EuroJackpot is only worth trusting if the instrument is *sensitive*. The same
battery (Family B + MMD + co-occurrence) applied to streams with a **known ground truth**:

| Source | Class | Verdict |
|---|---|---|
| MT19937, Xorshift64 | good (non-crypto) | **clear** |
| ChaCha20, AES-CTR-DRBG | cryptographic | **clear** (specificity) |
| MT19937 + injected bias | **defect** (marginal) | **FLAG** — narrow (Family B + MMD) |
| MT19937 + period-truncation | **defect** (short cycle) | **FLAG** — broad (all 3 pillars) |
| EuroJackpot (main 1–50) | real | **clear** (the honest null above) |

The same detector that stays silent on EuroJackpot **lights up on planted PRNG defects and
clears two crypto-grade RNGs** — and the *pattern* of which pillars fire reveals the defect
*kind* (a marginal bias hits Family B + MMD narrowly; a short period freezes the whole
distribution and trips all three). The honest null is a calibrated instrument, not blindness. The
framework is detector-agnostic: feeding it a PRNG stream is just a different `DrawRecord` source
(`ingestion/rng_streams.py`). Reproduce: `python scripts/prng_benchmark.py`.

**A supplementary information-theoretic lens.** Beyond the three core pillars, a **Lempel-Ziv 1976**
complexity test (`reporting/information_theory.py`; order-shuffle null over draw blocks, with a
`bz2` compression-ratio cross-check) adds a *sequential* view. It conditions on both the marginal
*and* the within-draw joint, so it is deliberately blind to a marginal bias (`+bias` stays clear)
yet fires sharply on the **period-truncation** defect (a frozen cycle is compressible) — and reads
real EuroJackpot as incompressible / clear (p ≈ 0.75). It is a **supplement, not a fourth
Disagreement-Protocol pillar** — that pillar set stays three-way (DoD-4 = 3/3).

## Methodological discipline

- **Pre-registration.** Every methodological choice (statistics, nulls, thresholds, effect-size
  grids) is frozen in `src/driftscope/methodology/preregistration_v7.md` (ACTIVE). Each revision
  carries a `revision_reason`, explicitly split into *clean* vs *data-informed* (the §0
  discipline).
- **Calibrated nulls.** Every detector's false-positive rate is validated ≈ α on an honest
  uniform null (DoD-2); the BOCPD reject threshold is calibrated *per field* (FPR ≈ 0.05).
- **Per-regime scope.** The negative control and Family B are evaluated *within each rule regime*
  (R1 = 133, R2 = 389, R3 = 436 draws); the 1–50 pool is invariant across regimes, so each is an
  independent negative control.
- **Reproducibility (DoD-6).** Every detector is a pure function of the stream; the RNG is seeded
  from the data contents (⊕ `BASE_SEED`), independent of call order. `scripts/archive.py` emits a
  deterministic SHA-256 manifest (a cold-machine re-run is bit-identical).

## Quickstart

Requires **Python 3.10**.

```bash
# install (editable, with dev tools)
pip install -e ".[dev]"
# On Windows 11 / Miniconda, if pip hits an SSL cert error:
#   pip install -e ".[dev]" --trusted-host pypi.org --trusted-host files.pythonhosted.org

# run the full audit on the bundled seed CSV (958 draws) and print the verdict
driftscope run

# options
driftscope run --n-perm 999 --figures --hook      # add the .webm hook animation (needs ffmpeg)
driftscope run --seed-csv path/to/draws.csv        # audit your own stream
```

`driftscope run` prints the positive/negative control verdict and the honest watchlist, and
(by default) writes the control-comparison and BOCPD figures to `artifacts/`.

Reproduce the full HTML report:

```bash
quarto render src/driftscope/reporting/report.qmd --to html
```

Explore interactively (optional Streamlit demo — detection matrix, the LZ76 *entropy lens*, and a
real-vs-uniform Turing test):

```bash
pip install -e ".[demo]"
streamlit run demo/app.py
```

## Project layout

```
src/driftscope/
├── ingestion/      # seed CSV loader + regime split + PRNG stream adapters (rng_streams.py)
├── methodology/    # the frozen science: BOCPD, MMD, co-occurrence, permutation,
│                   #   recurrence, multiple-testing (BH / Benjamini-Yekutieli),
│                   #   specification curve, block bootstrap + preregistration_v*.md
├── driftsim/       # planted-signal simulator (5 signals × 4 effect sizes) + calibration
├── reporting/      # disagreement protocol, static (matplotlib) + interactive (Plotly) plots,
│                   #   PRNG benchmark, information-theory supplement (LZ76), Quarto report
├── adaptive/       # honest watchlist (returns None unless DoD-3 AND DoD-4 pass)
├── pipeline.py     # end-to-end orchestrator: run_audit(draws) -> AuditReport
└── cli.py          # `driftscope run`
scripts/            # archive (SHA-256 manifest), prng_benchmark (reusability showcase)
demo/               # Streamlit audit explorer (optional, `pip install -e ".[demo]"`)
tests/              # 260 tests — calibration, invariants, FPR ≤ α, reproducibility, PRNG, info-theory
data/seed/          # eurojackpot_history.csv (958 draws, committed)
```

## Definition of Done

| DoD | Validated by | Criterion |
|---|---|---|
| DoD-1 | BOCPD on euron vs main | detects 2014/2022 pool changes; clean on 1–50 negative control |
| DoD-2 | `methodology/permutation.py` | FPR ≤ α = 0.05 ± MC error under a shuffled null |
| DoD-3 | `methodology/multiple_testing.py` | family-aware FDR (BH / Benjamini-Yekutieli) |
| DoD-4 | `reporting/disagreement.py` | every signal classified 3/3 · 2/3 · 1/3 · 0/3 |
| DoD-5 | `adaptive/honest_watchlist.py` | returns `None` when DoD-3/4 fail |
| DoD-6 | `core/seeds.py` + manifest | cold-machine re-run is bit-identical |

## Stack

Python 3.10 · NumPy 2.x + Numba 0.65.1 (JIT hot loops) · statsmodels · ruptures · SciPy ·
scikit-learn · Polars (not pandas) · Pydantic v2 · Typer · matplotlib + Plotly · Quarto report ·
optional Streamlit demo. CPU-only; the full pipeline peaks at ~4 GB RAM.

## License

MIT.
