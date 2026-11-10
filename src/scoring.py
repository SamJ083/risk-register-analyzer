"""Rating labels and 5x5 heat map counts for the risk register."""

import pandas as pd

from src import config

LEVELS = list(range(config.SCORE_MIN, config.SCORE_MAX + 1))

# (rating column prefix, likelihood column, impact column)
SCORE_PAIRS = [
    ("inherent", "likelihood", "impact"),
    ("residual", "residual_likelihood", "residual_impact"),
]


def rating_for(score):
    """Return the rating label for a score, or NA if there is no score."""
    if pd.isna(score):
        return pd.NA
    for label, lowest in config.RATING_BANDS:
        if score >= lowest:
            return label
    return pd.NA


def valid_inputs(df, lik_col, imp_col):
    """True for rows where likelihood and impact are whole numbers in range."""
    lik, imp = df[lik_col], df[imp_col]
    in_range = (
        lik.between(config.SCORE_MIN, config.SCORE_MAX)
        & imp.between(config.SCORE_MIN, config.SCORE_MAX)
    )
    whole = (lik == lik.round()) & (imp == imp.round())
    return in_range & whole


def add_ratings(df):
    """Return a copy of df with inherent_rating and residual_rating columns."""
    out = df.copy()
    for prefix, lik, imp in SCORE_PAIRS:
        valid = valid_inputs(out, lik, imp)
        score = (out[lik] * out[imp]).where(valid)
        out[f"{prefix}_rating"] = score.map(rating_for)
    return out


def heat_map(df, lik_col, imp_col):
    """Count risks per likelihood x impact cell.

    Returns (grid, excluded). The grid has likelihood 5..1 down the rows and
    impact 1..5 across the columns. excluded is the number of risks that
    could not be plotted because their inputs are invalid.
    """
    valid = valid_inputs(df, lik_col, imp_col)
    subset = df[valid]
    grid = pd.crosstab(subset[lik_col].astype(int), subset[imp_col].astype(int))
    grid = grid.reindex(index=LEVELS[::-1], columns=LEVELS, fill_value=0)
    grid.index.name = "likelihood"
    grid.columns.name = "impact"
    return grid, int((~valid).sum())