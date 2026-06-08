from app.services.backtest import PriceBar, run_moving_average_backtest


def test_moving_average_backtest_uses_fixed_fees_and_drawdown():
    prices = [
        PriceBar("2026-01-01", 100),
        PriceBar("2026-01-02", 102),
        PriceBar("2026-01-03", 105),
        PriceBar("2026-01-04", 103),
        PriceBar("2026-01-05", 107),
        PriceBar("2026-01-06", 111),
        PriceBar("2026-01-07", 108),
        PriceBar("2026-01-08", 112),
    ]

    result = run_moving_average_backtest(prices, entry_window=3, exit_window=2, fee_rate=0.001)

    assert result.total_return == 0.0759
    assert result.max_drawdown == -0.027
    assert result.trade_count == 1
    assert result.trades[0].entry_date == "2026-01-03"
    assert result.trades[0].exit_date == "2026-01-08"
