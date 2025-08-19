from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import math


@dataclass
class CorporateTaxItem:
    """法人税項目の基本クラス"""
    name: str
    amount: int
    description: str
    related_form: str  # 関連別表


@dataclass
class AdditionItem(CorporateTaxItem):
    """加算項目（損金不算入／益金算入）"""
    pass


@dataclass
class DeductionItem(CorporateTaxItem):
    """減算項目（益金不算入／損金算入）"""
    pass


@dataclass
class TaxCreditItem(CorporateTaxItem):
    """税額控除項目"""
    pass


@dataclass
class EnhancedCorporateTaxResult:
    """拡張法人税計算結果"""
    # 基本情報
    accounting_profit: int  # 当期純利益（会計利益）
    taxable_income: int     # 課税所得金額
    
    # 調整項目
    addition_items: List[AdditionItem]    # 加算項目
    deduction_items: List[DeductionItem]  # 減算項目
    total_additions: int                  # 加算合計
    total_deductions: int                 # 減算合計
    
    # 税額計算
    corporate_tax_base: int      # 法人税額（控除前）
    local_corporate_tax: int     # 地方法人税
    national_tax_total: int      # 国税ベース確定法人税額
    
    # 税額控除
    tax_credit_items: List[TaxCreditItem]  # 税額控除項目
    total_tax_credits: int                 # 税額控除合計
    corporate_tax_after_credits: int       # 控除後法人税額
    
    # 中間納付・仮払税金
    interim_payments: int        # 中間納付法人税額
    prepaid_taxes: int          # 仮払税金
    final_corporate_tax: int    # 最終法人税納付額
    
    # 地方税
    resident_tax_equal: int     # 住民税均等割
    resident_tax_income: int    # 住民税法人税割
    business_tax: int           # 法人事業税
    special_business_tax: int   # 特別法人事業税
    local_tax_total: int        # 地方税合計
    
    # 最終結果
    total_tax_payment: int      # 総合納付税額
    effective_rate: float       # 実効税率
    
    # メタ情報
    tax_year: int
    prefecture: str
    capital: int
    company_type: str


