-- DriftScope — schemat SQLite (append-only, single-writer CLI process)
-- Tylko metadane rezimow i runy kalibracji. NIE cache permutacji (zob. §3-alt).

CREATE TABLE IF NOT EXISTS regime_meta (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    regime_id    INTEGER NOT NULL,        -- 1, 2 lub 3
    label        TEXT    NOT NULL,        -- 'pre_2014', '2014_2022', 'post_2022'
    date_from    TEXT    NOT NULL,        -- ISO 8601 YYYY-MM-DD
    date_to      TEXT,                    -- NULL = do aktualnej daty (rezim 3)
    draw_count   INTEGER,
    euron_pool   INTEGER NOT NULL,        -- 10 (pre-2022), 12 (post-2022)
    created_at   TEXT    DEFAULT (datetime('now')),
    UNIQUE(regime_id)
);

CREATE TABLE IF NOT EXISTS calibration_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT    NOT NULL,   -- UUID lub timestamp
    test_name         TEXT    NOT NULL,   -- 'adf', 'kpss', 'bcpd', 'mmd', itd.
    regime_id         INTEGER NOT NULL,
    signal_type       TEXT    NOT NULL,   -- 'null_uniform', 'freq_shift', itd.
    effect_size       REAL,
    n_permutations    INTEGER NOT NULL,
    false_positive_rate REAL,
    true_positive_rate  REAL,
    base_seed         INTEGER NOT NULL,
    artifact_path     TEXT,              -- sciezka do parquet shard
    created_at        TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (regime_id) REFERENCES regime_meta(id)
);
