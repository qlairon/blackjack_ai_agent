"""Strategy tables: creation, basic strategy, JSON persistence and printing.

A strategy maps a state ``(player_total, dealer_upcard)`` to an action
(``STAND`` = 0 or ``HIT`` = 1). Player totals range over 4-20 and dealer
upcards over 2-11 (11 is an Ace), giving 170 states.
"""

import json
import random
from pathlib import Path

from .game import HIT, STAND, choose_action

PLAYER_TOTALS = range(4, 21)
DEALER_UPCARDS = range(2, 12)
NUM_STATES = len(PLAYER_TOTALS) * len(DEALER_UPCARDS)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "best_strategy.json"

_ACTION_TO_CHAR = {HIT: "H", STAND: "S"}
_CHAR_TO_ACTION = {"H": HIT, "S": STAND}


def all_states():
    for player_total in PLAYER_TOTALS:
        for dealer_upcard in DEALER_UPCARDS:
            yield player_total, dealer_upcard


def random_strategy(rng=random):
    return {state: rng.choice([STAND, HIT]) for state in all_states()}


def basic_strategy():
    """Textbook basic strategy for hard totals (no doubling or splitting)."""
    strategy = {}
    for player_total, dealer_upcard in all_states():
        if player_total >= 17:
            action = STAND
        elif 13 <= player_total <= 16:
            action = STAND if 2 <= dealer_upcard <= 6 else HIT
        elif player_total == 12:
            action = STAND if 4 <= dealer_upcard <= 6 else HIT
        else:
            action = HIT  # 4-11 can never bust, so always hit
        strategy[(player_total, dealer_upcard)] = action
    return strategy


# --- Persistence -----------------------------------------------------------

def save_strategy(strategy, path=DEFAULT_MODEL_PATH):
    """Save a strategy as readable JSON: one H/S string per player total."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = {
        str(total): "".join(
            _ACTION_TO_CHAR[choose_action(strategy, total, up)] for up in DEALER_UPCARDS
        )
        for total in PLAYER_TOTALS
    }
    data = {
        "description": "Rows are player totals; each character is the action "
        "against dealer upcards 2,3,4,5,6,7,8,9,10,A (H = hit, S = stand).",
        "strategy": rows,
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_strategy(path=DEFAULT_MODEL_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    strategy = {}
    for total, actions in data["strategy"].items():
        if len(actions) != len(DEALER_UPCARDS):
            raise ValueError(f"Row {total} must have {len(DEALER_UPCARDS)} actions")
        for upcard, char in zip(DEALER_UPCARDS, actions):
            strategy[(int(total), upcard)] = _CHAR_TO_ACTION[char.upper()]
    return strategy


# --- Display ---------------------------------------------------------------

def format_table(strategy, reference=None):
    """Render a strategy as a text grid.

    If ``reference`` is given, cells that match it are shown as ``.`` so that
    only the differences stand out.
    """
    header = "Player | Dealer shows:  2  3  4  5  6  7  8  9 10  A"
    lines = [header, "-" * len(header)]
    for total in PLAYER_TOTALS:
        cells = []
        for upcard in DEALER_UPCARDS:
            action = choose_action(strategy, total, upcard)
            if reference is not None and action == choose_action(reference, total, upcard):
                cells.append(".")
            else:
                cells.append(_ACTION_TO_CHAR[action])
        lines.append(f"  {total:2d}   |                " + "  ".join(cells))
    return "\n".join(lines)


def compare(strategy, reference):
    """Return (number of matching states, list of mismatches)."""
    matches = 0
    mistakes = []
    for state in all_states():
        ours = choose_action(strategy, *state)
        theirs = choose_action(reference, *state)
        if ours == theirs:
            matches += 1
        else:
            mistakes.append((state, ours, theirs))
    return matches, mistakes


def action_name(action):
    return "Hit" if action == HIT else "Stand"


def card_label(upcard):
    return "A" if upcard == 11 else str(upcard)
