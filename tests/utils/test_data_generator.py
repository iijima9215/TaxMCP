"""テストデータ生成ユーティリティ

TaxMCPサーバーのテスト用データを生成するためのユーティリティ関数群
"""

import random
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal


class TestDataGenerator:
    """テストデータ生成クラス"""
    
    @staticmethod
    def generate_income_tax_data(scenario: str = "normal", **kwargs) -> Dict[str, Any]:
        """所得税計算用テストデータ生成
        
        Args:
            scenario: テストシナリオ (normal, low_income, high_income, complex)
            **kwargs: 追加パラメータ（annual_income, tax_year, prefecture, city等）
            
        Returns:
            所得税計算用のテストデータ
        """
        base_data = {
            "annual_income": 5000000,
            "deductions": 480000,  # 基礎控除
            "dependents_count": 0,
            "tax_year": 2025,
            "prefecture": "東京都",
            "city": "新宿区"
        }
        
        if scenario == "low_income":
            base_data.update({
                "annual_income": random.randint(1000000, 3000000),
                "deductions": random.randint(480000, 800000),
                "dependents_count": random.randint(0, 2)
            })
        elif scenario == "high_income":
            base_data.update({
                "annual_income": random.randint(10000000, 50000000),
                "deductions": random.randint(480000, 2000000),
                "dependents_count": random.randint(0, 4)
            })
        elif scenario == "complex":
            base_data.update({
                "annual_income": random.randint(5000000, 15000000),
                "deductions": random.randint(1000000, 3000000),
                "dependents_count": random.randint(2, 6),
                "spouse_deduction": random.randint(0, 380000),
                "medical_deduction": random.randint(0, 500000),
                "donation_deduction": random.randint(0, 200000)
            })
        
        # kwargsで指定された値で上書き
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def generate_corporate_tax_data(scenario: str = "normal", **kwargs) -> Dict[str, Any]:
        """法人税計算用テストデータ生成
        
        Args:
            scenario: テストシナリオ (normal, small_company, large_company)
            **kwargs: 追加パラメータ（annual_income, revenue, expenses, company_type, tax_year等）
            
        Returns:
            法人税計算用のテストデータ
        """
        base_data = {
            "annual_income": 10000000,
            "company_type": "small_company",
            "tax_year": 2025,
            "prefecture": "東京都",
            "city": "千代田区"
        }
        
        if scenario == "small_company":
            base_data.update({
                "annual_income": random.randint(1000000, 8000000),
                "company_type": "small_company"
            })
        elif scenario == "large_company":
            base_data.update({
                "annual_income": random.randint(100000000, 1000000000),
                "company_type": "large_company"
            })
        
        # kwargsで指定された値で上書き
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def generate_consumption_tax_data(**kwargs) -> Dict[str, Any]:
        """消費税計算用テストデータ生成
        
        Args:
            **kwargs: 追加パラメータ（sales_amount, purchase_amount, tax_year等）
            
        Returns:
            消費税計算用のテストデータ
        """
        categories = ["food", "beverage", "general", "newspaper", "medicine"]
        
        base_data = {
            "date": date.today().isoformat(),
            "category": random.choice(categories),
            "amount": random.randint(100, 100000)
        }
        
        # kwargsで指定された値で上書き
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def generate_resident_tax_data(**kwargs) -> Dict[str, Any]:
        """住民税計算用テストデータ生成
        
        Args:
            **kwargs: 追加パラメータ（income, annual_income, prefecture, municipality, city, tax_year等）
            
        Returns:
            住民税計算用のテストデータ
        """
        prefectures = ["東京都", "大阪府", "神奈川県", "愛知県", "福岡県"]
        cities = {
            "東京都": ["新宿区", "渋谷区", "港区", "千代田区"],
            "大阪府": ["大阪市", "堺市", "東大阪市"],
            "神奈川県": ["横浜市", "川崎市", "相模原市"],
            "愛知県": ["名古屋市", "豊田市", "岡崎市"],
            "福岡県": ["福岡市", "北九州市", "久留米市"]
        }
        
        prefecture = random.choice(prefectures)
        city = random.choice(cities[prefecture])
        
        base_data = {
            "annual_income": random.randint(2000000, 10000000),
            "prefecture": prefecture,
            "city": city,
            "tax_year": 2025
        }
        
        # kwargsで指定された値で上書き
        base_data.update(kwargs)
        
        # incomeパラメータがある場合はannual_incomeにマッピング
        if "income" in kwargs:
            base_data["annual_income"] = kwargs["income"]
        
        # municipalityパラメータがある場合はcityにマッピング
        if "municipality" in kwargs:
            base_data["city"] = kwargs["municipality"]
            
        return base_data
    
    @staticmethod
    def generate_multi_year_data(years: int = 5) -> List[Dict[str, Any]]:
        """複数年シミュレーション用テストデータ生成
        
        Args:
            years: シミュレーション年数
            
        Returns:
            複数年分のテストデータ
        """
        base_income = random.randint(4000000, 8000000)
        data_list = []
        
        for i in range(years):
            # 年収の変動（±10%）
            income_variation = random.uniform(0.9, 1.1)
            annual_income = int(base_income * income_variation)
            
            data_list.append({
                "annual_income": annual_income,
                "deductions": 480000,
                "dependents_count": random.randint(0, 3),
                "tax_year": 2025 + i
            })
        
        return data_list
    
    @staticmethod
    def generate_edge_case_data() -> List[Dict[str, Any]]:
        """境界値テスト用データ生成
        
        Returns:
            境界値テスト用のデータリスト
        """
        return [
            # 最小値
            {"annual_income": 0, "deductions": 0, "dependents_count": 0, "tax_year": 2020},
            # 最大値（現実的な範囲）
            {"annual_income": 100000000, "deductions": 5000000, "dependents_count": 10, "tax_year": 2025},
            # 税率境界値
            {"annual_income": 1950000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 3300000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 6950000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 9000000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 18000000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 40000000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
        ]
    
    @staticmethod
    def generate_invalid_data() -> List[Dict[str, Any]]:
        """無効データテスト用データ生成
        
        Returns:
            無効データのリスト
        """
        return [
            # 負の値
            {"annual_income": -1000000, "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 5000000, "deductions": -100000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 5000000, "deductions": 480000, "dependents_count": -1, "tax_year": 2025},
            # 無効な年度
            {"annual_income": 5000000, "deductions": 480000, "dependents_count": 0, "tax_year": 1999},
            {"annual_income": 5000000, "deductions": 480000, "dependents_count": 0, "tax_year": 2030},
            # 型エラー
            {"annual_income": "invalid", "deductions": 480000, "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 5000000, "deductions": "invalid", "dependents_count": 0, "tax_year": 2025},
            {"annual_income": 5000000, "deductions": 480000, "dependents_count": "invalid", "tax_year": 2025},
            {"annual_income": 5000000, "deductions": 480000, "dependents_count": 0, "tax_year": "invalid"},
        ]
    
    @staticmethod
    def generate_rag_search_data() -> List[Dict[str, Any]]:
        """RAG検索用テストデータ生成
        
        Returns:
            RAG検索用のテストデータ
        """
        search_queries = [
            {"query": "基礎控除", "category": "income_tax", "expected_results": 5},
            {"query": "法人税率", "category": "corporate_tax", "expected_results": 3},
            {"query": "消費税 軽減税率", "category": "consumption_tax", "expected_results": 4},
            {"query": "住民税 計算", "category": "resident_tax", "expected_results": 6},
            {"query": "扶養控除", "category": "income_tax", "expected_results": 4},
            {"query": "事業税", "category": "corporate_tax", "expected_results": 3},
            {"query": "医療費控除", "category": "income_tax", "expected_results": 5},
            {"query": "地方法人税", "category": "corporate_tax", "expected_results": 2},
        ]
        
        return search_queries
    
    @staticmethod
    def generate_performance_test_data(count: int = 100) -> List[Dict[str, Any]]:
        """パフォーマンステスト用データ生成
        
        Args:
            count: 生成するデータ数
            
        Returns:
            パフォーマンステスト用のデータリスト
        """
        data_list = []
        
        for _ in range(count):
            data_list.append({
                "annual_income": random.randint(2000000, 20000000),
                "deductions": random.randint(480000, 2000000),
                "dependents_count": random.randint(0, 5),
                "tax_year": random.choice([2023, 2024, 2025]),
                "prefecture": random.choice(["東京都", "大阪府", "神奈川県", "愛知県"]),
                "city": random.choice(["新宿区", "大阪市", "横浜市", "名古屋市"])
            })
        
        return data_list
    
    @staticmethod
    def generate_security_test_data() -> List[Dict[str, Any]]:
        """セキュリティテスト用データ生成
        
        Returns:
            セキュリティテスト用のデータリスト
        """
        return [
            # SQLインジェクション試行
            {"annual_income": "'; DROP TABLE users; --", "deductions": 480000},
            {"query": "基礎控除'; DROP TABLE documents; --"},
            # XSS試行
            {"annual_income": "<script>alert('xss')</script>", "deductions": 480000},
            {"query": "<script>alert('xss')</script>"},
            # 異常に長い文字列
            {"annual_income": "A" * 10000, "deductions": 480000},
            {"query": "B" * 5000},
            # 特殊文字
            {"annual_income": "../../../etc/passwd", "deductions": 480000},
            {"query": "../../../../etc/passwd"},
            # NULLバイト
            {"annual_income": "test\x00", "deductions": 480000},
            {"query": "test\x00"},
        ]


class MockDataProvider:
    """モックデータプロバイダー"""
    
    @staticmethod
    def get_mock_tax_rates() -> Dict[str, Any]:
        """モック税率データ取得
        
        Returns:
            モック税率データ
        """
        return {
            "income_tax_brackets": [
                {"min_income": 0, "max_income": 1950000, "rate": 0.05},
                {"min_income": 1950001, "max_income": 3300000, "rate": 0.10},
                {"min_income": 3300001, "max_income": 6950000, "rate": 0.20},
                {"min_income": 6950001, "max_income": 9000000, "rate": 0.23},
                {"min_income": 9000001, "max_income": 18000000, "rate": 0.33},
                {"min_income": 18000001, "max_income": 40000000, "rate": 0.40},
                {"min_income": 40000001, "max_income": None, "rate": 0.45}
            ],
            "corporate_tax_rates": {
                "small_company": 0.15,
                "large_company": 0.23,
                "local_corporate_tax": 0.104
            },
            "consumption_tax_rates": {
                "standard": 0.10,
                "reduced": 0.08
            },
            "basic_deduction": 480000
        }
    
    @staticmethod
    def get_mock_external_api_response() -> Dict[str, Any]:
        """モック外部APIレスポンス取得
        
        Returns:
            モック外部APIレスポンス
        """
        return {
            "status": "success",
            "data": {
                "documents": [
                    {
                        "title": "所得税法第1条",
                        "content": "所得税は、個人の所得に対して課される税金である。",
                        "url": "https://example.com/law1",
                        "last_updated": "2024-12-01"
                    },
                    {
                        "title": "基礎控除について",
                        "content": "基礎控除は、すべての納税者に適用される控除である。",
                        "url": "https://example.com/deduction",
                        "last_updated": "2024-11-15"
                    }
                ],
                "total_count": 2
            }
        }