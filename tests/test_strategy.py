import random

from blackjack_ai.game import HIT, STAND
from blackjack_ai.genetic import EvolutionConfig, crossover, evolve, mutate
from blackjack_ai.strategy import (
    DEFAULT_MODEL_PATH,
    NUM_STATES,
    basic_strategy,
    compare,
    format_table,
    load_strategy,
    random_strategy,
    save_strategy,
)


def test_basic_strategy_key_cells():
    bs = basic_strategy()
    assert len(bs) == NUM_STATES
    assert bs[(16, 10)] == HIT
    assert bs[(16, 6)] == STAND
    assert bs[(12, 3)] == HIT
    assert bs[(12, 4)] == STAND
    assert bs[(11, 11)] == HIT
    assert bs[(17, 11)] == STAND


def test_save_and_load_roundtrip(tmp_path):
    strategy = random_strategy(random.Random(0))
    path = tmp_path / "s.json"
    save_strategy(strategy, path)
    assert load_strategy(path) == strategy


def test_bundled_model_loads():
    assert len(load_strategy(DEFAULT_MODEL_PATH)) == NUM_STATES


def test_compare_counts_differences():
    bs = basic_strategy()
    flipped = dict(bs)
    flipped[(16, 10)] = STAND
    matches, mistakes = compare(flipped, bs)
    assert matches == NUM_STATES - 1
    assert mistakes == [((16, 10), STAND, HIT)]


def test_format_table_marks_matches():
    table = format_table(basic_strategy(), reference=basic_strategy())
    assert "H" not in table.split("\n", 2)[2]


def test_crossover_and_mutate():
    rng = random.Random(0)
    a = {s: HIT for s in basic_strategy()}
    b = {s: STAND for s in basic_strategy()}
    child = crossover(a, b, rng)
    assert set(child) == set(a)
    assert 0 < sum(child.values()) < NUM_STATES
    assert mutate(dict(a), 0.0, rng) == a
    assert mutate(dict(a), 1.0, rng) == b


def test_evolve_smoke():
    config = EvolutionConfig(population_size=10, generations=3, games_per_agent=50, seed=42)
    result = evolve(config)
    assert len(result.best_history) == 3
    assert len(result.best_strategy) == NUM_STATES
