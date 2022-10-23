import numpy as np
import pandas as pd
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns

from .lob import LOB
from .generator import CancelGenerator, LimitOrderGenerator, MarketOrderGenerator
from .model import Df, LimitDf, CancelDf, MarketDf, Side, Sr


UNIT = 0.1
N_ROUND = 100
LIMIT_LAM_RANGE, LIMIT_XI_RANGE = (1, 3), (5, 10)
CANCEL_LAM_RANGE, CANCEL_XI_RANGE = (1, 1), (1, 5)
MARKET_LONG_LAM, MARKET_LONG_XI = 5, 50
MARKET_SHORT_LAM, MARKET_SHORT_XI = 5, 50

INIT_MID_PRICE = 100
INIT_WIDTH=15
INIT_LIMIT_ROUND = 10


def main():
    price_diffs_from_center = [UNIT * i for i in range(0, 101)]

    lo_generators: list[LimitOrderGenerator] = []
    ca_generators: list[CancelGenerator] = []

    for i, diff in enumerate(price_diffs_from_center):
        limit_lam = np.random.uniform(*LIMIT_LAM_RANGE)
        limit_xi = np.random.uniform(*LIMIT_XI_RANGE)
        cancel_lam = np.random.uniform(*CANCEL_LAM_RANGE)
        cancel_xi = np.random.uniform(*CANCEL_XI_RANGE)

        if i != 0:
            lower_price = INIT_MID_PRICE - diff
            upper_price = INIT_MID_PRICE + diff
            lo_generators.append(LimitOrderGenerator(lower_price, lam=limit_lam, xi=limit_xi, unit=UNIT))
            lo_generators.append(LimitOrderGenerator(upper_price, lam=limit_lam, xi=limit_xi, unit=UNIT))
            ca_generators.append(CancelGenerator(lower_price, lam=cancel_lam, xi=cancel_xi, unit=UNIT))
            ca_generators.append(CancelGenerator(upper_price, lam=cancel_lam, xi=cancel_xi, unit=UNIT))
        # 最初だけは丁度中央なので一つだけ
        else:
            lo_generators.append(LimitOrderGenerator(INIT_MID_PRICE, lam=limit_lam, xi=limit_xi, unit=UNIT))
            ca_generators.append(CancelGenerator(INIT_MID_PRICE, lam=cancel_lam, xi=cancel_xi, unit=UNIT))

    market_long_lam = MARKET_LONG_LAM
    market_long_xi = MARKET_LONG_XI
    market_short_lam = MARKET_SHORT_LAM
    market_short_xi = MARKET_SHORT_XI
    ml_generator = MarketOrderGenerator(Side.LONG, lam=market_long_lam, xi=market_long_xi, unit=UNIT)
    ms_generator = MarketOrderGenerator(Side.SHORT, lam=market_short_lam, xi=market_short_xi, unit=UNIT)

    lob = LOB(unit=UNIT)

    for _ in range(INIT_LIMIT_ROUND):
        limits = pd.concat([lo.run(INIT_MID_PRICE) for lo in lo_generators if lo.price != INIT_MID_PRICE])

        init_mid_price = lob.receive_orders(limits=limits)

    mid_price_history = [Sr({"time": 0, "mid_price": init_mid_price})]
    for t in range(1, N_ROUND+1):
        limits = pd.concat([lo.run(lob.mid_price) for lo in lo_generators])
        cancels = pd.concat([ca.run() for ca in ca_generators])
        markets = pd.concat([
            ml_generator.run(),
            ms_generator.run(),
        ])
        mid_price = lob.receive_orders(markets=markets, limits=limits, cancels=cancels)
        logger.info(f"[{t:04}]: {mid_price}")
        mid_price_history.append(Sr({"time": t, "mid_price": mid_price}))
    mid_price_history = Df(mid_price_history)

    fig, ax = plt.subplots()
    sns.lineplot(x="time", y="mid_price", data=mid_price_history, ax=ax)
    fig.savefig("img/figure.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
