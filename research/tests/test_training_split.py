import pandas as pd
import pytest
from plyshock.training.split import create_group_train_test_split


def test_create_group_train_test_split_has_no_game_id_leakage() -> None:
    dataframe = pd.DataFrame(
        {
            "game_id": [f"game-{index // 2}" for index in range(40)],
            "feature": range(40),
            "upset_label": [index % 2 for index in range(40)],
        }
    )

    train_df, test_df = create_group_train_test_split(
        dataframe, test_size=0.25, random_state=7
    )

    assert set(train_df["game_id"]).isdisjoint(set(test_df["game_id"]))
    assert len(train_df) + len(test_df) == len(dataframe)


def test_create_group_train_test_split_rejects_missing_group_column() -> None:
    dataframe = pd.DataFrame({"feature": [1, 2], "upset_label": [0, 1]})

    with pytest.raises(ValueError, match="group column"):
        create_group_train_test_split(dataframe)
