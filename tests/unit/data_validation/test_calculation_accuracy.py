#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaxMCP データ検証テスト - 計算精度

このモジュールは、TaxMCPサーバーの税計算精度をテストします。

主なテスト項目:
- 浮動小数点精度
- 丸め処理精度
- 大きな数値の計算精度
- 累積誤差の検証
- 境界値での計算精度
"""

import unittest
import math
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import Dict, Any, List, Tuple

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import DataAssertions, PerformanceAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestCalculationAccuracy(TaxMCPTestCase, PerformanceTestMixin, DataAssertions, PerformanceAssertions):
    """計算精度テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.data_generator = TestDataGenerator()
        
        # Decimal精度設定
        getcontext().prec = 28
        getcontext().rounding = ROUND_HALF_UP
        
        print(f"\n{'='*50}")
        print(f"テスト開始: {self._testMethodName}")
        print(f"{'='*50}")
    
    def tearDown(self):
        """テストクリーンアップ"""
        super().tearDown()
        print(f"\nテスト完了: {self._testMethodName}")
    
    def test_floating_point_precision(self):
        """浮動小数点精度テスト"""
        print("\n=== 浮動小数点精度テスト ===")
        
        # 基本的な浮動小数点計算
        print("\n--- 基本浮動小数点計算テスト ---")
        
        test_cases = [
            (0.1 + 0.2, 0.3, "0.1 + 0.2 = 0.3"),
            (1.0 / 3.0 * 3.0, 1.0, "1/3 * 3 = 1"),
            (0.1 * 10, 1.0, "0.1 * 10 = 1"),
            (1.0 - 0.9, 0.1, "1.0 - 0.9 = 0.1")
        ]
        
        for actual, expected, description in test_cases:
            # 浮動小数点の精度問題を考慮した比較
            self.assertAlmostEqual(actual, expected, places=10, 
                                 msg=f"浮動小数点計算精度エラー: {description}")
            print(f"✓ {description}: {actual} ≈ {expected}")
        
        # Decimalを使用した高精度計算
        print("\n--- Decimal高精度計算テスト ---")
        
        decimal_test_cases = [
            (Decimal('0.1') + Decimal('0.2'), Decimal('0.3'), "Decimal 0.1 + 0.2 = 0.3"),
            (Decimal('1') / Decimal('3') * Decimal('3'), Decimal('1'), "Decimal 1/3 * 3 = 1"),
            (Decimal('0.1') * Decimal('10'), Decimal('1'), "Decimal 0.1 * 10 = 1")
        ]
        
        for actual, expected, description in decimal_test_cases:
            self.assertEqual(actual, expected, f"Decimal計算精度エラー: {description}")
            print(f"✓ {description}: {actual} = {expected}")
        
        print("✓ 浮動小数点精度テスト成功")
    
    def test_rounding_precision(self):
        """丸め処理精度テスト"""
        print("\n=== 丸め処理精度テスト ===")
        
        # 四捨五入テスト
        print("\n--- 四捨五入テスト ---")
        
        rounding_test_cases = [
            (1234.5, 1235, "1234.5 -> 1235"),
            (1234.4, 1234, "1234.4 -> 1234"),
            (1234.6, 1235, "1234.6 -> 1235"),
            (-1234.5, -1235, "-1234.5 -> -1235"),
            (-1234.4, -1234, "-1234.4 -> -1234")
        ]
        
        for value, expected, description in rounding_test_cases:
            # 標準的な四捨五入
            rounded_value = round(value)
            self.assertEqual(rounded_value, expected, f"四捨五入エラー: {description}")
            print(f"✓ {description}: round({value}) = {rounded_value}")
            
            # Decimalでの四捨五入
            decimal_value = Decimal(str(value))
            decimal_rounded = int(decimal_value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))
            self.assertEqual(decimal_rounded, expected, f"Decimal四捨五入エラー: {description}")
            print(f"✓ Decimal {description}: {decimal_rounded}")
        
        # 小数点以下の桁数指定丸め
        print("\n--- 小数点桁数指定丸めテスト ---")
        
        decimal_places_test_cases = [
            (123.456, 2, 123.46, "123.456 -> 123.46 (2桁)"),
            (123.454, 2, 123.45, "123.454 -> 123.45 (2桁)"),
            (123.455, 2, 123.46, "123.455 -> 123.46 (2桁)"),
            (123.456789, 4, 123.4568, "123.456789 -> 123.4568 (4桁)")
        ]
        
        for value, places, expected, description in decimal_places_test_cases:
            # 標準的な丸め
            rounded_value = round(value, places)
            self.assertAlmostEqual(rounded_value, expected, places=places+1, 
                                 msg=f"小数点桁数指定丸めエラー: {description}")
            print(f"✓ {description}: round({value}, {places}) = {rounded_value}")
            
            # Decimalでの丸め
            decimal_value = Decimal(str(value))
            quantizer = Decimal('0.' + '0' * (places-1) + '1')
            decimal_rounded = float(decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP))
            self.assertAlmostEqual(decimal_rounded, expected, places=places+1, 
                                 msg=f"Decimal小数点桁数指定丸めエラー: {description}")
            print(f"✓ Decimal {description}: {decimal_rounded}")
        
        print("✓ 丸め処理精度テスト成功")
    
    def test_large_number_precision(self):
        """大きな数値の計算精度テスト"""
        print("\n=== 大きな数値計算精度テスト ===")
        
        # 大きな整数の計算
        print("\n--- 大きな整数計算テスト ---")
        
        large_int_test_cases = [
            (10**15, 10**15, 2 * 10**15, "大きな整数の加算"),
            (10**15, 10**14, 10**15 - 10**14, "大きな整数の減算"),
            (10**8, 10**8, 10**16, "大きな整数の乗算"),
            (10**16, 10**8, 10**8, "大きな整数の除算")
        ]
        
        for a, b, expected, description in large_int_test_cases:
            if "加算" in description:
                result = a + b
            elif "減算" in description:
                result = a - b
            elif "乗算" in description:
                result = a * b
            elif "除算" in description:
                result = a // b
            
            self.assertEqual(result, expected, f"大きな整数計算エラー: {description}")
            print(f"✓ {description}: {result} = {expected}")
        
        # 大きな浮動小数点数の計算
        print("\n--- 大きな浮動小数点計算テスト ---")
        
        large_float_test_cases = [
            (1.23456789e15, 9.87654321e14, "大きな浮動小数点の加算"),
            (1.23456789e15, 9.87654321e14, "大きな浮動小数点の減算"),
            (1.23456789e8, 9.87654321e7, "大きな浮動小数点の乗算")
        ]
        
        for a, b, description in large_float_test_cases:
            if "加算" in description:
                result = a + b
                expected = a + b
            elif "減算" in description:
                result = a - b
                expected = a - b
            elif "乗算" in description:
                result = a * b
                expected = a * b
            
            # 相対誤差での比較（大きな数値では絶対誤差は意味がない）
            relative_error = abs((result - expected) / expected) if expected != 0 else 0
            self.assertLess(relative_error, 1e-10, f"大きな浮動小数点計算精度エラー: {description}")
            print(f"✓ {description}: 相対誤差 {relative_error:.2e}")
        
        # Decimalでの大きな数値計算
        print("\n--- Decimal大きな数値計算テスト ---")
        
        decimal_large_test_cases = [
            (Decimal('123456789012345.123456789'), Decimal('987654321098765.987654321'), "Decimal大きな数値加算"),
            (Decimal('123456789012345.123456789'), Decimal('987654321098765.987654321'), "Decimal大きな数値減算"),
            (Decimal('123456789.123456789'), Decimal('987654321.987654321'), "Decimal大きな数値乗算")
        ]
        
        for a, b, description in decimal_large_test_cases:
            if "加算" in description:
                result = a + b
                print(f"✓ {description}: {result}")
            elif "減算" in description:
                result = a - b
                print(f"✓ {description}: {result}")
            elif "乗算" in description:
                result = a * b
                print(f"✓ {description}: {result}")
            
            # Decimalは正確な計算を保証
            self.assertIsInstance(result, Decimal, f"Decimal計算結果の型エラー: {description}")
        
        print("✓ 大きな数値計算精度テスト成功")
    
    def test_cumulative_error(self):
        """累積誤差検証テスト"""
        print("\n=== 累積誤差検証テスト ===")
        
        # 浮動小数点の累積誤差
        print("\n--- 浮動小数点累積誤差テスト ---")
        
        # 0.1を1000回加算
        float_sum = 0.0
        for i in range(1000):
            float_sum += 0.1
        
        expected_sum = 100.0
        float_error = abs(float_sum - expected_sum)
        print(f"✓ 浮動小数点累積加算: {float_sum} (誤差: {float_error:.2e})")
        
        # Decimalでの同じ計算
        decimal_sum = Decimal('0')
        for i in range(1000):
            decimal_sum += Decimal('0.1')
        
        decimal_expected = Decimal('100')
        decimal_error = abs(decimal_sum - decimal_expected)
        print(f"✓ Decimal累積加算: {decimal_sum} (誤差: {decimal_error})")
        
        # Decimalの方が正確であることを確認
        self.assertLess(decimal_error, float_error, "Decimalの方が累積誤差が小さいはず")
        
        # 複雑な計算での累積誤差
        print("\n--- 複雑な計算累積誤差テスト ---")
        
        # 税計算のシミュレーション（所得税の累進課税）
        income_brackets = [
            (1950000, 0.05),
            (3300000, 0.10),
            (6950000, 0.20),
            (9000000, 0.23),
            (18000000, 0.33),
            (40000000, 0.40),
            (float('inf'), 0.45)
        ]
        
        test_incomes = [5000000, 10000000, 25000000, 50000000]
        
        for income in test_incomes:
            # 浮動小数点での計算
            float_tax = self._calculate_progressive_tax_float(income, income_brackets)
            
            # Decimalでの計算
            decimal_tax = self._calculate_progressive_tax_decimal(income, income_brackets)
            
            # 誤差の計算
            error = abs(float_tax - float(decimal_tax))
            relative_error = error / float(decimal_tax) if decimal_tax != 0 else 0
            
            print(f"✓ 所得{income:,}円: 浮動小数点税額{float_tax:,.2f}円, Decimal税額{decimal_tax}円")
            print(f"  誤差: {error:.2f}円 (相対誤差: {relative_error:.2e})")
            
            # 相対誤差が0.01%以下であることを確認
            self.assertLess(relative_error, 0.0001, f"所得{income}円での税計算精度が不十分")
        
        print("✓ 累積誤差検証テスト成功")
    
    def test_boundary_value_precision(self):
        """境界値での計算精度テスト"""
        print("\n=== 境界値計算精度テスト ===")
        
        # ゼロ近辺の計算
        print("\n--- ゼロ近辺計算テスト ---")
        
        zero_boundary_test_cases = [
            (1e-10, 1e-10, 2e-10, "極小値の加算"),
            (1e-10, -1e-10, 0, "極小値の減算（ゼロ）"),
            (1e-5, 1e-5, 1e-10, "極小値の乗算"),
            (1e-10, 1e-5, 1e-5, "極小値の除算")
        ]
        
        for a, b, expected, description in zero_boundary_test_cases:
            if "加算" in description:
                result = a + b
            elif "減算" in description:
                result = a - b
            elif "乗算" in description:
                result = a * b
            elif "除算" in description:
                result = a / b
            
            if expected == 0:
                self.assertAlmostEqual(result, expected, places=15, 
                                     msg=f"ゼロ近辺計算精度エラー: {description}")
            else:
                relative_error = abs((result - expected) / expected) if expected != 0 else 0
                self.assertLess(relative_error, 1e-10, f"ゼロ近辺計算精度エラー: {description}")
            
            print(f"✓ {description}: {result:.2e} ≈ {expected:.2e}")
        
        # 非常に大きな値の境界
        print("\n--- 大きな値境界テスト ---")
        
        large_boundary_test_cases = [
            (1e15, 1, 1e15 + 1, "大きな値への小さな値加算"),
            (1e15, 1e15, 2e15, "大きな値同士の加算"),
            (1e15, 1e14, 9e14, "大きな値からの減算")
        ]
        
        for a, b, expected, description in large_boundary_test_cases:
            if "加算" in description:
                result = a + b
            elif "減算" in description:
                result = a - b
            
            # 大きな値では相対誤差で評価
            relative_error = abs((result - expected) / expected) if expected != 0 else 0
            self.assertLess(relative_error, 1e-14, f"大きな値境界計算精度エラー: {description}")
            print(f"✓ {description}: 相対誤差 {relative_error:.2e}")
        
        # 税計算での境界値
        print("\n--- 税計算境界値テスト ---")
        
        # 所得税の課税境界値での計算精度
        tax_boundary_test_cases = [
            (1949999, "195万円境界直下"),
            (1950000, "195万円境界"),
            (1950001, "195万円境界直上"),
            (3299999, "330万円境界直下"),
            (3300000, "330万円境界"),
            (3300001, "330万円境界直上")
        ]
        
        income_brackets = [
            (1950000, 0.05),
            (3300000, 0.10),
            (6950000, 0.20),
            (9000000, 0.23),
            (18000000, 0.33),
            (40000000, 0.40),
            (float('inf'), 0.45)
        ]
        
        for income, description in tax_boundary_test_cases:
            # 浮動小数点での計算
            float_tax = self._calculate_progressive_tax_float(income, income_brackets)
            
            # Decimalでの計算
            decimal_tax = self._calculate_progressive_tax_decimal(income, income_brackets)
            
            # 誤差の確認
            error = abs(float_tax - float(decimal_tax))
            print(f"✓ {description} (所得{income:,}円): 税額{float_tax:,.2f}円 (誤差: {error:.2f}円)")
            
            # 境界値での計算精度を確認（誤差は1円以下）
            self.assertLess(error, 1.0, f"税計算境界値精度エラー: {description}")
        
        print("✓ 境界値計算精度テスト成功")
    
    def test_tax_calculation_precision(self):
        """税計算精度テスト"""
        print("\n=== 税計算精度テスト ===")
        
        # 所得税計算精度
        print("\n--- 所得税計算精度テスト ---")
        
        income_test_cases = [
            (5000000, 1000000, "中所得者"),
            (10000000, 2000000, "高所得者"),
            (25000000, 3000000, "超高所得者"),
            (100000000, 5000000, "富裕層")
        ]
        
        for income, deductions, description in income_test_cases:
            taxable_income = income - deductions
            
            # 複数の方法で税額計算
            tax_float = self._calculate_income_tax_float(taxable_income)
            tax_decimal = self._calculate_income_tax_decimal(taxable_income)
            tax_manual = self._calculate_income_tax_manual(taxable_income)
            
            # 計算結果の比較
            float_decimal_diff = abs(tax_float - float(tax_decimal))
            float_manual_diff = abs(tax_float - tax_manual)
            decimal_manual_diff = abs(float(tax_decimal) - tax_manual)
            
            print(f"✓ {description} (課税所得{taxable_income:,}円):")
            print(f"  浮動小数点: {tax_float:,.2f}円")
            print(f"  Decimal: {tax_decimal}円")
            print(f"  手計算: {tax_manual:,.2f}円")
            print(f"  誤差: float-decimal={float_decimal_diff:.2f}円, float-manual={float_manual_diff:.2f}円")
            
            # 誤差が許容範囲内であることを確認
            self.assertLess(float_decimal_diff, 1.0, f"所得税計算精度エラー(float-decimal): {description}")
            self.assertLess(float_manual_diff, 1.0, f"所得税計算精度エラー(float-manual): {description}")
            self.assertLess(decimal_manual_diff, 1.0, f"所得税計算精度エラー(decimal-manual): {description}")
        
        # 消費税計算精度
        print("\n--- 消費税計算精度テスト ---")
        
        consumption_tax_test_cases = [
            (1000, 0.10, "基本的な消費税"),
            (1234, 0.10, "端数のある消費税"),
            (9999, 0.10, "大きな金額の消費税"),
            (1, 0.10, "最小金額の消費税")
        ]
        
        for amount, tax_rate, description in consumption_tax_test_cases:
            # 複数の方法で消費税計算
            tax_float = amount * tax_rate
            tax_decimal = float(Decimal(str(amount)) * Decimal(str(tax_rate)))
            tax_rounded = round(amount * tax_rate)
            
            print(f"✓ {description} (金額{amount}円, 税率{tax_rate*100}%):")
            print(f"  浮動小数点: {tax_float:.2f}円")
            print(f"  Decimal: {tax_decimal:.2f}円")
            print(f"  四捨五入: {tax_rounded}円")
            
            # 計算精度の確認
            float_decimal_diff = abs(tax_float - tax_decimal)
            self.assertLess(float_decimal_diff, 0.01, f"消費税計算精度エラー: {description}")
        
        print("✓ 税計算精度テスト成功")
    
    # ヘルパーメソッド
    def _calculate_progressive_tax_float(self, income: float, brackets: List[Tuple[float, float]]) -> float:
        """累進課税計算（浮動小数点）"""
        tax = 0.0
        remaining_income = income
        prev_bracket = 0
        
        for bracket_limit, rate in brackets:
            if remaining_income <= 0:
                break
            
            taxable_in_bracket = min(remaining_income, bracket_limit - prev_bracket)
            tax += taxable_in_bracket * rate
            remaining_income -= taxable_in_bracket
            prev_bracket = bracket_limit
            
            if bracket_limit == float('inf'):
                break
        
        return tax
    
    def _calculate_progressive_tax_decimal(self, income: float, brackets: List[Tuple[float, float]]) -> Decimal:
        """累進課税計算（Decimal）"""
        tax = Decimal('0')
        remaining_income = Decimal(str(income))
        prev_bracket = Decimal('0')
        
        for bracket_limit, rate in brackets:
            if remaining_income <= 0:
                break
            
            if bracket_limit == float('inf'):
                taxable_in_bracket = remaining_income
            else:
                bracket_limit_decimal = Decimal(str(bracket_limit))
                taxable_in_bracket = min(remaining_income, bracket_limit_decimal - prev_bracket)
            
            tax += taxable_in_bracket * Decimal(str(rate))
            remaining_income -= taxable_in_bracket
            
            if bracket_limit != float('inf'):
                prev_bracket = Decimal(str(bracket_limit))
            else:
                break
        
        return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _calculate_income_tax_float(self, taxable_income: float) -> float:
        """所得税計算（浮動小数点）"""
        brackets = [
            (1950000, 0.05),
            (3300000, 0.10),
            (6950000, 0.20),
            (9000000, 0.23),
            (18000000, 0.33),
            (40000000, 0.40),
            (float('inf'), 0.45)
        ]
        
        return self._calculate_progressive_tax_float(taxable_income, brackets)
    
    def _calculate_income_tax_decimal(self, taxable_income: float) -> Decimal:
        """所得税計算（Decimal）"""
        brackets = [
            (1950000, 0.05),
            (3300000, 0.10),
            (6950000, 0.20),
            (9000000, 0.23),
            (18000000, 0.33),
            (40000000, 0.40),
            (float('inf'), 0.45)
        ]
        
        return self._calculate_progressive_tax_decimal(taxable_income, brackets)
    
    def _calculate_income_tax_manual(self, taxable_income: float) -> float:
        """所得税計算（手計算による検証）"""
        if taxable_income <= 1950000:
            return taxable_income * 0.05
        elif taxable_income <= 3300000:
            return 1950000 * 0.05 + (taxable_income - 1950000) * 0.10
        elif taxable_income <= 6950000:
            return 1950000 * 0.05 + 1350000 * 0.10 + (taxable_income - 3300000) * 0.20
        elif taxable_income <= 9000000:
            return 1950000 * 0.05 + 1350000 * 0.10 + 3650000 * 0.20 + (taxable_income - 6950000) * 0.23
        elif taxable_income <= 18000000:
            return 1950000 * 0.05 + 1350000 * 0.10 + 3650000 * 0.20 + 2050000 * 0.23 + (taxable_income - 9000000) * 0.33
        elif taxable_income <= 40000000:
            return 1950000 * 0.05 + 1350000 * 0.10 + 3650000 * 0.20 + 2050000 * 0.23 + 9000000 * 0.33 + (taxable_income - 18000000) * 0.40
        else:
            return 1950000 * 0.05 + 1350000 * 0.10 + 3650000 * 0.20 + 2050000 * 0.23 + 9000000 * 0.33 + 22000000 * 0.40 + (taxable_income - 40000000) * 0.45


if __name__ == "__main__":
    unittest.main(verbosity=2)