class EnhancedCorporateTaxCalculator:
    """CompanyTax.mdの要件に基づく拡張法人税計算エンジン"""
    
    def __init__(self):
        self._corporate_tax_rates = self._get_corporate_tax_rates()
        self._business_tax_rates = self._get_business_tax_rates()
        self._local_corporate_tax_rates = self._get_local_corporate_tax_rates()
        self._resident_tax_rates = self._get_resident_tax_rates()
    
    def _get_corporate_tax_rates(self) -> Dict[int, Dict[str, float]]:
        """法人税率を取得"""
        return {
            2025: {
                "large_corporation": 0.232,  # 23.2% for large corporations
                "small_corporation": 0.15,   # 15% for small corporations (income ≤ 8M yen)
                "small_corporation_high": 0.232  # 23.2% for small corporations (income > 8M yen)
            },
            2024: {
                "large_corporation": 0.232,
                "small_corporation": 0.15,
                "small_corporation_high": 0.232
            },
            2023: {
                "large_corporation": 0.232,
                "small_corporation": 0.15,
                "small_corporation_high": 0.232
            }
        }
    
    def _get_business_tax_rates(self) -> Dict[str, List[Dict[str, Any]]]:
        """事業税率を取得"""
        return {
            "東京都": [
                {"min": 0, "max": 4000000, "rate": 0.037},      # 3.7%
                {"min": 4000001, "max": 8000000, "rate": 0.056}, # 5.6%
                {"min": 8000001, "max": None, "rate": 0.075}     # 7.5%
            ],
            "大阪府": [
                {"min": 0, "max": 4000000, "rate": 0.037},
                {"min": 4000001, "max": 8000000, "rate": 0.056},
                {"min": 8000001, "max": None, "rate": 0.075}
            ],
            "default": [
                {"min": 0, "max": 4000000, "rate": 0.037},
                {"min": 4000001, "max": 8000000, "rate": 0.056},
                {"min": 8000001, "max": None, "rate": 0.075}
            ]
        }
    
    def _get_local_corporate_tax_rates(self) -> Dict[int, float]:
        """地方法人税率を取得"""
        return {
            2025: 0.103,  # 10.3%
            2024: 0.103,
            2023: 0.103
        }
    
    def _get_resident_tax_rates(self) -> Dict[str, Dict[str, Any]]:
        """住民税率を取得"""
        return {
            "東京都": {
                "equal_rate": {  # 均等割
                    "capital_50m_below": 70000,    # 資本金5000万円以下
                    "capital_50m_1b": 180000,      # 資本金5000万円超～10億円以下
                    "capital_1b_above": 290000     # 資本金10億円超
                },
                "income_rate": 0.07  # 法人税割 7%
            },
            "default": {
                "equal_rate": {
                    "capital_50m_below": 70000,
                    "capital_50m_1b": 180000,
                    "capital_1b_above": 290000
                },
                "income_rate": 0.07
            }
        }
    
    def _get_default_addition_items(self, accounting_profit: int) -> List[AdditionItem]:
        """デフォルト加算項目を取得"""
        return [
            AdditionItem(
                name="寄附金損金不算入額",
                amount=int(accounting_profit * 0.001),  # 会計利益の0.1%をデフォルト
                description="限度額超過分",
                related_form="別表四・十四"
            ),
            AdditionItem(
                name="交際費損金不算入額",
                amount=int(accounting_profit * 0.002),  # 会計利益の0.2%をデフォルト
                description="限度超過分",
                related_form="別表四・十五"
            ),
            AdditionItem(
                name="過大役員給与",
                amount=0,  # デフォルト0
                description="定期同額給与・事前確定給与の要件外部分",
                related_form="別表四"
            ),
            AdditionItem(
                name="過大支払利息",
                amount=0,  # デフォルト0
                description="過大部分は損金不算入",
                related_form="別表四"
            ),
            AdditionItem(
                name="減価償却超過額",
                amount=int(accounting_profit * 0.005),  # 会計利益の0.5%をデフォルト
                description="会計＞税法償却額の場合",
                related_form="別表四・十六"
            ),
            AdditionItem(
                name="引当金繰入超過額",
                amount=0,  # デフォルト0
                description="会計計上が税法限度を超えた部分",
                related_form="別表四"
            ),
            AdditionItem(
                name="受取配当金益金算入額",
                amount=int(accounting_profit * 0.001),  # 会計利益の0.1%をデフォルト
                description="損益計算書に計上された全額",
                related_form="別表四・六"
            ),
            AdditionItem(
                name="留保金課税対象額",
                amount=0,  # デフォルト0（同族会社のみ適用）
                description="同族会社留保所得に対する加算課税",
                related_form="別表三"
            ),
            AdditionItem(
                name="法人税・住民税・事業税",
                amount=int(accounting_profit * 0.01),  # 会計利益の1%をデフォルト
                description="本税自体は損金不算入",
                related_form="別表五（二）"
            )
        ]
    
    def _get_default_deduction_items(self, accounting_profit: int) -> List[DeductionItem]:
        """デフォルト減算項目を取得"""
        return [
            DeductionItem(
                name="受取配当金益金不算入額",
                amount=int(accounting_profit * 0.001),  # 会計利益の0.1%をデフォルト
                description="法人間配当の益金不算入",
                related_form="別表四・六"
            ),
            DeductionItem(
                name="減価償却不足額",
                amount=0,  # デフォルト0
                description="会計＜税法償却額の場合",
                related_form="別表四・十六"
            ),
            DeductionItem(
                name="繰延資産償却不足額",
                amount=0,  # デフォルト0
                description="税法認容額との差額",
                related_form="別表四"
            ),
            DeductionItem(
                name="特別償却費",
                amount=0,  # デフォルト0
                description="特例償却",
                related_form="別表四・九・十六"
            ),
            DeductionItem(
                name="引当金・準備金繰入認容額",
                amount=0,  # デフォルト0
                description="税法上認められる部分",
                related_form="別表四"
            ),
            DeductionItem(
                name="繰越欠損金控除額",
                amount=0,  # デフォルト0（赤字がある場合のみ）
                description="青色申告法人の赤字控除",
                related_form="別表四・七"
            ),
            DeductionItem(
                name="災害損失金控除額",
                amount=0,  # デフォルト0
                description="災害損失の繰越控除",
                related_form="別表七"
            ),
            DeductionItem(
                name="グループ法人譲渡益繰延",
                amount=0,  # デフォルト0
                description="グループ内資産移転の益金繰延",
                related_form="別表二十"
            )
        ]
    
    def _get_default_tax_credit_items(self, corporate_tax_base: int) -> List[TaxCreditItem]:
        """デフォルト税額控除項目を取得"""
        return [
            TaxCreditItem(
                name="研究開発税制（試験研究費控除）",
                amount=int(corporate_tax_base * 0.02),  # 法人税額の2%をデフォルト
                description="研究開発費に応じた税額控除",
                related_form="別表十"
            ),
            TaxCreditItem(
                name="中小企業投資促進税制",
                amount=0,  # デフォルト0
                description="特定設備投資に伴う税額控除",
                related_form="別表九"
            ),
            TaxCreditItem(
                name="所得拡大促進税制",
                amount=0,  # デフォルト0
                description="給与総額増加に応じた控除",
                related_form="別表九"
            ),
            TaxCreditItem(
                name="外国税額控除",
                amount=0,  # デフォルト0
                description="国外で課税された税額を控除",
                related_form="別表八"
            ),
            TaxCreditItem(
                name="エネルギー環境投資促進税制",
                amount=0,  # デフォルト0
                description="環境関連設備投資の控除",
                related_form="別表九"
            ),
            TaxCreditItem(
                name="情報基盤強化税制",
                amount=0,  # デフォルト0
                description="IT投資に伴う控除",
                related_form="別表九"
            ),
            TaxCreditItem(
                name="中小企業者特別控除",
                amount=0,  # デフォルト0
                description="租税特別措置法に基づく控除",
                related_form="別表十一"
            )
        ]
    
    def _determine_company_type(self, capital: int) -> str:
        """会社区分を判定"""
        if capital > 100000000:  # 1億円超
            return "large_corporation"
        else:
            return "small_corporation"
    
    def _calculate_business_tax(self, taxable_income: int, prefecture: str) -> int:
        """事業税を計算"""
        brackets = self._business_tax_rates.get(prefecture, self._business_tax_rates["default"])
        
        business_tax = 0
        remaining_income = taxable_income
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
            
            bracket_max = bracket["max"] or float('inf')
            bracket_income = min(remaining_income, bracket_max - bracket["min"])
            
            if bracket_income > 0:
                business_tax += int(bracket_income * bracket["rate"])
                remaining_income -= bracket_income
        
        return business_tax
    
    def _calculate_resident_tax(self, corporate_tax: int, capital: int, prefecture: str) -> tuple[int, int]:
        """住民税を計算（均等割、法人税割）"""
        rates = self._resident_tax_rates.get(prefecture, self._resident_tax_rates["default"])
        
        # 均等割
        if capital <= 50000000:  # 5000万円以下
            equal_rate = rates["equal_rate"]["capital_50m_below"]
        elif capital <= 1000000000:  # 10億円以下
            equal_rate = rates["equal_rate"]["capital_50m_1b"]
        else:  # 10億円超
            equal_rate = rates["equal_rate"]["capital_1b_above"]
        
        # 法人税割
        income_rate = int(corporate_tax * rates["income_rate"])
        
        return equal_rate, income_rate
    
    def calculate_enhanced_corporate_tax(
        self,
        accounting_profit: int,
        tax_year: int = 2025,
        prefecture: str = "東京都",
        capital: int = 50000000,  # デフォルト5000万円
        addition_items: Optional[List[AdditionItem]] = None,
        deduction_items: Optional[List[DeductionItem]] = None,
        tax_credit_items: Optional[List[TaxCreditItem]] = None,
        interim_payments: int = 0,
        prepaid_taxes: int = 0
    ) -> EnhancedCorporateTaxResult:
        """CompanyTax.mdの要件に基づく拡張法人税計算"""
        
        # 入力検証
        if accounting_profit < 0:
            raise ValueError("会計利益は負の値にできません")
        
        if tax_year not in self._corporate_tax_rates:
            raise ValueError(f"税年度 {tax_year} はサポートされていません")
        
        # デフォルト項目を設定
        if addition_items is None:
            addition_items = self._get_default_addition_items(accounting_profit)
        
        if deduction_items is None:
            deduction_items = self._get_default_deduction_items(accounting_profit)
        
        # 1. 課税所得金額の算出
        total_additions = sum(item.amount for item in addition_items)
        total_deductions = sum(item.amount for item in deduction_items)
        taxable_income = max(0, accounting_profit + total_additions - total_deductions)
        
        # 2. 法人税額の計算
        company_type = self._determine_company_type(capital)
        
        if company_type == "small_corporation" and taxable_income <= 8000000:
            corporate_tax_base = int(taxable_income * 0.15)
        elif company_type == "small_corporation" and taxable_income > 8000000:
            corporate_tax_base = int(8000000 * 0.15 + (taxable_income - 8000000) * 0.232)
        else:
            corporate_tax_rate = self._corporate_tax_rates[tax_year]["large_corporation"]
            corporate_tax_base = int(taxable_income * corporate_tax_rate)
        
        # 3. 地方法人税
        local_corporate_tax_rate = self._local_corporate_tax_rates[tax_year]
        local_corporate_tax = int(corporate_tax_base * local_corporate_tax_rate)
        national_tax_total = corporate_tax_base + local_corporate_tax
        
        # 4. 税額控除の適用
        if tax_credit_items is None:
            tax_credit_items = self._get_default_tax_credit_items(corporate_tax_base)
        
        total_tax_credits = sum(item.amount for item in tax_credit_items)
        # 税額控除は法人税額を上限とする
        total_tax_credits = min(total_tax_credits, corporate_tax_base)
        corporate_tax_after_credits = corporate_tax_base - total_tax_credits
        
        # 5. 中間納付・仮払税金の控除
        final_corporate_tax = max(0, corporate_tax_after_credits - interim_payments - prepaid_taxes)
        
        # 6. 地方税の計算
        business_tax = self._calculate_business_tax(taxable_income, prefecture)
        special_business_tax = int(business_tax * 0.37)  # 特別法人事業税（事業税の37%）
        
        resident_tax_equal, resident_tax_income = self._calculate_resident_tax(
            corporate_tax_after_credits, capital, prefecture
        )
        
        local_tax_total = resident_tax_equal + resident_tax_income + business_tax + special_business_tax
        
        # 7. 総合納付税額
        total_tax_payment = final_corporate_tax + local_corporate_tax + local_tax_total
        
        # 実効税率
        effective_rate = (total_tax_payment / accounting_profit * 100) if accounting_profit > 0 else 0
        
        return EnhancedCorporateTaxResult(
            accounting_profit=accounting_profit,
            taxable_income=taxable_income,
            addition_items=addition_items,
            deduction_items=deduction_items,
            total_additions=total_additions,
            total_deductions=total_deductions,
            corporate_tax_base=corporate_tax_base,
            local_corporate_tax=local_corporate_tax,
            national_tax_total=national_tax_total,
            tax_credit_items=tax_credit_items,
            total_tax_credits=total_tax_credits,
            corporate_tax_after_credits=corporate_tax_after_credits,
            interim_payments=interim_payments,
            prepaid_taxes=prepaid_taxes,
            final_corporate_tax=final_corporate_tax,
            resident_tax_equal=resident_tax_equal,
            resident_tax_income=resident_tax_income,
            business_tax=business_tax,
            special_business_tax=special_business_tax,
            local_tax_total=local_tax_total,
            total_tax_payment=total_tax_payment,
            effective_rate=round(effective_rate, 2),
            tax_year=tax_year,
            prefecture=prefecture,
            capital=capital,
            company_type=company_type
        )


# グローバルインスタンス
enhanced_corporate_tax_calculator = EnhancedCorporateTaxCalculator()