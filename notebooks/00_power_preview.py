# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#   kernelspec:
#     display_name: Python 3.10
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 00 — Analytic Power Preview (W0)
#
# **Cel (PROJECT_BRIEF §5 Krok 0, roadmap W0):** zanim DriftSim cokolwiek wygeneruje,
# policz *analitycznie*, jakie effect sizes są w ogóle wykrywalne przy realnej liczbie
# losowań. Wynik jest **co-primary deliverable** (§7.2) — tabela "minimum detectable
# effect size @ 80% power" JEST wkładem niezależnie od tego, czy real data coś pokaże.
#
# ## Założenia (jawne — do potwierdzenia przed W2)
#
# 1. **Testy biegną PER REŻIM** (`regime_split.py`), więc wiążąca jest moc przy n
#    per-reżim, NIE pooled. Liczby ZWERYFIKOWANE na committed seed CSV (958 losowań,
#    2012-03-23 → 2026-05-26; granice z preregistration_v2 §1):
#    - R1 (2012-03-23 → 2014-10-03): n=133, euron [1..8]  (✓ 2/8)
#    - R2 (2014-10-10 → 2022-03-18): n=389, euron [1..10] (✓ 2/10)
#    - R3 (2022-03-25 → 2026):       n=436, euron [1..12] (✓ 2/12)
#    - pooled:                       n=958
#    UWAGA: brief miejscami pisze n=1500 — to BŁĄD (real total = 958; §6.1 "~700" też off).
#    0 losowań w luce 2014-10-03..10 → korekta daty 2014-10-10 jest czysta.
# 2. **Frequency-shift effect size** (preregistration_v2 §6, signal #1): jedna kategoria
#    p_k = 1/50 + δ, pozostałe 49 absorbują -δ/49 (suma = 1). δ ∈ {0.01,0.02,0.05,0.10}.
# 3. **Global multinomial GoF:** chi² z 49 df na wektorze zliczeń. n_obs = liczba
#    wylosowanych liczb = n_draws × 5 (przybliżenie iid-multinomial; ignoruje
#    ujemną zależność within-draw 5-z-50 → traktować jako lekko optymistyczne).
# 4. **Per-number inclusion test:** marginalna inkluzja q0 = 5/50 = 0.1; pod shiftem
#    q1 ≈ 5·(1/50 + δ) = 0.1 + 5δ (first-order, dla małych δ; dla δ=0.10 przekracza
#    reżim liniowy — oznaczone). Test 2-binowy chi² na n_draws losowaniach.
#
# Wszystko α = 0.05. Brak danych — czysto analityczne (statsmodels GofChisquarePower).

# %%
import sys

import numpy as np
import polars as pl
from statsmodels.stats.power import GofChisquarePower

# Windows console default cp1250 nie koduje ² itp. — wymuś UTF-8 dla print
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ALPHA = 0.05
N_CATS = 50
DRAW_SIZE = 5
P0 = 1.0 / N_CATS          # 0.02 — baseline prawdopodobieństwo kategorii
Q0 = DRAW_SIZE / N_CATS    # 0.10 — baseline marginalna inkluzja liczby
DELTAS = [0.01, 0.02, 0.05, 0.10]   # pre-registered (preregistration_v2 §6)
TARGET_POWER = 0.80

# n_draws per reżim — ZWERYFIKOWANE na seed CSV (958 losowań)
REGIME_N = {"R1 (n=133)": 133, "R2 (n=389)": 389, "R3 (n=436)": 436, "pooled (n=958)": 958}

gof = GofChisquarePower()


# %%
def cohen_w_single_shift(delta: float, p0: float = P0, k: int = N_CATS) -> float:
    """Cohen's w dla pojedynczego shiftu kategorii o delta (reszta absorbuje równo)."""
    # w^2 = delta^2/p0 + (k-1)*(delta/(k-1))^2/p0 = (delta^2/p0)*(1 + 1/(k-1))
    return (delta / np.sqrt(p0)) * np.sqrt(k / (k - 1))


def cohen_w_two_bin(q1: float, q0: float = Q0) -> float:
    """Cohen's w dla testu 2-binowego (inclusion prob q0 -> q1)."""
    return abs(q1 - q0) / np.sqrt(q0 * (1.0 - q0))


# %% [markdown]
# ## 1. Global multinomial GoF — power per (reżim, δ)

# %%
rows = []
for reg, n_draws in REGIME_N.items():
    n_obs = n_draws * DRAW_SIZE  # liczby wylosowane łącznie
    for d in DELTAS:
        w = cohen_w_single_shift(d)
        power = gof.power(effect_size=w, nobs=n_obs, n_bins=N_CATS, alpha=ALPHA)
        rows.append({"regime": reg, "n_draws": n_draws, "delta": d,
                     "cohen_w": round(float(w), 4), "power": round(float(power), 3)})

