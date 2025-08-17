"""Japanese tax calculation logic for the MCP server."""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class TaxYear(Enum):
    """Supported tax years."""
    Y2020 = 2020
    Y2021 = 2021
    Y2022 = 2022
    Y2023 = 2023
    Y2024 = 2024
    Y2025 = 2025


class Prefecture(Enum):
    """Japanese prefectures for local tax calculation."""
    TOKYO = "東京都"
    OSAKA = "大阪府"
    KANAGAWA = "神奈川県"
    AICHI = "愛知県"
    SAITAMA = "埼玉県"
    CHIBA = "千葉県"
    HYOGO = "兵庫県"
    HOKKAIDO = "北海道"
    FUKUOKA = "福岡県"
    SHIZUOKA = "静岡県"
    # Add more prefectures as needed


@dataclass
class TaxBracket:
    """Income tax bracket definition."""
    min_income: int
    max_income: Optional[int]
    rate: float
    deduction: int


@dataclass
class TaxCalculationResult:
    """Result of tax calculation."""
    gross_income: int
    taxable_income: int
    income_tax: int
    resident_tax: int
    total_tax: int
    effective_rate: float
    marginal_rate: float
    deductions_applied: Dict[str, int]
    tax_year: int
    prefecture: str


class JapaneseTaxCalculator:
    """Japanese tax calculation engine."""
    
    def __init__(self):
        self._income_tax_brackets = self._get_income_tax_brackets()
        self._consumption_tax_rates = self._get_consumption_tax_rates()
        self._resident_tax_rates = self._get_resident_tax_rates()
    
    def _get_income_tax_brackets(self) -> Dict[int, List[TaxBracket]]:
        """Get income tax brackets by year."""
        return {
            2025: [
                TaxBracket(0, 1950000, 0.05, 0),
                TaxBracket(1950001, 3300000, 0.10, 97500),
                TaxBracket(3300001, 6950000, 0.20, 427500),
                TaxBracket(6950001, 9000000, 0.23, 636000),
                TaxBracket(9000001, 18000000, 0.33, 1536000),
                TaxBracket(18000001, 40000000, 0.40, 2796000),
                TaxBracket(40000001, None, 0.45, 4796000),
            ],
            2024: [
                TaxBracket(0, 1950000, 0.05, 0),
                TaxBracket(1950001, 3300000, 0.10, 97500),
                TaxBracket(3300001, 6950000, 0.20, 427500),
                TaxBracket(6950001, 9000000, 0.23, 636000),
                TaxBracket(9000001, 18000000, 0.33, 1536000),
                TaxBracket(18000001, 40000000, 0.40, 2796000),
                TaxBracket(40000001, None, 0.45, 4796000),
            ],
            2023: [
                TaxBracket(0, 1950000, 0.05, 0),
                TaxBracket(1950001, 3300000, 0.10, 97500),
                TaxBracket(3300001, 6950000, 0.20, 427500),
                TaxBracket(6950001, 9000000, 0.23, 636000),
                TaxBracket(9000001, 18000000, 0.33, 1536000),
                TaxBracket(18000001, 40000000, 0.40, 2796000),
                TaxBracket(40000001, None, 0.45, 4796000),
            ],
            # Add more years as needed
        }
    
    def _get_consumption_tax_rates(self) -> Dict[str, Dict[str, float]]:
        """Get consumption tax rates by date and category."""
        return {
            "2019-10-01": {"standard": 0.10, "reduced": 0.08},
            "2014-04-01": {"standard": 0.08, "reduced": 0.08},
            "1997-04-01": {"standard": 0.05, "reduced": 0.05},
        }
    
    def _get_resident_tax_rates(self) -> Dict[str, Dict[str, float]]:
        """Get resident tax rates by prefecture."""
        return {
            "東京都": {"prefectural": 0.04, "municipal": 0.06},
            "大阪府": {"prefectural": 0.04, "municipal": 0.06},
            "神奈川県": {"prefectural": 0.04, "municipal": 0.06},
            "愛知県": {"prefectural": 0.04, "municipal": 0.06},
            # Add more prefectures with their specific rates
        }
    
    def calculate_income_tax(
        self,
        annual_income: int,
        tax_year: int = 2025,
        basic_deduction: int = 480000,
        employment_income_deduction: Optional[int] = None,
        dependents_count: int = 0,
        spouse_deduction: int = 0,
        social_insurance_deduction: int = 0,
        life_insurance_deduction: int = 0,
        earthquake_insurance_deduction: int = 0,
        medical_expense_deduction: int = 0,
        donation_deduction: int = 0,
    ) -> Dict[str, any]:
        """Calculate Japanese income tax."""
        
        # Calculate employment income deduction if not provided
        if employment_income_deduction is None:
            employment_income_deduction = self._calculate_employment_income_deduction(annual_income)
        
        # Calculate dependent deduction
        dependent_deduction = dependents_count * 380000  # Basic dependent deduction
        
        # Total deductions
        total_deductions = (
            basic_deduction +
            employment_income_deduction +
            dependent_deduction +
            spouse_deduction +
            social_insurance_deduction +
            life_insurance_deduction +
            earthquake_insurance_deduction +
            medical_expense_deduction +
            donation_deduction
        )
        
        # Calculate taxable income
        taxable_income = max(0, annual_income - total_deductions)
        
        # Calculate income tax
        income_tax = self._calculate_progressive_tax(taxable_income, tax_year)
        
        # Calculate effective and marginal rates
        effective_rate = (income_tax / annual_income * 100) if annual_income > 0 else 0
        marginal_rate = self._get_marginal_rate(taxable_income, tax_year)
        
        deductions_applied = {
            "basic_deduction": basic_deduction,
            "employment_income_deduction": employment_income_deduction,
            "dependent_deduction": dependent_deduction,
            "spouse_deduction": spouse_deduction,
            "social_insurance_deduction": social_insurance_deduction,
            "life_insurance_deduction": life_insurance_deduction,
            "earthquake_insurance_deduction": earthquake_insurance_deduction,
            "medical_expense_deduction": medical_expense_deduction,
            "donation_deduction": donation_deduction,
            "total_deductions": total_deductions,
        }
        
        return {
            "annual_income": annual_income,
            "taxable_income": taxable_income,
            "income_tax": income_tax,
            "effective_rate": round(effective_rate, 2),
            "marginal_rate": round(marginal_rate * 100, 2),
            "deductions_applied": deductions_applied,
            "tax_year": tax_year,
        }
    
    def _calculate_employment_income_deduction(self, annual_income: int) -> int:
        """Calculate employment income deduction based on annual income."""
        if annual_income <= 1625000:
            return 550000
        elif annual_income <= 1800000:
            return int(annual_income * 0.4 - 100000)
        elif annual_income <= 3600000:
            return int(annual_income * 0.3 + 80000)
        elif annual_income <= 6600000:
            return int(annual_income * 0.2 + 440000)
        elif annual_income <= 8500000:
            return int(annual_income * 0.1 + 1100000)
        else:
            return 1950000
    
    def _calculate_progressive_tax(self, taxable_income: int, tax_year: int) -> int:
        """Calculate progressive income tax."""
        if tax_year not in self._income_tax_brackets:
            raise ValueError(f"Tax year {tax_year} is not supported")
        
        brackets = self._income_tax_brackets[tax_year]
        
        for bracket in brackets:
            if bracket.max_income is None or taxable_income <= bracket.max_income:
                return int(taxable_income * bracket.rate - bracket.deduction)
        
        return 0
    
    def _get_marginal_rate(self, taxable_income: int, tax_year: int) -> float:
        """Get marginal tax rate for given income."""
        if tax_year not in self._income_tax_brackets:
            return 0.0
        
        brackets = self._income_tax_brackets[tax_year]
        
        for bracket in brackets:
            if bracket.max_income is None or taxable_income <= bracket.max_income:
                return bracket.rate
        
        return 0.0
    
    def get_consumption_tax_rate(self, date_str: str, category: str = "standard") -> Dict[str, any]:
        """Get consumption tax rate for a specific date and category."""
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Find the applicable rate by looking for the most recent rate change
        applicable_rate = None
        applicable_date = None
        
        for rate_date_str, rates in self._consumption_tax_rates.items():
            rate_date = datetime.strptime(rate_date_str, "%Y-%m-%d").date()
            if rate_date <= target_date:
                if applicable_date is None or rate_date > applicable_date:
                    applicable_date = rate_date
                    applicable_rate = rates.get(category, rates["standard"])
        
        if applicable_rate is None:
            applicable_rate = 0.05  # Default to 5% if no rate found
            applicable_date = date(1997, 4, 1)
        
        return {
            "consumption_tax_rate": applicable_rate,
            "category": category,
            "applicable_date": applicable_date.strftime("%Y-%m-%d"),
            "target_date": date_str,
        }
    
    def calculate_resident_tax(
        self,
        taxable_income: int,
        prefecture: str = "東京都",
        tax_year: int = 2025,
    ) -> Dict[str, any]:
        """Calculate resident tax (住民税)."""
        
        # Standard resident tax rates
        prefectural_rate = 0.04  # 4%
        municipal_rate = 0.06    # 6%
        
        # Get prefecture-specific rates if available
        if prefecture in self._resident_tax_rates:
            rates = self._resident_tax_rates[prefecture]
            prefectural_rate = rates["prefectural"]
            municipal_rate = rates["municipal"]
        
        # Calculate income-based resident tax
        prefectural_tax = int(taxable_income * prefectural_rate)
        municipal_tax = int(taxable_income * municipal_rate)
        
        # Add per-capita levy (均等割)
        prefectural_per_capita = 1500  # Standard amount
        municipal_per_capita = 3500    # Standard amount
        
        total_prefectural = prefectural_tax + prefectural_per_capita
        total_municipal = municipal_tax + municipal_per_capita
        total_resident_tax = total_prefectural + total_municipal
        
        return {
            "taxable_income": taxable_income,
            "prefecture": prefecture,
            "prefectural_tax": {
                "income_based": prefectural_tax,
                "per_capita": prefectural_per_capita,
                "total": total_prefectural,
            },
            "municipal_tax": {
                "income_based": municipal_tax,
                "per_capita": municipal_per_capita,
                "total": total_municipal,
            },
            "total_resident_tax": total_resident_tax,
            "tax_year": tax_year,
        }
    
    def simulate_multi_year_taxes(
        self,
        annual_incomes: List[int],
        start_year: int = 2025,
        prefecture: str = "東京都",
        dependents_count: int = 0,
        spouse_deduction: int = 0,
    ) -> List[Dict[str, any]]:
        """Simulate taxes for multiple years."""
        results = []
        
        for i, income in enumerate(annual_incomes):
            year = start_year + i
            
            # Calculate income tax
            income_tax_result = self.calculate_income_tax(
                annual_income=income,
                tax_year=year,
                dependents_count=dependents_count,
                spouse_deduction=spouse_deduction,
            )
            
            # Calculate resident tax
            resident_tax_result = self.calculate_resident_tax(
                taxable_income=income_tax_result["taxable_income"],
                prefecture=prefecture,
                tax_year=year,
            )
            
            # Combine results
            combined_result = {
                "year": year,
                "annual_income": income,
                "taxable_income": income_tax_result["taxable_income"],
                "income_tax": income_tax_result["income_tax"],
                "resident_tax": resident_tax_result["total_resident_tax"],
                "total_tax": income_tax_result["income_tax"] + resident_tax_result["total_resident_tax"],
                "effective_rate": income_tax_result["effective_rate"],
                "deductions_applied": income_tax_result["deductions_applied"],
                "prefecture": prefecture,
            }
            
            results.append(combined_result)
        
        return results


