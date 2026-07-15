from legalai.packages.pii.merger import merge_matches
from legalai.packages.pii.patterns import Match


def test_merge_matches_removes_overlap_by_priority():
    matches = [
        Match("TELEFON", 0, 10, "xxxxxxxxxx"),
        Match("TCKN", 0, 10, "xxxxxxxxxx"),  # aynı aralık, TCKN öncelikli
    ]
    merged = merge_matches(matches)
    assert len(merged) == 1
    assert merged[0].label == "TCKN"


def test_merge_matches_keeps_non_overlapping_matches_sorted_by_position():
    matches = [
        Match("EPOSTA", 20, 30, "a@b.com"),
        Match("TCKN", 0, 11, "10000000146"),
    ]
    merged = merge_matches(matches)
    assert [m.label for m in merged] == ["TCKN", "EPOSTA"]
