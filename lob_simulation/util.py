from decimal import ROUND_HALF_UP, Decimal


def round_precise(num: float, digit_num: float) -> float:
    rounded_num = Decimal(str(num)).quantize(
        Decimal(str(digit_num)), rounding=ROUND_HALF_UP
    )
    return float(rounded_num)
