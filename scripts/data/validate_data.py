#!/usr/bin/env python3
"""
Validate Data Script - Nexus Engine
Implementei este script para validar qualidade dos dados de mercado.
Decidi incluir verificações de missing data, outliers e inconsistências.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "python" / "src"))


class DataValidator:
    """
    Implementei esta classe para validar qualidade de dados de mercado.
    Decidi usar pandas para análise e incluir múltiplos tipos de validação.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues = []

    def validate_file(self, file_path: Path) -> Dict:
        """
        Valido um arquivo CSV de dados de mercado.

        Aprendi que validações sequenciais facilitam identificar problemas.
        """
        print(f"\n📊 Validating: {file_path.name}")

        try:
            # Load data
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)

            if self.verbose:
                print(f"   Shape: {df.shape}")
                print(f"   Columns: {list(df.columns)}")

            results = {
                "file": file_path.name,
                "rows": len(df),
                "columns": len(df.columns),
                "issues": [],
                "warnings": [],
                "valid": True
            }

            # Run validations
            results["issues"].extend(self._check_missing_data(df))
            results["issues"].extend(self._check_duplicates(df))
            results["issues"].extend(self._check_outliers(df))
            results["issues"].extend(self._check_data_gaps(df))
            results["warnings"].extend(self._check_low_volume(df))

            if results["issues"]:
                results["valid"] = False

            return results

        except Exception as e:
            return {
                "file": file_path.name,
                "rows": 0,
                "columns": 0,
                "issues": [f"Failed to read file: {e}"],
                "warnings": [],
                "valid": False
            }

    def _check_missing_data(self, df: pd.DataFrame) -> List[str]:
        """Verifico dados faltantes."""
        issues = []

        missing = df.isnull().sum()
        if missing.any():
            for col, count in missing[missing > 0].items():
                pct = (count / len(df)) * 100
                issues.append(f"Missing data in {col}: {count} ({pct:.1f}%)")

        return issues

    def _check_duplicates(self, df: pd.DataFrame) -> List[str]:
        """Verifico índices duplicados (datas duplicadas)."""
        issues = []

        duplicates = df.index.duplicated()
        if duplicates.any():
            count = duplicates.sum()
            issues.append(f"Duplicate timestamps: {count}")

        return issues

    def _check_outliers(self, df: pd.DataFrame) -> List[str]:
        """
        Verifico outliers usando IQR method.

        Decidi usar 3*IQR como threshold para evitar false positives.
        """
        issues = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            # Outliers são valores fora de [Q1 - 3*IQR, Q3 + 3*IQR]
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR

            outliers = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()

            if outliers > 0:
                pct = (outliers / len(df)) * 100
                if pct > 1:  # Report only if > 1%
                    issues.append(f"Outliers in {col}: {outliers} ({pct:.1f}%)")

        return issues

    def _check_data_gaps(self, df: pd.DataFrame) -> List[str]:
        """
        Verifico gaps no tempo (missing days).

        Aprendi que market data tem gaps naturais (weekends, holidays).
        """
        issues = []

        if not isinstance(df.index, pd.DatetimeIndex):
            return issues

        # Calculate expected trading days (approx 252 per year)
        date_range = (df.index.max() - df.index.min()).days
        expected_days = date_range * (252 / 365)  # Approximate trading days

        actual_days = len(df)
        gap_pct = ((expected_days - actual_days) / expected_days) * 100

        # Report if more than 10% gaps (beyond normal weekends/holidays)
        if gap_pct > 10:
            issues.append(f"Significant data gaps: {gap_pct:.1f}% missing")

        return issues

    def _check_low_volume(self, df: pd.DataFrame) -> List[str]:
        """Verifico dias com volume muito baixo."""
        warnings = []

        if "volume" in df.columns or "Volume" in df.columns:
            vol_col = "volume" if "volume" in df.columns else "Volume"

            # Find days with volume = 0 or very low
            zero_volume = (df[vol_col] == 0).sum()
            if zero_volume > 0:
                pct = (zero_volume / len(df)) * 100
                warnings.append(f"Zero volume days: {zero_volume} ({pct:.1f}%)")

            # Very low volume (bottom 5%)
            low_threshold = df[vol_col].quantile(0.05)
            low_volume = (df[vol_col] < low_threshold).sum()
            if low_volume > len(df) * 0.1:  # More than 10%
                warnings.append(f"Low volume days: {low_volume}")

        return warnings

    def print_report(self, results: List[Dict]) -> None:
        """Imprimo relatório consolidado."""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)

        total_files = len(results)
        valid_files = sum(1 for r in results if r["valid"])
        invalid_files = total_files - valid_files

        print(f"\nTotal files: {total_files}")
        print(f"Valid: {valid_files} ✓")
        print(f"Invalid: {invalid_files} ✗")

        # Print issues by file
        for result in results:
            if not result["valid"]:
                print(f"\n❌ {result['file']}")
                for issue in result["issues"]:
                    print(f"   • {issue}")

        # Print warnings
        warnings_count = sum(len(r["warnings"]) for r in results)
        if warnings_count > 0:
            print(f"\n⚠️  Total warnings: {warnings_count}")
            for result in results:
                if result["warnings"]:
                    print(f"\n{result['file']}:")
                    for warning in result["warnings"]:
                        print(f"   • {warning}")

        print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Validate market data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate all CSV files in directory
  python validate_data.py --dir data/market/historical

  # Validate specific files
  python validate_data.py --files AAPL_daily.csv GOOGL_daily.csv

  # Verbose output
  python validate_data.py --dir data/market/historical --verbose
        """
    )

    parser.add_argument(
        "--dir",
        "--directory",
        dest="directory",
        type=Path,
        help="Directory containing CSV files to validate"
    )

    parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        help="Specific files to validate"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Determine files to validate
    files_to_validate = []

    if args.directory:
        if not args.directory.exists():
            print(f"❌ Directory not found: {args.directory}")
            sys.exit(1)

        files_to_validate = list(args.directory.glob("*.csv"))
        if not files_to_validate:
            print(f"⚠️  No CSV files found in: {args.directory}")
            sys.exit(0)

    elif args.files:
        for file_path in args.files:
            if not file_path.exists():
                print(f"⚠️  File not found: {file_path}")
            else:
                files_to_validate.append(file_path)

    else:
        parser.error("Either --dir or --files must be specified")

    if not files_to_validate:
        print("❌ No files to validate")
        sys.exit(1)

    print("=" * 70)
    print("Nexus Engine - Data Validator")
    print("=" * 70)
    print(f"Files to validate: {len(files_to_validate)}")

    # Validate files
    validator = DataValidator(verbose=args.verbose)
    results = []

    for file_path in files_to_validate:
        result = validator.validate_file(file_path)
        results.append(result)

        # Print status
        status = "✓" if result["valid"] else "✗"
        print(f"{status} {file_path.name}: {result['rows']} rows")

    # Print report
    validator.print_report(results)

    # Exit code
    invalid_count = sum(1 for r in results if not r["valid"])
    sys.exit(1 if invalid_count > 0 else 0)


if __name__ == "__main__":
    main()