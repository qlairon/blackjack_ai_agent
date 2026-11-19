"""Core Blackjack engine: deck, hand and a single simulated round."""

import random

# Card values: 10, J, Q and K are all worth 10. An Ace is stored as 11 and
# drops to 1 automatically when the hand would otherwise bust.
CARD_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
ACE = 11

STAND = 0
HIT = 1


class Deck:
    """A standard 52-card deck (suits ignored) that reshuffles when low."""

    RESHUFFLE_THRESHOLD = 15

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.cards = []
        self.shuffle()

    def shuffle(self):
        self.cards = CARD_VALUES * 4
        self.rng.shuffle(self.cards)

    def deal(self):
        if len(self.cards) < self.RESHUFFLE_THRESHOLD:
            self.shuffle()
        return self.cards.pop()


class Hand:
    def __init__(self, cards=None):
        self.cards = list(cards) if cards else []

    def add_card(self, card):
        self.cards.append(card)

    def get_value(self):
        value = sum(self.cards)
        aces = self.cards.count(ACE)
        # Count Aces as 1 instead of 11 while the hand is over 21.
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value


def choose_action(strategy, player_total, dealer_upcard):
    """Look up the strategy's action, defaulting to HIT for unknown states."""
    return strategy.get((player_total, dealer_upcard), HIT)


def settle(player_total, dealer_total):
    """Return +1 if the player wins, -1 if they lose and 0 for a push."""
    if player_total > 21:
        return -1
    if dealer_total > 21 or player_total > dealer_total:
        return 1
    if player_total < dealer_total:
        return -1
    return 0


def play_round(deck, strategy):
    """Play one hand with the given strategy. Returns +1, 0 or -1."""
    player = Hand()
    dealer = Hand()

    player.add_card(deck.deal())
    dealer.add_card(deck.deal())
    player.add_card(deck.deal())
    dealer.add_card(deck.deal())

    dealer_upcard = dealer.cards[0]

    # Player's turn
    while player.get_value() < 21:
        if choose_action(strategy, player.get_value(), dealer_upcard) == HIT:
            player.add_card(deck.deal())
        else:
            break

    player_total = player.get_value()
    if player_total > 21:
        return -1

    # Dealer stands on all 17s
    while dealer.get_value() < 17:
        dealer.add_card(deck.deal())

    return settle(player_total, dealer.get_value())
