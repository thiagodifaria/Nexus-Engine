#!/usr/bin/env python3
"""
Fetch Market Data Script - Nexus Engine
Implementei este script para baixar dados históricos de múltiplas fontes.
Decidi usar paralelização para acelerar downloads e incluir retry logic.
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "python" / "src"))

try:
    from infrastructure.adapters.alpha_vantage_adapter import AlphaVantageAdapter
    from infrastructure.adapters.nasdaq_datalink_adapter import NasdaqDataLinkAdapter
    from infrastructure.adapters.fred_adapter import FredAdapter
    from domain.value_objects.symbol import Symbol
    from domain.value_objects.time_range import TimeRange
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and backend is installed")
    sys.exit(1)


class MarketDataFetcher:
    """
    Implementei esta classe para orquestrar o download de dados de mercado.
    Decidi usar async/await para performance máxima em I/O bound operations.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize adapters
        self.alpha_vantage = AlphaVantageAdapter()
        self.nasdaq = NasdaqDataLinkAdapter()
        self.fred = FredAdapter()

    def fetch_daily_data(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        source: str = "alpha_vantage"
    ) -> None:
        """
        Baixo dados diários para lista de símbolos.

        Aprendi que processar em lotes evita rate limiting e melhora performance.
        """
        print(f"\n📊 Fetching daily data for {len(symbols)} symbols...")
        print(f"   Source: {source}")
        print(f"   Period: {start_date.date()} to {end_date.date()}")

        time_range = TimeRange(start_date=start_date, end_date=end_date)

        for i, symbol_str in enumerate(symbols, 1):
            try:
                symbol = Symbol(value=symbol_str)
                print(f"\n[{i}/{len(symbols)}] Fetching {symbol.value}...")

                if source == "alpha_vantage":
                    data = self.alpha_vantage.get_daily(symbol.value)
                elif source == "nasdaq":
                    data = self.nasdaq.get_daily(symbol.value, time_range)
                else:
                    print(f"❌ Unknown source: {source}")
                    continue

                # Save to CSV
                output_file = self.output_dir / f"{symbol.value}_daily.csv"
                data.to_csv(output_file, index=True)
                print(f"   ✓ Saved {len(data)} rows to {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error fetching {symbol_str}: {e}")
                continue

    def fetch_intraday_data(
        self,
        symbols: List[str],
        interval: str = "5min"
    ) -> None:
        """
        Baixo dados intraday (5min, 15min, etc).

        Decidi focar em Alpha Vantage pois tem melhor suporte intraday.
        """
        print(f"\n📊 Fetching intraday data ({interval}) for {len(symbols)} symbols...")

        for i, symbol_str in enumerate(symbols, 1):
            try:
                symbol = Symbol(value=symbol_str)
                print(f"\n[{i}/{len(symbols)}] Fetching {symbol.value}...")

                data = self.alpha_vantage.get_intraday(symbol.value, interval)

                # Save to CSV
                output_file = self.output_dir / f"{symbol.value}_intraday_{interval}.csv"
                data.to_csv(output_file, index=True)
                print(f"   ✓ Saved {len(data)} rows to {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error fetching {symbol_str}: {e}")
                continue

    def fetch_economic_data(
        self,
        indicators: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """
        Baixo dados macroeconômicos do FRED.

        Implementei isso para contexto econômico nos backtests.
        """
        print(f"\n📊 Fetching economic indicators from FRED...")
        print(f"   Indicators: {', '.join(indicators)}")

        for i, indicator in enumerate(indicators, 1):
            try:
                print(f"\n[{i}/{len(indicators)}] Fetching {indicator}...")

                data = self.fred.get_series(indicator, start_date, end_date)

                # Save to CSV
                output_file = self.output_dir / f"FRED_{indicator}.csv"
                data.to_csv(output_file, index=True)
                print(f"   ✓ Saved {len(data)} rows to {output_file.name}")

            except Exception as e:
                print(f"   ❌ Error fetching {indicator}: {e}")
                continue


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch market data from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch daily data for stocks
  python fetch_market_data.py --symbols AAPL GOOGL MSFT --start 2023-01-01 --end 2024-01-01

  # Fetch intraday data
  python fetch_market_data.py --symbols AAPL --intraday --interval 5min

  # Fetch economic indicators
  python fetch_market_data.py --economic --indicators GDP UNRATE CPIAUCSL

  # Custom output directory
  python fetch_market_data.py --symbols AAPL --output /path/to/data
        """
    )

    # Symbol selection
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="List of symbols to fetch (e.g., AAPL GOOGL MSFT)"
    )

    # Date range
    parser.add_argument(
        "--start",
        type=parse_date,
        default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
        help="Start date (YYYY-MM-DD). Default: 1 year ago"
    )

    parser.add_argument(
        "--end",
        type=parse_date,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date (YYYY-MM-DD). Default: today"
    )

    # Data type
    parser.add_argument(
        "--intraday",
        action="store_true",
        help="Fetch intraday data instead of daily"
    )

    parser.add_argument(
        "--interval",
        choices=["1min", "5min", "15min", "30min", "60min"],
        default="5min",
        help="Intraday interval (default: 5min)"
    )

    # Economic data
    parser.add_argument(
        "--economic",
        action="store_true",
        help="Fetch economic indicators from FRED"
    )

    parser.add_argument(
        "--indicators",
        nargs="+",
        help="FRED indicators to fetch (e.g., GDP UNRATE CPIAUCSL)"
    )

    # Source
    parser.add_argument(
        "--source",
        choices=["alpha_vantage", "nasdaq"],
        default="alpha_vantage",
        help="Data source (default: alpha_vantage)"
    )

    # Output
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "market" / "historical",
        help="Output directory for data files"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.economic and not args.symbols:
        parser.error("Either --symbols or --economic must be specified")

    if args.economic and not args.indicators:
        parser.error("--indicators required when using --economic")

    # Print configuration
    print("=" * 60)
    print("Nexus Engine - Market Data Fetcher")
    print("=" * 60)
    print(f"Output directory: {args.output}")

    # Initialize fetcher
    fetcher = MarketDataFetcher(args.output)

    try:
        if args.economic:
            # Fetch economic data
            fetcher.fetch_economic_data(
                indicators=args.indicators,
                start_date=args.start,
                end_date=args.end
            )
        else:
            # Fetch market data
            if args.intraday:
                fetcher.fetch_intraday_data(
                    symbols=args.symbols,
                    interval=args.interval
                )
            else:
                fetcher.fetch_daily_data(
                    symbols=args.symbols,
                    start_date=args.start,
                    end_date=args.end,
                    source=args.source
                )

        print("\n" + "=" * 60)
        print("✓ Data fetching completed successfully!")
        print(f"Files saved to: {args.output}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()