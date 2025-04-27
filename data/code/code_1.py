import random

# Define card ranks (Ace through King)
RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

# Define suits (Clubs, Diamonds, Hearts, Spades)
SUITS = ['♣', '♦', '♥', '♠']

def get_card_value(card):
    """Returns the numerical value of the card."""
    if card[0] == 'A':
        return 14  # Ace is worth 14 points
    elif card[0] in ['T', 'J', "Q", "K"]:
        return int(card[0])
    else:
        return int(card[:-1])

def shuffle_deck(deck):
    """Shuffles the given deck of cards."""
    random.shuffle(deck)

class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []

    def draw(self, deck):
        """Draws one card from the deck and adds it to their hand."""
        self.hand.append(deck.pop())

    def show_hand(self):
        """Shows the current hand of the player."""
        print(f"{self.name}'s Hand: {', '.join(self.hand)}")

    def calculate_score(self):
        """Calculates the score of the player's hand based on standard poker scoring rules."""
        scores = {
            'High Card': 0,
            'Pair': 0,
             'Two Pair': 0,
              'Three of a Kind': 0,
               'Straight': 0,
                'Flush': 0,
                 'Full House': 0,
                  'Four of a Kind': -1,
                   'Straight Flush': -1,
                    'Royal Flush': -1
        }
        
        # Check for highest card
        highest_card = max(self.hand, key=get_card_value)
        if len(scores) > 0:
            scores['High Card'] = get_card_value(highest_card)
        
        # Check other combinations
        for rank in RANKS:
            pairs = [card for card in self.hand if card[-1] == SUITS[0] and get_card_value(card) == rank]
            if len(pairs) >= 2:
                scores['Pair'] += 1
        
        # Add more logic here for other possible hands
        
        return scores

def main():
    deck = []
    
    # Create a deck of cards
    for suit in SUITS:
        for rank in range(2, 15):  # Exclude Aces for now
            deck.append(f"{rank}{suit}")
            
    # Shuffle the deck
    shuffle_deck(deck)
    
    players = {}
    num_players = int(input("Enter number of players: "))
    
    for i in range(num_players):
        player_name = input(f"Enter name for player {i+1}: ")
        players[player_name] = Player(player_name)
        
    for _ in range(5):
        for player in players.values():
            player.draw(deck)
    
    print("\nFinal Hands:")
    for player in players.items():
        player.show_hand()
    
    winners = {}
    for player in sorted(players.values(), key=lambda x: x.calculate_score().values(), reverse=True):
        if not any(scores < 0 for scores in player.calculate_score().values()):
            winners[player.name] = player.calculate_score()
    
    if len(winners) == 1:
        winner = list(winners.keys())[0]
        print(f"\nWinner: {winner}!")
    elif len(winners) > 1:
        tiebreakers = [player.calculate_score() for player in winners.values()]
        print("\nTiebreaker Scores:")
        for idx, (_, score) in enumerate(zip(winners, tiebreakers)):
            print(f"{idx+1}. {score}")
        final_winner = input("\nEnter player index to determine the winner: ")
        try:
            final_winner_idx = int(final_winner) - 1
            final_winner_name = list(winners)[final_winner_idx]
            print(f"\nFinal Winner: {final_winner_name}!")
        except ValueError:
            print("\nInvalid choice! Defaulting to first placed player.")
            final_winner_name, _ = list(winners.items())[0]
            print(f"Default Final Winner: {final_winer_name}")
    else:
        print("\nNo valid outcomes found!")

if __name__ == "__main__":
    main()