from evogame.sim.recorder import GenerationLog, GenerationRecord


def test_log_starts_empty():
    log = GenerationLog()
    assert len(log) == 0


def test_record_appends():
    log = GenerationLog()
    log.record(gen=0, allele_freqs={"color": {"R": 0.5, "W": 0.5}}, predator_on=False, population_size=20)
    assert len(log) == 1
    assert log.records[0].gen == 0
    assert log.records[0].population_size == 20


def test_record_does_not_alias_caller_dict():
    log = GenerationLog()
    freqs = {"color": {"R": 0.5, "W": 0.5}}
    log.record(gen=0, allele_freqs=freqs, predator_on=False, population_size=20)
    freqs["color"]["R"] = 999.0
    assert log.records[0].allele_freqs["color"]["R"] == 0.5


def test_frequencies_over_time_preserves_first_seen_order():
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.4, "W": 0.4, "M": 0.2}}, False, 20)
    series = log.frequencies_over_time("color")
    assert list(series.keys()) == ["R", "W", "M"]


def test_frequencies_over_time_basic():
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}}, True, 18)
    series = log.frequencies_over_time("color")
    assert series == {"R": [0.5, 0.7], "W": [0.5, 0.3]}


def test_frequencies_over_time_handles_new_allele():
    """An allele that appears in gen 1 but not gen 0 should show 0.0 for gen 0."""
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.4, "W": 0.4, "M": 0.2}}, False, 20)
    series = log.frequencies_over_time("color")
    assert series == {"R": [0.5, 0.4], "W": [0.5, 0.4], "M": [0.0, 0.2]}


def test_frequencies_over_time_missing_gene():
    log = GenerationLog()
    log.record(0, {"color": {"R": 1.0}}, False, 20)
    assert log.frequencies_over_time("nonexistent") == {}
