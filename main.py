import chess
from engine.evaluate import parse_and_evaluate

def main():
    # Example FEN positions
    positions = [
        "r5k1/pp2p2p/2p1q1p1/3p4/5r2/1BBP2R1/PP1Q3P/R5K1 b - - 1 22"# Knight moved
    ]

    for fen in positions:
        print(parse_and_evaluate(fen))
        print("-" * 40)

if __name__ == "__main__":
    main()
