"""Genetic algorithm that evolves a Blackjack hit/stand strategy."""

import random
from dataclasses import dataclass, field

from .game import Deck, play_round
from .strategy import random_strategy


@dataclass
class EvolutionConfig:
    population_size: int = 200
    generations: int = 150
    games_per_agent: int = 5000
    elite_fraction: float = 0.2
    mutation_rate: float = 0.05
    seed: int | None = None


@dataclass
class EvolutionResult:
    best_strategy: dict
    best_history: list = field(default_factory=list)
    average_history: list = field(default_factory=list)


def crossover(parent1, parent2, rng=random):
    """Uniform crossover: each state's action comes from a random parent."""
    return {
        state: parent1[state] if rng.random() < 0.5 else parent2[state]
        for state in parent1
    }


def mutate(strategy, mutation_rate=0.05, rng=random):
    """Flip each action with probability ``mutation_rate`` (in place)."""
    for state in strategy:
        if rng.random() < mutation_rate:
            strategy[state] = 1 - strategy[state]
    return strategy


def fitness(strategy, deck, games):
    """Total reward (+1 win, 0 push, -1 loss) over ``games`` hands."""
    return sum(play_round(deck, strategy) for _ in range(games))


def evolve(config=None, on_generation=None):
    """Run the genetic algorithm.

    ``on_generation(gen, best, worst, average)`` is called after each
    generation is scored, if provided.
    """
    config = config or EvolutionConfig()
    rng = random.Random(config.seed)
    deck = Deck(rng)
    elite_count = max(2, int(config.population_size * config.elite_fraction))

    population = [random_strategy(rng) for _ in range(config.population_size)]
    result = EvolutionResult(best_strategy=population[0])

    for generation in range(1, config.generations + 1):
        scored = [(fitness(s, deck, config.games_per_agent), s) for s in population]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        best_score, best_strategy = scored[0]
        worst_score = scored[-1][0]
        average = sum(score for score, _ in scored) / len(scored)

        result.best_strategy = best_strategy
        result.best_history.append(best_score)
        result.average_history.append(average)
        if on_generation:
            on_generation(generation, best_score, worst_score, average)

        # Selection: the top performers become parents; the best survives as-is.
        parents = [s for _, s in scored[:elite_count]]
        next_generation = [best_strategy]
        while len(next_generation) < config.population_size:
            child = crossover(rng.choice(parents), rng.choice(parents), rng)
            next_generation.append(mutate(child, config.mutation_rate, rng))
        population = next_generation

    return result
