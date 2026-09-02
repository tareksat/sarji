import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from measure import percentile  # noqa: E402


def test_empty_series_has_no_percentile():
    assert percentile([], 50) is None


def test_p50_is_the_lower_median_at_ten_samples():
    # The default `--iterations 10`. The old formula reported ordered[5] here,
    # one rank high, which biased every published p50.
    values = [float(v) for v in range(1, 11)]
    assert percentile(values, 50) == 5.0


def test_p50_does_not_depend_on_sample_count_parity():
    # Six and twenty samples drawn from the same distribution must agree; the
    # old rounding flipped by one rank with the parity of the count.
    assert percentile([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], 50) == 30.0
    assert percentile([float(v) for v in range(1, 21)], 50) == 10.0


def test_p95_is_nearest_rank():
    assert percentile([float(v) for v in range(1, 21)], 95) == 19.0
    # With ten samples the 95th percentile genuinely is the largest value.
    assert percentile([float(v) for v in range(1, 11)], 95) == 10.0


def test_percentile_sorts_its_input():
    assert percentile([50.0, 10.0, 30.0, 20.0, 40.0], 50) == 30.0


def test_single_sample_is_every_percentile():
    assert percentile([7.0], 50) == 7.0
    assert percentile([7.0], 95) == 7.0
