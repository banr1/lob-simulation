from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
from loguru  import logger

from .model import CancelDf, Df, LimitDf, MarketDf, Side, Sr


class LOB:
    book: LimitDf = LimitDf()
    unit: float

    def __init__(self, unit: float) -> None:
        self.unit = unit

    def receive_orders(self, limits: LimitDf=None, cancels: CancelDf=None, markets: MarketDf = None) -> float:
        if limits is not None:
            self._receive_limits(limits)
        if cancels is not None:
            self._receive_cancels(cancels)
        if markets is not None:
            self._receive_markets(markets)

        return self.mid_price

    def _receive_limits(self, limits: LimitDf) -> None:
        self.book = pd.concat([self.book, limits])

    def _receive_cancels(self, cancels: CancelDf) -> None:
        # 便宜上cancelsをpriceで集約する、本ケースでは問題ない
        cancels = cancels.groupby("price").sum().reset_index()
        for _, c in cancels.iterrows():
            book_ = self.book.loc[self.book.price.eq(c.price), :]
            if len(book_) == 0:
                return

            c_amount = c.amount
            for idx, b in book_.iterrows():
                match_amount = min(b.amount, c_amount)
                # logger.info(f"cancel: {match_amount}")
                self.book.loc[idx, "amount"] = b.amount - match_amount
                c_amount = c_amount - match_amount

                if c_amount == 0:
                    break
            # 該当価格のLOB注文量が0のオーダーを掃除
            self.book.drop(
                self.book.loc[self.book.price.eq(c.price) & self.book.amount.eq(0)].index,
                inplace=True,
            )

    def _receive_markets(self, markets: MarketDf) -> None:
        for _, m in markets.iterrows():
            # MarketLongだったら、マッチ相手はLimitShortでask、つまり価格asc順にした上からマッチ
            # MarketShortだったら、マッチ相手はLimitShortでbid、つまり価格desc順にした上からマッチ
            is_asc = m.side == Side.LONG
            book_ = self.book.loc[self.book.side.eq(m.side.opposite), :] \
                .sort_values("price", ascending=is_asc)
            if len(book_) == 0:
                return

            m_amount = m.amount
            for idx, b in book_.iterrows():
                match_amount = min(b.amount, m_amount)
                self.book.loc[idx, "amount"] = b.amount - match_amount
                m_amount = m_amount - match_amount

                if m_amount == 0:
                    break
            # 該当価格のLOB注文量が0のオーダーを掃除
            self.book.drop(
                self.book.loc[self.book.side.eq(m.side.opposite) & self.book.amount.eq(0)].index,
                inplace=True,
            )

    def _round_precise(cls, num: float, unit: float) -> float:
        rounded_num = Decimal(str(num)).quantize(Decimal(str(unit)), rounding=ROUND_HALF_UP)
        return float(rounded_num)

    @property
    def agg_book(self) -> Df:
        def only_one_side(sr: Sr) -> str:
            assert (sr.nunique() == 1) & (sr.notnull().all())
            return sr[0]
        return self.book \
            .groupby("price", as_index=False) \
            .agg({"amount": "sum", "side": only_one_side}) \
            .sort_values("price", ascending=False) \
            .reset_index(drop=True)

    @property
    def agg_book_center(self) -> Df:
        best_ask_idx = self.agg_book.loc[self.agg_book.side.eq(Side.SHORT)].iloc[-1].name
        return self.agg_book.iloc[best_ask_idx-4: best_ask_idx+5, :]

    @property
    def best_ask(self) -> float:
        return self.book.loc[self.book.side.eq(Side.SHORT), "price"].min()

    @property
    def best_bid(self) -> float:
        return self.book.loc[self.book.side.eq(Side.LONG), "price"].max()

    @property
    def mid_price(self) -> float:
        mid_price_ = (self.best_ask + self.best_bid) / 2
        return self._round_precise(mid_price_, self.unit * 0.001)
