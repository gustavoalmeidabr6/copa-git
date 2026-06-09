import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.simulator import MatchSimulator

def test():
    sim = MatchSimulator()
    feats = sim.feature_builder.build_match_features("Germany", "Brazil")

    print("Germany Squad:")
    for p in feats['home_players'][:11]:
        print(f" - {p['name']} (Rating: {p['rating']})")

if __name__ == '__main__':
    test()