global_df = pl.DataFrame(rows)
print("=== GLOBAL MULTINOMIAL GoF (chi², 49 df) ===")
print(global_df.pivot(values="power", index=["regime", "n_draws"], on="delta"))

# %% [markdown]
# ## 2. Per-number inclusion test — power per (reżim, δ)

# %%
rows = []
for reg, n_draws in REGIME_N.items():
    for d in DELTAS:
        q1 = Q0 + DRAW_SIZE * d   # first-order
        capped = q1 >= 1.0
        q1 = min(q1, 0.999)
        w = cohen_w_two_bin(q1)
        power = gof.power(effect_size=w, nobs=n_draws, n_bins=2, alpha=ALPHA)
        rows.append({"regime": reg, "n_draws": n_draws, "delta": d, "q1": round(q1, 3),
                     "power": round(float(power), 3), "linear_ok": not capped})

pernum_df = pl.DataFrame(rows)
print("\n=== PER-NUMBER INCLUSION (2-bin chi², q0=0.1) ===")
print(pernum_df.pivot(values="power", index=["regime", "n_draws"], on="delta"))

# %% [markdown]
# ## 3. Minimum Detectable Effect (MDE) @ 80% power — co-primary deliverable

# %%
mde_rows = []
for reg, n_draws in REGIME_N.items():
    n_obs = n_draws * DRAW_SIZE
    # global: solve dla w, potem odwróć na delta
    w_mde = gof.solve_power(effect_size=None, nobs=n_obs, alpha=ALPHA,
                            power=TARGET_POWER, n_bins=N_CATS)
    delta_mde_global = float(w_mde) * np.sqrt(P0) / np.sqrt(N_CATS / (N_CATS - 1))
    # per-number: solve dla w (2-bin), potem na delta przez q
    w2_mde = gof.solve_power(effect_size=None, nobs=n_draws, alpha=ALPHA,
                             power=TARGET_POWER, n_bins=2)
    dq_mde = float(w2_mde) * np.sqrt(Q0 * (1 - Q0))
    delta_mde_pernum = dq_mde / DRAW_SIZE
    mde_rows.append({
        "regime": reg, "n_draws": n_draws,
        "MDE_delta_global": round(delta_mde_global, 4),
        "MDE_delta_pernum": round(delta_mde_pernum, 4),
    })

mde_df = pl.DataFrame(mde_rows)
print("\n=== MDE δ @ 80% power (mniejsze = lepiej; porównaj z pre-reg {0.01..0.10}) ===")
print(mde_df)

# %% [markdown]
# ## 4. Wnioski (do Negative Result Presentation Plan, §7.2)
#
# Liczby drukowane wyżej. Interpretacja w komórce poniżej (uzupełniana po uruchomieniu).

# %% [markdown]
# ## 5. Power curve (global GoF) — figura do W8 reuse

# %%
import matplotlib
matplotlib.use("Agg")  # headless — zapis do pliku bez GUI
import matplotlib.pyplot as plt

delta_grid = np.linspace(0.002, 0.10, 80)
fig, ax = plt.subplots(figsize=(7, 4.5))
for reg, n_draws in REGIME_N.items():
    n_obs = n_draws * DRAW_SIZE
    powers = [gof.power(effect_size=cohen_w_single_shift(d), nobs=n_obs,
                        n_bins=N_CATS, alpha=ALPHA) for d in delta_grid]
    ax.plot(delta_grid, powers, label=reg, linewidth=1.8)

ax.axhline(TARGET_POWER, color="#94A3B8", linestyle="--", linewidth=1, label="80% power")
for d in DELTAS:
    ax.axvline(d, color="#EF4444", alpha=0.25, linewidth=0.8)
ax.set_xlabel("frequency-shift δ (single category, p_k = 1/50 + δ)")
ax.set_ylabel("power (chi² GoF, 49 df, α=0.05)")
ax.set_title("DriftScope W0 — analytic power vs effect size, per regime")
ax.legend(fontsize=8, loc="lower right")
ax.grid(alpha=0.2)
fig.tight_layout()
out_png = "notebooks/00_power_preview.png"
fig.savefig(out_png, dpi=130)
print(f"\n[plot] zapisano {out_png}")

# %%
print("\nINTERPRETACJA:")
print(f"- Pre-registered δ rozciągają się {DELTAS} — sprawdź, które reżimy je łapią @ >70%.")
print("- Jeśli MDE_delta_global per-reżim > najmniejszego pre-reg δ (0.01), to δ=0.01")
print("  jest NIEwykrywalny w tym reżimie przy obecnym n — to jest publikowalny wynik.")
print("- R1 (~135) jest binding constraint: najmniej danych => najwyższe MDE.")
