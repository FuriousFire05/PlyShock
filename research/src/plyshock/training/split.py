"""Train/test splitting utilities for PlyShock models."""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


def create_group_train_test_split(
    df: pd.DataFrame,
    group_col: str = "game_id",
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a train/test split that keeps each game in exactly one split.

    Args:
        df: Feature dataframe.
        group_col: Column containing game identifiers.
        test_size: Fraction of groups assigned to the test split.
        random_state: Random seed for reproducible splitting.

    Returns:
        ``(train_df, test_df)``.

    Raises:
        ValueError: If ``group_col`` is missing or if a group leaks across splits.
    """
    if group_col not in df.columns:
        raise ValueError(f"Dataframe is missing group column {group_col!r}.")

    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_index, test_index = next(splitter.split(df, groups=df[group_col]))
    train_df = df.iloc[train_index].copy()
    test_df = df.iloc[test_index].copy()

    train_groups = set(train_df[group_col])
    test_groups = set(test_df[group_col])
    if train_groups.intersection(test_groups):
        raise ValueError("Group split leaked game ids across train and test splits.")

    return train_df, test_df
