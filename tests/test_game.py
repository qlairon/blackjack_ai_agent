import random

import pytest

from blackjack_ai.game import ACE, STAND, Deck, Hand, play_round, settle


@pytest.mark.parametrize(
    "cards, expected",
    [
        ([10, 7], 17),
        ([ACE, 10], 21),
        ([ACE, ACE], 12),
        ([ACE, 9, 5], 15),
        ([ACE, ACE, 9], 21),
        ([10, 10, 5], 25),
    ],
)
def test_hand_value(cards, expected):
    assert Hand(cards).get_value() == expected


@pytest.mark.parametrize(
    "player, dealer, expected",
    [(22, 18, -1), (20, 22, 1), (20, 18, 1), (17, 19, -1), (18, 18, 0)],
)
def test_settle(player, dealer, expected):
    assert settle(player, dealer) == expected


def test_deck_reshuffles_when_low():
    deck = Deck(random.Random(0))
    for _ in range(500):
        assert deck.deal() in {2, 3, 4, 5, 6, 7, 8, 9, 10, ACE}
    assert len(deck.cards) >= Deck.RESHUFFLE_THRESHOLD - 1


def test_play_round_returns_valid_outcome():
    deck = Deck(random.Random(1))
    always_hit = {}  # unknown states default to HIT
    always_stand = {(p, d): STAND for p in range(4, 21) for d in range(2, 12)}
    for strategy in (always_hit, always_stand):
        for _ in range(200):
            assert play_round(deck, strategy) in (-1, 0, 1)


def test_always_hitting_loses_badly():
    deck = Deck(random.Random(2))
    score = sum(play_round(deck, {}) for _ in range(2000))
    assert score < -500
