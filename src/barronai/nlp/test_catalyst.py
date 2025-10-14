from .catalyst_nlp import fetch_news, score_catalyst
def main():
    items = fetch_news("TSLA")
    agg = score_catalyst(items)
    print("HEADLINES:", len(items))
    print("CATALYST SCORE:", agg)
if __name__ == "__main__":
    main()