@dataclass
class CorporateTaxBracket:
    """Corporate tax bracket definition."""
    min_income: int
    max_income: Optional[int]
    rate: float


@dataclass
class CorporateTaxCalculationResult:
    """Result of corporate tax calculation."""
    gross_income: int
    taxable_income: int
    corporate_tax: int
    local_corporate_tax: int
    business_tax: int
    total_tax: int
    effective_rate: float
    tax_year: int
    prefecture: str
    company_type: str


class JapaneseCorporateTaxCalculator:
    """Japanese corporate tax calculation engine."""
    
    def __init__(self):
        self._corporate_tax_rates = self._get_corporate_tax_rates()
        self._business_tax_rates = self._get_business_tax_rates()
        self._local_corporate_tax_rates = self._get_local_corporate_tax_rates()
    
    def _get_corporate_tax_rates(self) -> Dict[int, Dict[str, float]]:
        """Get corporate tax rates by year and company type."""
        return {
            2025: {
                "large_corporation": 0.234,  # 23.4% for large corporations
                "small_corporation": 0.15,   # 15% for small corporations (income ≤ 8M yen)
                "small_corporation_high": 0.234  # 23.4% for small corporations (income > 8M yen)
            },
            2024: {
                "large_corporation": 0.234,
                "small_corporation": 0.15,
                "small_corporation_high": 0.234
            },
            2023: {
                "large_corporation": 0.234,
                "small_corporation": 0.15,
                "small_corporation_high": 0.234
            }
        }
    
    def _get_business_tax_rates(self) -> Dict[str, List[CorporateTaxBracket]]:
        """Get business tax rates by prefecture."""
        # Standard business tax rates (varies by prefecture, using Tokyo as example)
        return {
            "東京都": [
                CorporateTaxBracket(0, 4000000, 0.037),      # 3.7% for income ≤ 4M yen
                CorporateTaxBracket(4000001, 8000000, 0.056), # 5.6% for income 4M-8M yen
                CorporateTaxBracket(8000001, None, 0.075)     # 7.5% for income > 8M yen
            ],
            "大阪府": [
                CorporateTaxBracket(0, 4000000, 0.037),
                CorporateTaxBracket(4000001, 8000000, 0.056),
                CorporateTaxBracket(8000001, None, 0.075)
            ],
            # Add more prefectures with their specific rates
            "default": [
                CorporateTaxBracket(0, 4000000, 0.037),
                CorporateTaxBracket(4000001, 8000000, 0.056),
                CorporateTaxBracket(8000001, None, 0.075)
            ]
        }
    
    def _get_local_corporate_tax_rates(self) -> Dict[int, float]:
        """Get local corporate tax rates by year."""
        return {
            2025: 0.104,  # 10.4% of corporate tax
            2024: 0.104,
            2023: 0.104
        }
    
    def _determine_company_type(self, annual_income: int, capital: int = 100000000) -> str:
        """Determine company type based on capital and income."""
        # Large corporation: capital > 100M yen
        if capital > 100000000:
            return "large_corporation"
        # Small corporation with different rates based on income
        elif annual_income <= 8000000:
            return "small_corporation"
        else:
            return "small_corporation_high"
    
    def calculate_corporate_tax(
        self,
        annual_income: int,
        tax_year: int = 2025,
        prefecture: str = "東京都",
        capital: int = 100000000,
        deductions: int = 0
    ) -> Dict[str, any]:
        """Calculate corporate tax for a given income."""
        
        # Input validation
        if annual_income < 0:
            raise ValueError("Annual income cannot be negative")
        
        if tax_year not in self._corporate_tax_rates:
            raise ValueError(f"Tax year {tax_year} not supported")
        
        # Calculate taxable income
        taxable_income = max(0, annual_income - deductions)
        
        # Determine company type
        company_type = self._determine_company_type(annual_income, capital)
        
        # Calculate corporate tax
        corporate_tax_rate = self._corporate_tax_rates[tax_year][company_type]
        
        if company_type == "small_corporation":
            # Small corporation: 15% for income ≤ 8M yen, 23.4% for excess
            if taxable_income <= 8000000:
                corporate_tax = int(taxable_income * 0.15)
            else:
                corporate_tax = int(8000000 * 0.15 + (taxable_income - 8000000) * 0.234)
        else:
            corporate_tax = int(taxable_income * corporate_tax_rate)
        
        # Calculate local corporate tax (10.4% of corporate tax)
        local_corporate_tax_rate = self._local_corporate_tax_rates[tax_year]
        local_corporate_tax = int(corporate_tax * local_corporate_tax_rate)
        
        # Calculate business tax
        business_tax = self._calculate_business_tax(taxable_income, prefecture)
        
        # Calculate total tax
        total_tax = corporate_tax + local_corporate_tax + business_tax
        
        # Calculate effective rate
        effective_rate = (total_tax / annual_income * 100) if annual_income > 0 else 0
        
        return {
            "gross_income": annual_income,
            "taxable_income": taxable_income,
            "corporate_tax": corporate_tax,
            "local_corporate_tax": local_corporate_tax,
            "business_tax": business_tax,
            "total_tax": total_tax,
            "effective_rate": round(effective_rate, 2),
            "tax_year": tax_year,
            "prefecture": prefecture,
            "company_type": company_type,
            "deductions_applied": {"total_deductions": deductions}
        }
    
    def _calculate_business_tax(self, taxable_income: int, prefecture: str) -> int:
        """Calculate business tax based on income brackets."""
        brackets = self._business_tax_rates.get(prefecture, self._business_tax_rates["default"])
        
        business_tax = 0
        remaining_income = taxable_income
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
            
            bracket_max = bracket.max_income or float('inf')
            bracket_income = min(remaining_income, bracket_max - bracket.min_income)
            
            if bracket_income > 0:
                business_tax += int(bracket_income * bracket.rate)
                remaining_income -= bracket_income
        
        return business_tax
    
    def simulate_multi_year_corporate_taxes(
        self,
        annual_incomes: List[int],
        start_year: int = 2025,
        prefecture: str = "東京都",
        capital: int = 100000000,
        deductions: int = 0
    ) -> List[Dict[str, any]]:
        """Simulate corporate taxes for multiple years."""
        results = []
        
        for i, income in enumerate(annual_incomes):
            year = start_year + i
            
            # Calculate corporate tax
            tax_result = self.calculate_corporate_tax(
                annual_income=income,
                tax_year=year,
                prefecture=prefecture,
                capital=capital,
                deductions=deductions
            )
            
            results.append(tax_result)
        
        return results


# Global calculator instances
tax_calculator = JapaneseTaxCalculator()
corporate_tax_calculator = JapaneseCorporateTaxCalculator()