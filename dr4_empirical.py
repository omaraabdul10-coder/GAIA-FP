"""
dr4_empirical.py: the PRIMARY DR4 RVS combination required by amendment v0.5, A7.

The pre-stated V3 test (VBROAD_V2_PLAN.md) failed on real DR3 data: the physical per-system line-width model did not
beat a naive empirical combination. A7 therefore makes the empirical combination primary on DR4:

    score_emp = cmd_z + rvs_z
    cmd_z = -dM_G / sigma_CMD        (over-luminosity in units of the local main-sequence scatter)
    rvs_z = phase-locked line-width statistic z (rvs_phase_test / dr4_pipeline.rvs_z); its null is N(0, 1).
            A candidate without RVS epochs gets rvs_z = 0, so it is scored on the CMD alone.

No parameter is fitted. A higher score means more impostor-like. The physical likelihood (dr4_pipeline.score,
lik.llr_t with rvs_predict.SB1_TRUNCATE = True) is reported alongside as the secondary score.
"""
import numpy as np, pandas as pd

def empirical_score(X: pd.DataFrame) -> np.ndarray:
    cmd_z = -X['dm'].values / X['sig_cmd'].values
    rvs_z = X['z'].values if 'z' in X else np.full(len(X), np.nan)
    rvs_z = np.where(np.isfinite(rvs_z), rvs_z, 0.0)
    return cmd_z + rvs_z

def add_scores(X: pd.DataFrame) -> pd.DataFrame:
    """Add score_emp (primary, A7) next to the frozen physical P_impostor (secondary)."""
    X = X.copy(); X['score_emp'] = empirical_score(X); return X
