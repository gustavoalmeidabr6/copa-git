import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from models.simulator import MatchSimulator

def check_odds():
    sim = MatchSimulator()
    print("--- VEGAS ODDS ---")
    
    matchups = [
        ("Brazil", "Germany"),
        ("Brazil", "Netherlands")
    ]
    
    for h, a in matchups:
        odds = sim.vegas_probs.get((h, a))
        if odds:
            ph, pd, pa = odds
            print(f"{h} vs {a}:")
            print(f"  {h} Win: {ph*100:.1f}%")
            print(f"  Draw: {pd*100:.1f}%")
            print(f"  {a} Win: {pa*100:.1f}%")
        else:
            print(f"{h} vs {a}: NO ODDS FOUND IN CACHE")

if __name__ == '__main__':
    check_odds()
