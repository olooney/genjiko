import pytest
import pandas as pd
from genjiko import (
    intervals_overlap,
    validate_genjiko,
    partitions,
    is_nested_within,
    optimal_genjiko_for_partition,
    generate_all_genjiko_patterns,
    load_genjiko,
    bell_number
)


def test_intervals_overlap():
    assert intervals_overlap({1, 2}, {2, 3}) is True
    assert intervals_overlap({1, 2}, {3, 4}) is False
    assert intervals_overlap({1, 3}, {2}) is True
    assert intervals_overlap({1, 2, 3}, {3, 4, 5}) is True


def test_validate_genjiko():
    genjiko = [(1.0, {1, 2}), (1.0, {3, 4})]
    assert validate_genjiko(genjiko) is True

    invalid_genjiko = [(1.0, {1, 3}), (1.0, {2, 4})]
    assert validate_genjiko(invalid_genjiko) is False


def test_partitions():
    # test the known 5 partitions of a set of 3
    s = {1, 2, 3}
    result = list(partitions(s))
    expected = [
        [{1}, {2}, {3}],
        [{1, 2}, {3}],
        [{1, 3}, {2}],
        [{2, 3}, {1}],
        [{1, 2, 3}]
    ]

    def freeze(partitions):
        return frozenset(
            frozenset(
                frozenset(s) for s in partition
            )
            for partition in partitions
        )
    result = freeze(result)
    expected = freeze(expected)

    for partition in expected:
        assert partition in result

    for partition in result:
        assert partition in expected

    # test a set of five
    s5 = {1, 2, 3, 4, 5}
    result_5 = list(partitions(s5))
    assert len(result_5) == 52


def test_is_nested_within():
    assert is_nested_within({2, 3}, {1, 4}) is True
    assert is_nested_within({1, 4}, {1, 4}) is False
    assert is_nested_within({1, 2}, {3, 4}) is False


def test_optimal_genjiko_for_partition():
    partition = [{1, 2}, {3, 4}]
    genjiko = optimal_genjiko_for_partition(partition)
    assert len(genjiko) == len(partition)
    assert all(isinstance(height, float) and isinstance(group, set) for height, group in genjiko)


def test_generate_all_genjiko_patterns():
    patterns = list(generate_all_genjiko_patterns(5))
    assert len(patterns) > 0
    for genjiko in patterns:
        assert all(isinstance(height, float) and isinstance(group, set) for height, group in genjiko)
        assert validate_genjiko(genjiko)


def test_load_genjiko():
    # Call the function to load the genjiko data
    df = load_genjiko()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 52

    # Verify the structure of the DataFrame
    expected_columns = [
        "Chapter", 
        "Kanji", 
        "Romaji", 
        "English", 
        "Partition", 
        "Icon", 
        "Layout", 
        "Color",
    ]
    assert list(df.columns) == expected_columns

    # Check a sample row's data
    sample_row = df.iloc[0]
    assert isinstance(sample_row["Kanji"], str)
    assert isinstance(sample_row["Romaji"], str)
    assert isinstance(sample_row["Partition"], list)
    assert isinstance(sample_row["Layout"], list)
    assert isinstance(sample_row["Icon"], str)
    assert isinstance(sample_row["Color"], str)


def test_bell_number():
    assert bell_number(0) == 1
    assert bell_number(1) == 1
    assert bell_number(2) == 2
    assert bell_number(3) == 5
    assert bell_number(4) == 15
    assert bell_number(5) == 52
    assert bell_number(10) == 115975
    with pytest.raises(ValueError):
        bell_number(-1)



