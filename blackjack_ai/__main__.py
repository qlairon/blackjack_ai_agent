"""Command-line interface: ``python -m blackjack_ai <command>``."""

import argparse
import sys
from pathlib import Path

from .strategy import (
    DEFAULT_MODEL_PATH,
    NUM_STATES,
    PROJECT_ROOT,
    action_name,
    basic_strategy,
    card_label,
    compare,
    format_table,
    load_strategy,
    save_strategy,
)

DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"


def _load_or_exit(path):
    try:
        return load_strategy(path)
    except FileNotFoundError:
        sys.exit(f"Strategy file not found: {path}\nRun `python -m blackjack_ai train` first.")


def cmd_train(args):
    from .genetic import EvolutionConfig, evolve

    config = EvolutionConfig(
        population_size=args.population,
        generations=args.generations,
        games_per_agent=args.games,
        elite_fraction=args.elite,
        mutation_rate=args.mutation,
        seed=args.seed,
    )
    print(
        f"Evolving {config.population_size} agents for {config.generations} generations "
        f"({config.games_per_agent} games each)..."
    )

    def report(gen, best, worst, avg):
        print(f"Gen {gen:3d} | Best: {best:6d} | Worst: {worst:6d} | Avg: {avg:8.1f}")

    result = evolve(config, on_generation=report)

    print("\nBest strategy when the player has 16:")
    for upcard in range(2, 12):
        action = result.best_strategy[(16, upcard)]
        print(f"  Dealer shows {card_label(upcard):>2}: {action_name(action)}")

    save_strategy(result.best_strategy, args.output)
    print(f"\nStrategy saved to {args.output}")

    if not args.no_plot:
        plot_path = save_learning_curve(result, config, args.results_dir, show=args.show)
        print(f"Learning curve saved to {plot_path}")


def save_learning_curve(result, config, results_dir, show=False):
    import matplotlib

    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / "learning_curve.png"

    plt.figure(figsize=(10, 6))
    plt.plot(result.best_history, label="Best fitness", color="#1f77b4", linewidth=2)
    plt.plot(result.average_history, label="Average population fitness",
             color="#ff7f0e", linewidth=2, linestyle="--")
    plt.title("Genetic Algorithm Convergence:\nFitness vs. Generation in Blackjack Policy Optimization",
              fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Generation", fontsize=12)
    plt.ylabel(f"Fitness (sum of rewards over {config.games_per_agent:,} games)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.legend(loc="lower right", fontsize=11)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    if show:
        plt.show()
    plt.close()
    return path


def cmd_strategy(args):
    strategy = _load_or_exit(args.model)
    print(f"Strategy from {args.model}\n")
    print(format_table(strategy))
    print("\nKey: H = Hit, S = Stand")


def cmd_evaluate(args):
    strategy = _load_or_exit(args.model)
    reference = basic_strategy()
    matches, mistakes = compare(strategy, reference)

    print("--- DIFFERENCES FROM BASIC STRATEGY ('.' = matches) ---")
    print(format_table(strategy, reference=reference))

    print("\n--- RESULTS ---")
    print(f"Total states:    {NUM_STATES}")
    print(f"Correct actions: {matches}")
    print(f"Accuracy:        {matches / NUM_STATES:.2%}\n")

    if not mistakes:
        print("Flawless! 100% basic strategy.")
        return
    print("--- SAMPLE MISTAKES ---")
    for (total, upcard), ours, correct in mistakes[:10]:
        print(f"Hand {total:2d} vs dealer {card_label(upcard):>2} -> "
              f"AI chose {action_name(ours)}, basic strategy says {action_name(correct)}")
    if len(mistakes) > 10:
        print(f"...and {len(mistakes) - 10} more.")


def cmd_play(args):
    strategy = _load_or_exit(args.model)
    from .visualize import run

    run(strategy)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m blackjack_ai",
        description="Evolve, inspect and watch a Blackjack strategy learned by a genetic algorithm.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    model_help = f"strategy JSON file (default: {DEFAULT_MODEL_PATH.relative_to(PROJECT_ROOT)})"

    train = sub.add_parser("train", help="evolve a new strategy")
    train.add_argument("--population", type=int, default=200, help="agents per generation (default: 200)")
    train.add_argument("--generations", type=int, default=150, help="number of generations (default: 150)")
    train.add_argument("--games", type=int, default=5000, help="games played per agent per generation (default: 5000)")
    train.add_argument("--elite", type=float, default=0.2, help="fraction of top agents kept as parents (default: 0.2)")
    train.add_argument("--mutation", type=float, default=0.05, help="per-state mutation probability (default: 0.05)")
    train.add_argument("--seed", type=int, default=None, help="random seed for reproducible runs")
    train.add_argument("--output", type=Path, default=DEFAULT_MODEL_PATH, help="where to save the strategy")
    train.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR, help="where to save the learning curve")
    train.add_argument("--no-plot", action="store_true", help="skip the learning-curve plot")
    train.add_argument("--show", action="store_true", help="also open the plot in a window")
    train.set_defaults(func=cmd_train)

    for name, func, help_text in [
        ("strategy", cmd_strategy, "print the learned strategy as a table"),
        ("evaluate", cmd_evaluate, "compare the learned strategy with basic strategy"),
        ("play", cmd_play, "watch the AI play in a pygame window"),
    ]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH, help=model_help)
        p.set_defaults(func=func)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
