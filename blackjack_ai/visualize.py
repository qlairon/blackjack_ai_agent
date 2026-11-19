"""Watch the trained strategy play Blackjack in a pygame window."""

import random

import pygame

from .game import ACE, HIT, Deck, Hand, choose_action, settle
from .strategy import PROJECT_ROOT, card_label

WIDTH, HEIGHT = 800, 600
CARD_W, CARD_H = 84, 120
CARD_GAP = 96

TABLE_GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 200)

CARDS_DIR = PROJECT_ROOT / "assets" / "cards"
SUITS = ("clubs", "diamonds", "hearts", "spades")


class CardArt:
    """Loads the Kenney card sprites, falling back to drawn cards if missing."""

    def __init__(self):
        self.cache = {}
        self.available = (CARDS_DIR / "card_back.png").exists()

    def get(self, name):
        if name not in self.cache:
            image = pygame.image.load(str(CARDS_DIR / f"card_{name}.png")).convert_alpha()
            # The sprites are small pixel art with transparent padding: crop, then scale up.
            image = image.subsurface(image.get_bounding_rect())
            self.cache[name] = pygame.transform.scale(image, (CARD_W, CARD_H))
        return self.cache[name]


def face_for(value, rng):
    """Pick a concrete card image name (suit + rank) for a card value."""
    if value == ACE:
        rank = "A"
    elif value == 10:
        rank = rng.choice(["10", "J", "Q", "K"])
    else:
        rank = f"{value:02d}"
    return f"{rng.choice(SUITS)}_{rank}"


class Table:
    def __init__(self, screen, strategy):
        self.screen = screen
        self.strategy = strategy
        self.font = pygame.font.SysFont("arial", 36, bold=True)
        self.small_font = pygame.font.SysFont("arial", 24)
        self.art = CardArt()
        self.rng = random.Random()
        self.deck = Deck(self.rng)

    # --- Drawing ---------------------------------------------------------

    def text(self, message, x, y, color=WHITE, center=False, small=False):
        image = (self.small_font if small else self.font).render(message, True, color)
        rect = image.get_rect(center=(x, y)) if center else image.get_rect(topleft=(x, y))
        self.screen.blit(image, rect)

    def card(self, value, face, x, y, hidden=False):
        if self.art.available:
            self.screen.blit(self.art.get("back" if hidden else face), (x, y))
            return
        pygame.draw.rect(self.screen, WHITE, (x, y, CARD_W, CARD_H), border_radius=8)
        if hidden:
            pygame.draw.rect(self.screen, BLUE, (x + 5, y + 5, CARD_W - 10, CARD_H - 10), border_radius=5)
        else:
            pygame.draw.rect(self.screen, BLACK, (x, y, CARD_W, CARD_H), 2, border_radius=8)
            self.text(card_label(value), x + CARD_W // 2, y + CARD_H // 2, BLACK, center=True)

    def render(self, player, dealer, faces, message, hide_hole_card=True):
        self.screen.fill(TABLE_GREEN)

        if hide_hole_card:
            self.text(f"Dealer (showing {card_label(dealer.cards[0])})", 50, 40)
        else:
            self.text(f"Dealer (total {dealer.get_value()})", 50, 40)
        for i, value in enumerate(dealer.cards):
            self.card(value, faces["dealer"][i], 50 + i * CARD_GAP, 95, hidden=hide_hole_card and i == 1)

        self.text(f"AI (total {player.get_value()})", 50, 290)
        for i, value in enumerate(player.cards):
            self.card(value, faces["player"][i], 50 + i * CARD_GAP, 345)

        self.text(message, WIDTH // 2, 520, center=True)
        self.text("SPACE: next hand   ESC: quit", WIDTH // 2, 570, BLACK, center=True, small=True)
        pygame.display.flip()

    def title_screen(self):
        self.screen.fill(TABLE_GREEN)
        self.text("AI Blackjack", WIDTH // 2, HEIGHT // 2 - 50, center=True)
        self.text("Press SPACE to watch the AI play", WIDTH // 2, HEIGHT // 2 + 20, center=True, small=True)
        pygame.display.flip()

    # --- Game flow -------------------------------------------------------

    def pause(self, ms):
        """Wait while keeping the window responsive (and closable)."""
        end = pygame.time.get_ticks() + ms
        while pygame.time.get_ticks() < end:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    raise SystemExit
            pygame.time.wait(10)

    def deal(self, hand, faces):
        value = self.deck.deal()
        hand.add_card(value)
        faces.append(face_for(value, self.rng))

    def play_hand(self):
        player, dealer = Hand(), Hand()
        faces = {"player": [], "dealer": []}
        for _ in range(2):
            self.deal(player, faces["player"])
            self.deal(dealer, faces["dealer"])
        upcard = dealer.cards[0]
        show = lambda msg, hide=True: self.render(player, dealer, faces, msg, hide)

        show("AI is thinking...")
        self.pause(1500)

        while player.get_value() < 21:
            if choose_action(self.strategy, player.get_value(), upcard) == HIT:
                show("AI chooses to HIT")
                self.pause(1000)
                self.deal(player, faces["player"])
                show("Dealing card...")
                self.pause(1000)
            else:
                show("AI chooses to STAND")
                self.pause(1000)
                break

        player_total = player.get_value()
        if player_total > 21:
            show("AI BUSTS! Dealer wins.", hide=False)
            return

        show("Dealer's turn...", hide=False)
        self.pause(1500)
        while dealer.get_value() < 17:
            self.deal(dealer, faces["dealer"])
            show("Dealer hits...", hide=False)
            self.pause(1000)

        dealer_total = dealer.get_value()
        outcome = settle(player_total, dealer_total)
        if dealer_total > 21:
            message = "DEALER BUSTS! AI wins."
        elif outcome > 0:
            message = "AI WINS!"
        elif outcome < 0:
            message = "DEALER WINS."
        else:
            message = "PUSH (tie)."
        show(message, hide=False)


def run(strategy):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Blackjack AI")
    table = Table(screen, strategy)
    table.title_screen()

    try:
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    break
                if event.key == pygame.K_SPACE:
                    table.play_hand()
    except SystemExit:
        pass
    finally:
        pygame.quit()
