import sys
import os
import pandas as pd

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.simulator import MatchSimulator

def test():
    sim = MatchSimulator()
    print("Testing Germany vs Brazil")
    feats = sim.feature_builder.build_match_features("Germany", "Brazil")

    home_rating = feats["home_rating"]
    away_rating = feats["away_rating"]
    home_conf = feats.get("home_confidence", 0)
    away_conf = feats.get("away_confidence", 0)
    print(f"Germany Rating: {home_rating} (Conf: {home_conf})")
    print(f"Brazil Rating: {away_rating} (Conf: {away_conf})")
    print(f"Brazil Squad size: {len(feats['away_players'])}")
    for p in feats['away_players'][:11]:
        print(f" - {p['name']} (Rating: {p['rating']})")

if __name__ == '__main__':
    test()
