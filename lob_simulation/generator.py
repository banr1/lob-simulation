from uuid import uuid4

import numpy as np
from pandas.api.types import CategoricalDtype

from .model import CancelDf, CancelSr, LimitDf, LimitSr, MarketDf, MarketSr, Side


class LimitOrderGenerator:
    """
    Limit Orderを生成するクラス。
    ex)
    - price: 100
    - mu: 5
    - xi: 100
    - unit: 0.1
    のとき、...
    """

    def __init__(self, price: float, mu: float, xi: float, unit: float) -> None:
        self.price = price
        self.mu = mu
        self.xi = xi
        self.unit = unit

    def run(self, mid_price: float) -> LimitDf:
        if self.price < mid_price:
            side = Side.LONG
        elif self.price > mid_price:
            side = Side.SHORT
        else:
            return LimitDf()
        # 注文数: 平均muのPoisson dist.
        order_num = np.random.poisson(self.mu)
        if order_num == 0:
            return LimitDf()

        # それぞれの注文量: 1 + 平均xiのPoisson dist.
        order_amount = self.unit * (1 + np.random.poisson(self.xi))
        order_list = LimitDf(
            [
                LimitSr(
                    {"price": self.price, "amount": order_amount, "side": side},
                    name=uuid4(),
                )
                for _ in range(order_num)
            ]
        )
        order_list = order_list.astype(
            {"side": CategoricalDtype(categories=list(Side))}
        )

        return order_list


class MarketOrderGenerator:
    """
    Market Orderを生成するクラス。
    """

    def __init__(self, side: Side, mu: float, xi: float, unit: float) -> None:
        self.side = side
        self.mu = mu
        self.xi = xi
        self.unit = unit

    def run(self) -> MarketDf:
        # 注文数: 平均muのPoisson dist.
        order_num = np.random.poisson(self.mu)
        if order_num == 0:
            return MarketDf()

        # それぞれの注文量: 1 + 平均xiのPoisson dist.
        order_amount = self.unit * (1 + np.random.poisson(self.xi))
        order_list = MarketDf(
            [
                MarketSr({"amount": order_amount, "side": self.side}, name=uuid4())
                for _ in range(order_num)
            ]
        )
        order_list = order_list.astype(
            {"side": CategoricalDtype(categories=list(Side))}
        )

        return order_list


class CancelGenerator:
    def __init__(self, price: float, mu: float, xi: float, unit: float) -> None:
        self.price = price
        self.mu = mu
        self.xi = xi
        self.unit = unit

    def run(self) -> CancelDf:
        # 注文数: 平均muのPoisson dist.
        order_num = np.random.poisson(self.mu)
        # それぞれの注文量: 1 + 平均xiのPoisson dist.
        order_amount = self.unit * (1 + np.random.poisson(self.xi))
        order_list = CancelDf(
            [
                CancelSr({"price": self.price, "amount": order_amount}, name=uuid4())
                for _ in range(order_num)
            ]
        )
        return order_list
