import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo
from market_report import build_report


class ReportTests(unittest.TestCase):
    def test_report_contains_four_markets_and_percentages(self):
        def mock_fetch(symbol):
            return (date(2026, 11, 11), 100.0), (date(2026, 11, 12), 101.0)
        content = build_report(datetime(2026, 11, 12, 17, 30, tzinfo=ZoneInfo('Asia/Kolkata')), mock_fetch)
        for market in ('Nifty 50', 'Bank Nifty', 'BSE Sensex', 'USD/INR'):
            self.assertIn(market, content)
        self.assertIn('+1.00%', content)
        self.assertIn('₹101.0000', content)

    def test_all_sources_failed(self):
        def failed_fetch(symbol):
            raise RuntimeError('network')
        with self.assertRaisesRegex(RuntimeError, 'All market-data requests failed'):
            build_report(datetime(2026, 11, 12, tzinfo=ZoneInfo('Asia/Kolkata')), failed_fetch)


if __name__ == '__main__':
    unittest.main()
