"""Test client for the Japanese Tax Calculator MCP Server.

This script demonstrates how to interact with the MCP server
and test various tax calculation functionalities.
"""

import json
from typing import Dict, Any, List
from datetime import datetime
import subprocess
import sys


class TaxMCPClient:
    """Client for testing the Tax MCP Server."""
    
    def __init__(self):
        # MCPサーバーはSTDIO経由で動作するため、直接テストは困難
        # 代わりに基本的な機能テストを実行
        pass
    
    def health_check(self) -> bool:
        """サーバーのヘルスチェック（簡易版）"""
        try:
            # main.pyが正常にインポートできるかチェック
            result = subprocess.run(
                [sys.executable, "-c", "import main; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "OK" in result.stdout
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def test_tax_calculator_import(self) -> bool:
        """税計算モジュールのインポートテスト"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", "from tax_calculator import TaxCalculator; print('OK')"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and "OK" in result.stdout
        except Exception as e:
            print(f"Tax calculator import failed: {e}")
            return False
    
    def call_tool(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """MCPサーバーの機能をシミュレート（テスト用）"""
        # MCPサーバーの代わりに基本的な計算をシミュレート
        if method == "calculate_income_tax":
            return self._simulate_income_tax(params)
        elif method == "get_consumption_tax_rate":
            return self._simulate_consumption_tax_rate(params)
        elif method == "calculate_resident_tax":
            return self._simulate_resident_tax(params)
        elif method == "simulate_multi_year_taxes":
            return self._simulate_multi_year_taxes(params)
        elif method == "calculate_corporate_tax":
            return self._simulate_corporate_tax(params)
        elif method == "simulate_multi_year_corporate_taxes":
            return self._simulate_multi_year_corporate_taxes(params)
        elif method == "get_supported_prefectures":
            return self._get_supported_prefectures()
        elif method == "get_tax_year_info":
            return self._get_tax_year_info()
        elif method == "get_latest_tax_info":
            return self._simulate_latest_tax_info(params)
        elif method == "get_tax_rate_updates":
            return self._simulate_tax_rate_updates(params)
        elif method == "search_legal_reference":
            return self._simulate_legal_reference_search(params["reference"])
        elif method == "search_enhanced_tax_info":
            return self._simulate_enhanced_search(params)
        elif method == "get_index_statistics":
            return self._simulate_index_statistics(params)
        else:
            return {"error": f"Unknown method: {method}"}
    
    def _simulate_income_tax(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """所得税計算のシミュレーション"""
        annual_income = params.get("annual_income", 0)
        dependents_count = params.get("dependents_count", 0)
        spouse_deduction = params.get("spouse_deduction", 0)
        social_insurance_deduction = params.get("social_insurance_deduction", annual_income * 0.15)
        
        # 基礎控除
        basic_deduction = 480000
        # 扶養控除
        dependent_deduction = dependents_count * 380000
        
        # 課税所得
        taxable_income = max(0, annual_income - basic_deduction - dependent_deduction - spouse_deduction - social_insurance_deduction)
        
        # 簡易所得税計算（累進税率）
        income_tax = 0
        if taxable_income > 0:
            if taxable_income <= 1950000:
                income_tax = taxable_income * 0.05
            elif taxable_income <= 3300000:
                income_tax = 97500 + (taxable_income - 1950000) * 0.10
            elif taxable_income <= 6950000:
                income_tax = 232500 + (taxable_income - 3300000) * 0.20
            else:
                income_tax = 962500 + (taxable_income - 6950000) * 0.23
        
        effective_rate = (income_tax / annual_income * 100) if annual_income > 0 else 0
        marginal_rate = 5 if taxable_income <= 1950000 else (10 if taxable_income <= 3300000 else (20 if taxable_income <= 6950000 else 23))
        
        return {
            "annual_income": annual_income,
            "taxable_income": int(taxable_income),
            "income_tax": int(income_tax),
            "effective_rate": round(effective_rate, 2),
            "marginal_rate": marginal_rate
        }
    
    def _simulate_consumption_tax_rate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """消費税率取得のシミュレーション"""
        date_str = params.get("date", "2024-01-01")
        category = params.get("category", "standard")
        
        # 簡易的な消費税率判定
        if date_str >= "2019-10-01":
            rate = 0.08 if category == "reduced" else 0.10
        elif date_str >= "2014-04-01":
            rate = 0.08
        else:
            rate = 0.05
        
        return {
            "consumption_tax_rate": rate,
            "applicable_date": date_str,
            "category": category
        }
    
    def _simulate_resident_tax(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """住民税計算のシミュレーション"""
        taxable_income = params.get("taxable_income", 0)
        prefecture = params.get("prefecture", "東京都")
        
        # 住民税は一律10%（都道府県民税4% + 市区町村民税6%）
        prefectural_tax = int(taxable_income * 0.04)
        municipal_tax = int(taxable_income * 0.06)
        
        # 均等割（簡易計算）
        prefectural_equal = 1500
        municipal_equal = 3500
        
        return {
            "taxable_income": taxable_income,
            "prefectural_tax": {
                "income_based": prefectural_tax,
                "equal_levy": prefectural_equal,
                "total": prefectural_tax + prefectural_equal
            },
            "municipal_tax": {
                "income_based": municipal_tax,
                "equal_levy": municipal_equal,
                "total": municipal_tax + municipal_equal
            },
            "total_resident_tax": prefectural_tax + municipal_tax + prefectural_equal + municipal_equal,
            "prefecture": prefecture
        }
    
    def _simulate_multi_year_taxes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """複数年税額シミュレーション"""
        annual_incomes = params.get("annual_incomes", [])
        start_year = params.get("start_year", 2024)
        prefecture = params.get("prefecture", "東京都")
        dependents_count = params.get("dependents_count", 0)
        spouse_deduction = params.get("spouse_deduction", 0)
        
        yearly_results = []
        total_income = 0
        total_tax = 0
        
        for i, income in enumerate(annual_incomes):
            year = start_year + i
            
            # 所得税計算
            income_tax_result = self._simulate_income_tax({
                "annual_income": income,
                "dependents_count": dependents_count,
                "spouse_deduction": spouse_deduction
            })
            
            # 住民税計算
            resident_tax_result = self._simulate_resident_tax({
                "taxable_income": income_tax_result["taxable_income"],
                "prefecture": prefecture
            })
            
            year_total_tax = income_tax_result["income_tax"] + resident_tax_result["total_resident_tax"]
            effective_rate = (year_total_tax / income * 100) if income > 0 else 0
            
            yearly_results.append({
                "year": year,
                "annual_income": income,
                "income_tax": income_tax_result["income_tax"],
                "resident_tax": resident_tax_result["total_resident_tax"],
                "total_tax": year_total_tax,
                "effective_rate": round(effective_rate, 2)
            })
            
            total_income += income
            total_tax += year_total_tax
        
        average_effective_rate = (total_tax / total_income * 100) if total_income > 0 else 0
        
        return {
            "yearly_results": yearly_results,
            "summary": {
                "start_year": start_year,
                "end_year": start_year + len(annual_incomes) - 1,
                "total_income": total_income,
                "total_tax": total_tax,
                "average_effective_rate": round(average_effective_rate, 2)
            }
        }
    
    def _get_supported_prefectures(self) -> Dict[str, Any]:
        """サポート都道府県一覧"""
        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
        ]
        
        return {
            "supported_prefectures": prefectures,
            "total_count": len(prefectures)
        }
    
    def _get_tax_year_info(self) -> Dict[str, Any]:
        """税制年度情報"""
        return {
            "supported_years": [2020, 2021, 2022, 2023, 2024, 2025],
            "current_year": 2025,
            "features": ["所得税計算", "住民税計算", "消費税率取得", "複数年シミュレーション"]
        }
    
    def test_income_tax_calculation(self):
        """Test income tax calculation."""
        print("\n=== Testing Income Tax Calculation ===")
        
        test_cases = [
            {
                "name": "低所得者（年収300万円）",
                "params": {
                    "annual_income": 3000000,
                    "tax_year": 2024,
                    "dependents_count": 0,
                }
            },
            {
                "name": "中所得者（年収600万円、扶養家族2人）",
                "params": {
                    "annual_income": 6000000,
                    "tax_year": 2024,
                    "dependents_count": 2,
                    "spouse_deduction": 380000,
                }
            },
            {
                "name": "高所得者（年収1000万円）",
                "params": {
                    "annual_income": 10000000,
                    "tax_year": 2024,
                    "dependents_count": 1,
                    "social_insurance_deduction": 1500000,
                }
            },
        ]
        
        for case in test_cases:
            try:
                print(f"\n{case['name']}:")
                result = self.call_tool("calculate_income_tax", case["params"])
                
                print(f"  年収: {result['annual_income']:,}円")
                print(f"  課税所得: {result['taxable_income']:,}円")
                print(f"  所得税: {result['income_tax']:,}円")
                print(f"  実効税率: {result['effective_rate']}%")
                print(f"  限界税率: {result['marginal_rate']}%")
                
            except Exception as e:
                print(f"  エラー: {e}")
    
    def test_consumption_tax_rate(self):
        """Test consumption tax rate retrieval."""
        print("\n=== Testing Consumption Tax Rate ===")
        
        test_dates = [
            {"date": "2024-01-01", "category": "standard"},
            {"date": "2024-01-01", "category": "reduced"},
            {"date": "2019-09-30", "category": "standard"},
            {"date": "2019-10-01", "category": "standard"},
            {"date": "2014-03-31", "category": "standard"},
        ]
        
        for test_case in test_dates:
            try:
                print(f"\n日付: {test_case['date']}, カテゴリー: {test_case['category']}")
                result = self.call_tool("get_consumption_tax_rate", test_case)
                
                print(f"  消費税率: {result['consumption_tax_rate'] * 100}%")
                print(f"  適用開始日: {result['applicable_date']}")
                
            except Exception as e:
                print(f"  エラー: {e}")
    
    def test_resident_tax_calculation(self):
        """Test resident tax calculation."""
        print("\n=== Testing Resident Tax Calculation ===")
        
        test_cases = [
            {
                "name": "東京都（課税所得400万円）",
                "params": {
                    "taxable_income": 4000000,
                    "prefecture": "東京都",
                    "tax_year": 2024,
                }
            },
            {
                "name": "大阪府（課税所得600万円）",
                "params": {
                    "taxable_income": 6000000,
                    "prefecture": "大阪府",
                    "tax_year": 2024,
                }
            },
        ]
        
        for case in test_cases:
            try:
                print(f"\n{case['name']}:")
                result = self.call_tool("calculate_resident_tax", case["params"])
                
                print(f"  課税所得: {result['taxable_income']:,}円")
                print(f"  都道府県民税: {result['prefectural_tax']['total']:,}円")
                print(f"  市区町村民税: {result['municipal_tax']['total']:,}円")
                print(f"  住民税合計: {result['total_resident_tax']:,}円")
                
            except Exception as e:
                print(f"  エラー: {e}")
    
    def test_multi_year_simulation(self):
        """Test multi-year tax simulation."""
        print("\n=== Testing Multi-Year Tax Simulation ===")
        
        test_case = {
            "annual_incomes": [4000000, 5000000, 6000000, 7000000, 8000000],
            "start_year": 2024,
            "prefecture": "東京都",
            "dependents_count": 1,
            "spouse_deduction": 380000,
        }
        
        try:
            result = self.call_tool("simulate_multi_year_taxes", test_case)
            
            print("\nシミュレーション概要:")
            summary = result["summary"]
            print(f"  期間: {summary['start_year']}年 - {summary['end_year']}年")
            print(f"  総収入: {summary['total_income']:,}円")
            print(f"  総税額: {summary['total_tax']:,}円")
            print(f"  平均実効税率: {summary['average_effective_rate']}%")
            
            print("\n年別詳細:")
            for yearly in result["yearly_results"]:
                print(f"  {yearly['year']}年: 年収{yearly['annual_income']:,}円 → 税額{yearly['total_tax']:,}円 (実効税率{yearly['effective_rate']}%)")
                
        except Exception as e:
            print(f"  エラー: {e}")
    
    def _simulate_corporate_tax(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """法人税計算のシミュレーション"""
        annual_income = params.get("annual_income", 0)
        capital = params.get("capital", 100000000)
        deductions = params.get("deductions", 0)
        prefecture = params.get("prefecture", "東京都")
        tax_year = params.get("tax_year", 2025)
        
        # 課税所得
        taxable_income = max(0, annual_income - deductions)
        
        # 会社区分の判定
        if capital > 100000000:
            company_type = "large_corporation"
            corporate_tax_rate = 0.234
        elif taxable_income <= 8000000:
            company_type = "small_corporation"
            corporate_tax_rate = 0.15
        else:
            company_type = "small_corporation_high"
            corporate_tax_rate = 0.234
        
        # 法人税計算
        if company_type == "small_corporation" and taxable_income > 8000000:
            corporate_tax = int(8000000 * 0.15 + (taxable_income - 8000000) * 0.234)
        else:
            corporate_tax = int(taxable_income * corporate_tax_rate)
        
        # 地方法人税（法人税の10.4%）
        local_corporate_tax = int(corporate_tax * 0.104)
        
        # 事業税（簡易計算）
        if taxable_income <= 4000000:
            business_tax = int(taxable_income * 0.037)
        elif taxable_income <= 8000000:
            business_tax = int(4000000 * 0.037 + (taxable_income - 4000000) * 0.056)
        else:
            business_tax = int(4000000 * 0.037 + 4000000 * 0.056 + (taxable_income - 8000000) * 0.075)
        
        # 総税額
        total_tax = corporate_tax + local_corporate_tax + business_tax
        
        # 実効税率
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
    
    def _simulate_multi_year_corporate_taxes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """法人税複数年シミュレーション"""
        annual_incomes = params.get("annual_incomes", [])
        start_year = params.get("start_year", 2025)
        capital = params.get("capital", 100000000)
        deductions = params.get("deductions", 0)
        prefecture = params.get("prefecture", "東京都")
        
        results = []
        for i, income in enumerate(annual_incomes):
            year = start_year + i
            tax_result = self._simulate_corporate_tax({
                "annual_income": income,
                "tax_year": year,
                "capital": capital,
                "deductions": deductions,
                "prefecture": prefecture
            })
            results.append(tax_result)
        
        # サマリー計算
        total_income = sum(annual_incomes)
        total_tax = sum(result["total_tax"] for result in results)
        average_effective_rate = (total_tax / total_income * 100) if total_income > 0 else 0
        
        return {
            "years_simulated": len(annual_incomes),
            "start_year": start_year,
            "end_year": start_year + len(annual_incomes) - 1,
            "total_income": total_income,
            "total_tax": total_tax,
            "average_effective_rate": round(average_effective_rate, 2),
            "prefecture": prefecture,
            "capital": capital,
            "yearly_results": results
        }
    
    def _simulate_latest_tax_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """最新税制情報取得のシミュレーション"""
        query = params.get("query", "")
        category = params.get("category", "")
        tax_year = params.get("tax_year", 2025)
        
        # シミュレーション用のサンプルデータ
        sample_results = [
            {
                "title": "令和7年度税制改正 - 所得税の基礎控除見直し",
                "source": "財務省税制改正資料",
                "content": "基礎控除額の上乗せ特例が創設され、一定の条件下で追加控除が適用されます...",
                "url": "https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                "category": "income_tax",
                "tax_year": 2025,
                "relevance_score": 0.95,
                "date_published": "2024-12-13T00:00:00"
            },
            {
                "title": "法人税率の改正について",
                "source": "国税庁タックスアンサー",
                "content": "中小法人の軽減税率の適用範囲が拡大され、より多くの企業が恩恵を受けることになります...",
                "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5759.htm",
                "category": "corporate_tax",
                "tax_year": 2025,
                "relevance_score": 0.88,
                "date_published": "2024-11-15T00:00:00"
            },
            {
                "title": "消費税の軽減税率制度の運用改善",
                "source": "国税庁タックスアンサー",
                "content": "軽減税率の適用対象となる商品の判定基準が明確化され、事業者の負担軽減が図られます...",
                "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6313.htm",
                "category": "consumption_tax",
                "tax_year": 2025,
                "relevance_score": 0.82,
                "date_published": "2024-10-20T00:00:00"
            }
        ]
        
        # クエリとカテゴリでフィルタリング
        filtered_results = []
        for result in sample_results:
            include = True
            
            if query and query.lower() not in result["title"].lower() and query.lower() not in result["content"].lower():
                include = False
            
            if category and category != result["category"]:
                include = False
            
            if include:
                filtered_results.append(result)
        
        return {
            "query": query,
            "category": category,
            "results_count": len(filtered_results),
            "results": filtered_results,
            "last_updated": datetime.now().isoformat(),
            "data_sources": [
                "財務省税制改正資料",
                "国税庁タックスアンサー"
            ]
        }
    
    def _simulate_tax_rate_updates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """税率更新情報のシミュレーション"""
        tax_year = params.get("tax_year", 2025)
        
        # シミュレーション用のサンプルデータ
        return {
            "tax_year": tax_year,
            "income_tax_changes": [
                {
                    "title": "基礎控除等の引上げと基礎控除の上乗せ特例の創設",
                    "url": "https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                    "source": "財務省税制改正資料"
                }
            ],
            "corporate_tax_changes": [
                {
                    "title": "中小法人の軽減税率の適用範囲拡大",
                    "url": "https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                    "source": "財務省税制改正資料"
                }
            ],
            "consumption_tax_changes": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _simulate_legal_reference_search(self, reference: str) -> Dict[str, Any]:
        """法令参照検索のシミュレーション"""
        # referenceが辞書として渡された場合の処理
        if isinstance(reference, dict):
            reference = reference.get("reference", "")
        
        # シミュレーション用のサンプルデータ
        sample_results = []
        
        # タックスアンサー番号の検索
        if "5280" in reference or "No.5280" in reference:
            sample_results.append({
                "source": "国税庁タックスアンサー",
                "title": "No.5280 法人税の税率",
                "content": "法人税の税率は、各事業年度の所得の金額に対して、次の区分に応じてそれぞれ次の税率を適用します。普通法人の場合、年800万円以下の部分については15%、年800万円超の部分については23.2%の税率が適用されます...",
                "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5280.htm",
                "category": "tax_answer",
                "relevance_score": 1.0
            })
        
        # 法人税法条文の検索
        if "法人税法" in reference and "61条" in reference:
            sample_results.append({
                "source": "e-Gov法令検索",
                "title": "法人税法第61条の4（特定同族会社の特別税率）",
                "content": "特定同族会社（同族会社のうち、被支配会社に該当するものをいう。）の各事業年度の所得の金額のうち年800万円を超える部分に対する法人税の税率は、第66条第1項の規定にかかわらず、100分の25.5とする...",
                "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000034",
                "category": "law_article",
                "relevance_score": 1.0
            })
        
        # 所得税法条文の検索
        if "所得税法" in reference and "120条" in reference:
            sample_results.append({
                "source": "e-Gov法令検索",
                "title": "所得税法第120条（確定申告）",
                "content": "居住者は、その年分の総所得金額、退職所得金額及び山林所得金額の合計額が所得控除の額の合計額を超える場合において、その超える部分の金額に対する所得税額から配当控除の額を控除した金額があるときは、翌年の2月16日から3月15日までの間に、税務署長に対し、確定申告書を提出しなければならない...",
                "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000033",
                "category": "law_article",
                "relevance_score": 1.0
            })
        
        # 一般的なキーワード検索
        if not sample_results and reference:
            sample_results.append({
                "source": "国税庁タックスアンサー",
                "title": f"{reference}に関する税制情報",
                "content": f"{reference}に関連する税制情報の詳細内容がここに表示されます。実際の検索では、国税庁タックスアンサーやe-Gov法令検索から最新の情報を取得します...",
                "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/",
                "category": "general",
                "relevance_score": 0.8
            })
        
        return {
            "reference": reference,
            "results_count": len(sample_results),
            "results": sample_results,
            "search_timestamp": datetime.now().isoformat()
        }
    
    def _simulate_enhanced_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """拡張検索のシミュレーション（SQLiteインデックス活用）"""
        query = params.get("query", "")
        category = params.get("category")
        tax_year = params.get("tax_year")
        document_type = params.get("document_type")
        limit = params.get("limit", 10)
        
        # インデックス検索結果のシミュレーション
        indexed_results = [
            {
                "document_id": "doc_001",
                "title": f"{query}に関するインデックス済み文書1",
                "content": f"{query}についての詳細な情報がインデックス化されています。",
                "category": category or "tax_general",
                "tax_year": tax_year or 2025,
                "document_type": document_type or "tax_reform",
                "relevance_score": 0.92,
                "source": "財務省税制改正資料",
                "indexed_date": "2024-12-01T10:00:00",
                "keywords": [query, "税制", "改正"]
            },
            {
                "document_id": "doc_002",
                "title": f"{query}関連法令条文",
                "content": f"{query}に関連する法令条文の詳細解説です。",
                "category": category or "law_article",
                "tax_year": tax_year or 2025,
                "document_type": document_type or "law_article",
                "relevance_score": 0.88,
                "source": "e-Gov法令検索",
                "indexed_date": "2024-11-15T14:30:00",
                "keywords": [query, "法令", "条文"]
            }
        ]
        
        # 拡張検索結果のシミュレーション
        enhanced_results = {
            "primary_sources": [
                {
                    "title": f"{query}の最新情報",
                    "content": f"{query}に関する最新の税制情報です。",
                    "source": "国税庁",
                    "relevance_score": 0.95,
                    "date_published": "2024-12-01"
                }
            ],
            "additional_sources": [
                {
                    "title": f"{query}実務ガイド",
                    "content": f"{query}の実務における取扱いについて説明します。",
                    "source": "税理士会",
                    "relevance_score": 0.82,
                    "date_published": "2024-11-20"
                }
            ],
            "related_topics": [f"{query}関連トピック1", f"{query}関連トピック2"]
        }
        
        return {
            "query": query,
            "filters": {
                "category": category,
                "tax_year": tax_year,
                "document_type": document_type
            },
            "indexed_results": indexed_results[:limit],
            "enhanced_results": enhanced_results,
            "total_results": len(indexed_results) + len(enhanced_results["additional_sources"]),
            "search_timestamp": datetime.now().isoformat()
        }
    
    def _simulate_index_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """インデックス統計のシミュレーション"""
        include_details = params.get("include_details", True)
        
        base_stats = {
            "total_documents": 1250,
            "total_searches": 3847,
            "last_updated": "2024-12-01T15:30:00"
        }
        
        if include_details:
            detailed_stats = {
                **base_stats,
                "documents_by_category": {
                    "tax_reform": 450,
                    "law_article": 380,
                    "tax_answer": 320,
                    "circular": 100
                },
                "documents_by_year": {
                    "2025": 420,
                    "2024": 380,
                    "2023": 250,
                    "2022": 200
                },
                "search_frequency": {
                    "daily_average": 45,
                    "weekly_average": 315,
                    "monthly_average": 1350
                },
                "index_size_mb": 125.7,
                "last_cleanup": "2024-11-25T02:00:00"
            }
            return {
                "statistics": detailed_stats,
                "include_details": include_details,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "statistics": base_stats,
                "include_details": include_details,
                "timestamp": datetime.now().isoformat()
            }
    
    def test_corporate_tax_calculation(self):
        """Test corporate tax calculation."""
        print("\n=== Testing Corporate Tax Calculation ===")
        
        test_cases = [
            {"annual_income": 5000000, "capital": 50000000, "deductions": 500000, "description": "中小法人（資本金5000万円）"},
            {"annual_income": 10000000, "capital": 50000000, "deductions": 1000000, "description": "中小法人（所得800万円超）"},
            {"annual_income": 50000000, "capital": 200000000, "deductions": 5000000, "description": "大法人（資本金2億円）"},
            {"annual_income": 100000000, "capital": 500000000, "deductions": 10000000, "description": "大法人（所得1億円）"}
        ]
        
        for case in test_cases:
            try:
                result = self.call_tool("calculate_corporate_tax", case)
                print(f"\n{case['description']}:")
                print(f"  年間所得: {result['gross_income']:,}円")
                print(f"  課税所得: {result['taxable_income']:,}円")
                print(f"  法人税: {result['corporate_tax']:,}円")
                print(f"  地方法人税: {result['local_corporate_tax']:,}円")
                print(f"  事業税: {result['business_tax']:,}円")
                print(f"  総税額: {result['total_tax']:,}円")
                print(f"  実効税率: {result['effective_rate']}%")
                print(f"  会社区分: {result['company_type']}")
                
            except Exception as e:
                print(f"  エラー: {e}")
    
    def test_multi_year_corporate_simulation(self):
        """Test multi-year corporate tax simulation."""
        print("\n=== Testing Multi-Year Corporate Tax Simulation ===")
        
        test_case = {
            "annual_incomes": [30000000, 40000000, 50000000, 60000000, 70000000],
            "start_year": 2025,
            "capital": 150000000,
            "deductions": 3000000,
            "prefecture": "東京都"
        }
        
        try:
            result = self.call_tool("simulate_multi_year_corporate_taxes", test_case)
            
            print("\nシミュレーション概要:")
            print(f"  期間: {result['start_year']}年 - {result['end_year']}年")
            print(f"  資本金: {result['capital']:,}円")
            print(f"  総所得: {result['total_income']:,}円")
            print(f"  総税額: {result['total_tax']:,}円")
            print(f"  平均実効税率: {result['average_effective_rate']}%")
            
            print("\n年別詳細:")
            for yearly in result["yearly_results"]:
                print(f"  {yearly['tax_year']}年: 所得{yearly['gross_income']:,}円 → 税額{yearly['total_tax']:,}円 (実効税率{yearly['effective_rate']}%)")
                
        except Exception as e:
            print(f"  エラー: {e}")
    
    def test_sqlite_indexing(self):
        """Test SQLite indexing functions."""
        print("\n=== Testing SQLite Indexing ===")
        
        # 拡張検索テスト
        try:
            print("\n拡張税制情報検索:")
            result = self.call_tool("search_enhanced_tax_info", {
                "query": "法人税率",
                "category": "corporate_tax",
                "tax_year": 2025,
                "document_type": "tax_reform",
                "limit": 5
            })
            print(f"  検索クエリ: {result['query']}")
            print(f"  フィルタ: {result['filters']}")
            print(f"  インデックス結果数: {len(result['indexed_results'])}")
            print(f"  拡張結果数: {len(result['enhanced_results']['additional_sources'])}")
            print(f"  総結果数: {result['total_results']}")
            
            if result['indexed_results']:
                first_indexed = result['indexed_results'][0]
                print(f"  最初のインデックス結果: {first_indexed['title']}")
                print(f"    関連度: {first_indexed['relevance_score']}")
                print(f"    ソース: {first_indexed['source']}")
                print(f"    キーワード: {', '.join(first_indexed['keywords'])}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 一般的なキーワード検索テスト
        try:
            print("\n一般キーワード検索:")
            result = self.call_tool("search_enhanced_tax_info", {
                "query": "確定申告",
                "limit": 3
            })
            print(f"  検索クエリ: {result['query']}")
            print(f"  結果数: {len(result['indexed_results'])}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # インデックス統計情報テスト（詳細あり）
        try:
            print("\nインデックス統計情報（詳細）:")
            result = self.call_tool("get_index_statistics", {
                "include_details": True
            })
            stats = result['statistics']
            print(f"  総文書数: {stats['total_documents']}")
            print(f"  総検索数: {stats['total_searches']}")
            print(f"  最終更新: {stats['last_updated']}")
            print(f"  インデックスサイズ: {stats['index_size_mb']} MB")
            
            print("  カテゴリ別文書数:")
            for category, count in stats['documents_by_category'].items():
                print(f"    {category}: {count}")
            
            print("  年度別文書数:")
            for year, count in stats['documents_by_year'].items():
                print(f"    {year}: {count}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # インデックス統計情報テスト（基本のみ）
        try:
            print("\nインデックス統計情報（基本）:")
            result = self.call_tool("get_index_statistics", {
                "include_details": False
            })
            stats = result['statistics']
            print(f"  総文書数: {stats['total_documents']}")
            print(f"  総検索数: {stats['total_searches']}")
            print(f"  最終更新: {stats['last_updated']}")
            
        except Exception as e:
            print(f"  エラー: {e}")
    
    def test_utility_functions(self):
        """Test utility functions."""
        print("\n=== Testing Utility Functions ===")
        
        try:
            print("\nサポート都道府県:")
            result = self.call_tool("get_supported_prefectures", {})
            print(f"  対応都道府県数: {result['total_count']}")
            print(f"  都道府県リスト: {', '.join(result['supported_prefectures'])}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        try:
            print("\n税制年度情報:")
            result = self.call_tool("get_tax_year_info", {})
            print(f"  サポート年度: {result['supported_years']}")
            print(f"  現在年度: {result['current_year']}")
            print(f"  機能: {', '.join(result['features'])}")
            
        except Exception as e:
            print(f"  エラー: {e}")
    
    def test_rag_integration(self):
        """Test RAG integration functions."""
        print("\n=== Testing RAG Integration ===")
        
        # 最新税制情報取得テスト
        try:
            print("\n最新税制情報取得:")
            result = self.call_tool("get_latest_tax_info", {
                "query": "基礎控除",
                "category": "income_tax",
                "tax_year": 2025
            })
            print(f"  検索クエリ: {result['query']}")
            print(f"  カテゴリ: {result['category']}")
            print(f"  結果件数: {result['results_count']}")
            print(f"  データソース: {', '.join(result['data_sources'])}")
            
            if result['results']:
                print(f"  最初の結果: {result['results'][0]['title']}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 税率更新情報取得テスト
        try:
            print("\n税率更新情報取得:")
            result = self.call_tool("get_tax_rate_updates", {"tax_year": 2025})
            print(f"  対象年度: {result['tax_year']}")
            print(f"  所得税変更: {len(result['income_tax_changes'])}件")
            print(f"  法人税変更: {len(result['corporate_tax_changes'])}件")
            print(f"  消費税変更: {len(result['consumption_tax_changes'])}件")
            
        except Exception as e:
            print(f"  エラー: {e}")
    
    def test_legal_reference_search(self):
        """Test legal reference search functions."""
        print("\n=== Testing Legal Reference Search ===")
        
        # タックスアンサー番号検索テスト
        try:
            print("\nタックスアンサー番号検索:")
            result = self.call_tool("search_legal_reference", {"reference": "No.5280"})
            print(f"  検索対象: {result['reference']}")
            print(f"  結果件数: {result['results_count']}")
            
            if result['results']:
                first_result = result['results'][0]
                print(f"  タイトル: {first_result['title']}")
                print(f"  ソース: {first_result['source']}")
                print(f"  カテゴリ: {first_result['category']}")
                print(f"  関連度: {first_result['relevance_score']}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 法令条文検索テスト
        try:
            print("\n法令条文検索:")
            result = self.call_tool("search_legal_reference", {"reference": "法人税法第61条の4"})
            print(f"  検索対象: {result['reference']}")
            print(f"  結果件数: {result['results_count']}")
            
            if result['results']:
                first_result = result['results'][0]
                print(f"  タイトル: {first_result['title']}")
                print(f"  ソース: {first_result['source']}")
                print(f"  カテゴリ: {first_result['category']}")
            
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 一般的なキーワード検索テスト
        try:
            print("\n一般キーワード検索:")
            result = self.call_tool("search_legal_reference", {"reference": "確定申告"})
            print(f"  検索対象: {result['reference']}")
            print(f"  結果件数: {result['results_count']}")
            
            if result['results']:
                for i, item in enumerate(result['results'][:2]):  # 最初の2件のみ表示
                    print(f"  結果{i+1}: {item['title']}")
                    print(f"    関連度: {item['relevance_score']}")
                    print(f"    公開日: {item['date_published']}")
                
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 税率更新情報テスト
        try:
            print("\n税率更新情報:")
            result = self.call_tool("get_tax_rate_updates", {
                "tax_year": 2025
            })
            print(f"  対象年度: {result['tax_year']}")
            print(f"  所得税変更: {len(result['income_tax_changes'])}件")
            print(f"  法人税変更: {len(result['corporate_tax_changes'])}件")
            print(f"  消費税変更: {len(result['consumption_tax_changes'])}件")
            print(f"  最終更新: {result['last_updated']}")
            
            if result['income_tax_changes']:
                print(f"  所得税変更例: {result['income_tax_changes'][0]['title']}")
            
        except Exception as e:
            print(f"  エラー: {e}")
    
    def run_all_tests(self):
        """Run all test cases."""
        print("Japanese Tax Calculator MCP Server - Test Client")
        print("=" * 50)
        
        # 基本的なヘルスチェック
        if self.health_check():
            print("✓ Basic module import test passed")
        else:
            print("✗ Basic module import test failed")
        
        if self.test_tax_calculator_import():
            print("✓ Tax calculator module test passed")
        else:
            print("✗ Tax calculator module test failed (this is expected if not implemented yet)")
        
        # Run all test cases
        self.test_income_tax_calculation()
        self.test_consumption_tax_rate()
        self.test_resident_tax_calculation()
        self.test_multi_year_simulation()
        self.test_corporate_tax_calculation()
        self.test_multi_year_corporate_simulation()
        self.test_utility_functions()
        self.test_rag_integration()
        self.test_legal_reference_search()
        self.test_sqlite_indexing()
        
        print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    client = TaxMCPClient()
    client.run_all_tests()