import asyncio
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.simulator import MatchSimulator

def test():
    sim = MatchSimulator()
    print("Brazil vs Germany")
    res1 = sim.simulate_match("Brazil", "Germany")
    print(f"Brazil (Home): {res1['win_prob_home']}%")
    print(f"Draw: {res1['win_prob_draw']}%")
    print(f"Germany (Away): {res1['win_prob_away']}%")
    print(f"Brazil Rating: {res1['match_context']['home_rating']}")
    print(f"Germany Rating: {res1['match_context']['away_rating']}")

    print("\nGermany vs Brazil")
    res2 = sim.simulate_match("Germany", "Brazil")
    print(f"Germany (Home): {res2['win_prob_home']}%")
    print(f"Draw: {res2['win_prob_draw']}%")
    print(f"Brazil (Away): {res2['win_prob_away']}%")
    print(f"Germany Rating: {res2['match_context']['home_rating']}")
    print(f"Brazil Rating: {res2['match_context']['away_rating']}")

if __name__ == '__main__':
    test()
