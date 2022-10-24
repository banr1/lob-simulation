import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger

from .generator import CancelGenerator, LimitOrderGenerator, MarketOrderGenerator
from .lob import LOB
from .model import Df, Side, Sr

UNIT = 0.1
N_ROUND = 100
LIMIT_MU_RANGE, LIMIT_XI_RANGE = (1, 3), (5, 15)
CANCEL_MU_RANGE, CANCEL_XI_RANGE = (1, 1), (1, 5)
MARKET_LONG_MU, MARKET_LONG_XI = 5, 50
MARKET_SHORT_MU, MARKET_SHORT_XI = 5, 50
RANDOM_SEED = 0

INIT_MID_PRICE = 100
INIT_WIDTH = 15
INIT_LIMIT_ROUND = 10

np.random.seed(RANDOM_SEED)


def main() -> None:
    price_diffs_from_center = [UNIT * i for i in range(0, 101)]

    lo_generators: list[LimitOrderGenerator] = []
    ca_generators: list[CancelGenerator] = []

    for i, diff in enumerate(price_diffs_from_center):
        limit_mu = np.random.uniform(*LIMIT_MU_RANGE)
        limit_xi = np.random.uniform(*LIMIT_XI_RANGE)
        cancel_mu = np.random.uniform(*CANCEL_MU_RANGE)
        cancel_xi = np.random.uniform(*CANCEL_XI_RANGE)

        if i != 0:
            lower_price = INIT_MID_PRICE - diff
            upper_price = INIT_MID_PRICE + diff
            lo_generators.append(
                LimitOrderGenerator(lower_price, mu=limit_mu, xi=limit_xi, unit=UNIT)
            )
            lo_generators.append(
                LimitOrderGenerator(upper_price, mu=limit_mu, xi=limit_xi, unit=UNIT)
            )
            ca_generators.append(
                CancelGenerator(lower_price, mu=cancel_mu, xi=cancel_xi, unit=UNIT)
            )
            ca_generators.append(
                CancelGenerator(upper_price, mu=cancel_mu, xi=cancel_xi, unit=UNIT)
            )
        # 最初だけは丁度中央なので一つだけ
        else:
            lo_generators.append(
                LimitOrderGenerator(INIT_MID_PRICE, mu=limit_mu, xi=limit_xi, unit=UNIT)
            )
            ca_generators.append(
                CancelGenerator(INIT_MID_PRICE, mu=cancel_mu, xi=cancel_xi, unit=UNIT)
            )

    market_long_mu = MARKET_LONG_MU
    market_long_xi = MARKET_LONG_XI
    market_short_mu = MARKET_SHORT_MU
    market_short_xi = MARKET_SHORT_XI
    ml_generator = MarketOrderGenerator(
        Side.LONG, mu=market_long_mu, xi=market_long_xi, unit=UNIT
    )
    ms_generator = MarketOrderGenerator(
        Side.SHORT, mu=market_short_mu, xi=market_short_xi, unit=UNIT
    )

    lob = LOB(unit=UNIT)

    for _ in range(INIT_LIMIT_ROUND):
        limits = pd.concat(
            [
                lo.run(INIT_MID_PRICE)
                for lo in lo_generators
                if lo.price != INIT_MID_PRICE
            ]
        )

        init_mid_price = lob.receive_orders(limits=limits)

    mid_price_history = [Sr({"time": 0, "mid_price": init_mid_price})]
    for t in range(1, N_ROUND + 1):
        limits = pd.concat([lo.run(lob.mid_price) for lo in lo_generators])
        cancels = pd.concat([ca.run() for ca in ca_generators])
        markets = pd.concat(
            [
                ml_generator.run(),
                ms_generator.run(),
            ]
        )
        mid_price = lob.receive_orders(markets=markets, limits=limits, cancels=cancels)
        logger.info(f"[{t:04}]: {mid_price}")
        mid_price_history.append(Sr({"time": t, "mid_price": mid_price}))
    mid_price_history = Df(mid_price_history)

    fig, ax = plt.subplots()
    sns.lineplot(x="time", y="mid_price", data=mid_price_history, ax=ax)
    fig.savefig("img/figure.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
