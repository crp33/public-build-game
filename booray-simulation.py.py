# Oh Hey BooRay Simulation
# Calculates house edge and frequencies for the Oh Hey BooRay casino card game

import numpy as np
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class GameResult:
    tricks_won: int
    used_all_trump: bool
    used_akq_trump: bool
    initial_hand: List
    final_hand: List
    og3_type: str
    og3_payout: float
    ante_result: float
    booray_result: float
    play_result: float

class OhHeyBooray:
    def __init__(self):
        self.ranks = {2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 8:8, 9:9, 10:10, 11:'J', 12:'Q', 13:'K', 14:'A'}
        self.deck = [(rank, suit) for rank in range(2,15) for suit in ['H','D','C','S']]
        
    def deal_cards(self) -> Tuple[List, List]:
        deck = self.deck.copy()
        np.random.shuffle(deck)
        return deck[:3], deck[3:6]
    
    def evaluate_og3(self, hand: List) -> Tuple[str, float]:
        ranks = sorted([card[0] for card in hand])
        suits = [card[1] for card in hand]
        
        if len(set(suits)) == 1 and ranks == [12,13,14]:
            return "Mini Royal", 50
        if len(set(suits)) == 1 and ranks[2] - ranks[0] == 2:
            return "Straight Flush", 40
        if len(set(ranks)) == 1:
            return "Trips", 30
        if ranks[2] - ranks[0] == 2:
            return "Straight", 6
        if len(set(suits)) == 1:
            return "Flush", 3
        if len(set(ranks)) == 2:
            return "Pair", 1
        return "Loss", -1
            
    def should_draw(self, hand: List, trump_suit: str) -> Tuple[bool, List]:
        trump_cards = [card for card in hand if card[1] == trump_suit]
        if len(trump_cards) >= 2:
            return False, []
        
        non_trump = [card for card in hand if card[1] != trump_suit]
        low_cards = [card for card in non_trump if card[0] < 10]
        return len(low_cards) > 0, low_cards
    
    def evaluate_trick(self, player_card: Tuple, dealer_card: Tuple, trump_suit: str) -> bool:
        if player_card[1] == dealer_card[1]:
            return player_card[0] > dealer_card[0]
        elif player_card[1] == trump_suit:
            return True
        elif dealer_card[1] == trump_suit:
            return False
        return False
        
    def play_game(self) -> GameResult:
        player_hand, dealer_hand = self.deal_cards()
        trump_suit = dealer_hand[2][1]
        
        initial_hand = player_hand.copy()
        og3_type, og3_payout = self.evaluate_og3(initial_hand)
        
        should_draw, cards_to_draw = self.should_draw(player_hand, trump_suit)
        if should_draw:
            remaining_deck = [card for card in self.deck if card not in player_hand + dealer_hand]
            np.random.shuffle(remaining_deck)
            for card in cards_to_draw:
                player_hand.remove(card)
                player_hand.append(remaining_deck.pop())
                
        tricks_won = 0
        used_trump = []
        
        for i, dealer_card in enumerate(dealer_hand):
            playable = [card for card in player_hand if card[1] == dealer_card[1]]
            if not playable:
                playable = [card for card in player_hand if card[1] == trump_suit]
            if not playable:
                playable = player_hand
                
            play_card = max(playable, key=lambda x: x[0])
            player_hand.remove(play_card)
            
            if play_card[1] == trump_suit:
                used_trump.append(play_card)
                
            if self.evaluate_trick(play_card, dealer_card, trump_suit):
                tricks_won += 1
                
        # Calculate results
        ante_result = -1.0
        booray_result = -1.0
        play_result = -1.0

        if tricks_won >= 1:
            ante_result = 1.0
            booray_result = 0.0  # Push for 1 or 2 tricks
            play_result = 0.0    # Push for 1 trick
            
        if tricks_won >= 2:
            play_result = 1.0    # 1:1 for 2 tricks
            
        if tricks_won == 3:
            play_result = 2.0    # 2:1 for 3 tricks
            if sorted([card[0] for card in used_trump]) == [12,13,14] and len(set([card[1] for card in used_trump])) == 1:
                booray_result = 500.0  # AKQ trump
            elif len(used_trump) == 3:
                booray_result = 10.0    # All trump
            else:
                booray_result = 1.0     # Regular 3-trick win
                
        return GameResult(
            tricks_won=tricks_won,
            used_all_trump=len(used_trump) == 3,
            used_akq_trump=sorted([card[0] for card in used_trump]) == [12,13,14] if len(used_trump) == 3 else False,
            initial_hand=initial_hand,
            final_hand=player_hand,
            og3_type=og3_type,
            og3_payout=og3_payout,
            ante_result=ante_result,
            booray_result=booray_result,
            play_result=play_result
        )

def run_simulation(n_trials: int = 1000000) -> Dict:
    game = OhHeyBooray()
    results = defaultdict(int)
    payouts = defaultdict(list)
    
    for _ in range(n_trials):
        result = game.play_game()
        results[f'tricks_{result.tricks_won}'] += 1
        results[f'og3_{result.og3_type}'] += 1
        
        if result.used_all_trump:
            results['all_trump'] += 1
        if result.used_akq_trump:
            results['akq_trump'] += 1
            
        payouts['ante'].append(result.ante_result)
        payouts['booray'].append(result.booray_result)
        payouts['play'].append(result.play_result)
        payouts['og3'].append(result.og3_payout)
        
    house_edge = {
        'ante': -np.mean(payouts['ante']) * 100,
        'booray': -np.mean(payouts['booray']) * 100,
        'play': -np.mean(payouts['play']) * 100,
        'og3': -np.mean(payouts['og3']) * 100,
        'total': -(np.mean(payouts['ante']) + np.mean(payouts['booray']) + 
                  np.mean(payouts['play']) + np.mean(payouts['og3'])) * 100
    }
    
    return {
        'frequencies': {k: v/n_trials for k, v in results.items()},
        'house_edge': house_edge
    }

if __name__ == "__main__":
    # Run simulation and print results
    print("Running Oh Hey BooRay simulation...")
    results = run_simulation(1000000)
    
    print("\nFrequencies:")
    for k, v in results['frequencies'].items():
        print(f"{k}: {v*100:.2f}%")
        
    print("\nHouse Edge:")
    for k, v in results['house_edge'].items():
        print(f"{k}: {v:.2f}%")
