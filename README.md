# Blackjack AI: Genetic Algorithm

An AI that **teaches itself to play Blackjack** with a genetic algorithm. It has no prior knowledge of the game. A population of random strategies plays thousands of hands, and the strongest strategies breed and mutate into the next generation. Over many generations the population converges toward the mathematically optimal *basic strategy*.

The project includes:

- **A training script** that evolves a strategy and plots its learning curve.
- **An evaluator** that scores the learned strategy against textbook basic strategy.
- **A strategy viewer** that prints the learned hit/stand table.
- **A pygame visualizer** where you can watch the AI play hand by hand.

## How it works

A strategy (the AI's "DNA") is a lookup table with one action, **Hit** or **Stand**, for each of 170 game states:

| | |
|---|---|
| Player total | 4 – 20 |
| Dealer upcard | 2 – 10, Ace |

Each generation runs the following steps:

1. **Fitness.** Every agent plays `N` hands (default 5,000) and scores +1 for a win, 0 for a push and −1 for a loss.
2. **Selection.** The top 20% become parents. The best agent is copied unchanged into the next generation (elitism).
3. **Crossover.** Each child takes each state's action from one of two random parents.
4. **Mutation.** Each action is flipped with a 5% probability.

**Simplifications:** the game uses a single 52-card deck that reshuffles when fewer than 15 cards remain, and the dealer stands on 17. Only hit and stand are modelled, so there is no doubling, splitting or soft-hand distinction, and a natural blackjack pays 1:1.

## Getting started

Requires Python 3.10+.

```bash
git clone https://github.com/qlairon/blackjack_ai_agent.git
cd blackjack_ai_agent
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

> The visualizer uses [`pygame-ce`](https://pyga.me/), a drop-in replacement for `pygame` with wheels for newer Python versions. If you already have `pygame` installed, uninstall it first (`pip uninstall pygame`), because the two packages conflict.

## Usage

A pre-trained strategy is included in [`models/best_strategy.json`](models/best_strategy.json), so you can try every command right away.

```bash
python -m blackjack_ai play        # watch the AI play (SPACE = next hand, ESC = quit)
python -m blackjack_ai strategy    # print the learned hit/stand table
python -m blackjack_ai evaluate    # compare it with perfect basic strategy
python -m blackjack_ai train       # evolve a new strategy from scratch
```

### Training options

```bash
python -m blackjack_ai train --population 200 --generations 150 --games 5000 --seed 42
```

| Option | Default | Description |
|---|---|---|
| `--population` | 200 | Agents per generation |
| `--generations` | 150 | Number of generations |
| `--games` | 5000 | Hands each agent plays per generation |
| `--elite` | 0.2 | Fraction of top agents used as parents |
| `--mutation` | 0.05 | Per-state mutation probability |
| `--seed` | random | Seed for reproducible runs |
| `--output` | `models/best_strategy.json` | Where to save the strategy |
| `--no-plot` / `--show` | | Skip the learning-curve plot, or also open it in a window |

The learning curve is saved to `results/learning_curve.png`.

> ⚠️ The default settings simulate 150 million hands, which takes a long time in pure Python. For a quick experiment, try `--population 50 --generations 30 --games 1000`.

### Strategy file format

Strategies are stored as plain JSON. Each row is a player total, and each character is the action against dealer upcards `2 3 4 5 6 7 8 9 10 A`:

```json
"16": "SSSSSHHHHH"
```

## Project structure

```
blackjack_ai/
  __main__.py     command-line interface
  game.py         deck, hand and round simulation
  genetic.py      selection, crossover, mutation, evolution loop
  strategy.py     basic strategy, JSON save/load, table formatting
  visualize.py    pygame visualizer
models/           trained strategies
assets/cards/     card sprites
tests/            pytest suite
```

## Running tests

```bash
pip install pytest
pytest
```

## Credits

Card art: [Playing Cards Pack](https://kenney.nl/assets/playing-cards-pack) by Kenney, licensed under [CC0](assets/cards/LICENSE.txt).

## License

[MIT](LICENSE)
