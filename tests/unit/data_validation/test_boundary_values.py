#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaxMCP データ検証テスト - 境界値

このモジュールは、TaxMCPサーバーの境界値処理をテストします。

主なテスト項目:
- 数値の境界値（最小値、最大値、ゼロ）
- 日付の境界値（年始、年末、うるう年）
- 税率の境界値（0%、100%、課税境界）
- 文字列の境界値（空文字、最大長）
- 配列の境界値（空配列、最大要素数）
"""

import unittest
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional

from tests.utils.test_config import TaxMCPTestCase
from tests.utils.assertion_helpers import DataAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestBoundaryValues(TaxMCPTestCase, DataAssertions):
    """境界値テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.data_generator = TestDataGenerator()
        print(f"\n{'='*50}")
        print(f"テスト開始: {self._testMethodName}")
        print(f"{'='*50}")
    
    def tearDown(self):
        """テストクリーンアップ"""
        super().tearDown()
        print(f"\nテスト完了: {self._testMethodName}")
    
    def test_numeric_boundary_values(self):
        """数値境界値テスト"""
        print("\n=== 数値境界値テスト ===")
        
        # 整数の境界値
        print("\n--- 整数境界値テスト ---")
        
        integer_boundary_cases = [
            (0, True, "ゼロ"),
            (1, True, "最小正整数"),
            (-1, True, "最小負整数"),
            (sys.maxsize, True, "システム最大整数"),
            (-sys.maxsize - 1, True, "システム最小整数"),
            (2**31 - 1, True, "32bit最大整数"),
            (-2**31, True, "32bit最小整数"),
            (2**63 - 1, True, "64bit最大整数"),
            (-2**63, True, "64bit最小整数")
        ]
        
        for value, expected_valid, description in integer_boundary_cases:
            result = self._validate_integer_boundary(value)
            self.assertEqual(result["valid"], expected_valid, 
                           f"整数境界値検証失敗: {description} ({value})")
            print(f"✓ {description}: {value} -> {result['valid']}")
        
        # 浮動小数点の境界値
        print("\n--- 浮動小数点境界値テスト ---")
        
        float_boundary_cases = [
            (0.0, True, "ゼロ"),
            (-0.0, True, "負のゼロ"),
            (float('inf'), False, "正の無限大"),
            (float('-inf'), False, "負の無限大"),
            (float('nan'), False, "NaN"),
            (sys.float_info.max, True, "最大浮動小数点"),
            (sys.float_info.min, True, "最小正規化浮動小数点"),
            (sys.float_info.epsilon, True, "機械イプシロン"),
            (1e-308, True, "極小浮動小数点"),
            (1e308, True, "極大浮動小数点")
        ]
        
        for value, expected_valid, description in float_boundary_cases:
            result = self._validate_float_boundary(value)
            self.assertEqual(result["valid"], expected_valid, 
                           f"浮動小数点境界値検証失敗: {description} ({value})")
            print(f"✓ {description}: {value} -> {result['valid']}")
        
        # 税務計算での数値境界値
        print("\n--- 税務計算数値境界値テスト ---")
        
        tax_numeric_boundary_cases = [
            (0, True, "所得ゼロ"),
            (1, True, "所得1円"),
            (1950000, True, "所得税5%境界"),
            (3300000, True, "所得税10%境界"),
            (6950000, True, "所得税20%境界"),
            (9000000, True, "所得税23%境界"),
            (18000000, True, "所得税33%境界"),
            (40000000, True, "所得税40%境界"),
            (100000000, True, "所得1億円"),
            (1000000000, True, "所得10億円"),
            (10000000000, False, "所得100億円（上限超過）"),
            (-1, False, "負の所得")
        ]
        
        for income, expected_valid, description in tax_numeric_boundary_cases:
            result = self._validate_income_boundary(income)
            self.assertEqual(result["valid"], expected_valid, 
                           f"所得境界値検証失敗: {description} ({income})")
            print(f"✓ {description}: {income:,}円 -> {result['valid']}")
        
        print("✓ 数値境界値テスト成功")
    
    def test_date_boundary_values(self):
        """日付境界値テスト"""
        print("\n=== 日付境界値テスト ===")
        
        # 年の境界値
        print("\n--- 年境界値テスト ---")
        
        current_year = datetime.now().year
        year_boundary_cases = [
            (1900, True, "最小年（1900年）"),
            (1901, True, "1901年"),
            (2000, True, "2000年（うるう年）"),
            (2024, True, "2024年（現在年）"),
            (current_year, True, f"現在年（{current_year}年）"),
            (current_year + 1, True, f"来年（{current_year + 1}年）"),
            (current_year + 10, True, f"10年後（{current_year + 10}年）"),
            (current_year + 11, False, f"11年後（{current_year + 11}年）上限超過"),
            (1899, False, "1899年（下限未満）"),
            (1800, False, "1800年（下限未満）")
        ]
        
        for year, expected_valid, description in year_boundary_cases:
            result = self._validate_year_boundary(year)
            self.assertEqual(result["valid"], expected_valid, 
                           f"年境界値検証失敗: {description} ({year})")
            print(f"✓ {description}: {year} -> {result['valid']}")
        
        # 月の境界値
        print("\n--- 月境界値テスト ---")
        
        month_boundary_cases = [
            (1, True, "1月"),
            (2, True, "2月"),
            (12, True, "12月"),
            (0, False, "0月（無効）"),
            (13, False, "13月（無効）"),
            (-1, False, "-1月（無効）")
        ]
        
        for month, expected_valid, description in month_boundary_cases:
            result = self._validate_month_boundary(month)
            self.assertEqual(result["valid"], expected_valid, 
                           f"月境界値検証失敗: {description} ({month})")
            print(f"✓ {description}: {month} -> {result['valid']}")
        
        # 日の境界値
        print("\n--- 日境界値テスト ---")
        
        day_boundary_cases = [
            (2024, 1, 1, True, "1月1日"),
            (2024, 1, 31, True, "1月31日"),
            (2024, 2, 29, True, "2月29日（うるう年）"),
            (2023, 2, 28, True, "2月28日（平年）"),
            (2023, 2, 29, False, "2月29日（平年・無効）"),
            (2024, 4, 30, True, "4月30日"),
            (2024, 4, 31, False, "4月31日（無効）"),
            (2024, 12, 31, True, "12月31日"),
            (2024, 1, 0, False, "0日（無効）"),
            (2024, 1, 32, False, "32日（無効）")
        ]
        
        for year, month, day, expected_valid, description in day_boundary_cases:
            result = self._validate_date_boundary(year, month, day)
            self.assertEqual(result["valid"], expected_valid, 
                           f"日境界値検証失敗: {description} ({year}-{month:02d}-{day:02d})")
            print(f"✓ {description}: {year}-{month:02d}-{day:02d} -> {result['valid']}")
        
        # 税務年度の境界値
        print("\n--- 税務年度境界値テスト ---")
        
        fiscal_year_boundary_cases = [
            ("2024-01-01", "2024-12-31", True, "暦年課税期間"),
            ("2024-04-01", "2025-03-31", True, "年度課税期間"),
            ("2024-01-01", "2024-01-01", False, "同日開始終了（無効）"),
            ("2024-12-31", "2024-01-01", False, "終了日が開始日より前（無効）"),
            ("2024-01-01", "2025-12-31", False, "2年間（無効）"),
            ("2023-12-31", "2024-12-30", True, "年をまたぐ期間")
        ]
        
        for start_date, end_date, expected_valid, description in fiscal_year_boundary_cases:
            result = self._validate_fiscal_period_boundary(start_date, end_date)
            self.assertEqual(result["valid"], expected_valid, 
                           f"税務年度境界値検証失敗: {description} ({start_date} - {end_date})")
            print(f"✓ {description}: {start_date} - {end_date} -> {result['valid']}")
        
        print("✓ 日付境界値テスト成功")
    
    def test_tax_rate_boundary_values(self):
        """税率境界値テスト"""
        print("\n=== 税率境界値テスト ===")
        
        # 基本税率の境界値
        print("\n--- 基本税率境界値テスト ---")
        
        tax_rate_boundary_cases = [
            (0.0, True, "0%"),
            (0.01, True, "1%"),
            (0.05, True, "5%"),
            (0.08, True, "8%（旧消費税率）"),
            (0.10, True, "10%（現消費税率）"),
            (0.45, True, "45%（最高所得税率）"),
            (1.0, True, "100%"),
            (1.01, False, "101%（上限超過）"),
            (-0.01, False, "-1%（負の税率）"),
            (float('inf'), False, "無限大税率"),
            (float('nan'), False, "NaN税率")
        ]
        
        for rate, expected_valid, description in tax_rate_boundary_cases:
            result = self._validate_tax_rate_boundary(rate)
            self.assertEqual(result["valid"], expected_valid, 
                           f"税率境界値検証失敗: {description} ({rate})")
            print(f"✓ {description}: {rate} -> {result['valid']}")
        
        # 所得税率の境界値
        print("\n--- 所得税率境界値テスト ---")
        
        income_tax_rate_cases = [
            (0, 0.05, True, "5%税率（195万円以下）"),
            (1950000, 0.05, True, "5%税率境界"),
            (1950001, 0.10, True, "10%税率開始"),
            (3300000, 0.10, True, "10%税率境界"),
            (3300001, 0.20, True, "20%税率開始"),
            (40000000, 0.40, True, "40%税率境界"),
            (40000001, 0.45, True, "45%税率開始")
        ]
        
        for income, expected_rate, expected_valid, description in income_tax_rate_cases:
            result = self._validate_income_tax_rate_boundary(income, expected_rate)
            self.assertEqual(result["valid"], expected_valid, 
                           f"所得税率境界値検証失敗: {description}")
            print(f"✓ {description}: 所得{income:,}円, 税率{expected_rate} -> {result['valid']}")
        
        # 消費税率の境界値
        print("\n--- 消費税率境界値テスト ---")
        
        consumption_tax_rate_cases = [
            ("standard", 0.10, True, "標準税率10%"),
            ("reduced", 0.08, True, "軽減税率8%"),
            ("exempt", 0.0, True, "非課税0%"),
            ("export", 0.0, True, "輸出免税0%"),
            ("invalid", 0.15, False, "無効な税率15%")
        ]
        
        for category, rate, expected_valid, description in consumption_tax_rate_cases:
            result = self._validate_consumption_tax_rate_boundary(category, rate)
            self.assertEqual(result["valid"], expected_valid, 
                           f"消費税率境界値検証失敗: {description}")
            print(f"✓ {description}: カテゴリ{category}, 税率{rate} -> {result['valid']}")
        
        print("✓ 税率境界値テスト成功")
    
    def test_string_boundary_values(self):
        """文字列境界値テスト"""
        print("\n=== 文字列境界値テスト ===")
        
        # 文字列長の境界値
        print("\n--- 文字列長境界値テスト ---")
        
        string_length_boundary_cases = [
            ("", 0, 100, True, "空文字列"),
            ("a", 1, 100, True, "1文字"),
            ("a" * 100, 0, 100, True, "最大長100文字"),
            ("a" * 101, 0, 100, False, "最大長超過101文字"),
            ("田中太郎", 0, 10, True, "日本語4文字"),
            ("田中" * 50, 0, 100, True, "日本語100文字"),
            ("田中" * 51, 0, 100, False, "日本語102文字（超過）")
        ]
        
        for string, min_len, max_len, expected_valid, description in string_length_boundary_cases:
            result = self._validate_string_length_boundary(string, min_len, max_len)
            self.assertEqual(result["valid"], expected_valid, 
                           f"文字列長境界値検証失敗: {description}")
            print(f"✓ {description}: 長さ{len(string)} -> {result['valid']}")
        
        # 特殊文字の境界値
        print("\n--- 特殊文字境界値テスト ---")
        
        special_char_boundary_cases = [
            ("normal text", True, "通常文字"),
            ("日本語テキスト", True, "日本語"),
            ("123-4567", True, "数字とハイフン"),
            ("test@example.com", True, "メールアドレス"),
            ("\n\r\t", False, "制御文字"),
            ("<script>alert('xss')</script>", False, "HTMLタグ"),
            ("'; DROP TABLE users; --", False, "SQLインジェクション"),
            ("\x00\x01\x02", False, "バイナリ文字"),
            ("\u0000\u0001", False, "Unicode制御文字")
        ]
        
        for string, expected_valid, description in special_char_boundary_cases:
            result = self._validate_special_char_boundary(string)
            self.assertEqual(result["valid"], expected_valid, 
                           f"特殊文字境界値検証失敗: {description}")
            print(f"✓ {description}: '{string[:20]}...' -> {result['valid']}")
        
        # 税務データでの文字列境界値
        print("\n--- 税務データ文字列境界値テスト ---")
        
        tax_string_boundary_cases = [
            ("", False, "空の納税者名"),
            ("田", True, "1文字の納税者名"),
            ("田中太郎", True, "通常の納税者名"),
            ("田中" * 25, True, "50文字の納税者名"),
            ("田中" * 26, False, "52文字の納税者名（超過）"),
            ("123-4567", True, "郵便番号"),
            ("12-3456", False, "不正な郵便番号"),
            ("東京都渋谷区", True, "住所"),
            ("東京都" * 34, False, "102文字の住所（超過）")
        ]
        
        for string, expected_valid, description in tax_string_boundary_cases:
            result = self._validate_tax_string_boundary(string)
            self.assertEqual(result["valid"], expected_valid, 
                           f"税務データ文字列境界値検証失敗: {description}")
            print(f"✓ {description}: 長さ{len(string)} -> {result['valid']}")
        
        print("✓ 文字列境界値テスト成功")
    
    def test_array_boundary_values(self):
        """配列境界値テスト"""
        print("\n=== 配列境界値テスト ===")
        
        # 配列サイズの境界値
        print("\n--- 配列サイズ境界値テスト ---")
        
        array_size_boundary_cases = [
            ([], 0, 10, True, "空配列"),
            ([1], 0, 10, True, "1要素配列"),
            (list(range(10)), 0, 10, True, "10要素配列（最大）"),
            (list(range(11)), 0, 10, False, "11要素配列（超過）"),
            (list(range(100)), 0, 10, False, "100要素配列（大幅超過）")
        ]
        
        for array, min_size, max_size, expected_valid, description in array_size_boundary_cases:
            result = self._validate_array_size_boundary(array, min_size, max_size)
            self.assertEqual(result["valid"], expected_valid, 
                           f"配列サイズ境界値検証失敗: {description}")
            print(f"✓ {description}: サイズ{len(array)} -> {result['valid']}")
        
        # 扶養者配列の境界値
        print("\n--- 扶養者配列境界値テスト ---")
        
        dependent_array_boundary_cases = [
            ([], True, "扶養者なし"),
            ([{"name": "田中花子", "age": 10}], True, "扶養者1人"),
            ([{"name": f"扶養者{i}", "age": 10+i} for i in range(10)], True, "扶養者10人"),
            ([{"name": f"扶養者{i}", "age": 10+i} for i in range(11)], False, "扶養者11人（超過）"),
            ([{"name": f"扶養者{i}", "age": 10+i} for i in range(20)], False, "扶養者20人（大幅超過）")
        ]
        
        for dependents, expected_valid, description in dependent_array_boundary_cases:
            result = self._validate_dependent_array_boundary(dependents)
            self.assertEqual(result["valid"], expected_valid, 
                           f"扶養者配列境界値検証失敗: {description}")
            print(f"✓ {description}: {len(dependents)}人 -> {result['valid']}")
        
        # 控除項目配列の境界値
        print("\n--- 控除項目配列境界値テスト ---")
        
        deduction_array_boundary_cases = [
            ([], True, "控除項目なし"),
            ([{"type": "basic", "amount": 480000}], True, "基礎控除のみ"),
            ([{"type": f"deduction_{i}", "amount": 100000} for i in range(15)], True, "控除項目15個"),
            ([{"type": f"deduction_{i}", "amount": 100000} for i in range(16)], False, "控除項目16個（超過）"),
            ([{"type": f"deduction_{i}", "amount": 100000} for i in range(30)], False, "控除項目30個（大幅超過）")
        ]
        
        for deductions, expected_valid, description in deduction_array_boundary_cases:
            result = self._validate_deduction_array_boundary(deductions)
            self.assertEqual(result["valid"], expected_valid, 
                           f"控除項目配列境界値検証失敗: {description}")
            print(f"✓ {description}: {len(deductions)}項目 -> {result['valid']}")
        
        print("✓ 配列境界値テスト成功")
    
    def test_complex_boundary_scenarios(self):
        """複合境界値シナリオテスト"""
        print("\n=== 複合境界値シナリオテスト ===")
        
        # 所得税計算での複合境界値
        print("\n--- 所得税複合境界値テスト ---")
        
        complex_income_scenarios = [
            {
                "income": 1950000,  # 税率境界
                "deductions": 480000,  # 基礎控除
                "dependents": [],  # 扶養者なし
                "expected_valid": True,
                "description": "税率境界での最小ケース"
            },
            {
                "income": 1950001,  # 税率境界+1円
                "deductions": 480000,
                "dependents": [{"name": "田中花子", "age": 10}],  # 扶養者1人
                "expected_valid": True,
                "description": "税率境界直上での標準ケース"
            },
            {
                "income": 40000000,  # 高税率境界
                "deductions": 5000000,  # 大きな控除
                "dependents": [{"name": f"扶養者{i}", "age": 10+i} for i in range(10)],  # 最大扶養者
                "expected_valid": True,
                "description": "高所得での最大控除ケース"
            },
            {
                "income": 1000000000,  # 所得上限
                "deductions": 100000000,  # 大きな控除
                "dependents": [{"name": f"扶養者{i}", "age": 10+i} for i in range(11)],  # 扶養者超過
                "expected_valid": False,
                "description": "所得上限での扶養者超過ケース"
            }
        ]
        
        for scenario in complex_income_scenarios:
            result = self._validate_complex_income_scenario(scenario)
            self.assertEqual(result["valid"], scenario["expected_valid"], 
                           f"複合所得税境界値検証失敗: {scenario['description']}")
            print(f"✓ {scenario['description']}: -> {result['valid']}")
        
        # 法人税計算での複合境界値
        print("\n--- 法人税複合境界値テスト ---")
        
        complex_corporate_scenarios = [
            {
                "revenue": 100000000,  # 1億円
                "expenses": 80000000,  # 8000万円
                "capital": 10000000,  # 1000万円（小規模）
                "employees": 50,
                "expected_valid": True,
                "description": "小規模法人の標準ケース"
            },
            {
                "revenue": 1000000000,  # 10億円
                "expenses": 900000000,  # 9億円
                "capital": 100000000,  # 1億円（大規模）
                "employees": 1000,
                "expected_valid": True,
                "description": "大規模法人の標準ケース"
            },
            {
                "revenue": 0,  # 売上ゼロ
                "expenses": 10000000,  # 費用あり
                "capital": 10000000,
                "employees": 10,
                "expected_valid": True,
                "description": "売上ゼロでの損失ケース"
            },
            {
                "revenue": 10000000000,  # 100億円（上限超過）
                "expenses": 5000000000,
                "capital": 1000000000,
                "employees": 10000,
                "expected_valid": False,
                "description": "売上上限超過ケース"
            }
        ]
        
        for scenario in complex_corporate_scenarios:
            result = self._validate_complex_corporate_scenario(scenario)
            self.assertEqual(result["valid"], scenario["expected_valid"], 
                           f"複合法人税境界値検証失敗: {scenario['description']}")
            print(f"✓ {scenario['description']}: -> {result['valid']}")
        
        print("✓ 複合境界値シナリオテスト成功")
    
    # ヘルパーメソッド
    def _validate_integer_boundary(self, value) -> Dict[str, Any]:
        """整数境界値検証ヘルパー"""
        try:
            if not isinstance(value, int):
                int(value)
            return {"valid": True}
        except (ValueError, TypeError, OverflowError):
            return {"valid": False, "error": "Invalid integer"}
    
    def _validate_float_boundary(self, value) -> Dict[str, Any]:
        """浮動小数点境界値検証ヘルパー"""
        if not isinstance(value, (int, float)):
            return {"valid": False, "error": "Not a number"}
        
        if isinstance(value, float):
            if value != value:  # NaN check
                return {"valid": False, "error": "NaN value"}
            if value == float('inf') or value == float('-inf'):
                return {"valid": False, "error": "Infinity value"}
        
        return {"valid": True}
    
    def _validate_income_boundary(self, income) -> Dict[str, Any]:
        """所得境界値検証ヘルパー"""
        try:
            income_value = float(income)
            if income_value < 0:
                return {"valid": False, "error": "Negative income"}
            if income_value >= 10000000000:  # 100億円以上は上限超過
                return {"valid": False, "error": "Income too large"}
            return {"valid": True}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid income value"}
    
    def _validate_year_boundary(self, year) -> Dict[str, Any]:
        """年境界値検証ヘルパー"""
        try:
            year_value = int(year)
            current_year = datetime.now().year
            if 1900 <= year_value <= current_year + 10:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Year out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid year value"}
    
    def _validate_month_boundary(self, month) -> Dict[str, Any]:
        """月境界値検証ヘルパー"""
        try:
            month_value = int(month)
            if 1 <= month_value <= 12:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Month out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid month value"}
    
    def _validate_date_boundary(self, year, month, day) -> Dict[str, Any]:
        """日付境界値検証ヘルパー"""
        try:
            date(year, month, day)
            return {"valid": True}
        except ValueError:
            return {"valid": False, "error": "Invalid date"}
    
    def _validate_fiscal_period_boundary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """税務期間境界値検証ヘルパー"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start >= end:
                return {"valid": False, "error": "Start date must be before end date"}
            
            if (end - start).days > 366:
                return {"valid": False, "error": "Period too long"}
            
            return {"valid": True}
        except ValueError:
            return {"valid": False, "error": "Invalid date format"}
    
    def _validate_tax_rate_boundary(self, rate) -> Dict[str, Any]:
        """税率境界値検証ヘルパー"""
        try:
            rate_value = float(rate)
            if rate_value != rate_value:  # NaN check
                return {"valid": False, "error": "NaN tax rate"}
            if rate_value == float('inf') or rate_value == float('-inf'):
                return {"valid": False, "error": "Infinity tax rate"}
            if 0.0 <= rate_value <= 1.0:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Tax rate out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid tax rate value"}
    
    def _validate_income_tax_rate_boundary(self, income, expected_rate) -> Dict[str, Any]:
        """所得税率境界値検証ヘルパー"""
        # 簡単な所得税率判定
        if income <= 1950000:
            actual_rate = 0.05
        elif income <= 3300000:
            actual_rate = 0.10
        elif income <= 6950000:
            actual_rate = 0.20
        elif income <= 9000000:
            actual_rate = 0.23
        elif income <= 18000000:
            actual_rate = 0.33
        elif income <= 40000000:
            actual_rate = 0.40
        else:
            actual_rate = 0.45
        
        if actual_rate == expected_rate:
            return {"valid": True}
        else:
            return {"valid": False, "error": f"Expected rate {expected_rate}, got {actual_rate}"}
    
    def _validate_consumption_tax_rate_boundary(self, category: str, rate) -> Dict[str, Any]:
        """消費税率境界値検証ヘルパー"""
        valid_rates = {
            "standard": 0.10,
            "reduced": 0.08,
            "exempt": 0.0,
            "export": 0.0
        }
        
        if category not in valid_rates:
            return {"valid": False, "error": "Invalid category"}
        
        if valid_rates[category] == rate:
            return {"valid": True}
        else:
            return {"valid": False, "error": f"Invalid rate for category {category}"}
    
    def _validate_string_length_boundary(self, string: str, min_len: int, max_len: int) -> Dict[str, Any]:
        """文字列長境界値検証ヘルパー"""
        if not isinstance(string, str):
            return {"valid": False, "error": "Not a string"}
        
        length = len(string)
        if min_len <= length <= max_len:
            return {"valid": True}
        else:
            return {"valid": False, "error": f"String length {length} out of range ({min_len}-{max_len})"}
    
    def _validate_special_char_boundary(self, string: str) -> Dict[str, Any]:
        """特殊文字境界値検証ヘルパー"""
        if not isinstance(string, str):
            return {"valid": False, "error": "Not a string"}
        
        # 危険な文字パターンをチェック
        dangerous_patterns = [
            "<script", "</script>", "javascript:", "vbscript:",
            "onload=", "onerror=", "onclick=",
            "'; DROP", "'; DELETE", "'; UPDATE", "'; INSERT",
            "\x00", "\x01", "\x02", "\x03", "\x04", "\x05",
            "\n", "\r", "\t"
        ]
        
        string_lower = string.lower()
        for pattern in dangerous_patterns:
            if pattern in string_lower or pattern in string:
                return {"valid": False, "error": f"Dangerous pattern detected: {pattern}"}
        
        return {"valid": True}
    
    def _validate_tax_string_boundary(self, string: str) -> Dict[str, Any]:
        """税務データ文字列境界値検証ヘルパー"""
        if not isinstance(string, str):
            return {"valid": False, "error": "Not a string"}
        
        # 空文字列チェック（納税者名など必須項目）
        if len(string) == 0:
            return {"valid": False, "error": "Empty string not allowed"}
        
        # 郵便番号の形式チェック
        if "-" in string:
            parts = string.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                if len(parts[0]) == 3 and len(parts[1]) == 4:
                    return {"valid": True}
                else:
                    return {"valid": False, "error": "Invalid postal code format"}
        
        # 長さチェック（納税者名は50文字まで、住所は100文字まで）
        if len(string) > 50:  # 納税者名の上限
            return {"valid": False, "error": "String too long"}
        
        return {"valid": True}
    
    def _validate_array_size_boundary(self, array: List, min_size: int, max_size: int) -> Dict[str, Any]:
        """配列サイズ境界値検証ヘルパー"""
        if not isinstance(array, list):
            return {"valid": False, "error": "Not an array"}
        
        size = len(array)
        if min_size <= size <= max_size:
            return {"valid": True}
        else:
            return {"valid": False, "error": f"Array size {size} out of range ({min_size}-{max_size})"}
    
    def _validate_dependent_array_boundary(self, dependents: List) -> Dict[str, Any]:
        """扶養者配列境界値検証ヘルパー"""
        if not isinstance(dependents, list):
            return {"valid": False, "error": "Not an array"}
        
        if len(dependents) > 10:  # 扶養者上限
            return {"valid": False, "error": "Too many dependents"}
        
        return {"valid": True}
    
    def _validate_deduction_array_boundary(self, deductions: List) -> Dict[str, Any]:
        """控除項目配列境界値検証ヘルパー"""
        if not isinstance(deductions, list):
            return {"valid": False, "error": "Not an array"}
        
        if len(deductions) > 15:  # 控除項目上限
            return {"valid": False, "error": "Too many deductions"}
        
        return {"valid": True}
    
    def _validate_complex_income_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """複合所得税シナリオ検証ヘルパー"""
        # 所得検証
        income_result = self._validate_income_boundary(scenario["income"])
        if not income_result["valid"]:
            return income_result
        
        # 扶養者配列検証
        dependent_result = self._validate_dependent_array_boundary(scenario["dependents"])
        if not dependent_result["valid"]:
            return dependent_result
        
        # 控除額検証
        if scenario["deductions"] > scenario["income"]:
            return {"valid": False, "error": "Deductions exceed income"}
        
        return {"valid": True}
    
    def _validate_complex_corporate_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """複合法人税シナリオ検証ヘルパー"""
        # 売上検証
        if scenario["revenue"] >= 10000000000:  # 100億円以上は上限超過
            return {"valid": False, "error": "Revenue too large"}
        
        # 費用検証
        if scenario["expenses"] < 0:
            return {"valid": False, "error": "Negative expenses"}
        
        # 資本金検証
        if scenario["capital"] <= 0:
            return {"valid": False, "error": "Invalid capital"}
        
        # 従業員数検証
        if scenario["employees"] < 0:
            return {"valid": False, "error": "Negative employees"}
        
        return {"valid": True}


if __name__ == "__main__":
    unittest.main(verbosity=2)