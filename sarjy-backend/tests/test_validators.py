import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from measure import (  # noqa: E402
    VALIDATORS,
    is_four_sentences,
    looks_like_weather,
    mentions_paris,
    percentile,
    render_table,
    sentence_count,
    stream_integrity_ok,
    valid_rows,
)


def test_every_study_prompt_has_a_validator():
    assert set(VALIDATORS) == {
        "In one sentence, what is the capital of France?",
        "Describe Paris in exactly four sentences.",
        "What's the weather in Riyadh right now?",
    }


def test_capital_validator_accepts_the_answer():
    assert mentions_paris("The capital of France is Paris.")


def test_capital_validator_is_case_insensitive():
    assert mentions_paris("paris, of course.")


def test_capital_validator_rejects_the_wrong_city():
    assert not mentions_paris("The capital of France is London.")


def test_capital_validator_rejects_an_error_reply():
    # The failure mode this whole check exists for: a fast 502 body.
    assert not mentions_paris("Sarjy is having trouble responding right now.")


def test_four_sentences_counts_the_terminators():
    assert sentence_count("One. Two! Three? Four.") == 4


def test_four_sentences_ignores_empty_segments():
    # Trailing whitespace after the last terminator must not count as a fifth.
    assert sentence_count("One. Two. Three. Four.   ") == 4


def test_four_sentences_counts_an_unterminated_tail():
    assert sentence_count("One. Two. Three. Four") == 4


def test_four_sentences_accepts_the_tolerance_band():
    assert is_four_sentences("One. Two. Three.")
    assert is_four_sentences("One. Two. Three. Four. Five.")


def test_four_sentences_rejects_a_one_liner():
    assert not is_four_sentences("Paris is the capital of France.")


def test_four_sentences_rejects_a_long_answer():
    assert not is_four_sentences(". ".join(f"Sentence {n}" for n in range(1, 9)) + ".")


def test_weather_validator_accepts_the_city():
    assert looks_like_weather("It is clear in riyadh right now.")


def test_weather_validator_accepts_a_degree_sign_temperature():
    assert looks_like_weather("Currently 34°C and clear.")


def test_weather_validator_accepts_a_temperature_without_a_degree_sign():
    assert looks_like_weather("Currently 34C and clear.")
    assert looks_like_weather("Currently 93 F and clear.")


def test_weather_validator_rejects_a_reply_with_neither():
    assert not looks_like_weather("I am not able to check the weather.")


def test_weather_validator_does_not_read_a_unit_word_as_a_unit():
    # "34 Celsius" has no bare C/F token, so the city name is what must carry
    # this reply -- and here there is none.
    assert not looks_like_weather("The forecast said 34 Celsius somewhere.")


def test_stream_integrity_accepts_deltas_that_rebuild_the_reply():
    assert stream_integrity_ok(["Hello", " ", "there."], "Hello there.")


def test_stream_integrity_rejects_a_missing_delta():
    assert not stream_integrity_ok(["Hello", "there."], "Hello there.")


def test_stream_integrity_rejects_reordered_deltas():
    assert not stream_integrity_ok(["there.", "Hello "], "Hello there.")


def test_stream_integrity_accepts_an_empty_tool_only_turn():
    assert stream_integrity_ok([], "")


def _row(total_ms, ok=True, failed_check=None):
    row = {"total_ms": total_ms, "ok": ok}
    if failed_check is not None:
        row["failed_check"] = failed_check
    return row


def test_valid_rows_drops_failed_turns():
    rows = [_row(100.0), _row(5.0, ok=False, failed_check="content"), _row(300.0)]
    assert [r["total_ms"] for r in valid_rows(rows)] == [100.0, 300.0]


def test_failed_rows_do_not_contribute_to_percentiles():
    # A 502 answers in single-digit milliseconds. Left in the sample it would
    # halve the reported p50, which is exactly the flattering result to avoid.
    rows = [
        _row(100.0),
        _row(200.0),
        _row(300.0),
        _row(2.0, ok=False, failed_check="content"),
        _row(3.0, ok=False, failed_check="persistence"),
    ]
    values = [r["total_ms"] for r in valid_rows(rows)]
    assert percentile(values, 50) == 200.0

    table = render_table("t", "http://localhost:8080", "p", rows)
    assert "Valid: 3/5 turns" in table
    assert "| `total_ms` | 200.0 | 300.0 |" in table


def test_the_table_lists_each_failure_by_iteration():
    rows = [_row(100.0), _row(2.0, ok=False, failed_check="tool_not_called")]
    table = render_table("t", "http://localhost:8080", "p", rows)
    assert "Valid: 1/2 turns" in table
    assert "- 2 → tool_not_called" in table


def test_the_raw_dump_keeps_failed_rows():
    rows = [_row(100.0), _row(2.0, ok=False, failed_check="stream_integrity")]
    table = render_table("t", "http://localhost:8080", "p", rows)
    assert '"failed_check": "stream_integrity"' in table
