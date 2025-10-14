from ..data.provider import get_provider
from ..nlp.catalyst_nlp import fetch_news, score_catalyst
from ..agents.signal_builder import SignalBuilder

def main():
    prov = get_provider("yahoo")
    df = prov.quote_snapshot(["TSLA"]).fillna(method="ffill")
    last = df.iloc[0]["last"]
    news = fetch_news("TSLA")
    cat = score_catalyst(news)
    sb = SignalBuilder()
    sig = sb.build(
        ticker="TSLA",
        structure_score=0.6,       # placeholder until we compute pattern strength
        catalyst_score=cat["score"],
        narrative_score=0.4,       # placeholder for theme/narrative
        reasons={"examples": cat["examples"], "catalyst_reason": cat["reason"]}
    )
    print("SIGNAL:", sig)
if __name__ == "__main__":
    main()
