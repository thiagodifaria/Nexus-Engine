#!/usr/bin/env python3
"""
Seed Database Script - Nexus Engine
Implementei este script para popular o banco de dados com dados exemplo.
Decidi incluir estratégias pré-configuradas e backtests de demonstração.
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "python" / "src"))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from infrastructure.database.models import Base, Strategy, Backtest, Trade
    from infrastructure.database.postgres_client import PostgresClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root and backend is installed")
    sys.exit(1)


class DatabaseSeeder:
    """
    Implementei esta classe para popular o database com dados exemplo.
    Decidi criar estratégias realistas e backtests com resultados variados.
    """

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        """Crio todas as tabelas se não existirem."""
        print("📦 Creating database tables...")
        Base.metadata.create_all(self.engine)
        print("   ✓ Tables created")

    def seed_strategies(self) -> Dict[str, int]:
        """
        Populo banco com estratégias exemplo.

        Decidi incluir as 3 principais estratégias do C++ engine.
        """
        print("\n📊 Seeding strategies...")

        strategies_data = [
            {
                "name": "SMA Crossover 50/200",
                "strategy_type": "SMA_CROSSOVER",
                "description": "Classic Golden Cross strategy using 50 and 200-day moving averages",
                "parameters": {
                    "fast_period": 50,
                    "slow_period": 200,
                    "position_size": 1.0
                },
                "is_active": True
            },
            {
                "name": "MACD 12/26/9",
                "strategy_type": "MACD",
                "description": "MACD strategy with standard parameters",
                "parameters": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9,
                    "position_size": 1.0
                },
                "is_active": True
            },
            {
                "name": "RSI Mean Reversion",
                "strategy_type": "RSI",
                "description": "Mean reversion strategy using RSI indicator",
                "parameters": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70,
                    "position_size": 1.0
                },
                "is_active": True
            },
            {
                "name": "SMA Crossover 20/50 (Fast)",
                "strategy_type": "SMA_CROSSOVER",
                "description": "Faster SMA crossover for short-term trading",
                "parameters": {
                    "fast_period": 20,
                    "slow_period": 50,
                    "position_size": 0.5
                },
                "is_active": True
            },
            {
                "name": "RSI Aggressive",
                "strategy_type": "RSI",
                "description": "Aggressive RSI with tighter bounds",
                "parameters": {
                    "period": 14,
                    "oversold": 20,
                    "overbought": 80,
                    "position_size": 1.5
                },
                "is_active": False  # Desativada por ser muito agressiva
            }
        ]

        strategy_ids = {}

        for data in strategies_data:
            strategy = Strategy(
                name=data["name"],
                strategy_type=data["strategy_type"],
                description=data["description"],
                parameters=data["parameters"],
                is_active=data["is_active"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.session.add(strategy)
            self.session.flush()  # Get ID
            strategy_ids[data["name"]] = strategy.id

            status = "✓" if data["is_active"] else "○"
            print(f"   {status} {data['name']} (ID: {strategy.id})")

        self.session.commit()
        print(f"\n   ✓ {len(strategies_data)} strategies seeded")
        return strategy_ids

    def seed_backtests(self, strategy_ids: Dict[str, int]) -> List[int]:
        """
        Populo banco com backtests exemplo.

        Aprendi que incluir resultados variados ajuda a testar visualizações.
        """
        print("\n📊 Seeding backtests...")

        backtests_data = [
            {
                "strategy_name": "SMA Crossover 50/200",
                "symbols": ["AAPL"],
                "start_date": datetime(2023, 1, 1),
                "end_date": datetime(2023, 12, 31),
                "initial_capital": 100000.0,
                "final_capital": 115000.0,
                "total_trades": 24,
                "winning_trades": 15,
                "losing_trades": 9,
                "metrics": {
                    "total_return": 0.15,
                    "sharpe_ratio": 1.25,
                    "max_drawdown": -0.08,
                    "win_rate": 0.625
                }
            },
            {
                "strategy_name": "MACD 12/26/9",
                "symbols": ["GOOGL"],
                "start_date": datetime(2023, 1, 1),
                "end_date": datetime(2023, 12, 31),
                "initial_capital": 100000.0,
                "final_capital": 108500.0,
                "total_trades": 18,
                "winning_trades": 11,
                "losing_trades": 7,
                "metrics": {
                    "total_return": 0.085,
                    "sharpe_ratio": 0.95,
                    "max_drawdown": -0.12,
                    "win_rate": 0.611
                }
            },
            {
                "strategy_name": "RSI Mean Reversion",
                "symbols": ["MSFT"],
                "start_date": datetime(2023, 1, 1),
                "end_date": datetime(2023, 12, 31),
                "initial_capital": 100000.0,
                "final_capital": 94500.0,
                "total_trades": 32,
                "winning_trades": 14,
                "losing_trades": 18,
                "metrics": {
                    "total_return": -0.055,
                    "sharpe_ratio": -0.35,
                    "max_drawdown": -0.15,
                    "win_rate": 0.4375
                }
            },
            {
                "strategy_name": "SMA Crossover 20/50 (Fast)",
                "symbols": ["AAPL", "GOOGL", "MSFT"],
                "start_date": datetime(2023, 6, 1),
                "end_date": datetime(2023, 12, 31),
                "initial_capital": 150000.0,
                "final_capital": 162000.0,
                "total_trades": 45,
                "winning_trades": 28,
                "losing_trades": 17,
                "metrics": {
                    "total_return": 0.08,
                    "sharpe_ratio": 1.15,
                    "max_drawdown": -0.06,
                    "win_rate": 0.622
                }
            }
        ]

        backtest_ids = []

        for data in backtests_data:
            strategy_id = strategy_ids.get(data["strategy_name"])
            if not strategy_id:
                print(f"   ⚠️  Strategy not found: {data['strategy_name']}")
                continue

            backtest = Backtest(
                strategy_id=strategy_id,
                symbols=data["symbols"],
                start_date=data["start_date"],
                end_date=data["end_date"],
                initial_capital=data["initial_capital"],
                final_capital=data["final_capital"],
                total_trades=data["total_trades"],
                winning_trades=data["winning_trades"],
                losing_trades=data["losing_trades"],
                metrics=data["metrics"],
                status="completed",
                created_at=datetime.utcnow()
            )

            self.session.add(backtest)
            self.session.flush()
            backtest_ids.append(backtest.id)

            return_pct = data["metrics"]["total_return"] * 100
            status = "✓" if return_pct > 0 else "✗"
            print(f"   {status} {data['strategy_name']} on {', '.join(data['symbols'])}: {return_pct:+.1f}%")

        self.session.commit()
        print(f"\n   ✓ {len(backtests_data)} backtests seeded")
        return backtest_ids

    def seed_trades(self, backtest_ids: List[int]) -> None:
        """
        Populo banco com trades exemplo para cada backtest.

        Decidi criar apenas alguns trades representativos por backtest.
        """
        print("\n📊 Seeding sample trades...")

        total_trades = 0

        for backtest_id in backtest_ids[:2]:  # Apenas primeiros 2 backtests
            # Create some sample trades
            trades_data = [
                {
                    "backtest_id": backtest_id,
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 100.0,
                    "price": 150.50,
                    "timestamp": datetime(2023, 3, 15, 10, 30),
                    "pnl": 0.0
                },
                {
                    "backtest_id": backtest_id,
                    "symbol": "AAPL",
                    "side": "sell",
                    "quantity": 100.0,
                    "price": 158.75,
                    "timestamp": datetime(2023, 4, 20, 14, 15),
                    "pnl": 825.0  # (158.75 - 150.50) * 100
                },
                {
                    "backtest_id": backtest_id,
                    "symbol": "AAPL",
                    "side": "buy",
                    "quantity": 150.0,
                    "price": 162.00,
                    "timestamp": datetime(2023, 6, 10, 9, 45),
                    "pnl": 0.0
                },
                {
                    "backtest_id": backtest_id,
                    "symbol": "AAPL",
                    "side": "sell",
                    "quantity": 150.0,
                    "price": 159.25,
                    "timestamp": datetime(2023, 7, 5, 15, 30),
                    "pnl": -412.5  # (159.25 - 162.00) * 150
                }
            ]

            for trade_data in trades_data:
                trade = Trade(**trade_data)
                self.session.add(trade)
                total_trades += 1

        self.session.commit()
        print(f"   ✓ {total_trades} sample trades seeded")

    def clear_all_data(self):
        """Limpo todos os dados do banco (CUIDADO!)."""
        print("⚠️  Clearing all data from database...")
        self.session.query(Trade).delete()
        self.session.query(Backtest).delete()
        self.session.query(Strategy).delete()
        self.session.commit()
        print("   ✓ All data cleared")


def main():
    parser = argparse.ArgumentParser(
        description="Seed database with sample data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed with default data
  python seed_database.py

  # Clear and reseed
  python seed_database.py --clear

  # Use custom database URL
  python seed_database.py --db postgresql://user:pass@localhost/nexus
        """
    )

    parser.add_argument(
        "--db",
        "--database-url",
        dest="database_url",
        default="postgresql://nexus_user:nexus_secure_password@localhost:5432/nexus",
        help="Database URL (default: local PostgreSQL)"
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all existing data before seeding"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Nexus Engine - Database Seeder")
    print("=" * 60)

    try:
        seeder = DatabaseSeeder(args.database_url)

        # Create tables
        seeder.create_tables()

        # Clear if requested
        if args.clear:
            seeder.clear_all_data()

        # Seed data
        strategy_ids = seeder.seed_strategies()
        backtest_ids = seeder.seed_backtests(strategy_ids)
        seeder.seed_trades(backtest_ids)

        print("\n" + "=" * 60)
        print("✓ Database seeding completed successfully!")
        print("=" * 60)
        print(f"\nDatabase: {args.database_url.split('@')[1] if '@' in args.database_url else 'local'}")
        print(f"Strategies: {len(strategy_ids)}")
        print(f"Backtests: {len(backtest_ids)}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()