from .position_manager import Position
from .execution_loop import manage_position
def main():
    pos = Position(ticker="TSLA", qty=100, entry=240.0, stop=230.0, take1=0, take2=0)
    res = manage_position(pos, cushion_pct=0.8)
    print(res)
if __name__ == "__main__":
    main()
