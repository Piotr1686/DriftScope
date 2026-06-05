# DriftScope

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

## Project layout

```
src/driftscope/
├── ingestion/      # seed CSV loader + regime split (2014-10-10 / 2022-03-25 boundaries)
├── methodology/    # the frozen science: BOCPD, MMD, co-occurrence, permutation,
│                   #   recurrence, multiple-testing (BH / Benjamini-Yekutieli),
│                   #   specification curve, block bootstrap + preregistration_v*.md
├── driftsim/       # planted-signal simulator (5 signals × 4 effect sizes) + calibration
├── reporting/      # disagreement protocol, static (matplotlib) + interactive (Plotly) plots,
│                   #   Quarto report
├── adaptive/       # honest watchlist (returns None unless DoD-3 AND DoD-4 pass)
├── pipeline.py     # end-to-end orchestrator: run_audit(draws) -> AuditReport
└── cli.py          # `driftscope run`
tests/              # 221 tests — calibration, invariants, FPR ≤ α, reproducibility
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
scikit-learn · Polars (not pandas) · Pydantic v2 · Typer · matplotlib + Plotly · Quarto report.
CPU-only; the full pipeline peaks at ~4 GB RAM.

## License

MIT.
