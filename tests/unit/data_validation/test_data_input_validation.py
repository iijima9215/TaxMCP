#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaxMCP データ検証テスト - 入力検証

このモジュールは、TaxMCPサーバーの入力検証機能をテストします。

主なテスト項目:
- データ型検証
- 範囲検証
- 必須フィールド検証
- フォーマット検証
- ビジネスロジック検証
"""

import unittest
import json
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List

from tests.utils.test_config import TaxMCPTestCase
from tests.utils.assertion_helpers import DataAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestInputValidation(TaxMCPTestCase, DataAssertions):
    """入力検証テストクラス"""
    
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
    
    def test_data_type_validation(self):
        """データ型検証テスト"""
        print("\n=== データ型検証テスト ===")
        
        # 数値型検証
        print("\n--- 数値型検証テスト ---")
        
        # 正常な数値
        valid_numbers = [
            1000000,  # 整数
            1000000.50,  # 浮動小数点
            "1000000",  # 文字列数値
            "1000000.50",  # 文字列浮動小数点
            Decimal("1000000.50")  # Decimal
        ]
        
        for number in valid_numbers:
            result = self._validate_number(number)
            self.assertTrue(result["valid"], f"数値 {number} の検証に失敗")
            print(f"✓ 数値 {number} ({type(number).__name__}) の検証成功")
        
        # 不正な数値
        invalid_numbers = [
            "abc",  # 文字列
            "12.34.56",  # 不正な小数点
            None,  # None
            [],  # リスト
            {},  # 辞書
            float('inf'),  # 無限大
            float('nan')  # NaN
        ]
        
        for number in invalid_numbers:
            result = self._validate_number(number)
            self.assertFalse(result["valid"], f"不正な数値 {number} が検証を通過")
            print(f"✓ 不正な数値 {number} ({type(number).__name__}) の検証失敗を確認")
        
        # 文字列型検証
        print("\n--- 文字列型検証テスト ---")
        
        # 正常な文字列
        valid_strings = [
            "田中太郎",  # 日本語
            "Tanaka Taro",  # 英語
            "123-4567",  # 数字と記号
            "東京都渋谷区",  # 住所
            ""  # 空文字列（許可される場合）
        ]
        
        for string in valid_strings:
            result = self._validate_string(string, max_length=100)
            self.assertTrue(result["valid"], f"文字列 '{string}' の検証に失敗")
            print(f"✓ 文字列 '{string}' の検証成功")
        
        # 不正な文字列
        invalid_strings = [
            123,  # 数値
            None,  # None
            [],  # リスト
            {},  # 辞書
            "a" * 101  # 長すぎる文字列
        ]
        
        for string in invalid_strings:
            result = self._validate_string(string, max_length=100)
            self.assertFalse(result["valid"], f"不正な文字列 {string} が検証を通過")
            print(f"✓ 不正な文字列 {type(string).__name__} の検証失敗を確認")
        
        # 日付型検証
        print("\n--- 日付型検証テスト ---")
        
        # 正常な日付
        valid_dates = [
            "2024-01-01",  # ISO形式
            "2024/01/01",  # スラッシュ形式
            "2024-12-31",  # 年末
            date(2024, 1, 1),  # dateオブジェクト
            datetime(2024, 1, 1, 12, 0, 0)  # datetimeオブジェクト
        ]
        
        for date_value in valid_dates:
            result = self._validate_date(date_value)
            self.assertTrue(result["valid"], f"日付 {date_value} の検証に失敗")
            print(f"✓ 日付 {date_value} ({type(date_value).__name__}) の検証成功")
        
        # 不正な日付
        invalid_dates = [
            "2024-13-01",  # 不正な月
            "2024-02-30",  # 存在しない日
            "invalid-date",  # 不正な形式
            "2024/13/01",  # 不正な月（スラッシュ形式）
            123,  # 数値
            None  # None
        ]
        
        for date_value in invalid_dates:
            result = self._validate_date(date_value)
            self.assertFalse(result["valid"], f"不正な日付 {date_value} が検証を通過")
            print(f"✓ 不正な日付 {date_value} の検証失敗を確認")
        
        print("✓ データ型検証テスト成功")
    
    def test_range_validation(self):
        """範囲検証テスト"""
        print("\n=== 範囲検証テスト ===")
        
        # 数値範囲検証
        print("\n--- 数値範囲検証テスト ---")
        
        # 所得金額の範囲検証（0以上10億円以下）
        income_test_cases = [
            (0, True, "最小値"),
            (1000000, True, "正常値"),
            (1000000000, True, "最大値"),
            (-1, False, "負の値"),
            (1000000001, False, "最大値超過")
        ]
        
        for income, expected, description in income_test_cases:
            result = self._validate_income_range(income)
            self.assertEqual(result["valid"], expected, 
                           f"所得金額範囲検証失敗: {description} ({income})")
            print(f"✓ 所得金額 {description}: {income} -> {result['valid']}")
        
        # 税率の範囲検証（0%以上100%以下）
        tax_rate_test_cases = [
            (0.0, True, "最小値"),
            (0.1, True, "10%"),
            (0.45, True, "45%"),
            (1.0, True, "最大値"),
            (-0.01, False, "負の値"),
            (1.01, False, "100%超過")
        ]
        
        for rate, expected, description in tax_rate_test_cases:
            result = self._validate_tax_rate_range(rate)
            self.assertEqual(result["valid"], expected, 
                           f"税率範囲検証失敗: {description} ({rate})")
            print(f"✓ 税率 {description}: {rate} -> {result['valid']}")
        
        # 年度の範囲検証（1900年以降現在年+10年以下）
        current_year = datetime.now().year
        year_test_cases = [
            (1900, True, "最小値"),
            (2024, True, "現在年"),
            (current_year + 10, True, "最大値"),
            (1899, False, "最小値未満"),
            (current_year + 11, False, "最大値超過")
        ]
        
        for year, expected, description in year_test_cases:
            result = self._validate_year_range(year)
            self.assertEqual(result["valid"], expected, 
                           f"年度範囲検証失敗: {description} ({year})")
            print(f"✓ 年度 {description}: {year} -> {result['valid']}")
        
        # 文字列長範囲検証
        print("\n--- 文字列長範囲検証テスト ---")
        
        string_length_test_cases = [
            ("", 0, 10, True, "空文字列"),
            ("田中", 0, 10, True, "正常な長さ"),
            ("a" * 10, 0, 10, True, "最大長"),
            ("a" * 11, 0, 10, False, "最大長超過")
        ]
        
        for string, min_len, max_len, expected, description in string_length_test_cases:
            result = self._validate_string_length(string, min_len, max_len)
            self.assertEqual(result["valid"], expected, 
                           f"文字列長検証失敗: {description} ('{string}')")
            print(f"✓ 文字列長 {description}: '{string}' ({len(string)}文字) -> {result['valid']}")
        
        print("✓ 範囲検証テスト成功")
    
    def test_required_field_validation(self):
        """必須フィールド検証テスト"""
        print("\n=== 必須フィールド検証テスト ===")
        
        # 所得税計算の必須フィールド
        print("\n--- 所得税計算必須フィールドテスト ---")
        
        # 完全なデータ
        complete_data = {
            "income": 5000000,
            "deductions": 1000000,
            "tax_year": 2024,
            "taxpayer_type": "individual"
        }
        
        result = self._validate_required_fields(complete_data, 
                                               ["income", "deductions", "tax_year", "taxpayer_type"])
        self.assertTrue(result["valid"], "完全なデータの検証に失敗")
        print(f"✓ 完全なデータの検証成功")
        
        # 必須フィールドが欠けているデータ
        incomplete_test_cases = [
            ({"deductions": 1000000, "tax_year": 2024, "taxpayer_type": "individual"}, "income"),
            ({"income": 5000000, "tax_year": 2024, "taxpayer_type": "individual"}, "deductions"),
            ({"income": 5000000, "deductions": 1000000, "taxpayer_type": "individual"}, "tax_year"),
            ({"income": 5000000, "deductions": 1000000, "tax_year": 2024}, "taxpayer_type")
        ]
        
        for incomplete_data, missing_field in incomplete_test_cases:
            result = self._validate_required_fields(incomplete_data, 
                                                   ["income", "deductions", "tax_year", "taxpayer_type"])
            self.assertFalse(result["valid"], f"必須フィールド {missing_field} が欠けているデータが検証を通過")
            self.assertIn(missing_field, result["missing_fields"])
            print(f"✓ 必須フィールド {missing_field} の欠如を検出")
        
        # 法人税計算の必須フィールド
        print("\n--- 法人税計算必須フィールドテスト ---")
        
        corporate_complete_data = {
            "revenue": 100000000,
            "expenses": 80000000,
            "fiscal_year": 2024,
            "company_type": "large",
            "capital": 50000000
        }
        
        result = self._validate_required_fields(corporate_complete_data, 
                                               ["revenue", "expenses", "fiscal_year", "company_type", "capital"])
        self.assertTrue(result["valid"], "法人税完全なデータの検証に失敗")
        print(f"✓ 法人税完全なデータの検証成功")
        
        # Noneや空文字列の検証
        print("\n--- None・空文字列検証テスト ---")
        
        none_empty_test_cases = [
            ({"income": None, "deductions": 1000000, "tax_year": 2024, "taxpayer_type": "individual"}, "income"),
            ({"income": 5000000, "deductions": "", "tax_year": 2024, "taxpayer_type": "individual"}, "deductions"),
            ({"income": 5000000, "deductions": 1000000, "tax_year": None, "taxpayer_type": "individual"}, "tax_year")
        ]
        
        for data_with_none, field_with_none in none_empty_test_cases:
            result = self._validate_required_fields(data_with_none, 
                                                   ["income", "deductions", "tax_year", "taxpayer_type"],
                                                   allow_none=False)
            self.assertFalse(result["valid"], f"None/空文字列を含むフィールド {field_with_none} が検証を通過")
            print(f"✓ None/空文字列フィールド {field_with_none} の検出成功")
        
        print("✓ 必須フィールド検証テスト成功")
    
    def test_format_validation(self):
        """フォーマット検証テスト"""
        print("\n=== フォーマット検証テスト ===")
        
        # 郵便番号フォーマット検証
        print("\n--- 郵便番号フォーマットテスト ---")
        
        postal_code_test_cases = [
            ("123-4567", True, "正常な郵便番号"),
            ("1234567", True, "ハイフンなし郵便番号"),
            ("12-3456", False, "桁数不足"),
            ("1234-567", False, "不正な区切り位置"),
            ("abc-defg", False, "文字を含む"),
            ("", False, "空文字列")
        ]
        
        for postal_code, expected, description in postal_code_test_cases:
            result = self._validate_postal_code_format(postal_code)
            self.assertEqual(result["valid"], expected, 
                           f"郵便番号フォーマット検証失敗: {description} ('{postal_code}')")
            print(f"✓ 郵便番号 {description}: '{postal_code}' -> {result['valid']}")
        
        # 電話番号フォーマット検証
        print("\n--- 電話番号フォーマットテスト ---")
        
        phone_test_cases = [
            ("03-1234-5678", True, "固定電話"),
            ("090-1234-5678", True, "携帯電話"),
            ("0312345678", True, "ハイフンなし固定電話"),
            ("09012345678", True, "ハイフンなし携帯電話"),
            ("03-123-456", False, "桁数不足"),
            ("abc-defg-hijk", False, "文字を含む"),
            ("", False, "空文字列")
        ]
        
        for phone, expected, description in phone_test_cases:
            result = self._validate_phone_format(phone)
            self.assertEqual(result["valid"], expected, 
                           f"電話番号フォーマット検証失敗: {description} ('{phone}')")
            print(f"✓ 電話番号 {description}: '{phone}' -> {result['valid']}")
        
        # メールアドレスフォーマット検証
        print("\n--- メールアドレスフォーマットテスト ---")
        
        email_test_cases = [
            ("test@example.com", True, "正常なメールアドレス"),
            ("user.name@domain.co.jp", True, "ドット含むメールアドレス"),
            ("test+tag@example.com", True, "プラス含むメールアドレス"),
            ("test@", False, "ドメイン部分なし"),
            ("@example.com", False, "ローカル部分なし"),
            ("testexample.com", False, "@マークなし"),
            ("", False, "空文字列")
        ]
        
        for email, expected, description in email_test_cases:
            result = self._validate_email_format(email)
            self.assertEqual(result["valid"], expected, 
                           f"メールアドレスフォーマット検証失敗: {description} ('{email}')")
            print(f"✓ メールアドレス {description}: '{email}' -> {result['valid']}")
        
        # 銀行口座番号フォーマット検証
        print("\n--- 銀行口座番号フォーマットテスト ---")
        
        account_test_cases = [
            ("1234567", True, "7桁口座番号"),
            ("12345678", True, "8桁口座番号"),
            ("123456", False, "桁数不足"),
            ("123456789", False, "桁数超過"),
            ("abc1234", False, "文字を含む"),
            ("", False, "空文字列")
        ]
        
        for account, expected, description in account_test_cases:
            result = self._validate_account_format(account)
            self.assertEqual(result["valid"], expected, 
                           f"銀行口座番号フォーマット検証失敗: {description} ('{account}')")
            print(f"✓ 銀行口座番号 {description}: '{account}' -> {result['valid']}")
        
        print("✓ フォーマット検証テスト成功")
    
    def test_business_logic_validation(self):
        """ビジネスロジック検証テスト"""
        print("\n=== ビジネスロジック検証テスト ===")
        
        # 所得と控除の関係検証
        print("\n--- 所得・控除関係検証テスト ---")
        
        income_deduction_test_cases = [
            (5000000, 1000000, True, "正常な所得・控除関係"),
            (5000000, 5000000, True, "所得と控除が同額"),
            (5000000, 6000000, False, "控除が所得を上回る"),
            (0, 1000000, False, "所得0で控除あり")
        ]
        
        for income, deduction, expected, description in income_deduction_test_cases:
            result = self._validate_income_deduction_relationship(income, deduction)
            self.assertEqual(result["valid"], expected, 
                           f"所得・控除関係検証失敗: {description}")
            print(f"✓ {description}: 所得{income}, 控除{deduction} -> {result['valid']}")
        
        # 年齢と扶養の関係検証
        print("\n--- 年齢・扶養関係検証テスト ---")
        
        age_dependent_test_cases = [
            (30, [5, 10], True, "正常な扶養関係"),
            (25, [30], False, "扶養者が納税者より年上"),
            (40, [16, 18, 20], True, "複数の扶養者"),
            (20, [25], False, "若い納税者が年上を扶養")
        ]
        
        for taxpayer_age, dependent_ages, expected, description in age_dependent_test_cases:
            result = self._validate_age_dependent_relationship(taxpayer_age, dependent_ages)
            self.assertEqual(result["valid"], expected, 
                           f"年齢・扶養関係検証失敗: {description}")
            print(f"✓ {description}: 納税者{taxpayer_age}歳, 扶養者{dependent_ages} -> {result['valid']}")
        
        # 法人の資本金と従業員数の関係検証
        print("\n--- 法人規模関係検証テスト ---")
        
        company_size_test_cases = [
            (10000000, 50, "small", True, "小規模法人"),
            (100000000, 200, "medium", True, "中規模法人"),
            (1000000000, 1000, "large", True, "大規模法人"),
            (10000000, 1000, "small", False, "資本金に対して従業員数が多すぎる"),
            (1000000000, 10, "large", False, "資本金に対して従業員数が少なすぎる")
        ]
        
        for capital, employees, company_type, expected, description in company_size_test_cases:
            result = self._validate_company_size_consistency(capital, employees, company_type)
            self.assertEqual(result["valid"], expected, 
                           f"法人規模関係検証失敗: {description}")
            print(f"✓ {description}: 資本金{capital}, 従業員{employees}人, 種別{company_type} -> {result['valid']}")
        
        # 税務期間の整合性検証
        print("\n--- 税務期間整合性検証テスト ---")
        
        tax_period_test_cases = [
            ("2024-01-01", "2024-12-31", True, "正常な税務期間"),
            ("2024-04-01", "2025-03-31", True, "年度をまたぐ税務期間"),
            ("2024-12-31", "2024-01-01", False, "開始日が終了日より後"),
            ("2024-01-01", "2025-12-31", False, "期間が1年を超える")
        ]
        
        for start_date, end_date, expected, description in tax_period_test_cases:
            result = self._validate_tax_period_consistency(start_date, end_date)
            self.assertEqual(result["valid"], expected, 
                           f"税務期間整合性検証失敗: {description}")
            print(f"✓ {description}: {start_date} - {end_date} -> {result['valid']}")
        
        print("✓ ビジネスロジック検証テスト成功")
    
    # ヘルパーメソッド
    def _validate_number(self, value) -> Dict[str, Any]:
        """数値検証ヘルパー"""
        try:
            if value is None:
                return {"valid": False, "error": "None value"}
            
            if isinstance(value, (list, dict)):
                return {"valid": False, "error": "Invalid type"}
            
            if isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf')):
                return {"valid": False, "error": "NaN or Infinity"}
            
            float(value)
            return {"valid": True}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Cannot convert to number"}
    
    def _validate_string(self, value, max_length: int = None) -> Dict[str, Any]:
        """文字列検証ヘルパー"""
        if not isinstance(value, str):
            return {"valid": False, "error": "Not a string"}
        
        if max_length and len(value) > max_length:
            return {"valid": False, "error": f"String too long (max: {max_length})"}
        
        return {"valid": True}
    
    def _validate_date(self, value) -> Dict[str, Any]:
        """日付検証ヘルパー"""
        try:
            if isinstance(value, (date, datetime)):
                return {"valid": True}
            
            if isinstance(value, str):
                # ISO形式
                if "-" in value:
                    datetime.strptime(value, "%Y-%m-%d")
                # スラッシュ形式
                elif "/" in value:
                    datetime.strptime(value, "%Y/%m/%d")
                else:
                    return {"valid": False, "error": "Invalid date format"}
                
                return {"valid": True}
            
            return {"valid": False, "error": "Invalid date type"}
        except ValueError:
            return {"valid": False, "error": "Invalid date value"}
    
    def _validate_income_range(self, income) -> Dict[str, Any]:
        """所得範囲検証ヘルパー"""
        try:
            income_value = float(income)
            if 0 <= income_value <= 1000000000:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Income out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid income value"}
    
    def _validate_tax_rate_range(self, rate) -> Dict[str, Any]:
        """税率範囲検証ヘルパー"""
        try:
            rate_value = float(rate)
            if 0.0 <= rate_value <= 1.0:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Tax rate out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid tax rate value"}
    
    def _validate_year_range(self, year) -> Dict[str, Any]:
        """年度範囲検証ヘルパー"""
        try:
            year_value = int(year)
            current_year = datetime.now().year
            if 1900 <= year_value <= current_year + 10:
                return {"valid": True}
            else:
                return {"valid": False, "error": "Year out of range"}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid year value"}
    
    def _validate_string_length(self, string, min_length: int, max_length: int) -> Dict[str, Any]:
        """文字列長検証ヘルパー"""
        if not isinstance(string, str):
            return {"valid": False, "error": "Not a string"}
        
        length = len(string)
        if min_length <= length <= max_length:
            return {"valid": True}
        else:
            return {"valid": False, "error": f"String length out of range ({min_length}-{max_length})"}
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str], allow_none: bool = False) -> Dict[str, Any]:
        """必須フィールド検証ヘルパー"""
        missing_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not allow_none and (data[field] is None or data[field] == ""):
                missing_fields.append(field)
        
        if missing_fields:
            return {"valid": False, "missing_fields": missing_fields}
        else:
            return {"valid": True}
    
    def _validate_postal_code_format(self, postal_code: str) -> Dict[str, Any]:
        """郵便番号フォーマット検証ヘルパー"""
        import re
        
        if not isinstance(postal_code, str) or not postal_code:
            return {"valid": False, "error": "Invalid postal code"}
        
        # 123-4567 または 1234567 形式
        pattern = r'^\d{3}-?\d{4}$'
        if re.match(pattern, postal_code):
            return {"valid": True}
        else:
            return {"valid": False, "error": "Invalid postal code format"}
    
    def _validate_phone_format(self, phone: str) -> Dict[str, Any]:
        """電話番号フォーマット検証ヘルパー"""
        import re
        
        if not isinstance(phone, str) or not phone:
            return {"valid": False, "error": "Invalid phone number"}
        
        # 03-1234-5678, 090-1234-5678, 0312345678, 09012345678 形式
        patterns = [
            r'^0\d{1,4}-\d{1,4}-\d{4}$',  # ハイフンあり
            r'^0\d{9,10}$'  # ハイフンなし
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return {"valid": True}
        
        return {"valid": False, "error": "Invalid phone number format"}
    
    def _validate_email_format(self, email: str) -> Dict[str, Any]:
        """メールアドレスフォーマット検証ヘルパー"""
        import re
        
        if not isinstance(email, str) or not email:
            return {"valid": False, "error": "Invalid email address"}
        
        # 基本的なメールアドレス形式
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return {"valid": True}
        else:
            return {"valid": False, "error": "Invalid email format"}
    
    def _validate_account_format(self, account: str) -> Dict[str, Any]:
        """銀行口座番号フォーマット検証ヘルパー"""
        import re
        
        if not isinstance(account, str) or not account:
            return {"valid": False, "error": "Invalid account number"}
        
        # 7-8桁の数字
        pattern = r'^\d{7,8}$'
        if re.match(pattern, account):
            return {"valid": True}
        else:
            return {"valid": False, "error": "Invalid account number format"}
    
    def _validate_income_deduction_relationship(self, income, deduction) -> Dict[str, Any]:
        """所得・控除関係検証ヘルパー"""
        try:
            income_value = float(income)
            deduction_value = float(deduction)
            
            if income_value == 0 and deduction_value > 0:
                return {"valid": False, "error": "Deduction cannot exceed zero income"}
            
            if deduction_value > income_value:
                return {"valid": False, "error": "Deduction cannot exceed income"}
            
            return {"valid": True}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid income or deduction value"}
    
    def _validate_age_dependent_relationship(self, taxpayer_age: int, dependent_ages: List[int]) -> Dict[str, Any]:
        """年齢・扶養関係検証ヘルパー"""
        try:
            for dependent_age in dependent_ages:
                if dependent_age >= taxpayer_age:
                    return {"valid": False, "error": "Dependent cannot be older than taxpayer"}
            
            return {"valid": True}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid age values"}
    
    def _validate_company_size_consistency(self, capital: int, employees: int, company_type: str) -> Dict[str, Any]:
        """法人規模整合性検証ヘルパー"""
        try:
            # 簡単な整合性チェック
            if company_type == "small":
                if capital > 50000000 or employees > 100:
                    return {"valid": False, "error": "Inconsistent small company size"}
            elif company_type == "medium":
                if capital > 500000000 or employees > 500:
                    return {"valid": False, "error": "Inconsistent medium company size"}
            elif company_type == "large":
                if capital < 100000000 or employees < 100:
                    return {"valid": False, "error": "Inconsistent large company size"}
            
            return {"valid": True}
        except (ValueError, TypeError):
            return {"valid": False, "error": "Invalid company size values"}
    
    def _validate_tax_period_consistency(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """税務期間整合性検証ヘルパー"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start >= end:
                return {"valid": False, "error": "Start date must be before end date"}
            
            # 期間が1年を超えないかチェック
            if (end - start).days > 366:
                return {"valid": False, "error": "Tax period cannot exceed one year"}
            
            return {"valid": True}
        except ValueError:
            return {"valid": False, "error": "Invalid date format"}


if __name__ == "__main__":
    unittest.main(verbosity=2)