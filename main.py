"""Japanese Tax Calculator MCP Server.

This server provides tax calculation tools for Japanese tax system
including income tax, consumption tax, and resident tax calculations.
"""

import logging
import structlog
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastmcp import FastMCP
from pydantic import BaseModel, Field

from config import settings
from tax_calculator import tax_calculator, corporate_tax_calculator
from security import security_manager, audit_logger, validate_and_sanitize
from rag_integration import rag_integration


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# Initialize FastMCP server
app = FastMCP(settings.server_name)


# FastMCPはHTTPエンドポイントをサポートしていないため、ヘルスチェックは削除


# Pydantic models for request validation
class IncomeDetails(BaseModel):
    """Income and deduction details for tax calculation."""
    annual_income: int = Field(..., ge=0, description="年収（円）")
    basic_deduction: int = Field(default=480000, ge=0, description="基礎控除（円）")
    employment_income_deduction: Optional[int] = Field(default=None, ge=0, description="給与所得控除（円）")
    dependents_count: int = Field(default=0, ge=0, description="扶養家族数")
    spouse_deduction: int = Field(default=0, ge=0, description="配偶者控除（円）")
    social_insurance_deduction: int = Field(default=0, ge=0, description="社会保険料控除（円）")
    life_insurance_deduction: int = Field(default=0, ge=0, description="生命保険料控除（円）")
    earthquake_insurance_deduction: int = Field(default=0, ge=0, description="地震保険料控除（円）")
    medical_expense_deduction: int = Field(default=0, ge=0, description="医療費控除（円）")
    donation_deduction: int = Field(default=0, ge=0, description="寄附金控除（円）")


class MultiYearIncomeRequest(BaseModel):
    """Multi-year income simulation request."""
    annual_incomes: List[int] = Field(..., min_items=1, max_items=10, description="年収リスト（円）")
    start_year: int = Field(default=2024, ge=2020, le=2030, description="開始年度")
    prefecture: str = Field(default="東京都", description="都道府県")
    dependents_count: int = Field(default=0, ge=0, description="扶養家族数")
    spouse_deduction: int = Field(default=0, ge=0, description="配偶者控除（円）")


class CorporateIncomeDetails(BaseModel):
    """Corporate income and deduction details for tax calculation."""
    annual_income: int = Field(..., ge=0, description="年間所得（円）")
    capital: int = Field(default=100000000, ge=1000000, description="資本金（円）")
    deductions: int = Field(default=0, ge=0, description="各種控除の合計（円）")


class MultiYearCorporateIncomeRequest(BaseModel):
    """Multi-year corporate income simulation request."""
    annual_incomes: List[int] = Field(..., min_items=1, max_items=10, description="年間所得リスト（円）")
    start_year: int = Field(default=2025, ge=2020, le=2030, description="開始年度")
    prefecture: str = Field(default="東京都", description="都道府県")
    capital: int = Field(default=100000000, ge=1000000, description="資本金（円）")
    deductions: int = Field(default=0, ge=0, description="各種控除の合計（円）")


class TaxInfoRequest(BaseModel):
    """Tax information search request."""
    query: str = Field(
        description="Search query for tax information",
        default=""
    )
    category: str = Field(
        description="Tax category filter (income_tax, corporate_tax, consumption_tax, etc.)",
        default=""
    )
    tax_year: int = Field(
        description="Target tax year",
        default=2025,
        ge=2020,
        le=2030
    )


class LegalReferenceRequest(BaseModel):
    """Legal reference search request."""
    reference: str = Field(
        description="Legal reference to search (e.g., '法人税法第61条の4', 'No.5280', 'タックスアンサー 5280')"
    )


class EnhancedSearchRequest(BaseModel):
    """拡張検索リクエスト（SQLiteインデックス活用）"""
    query: str = Field(description="検索クエリ")
    category: Optional[str] = Field(default=None, description="税制カテゴリ（income_tax, corporate_tax, consumption_tax等）")
    tax_year: Optional[int] = Field(default=None, ge=2020, le=2030, description="対象年度")
    document_type: Optional[str] = Field(default=None, description="文書タイプ（tax_reform, law_article, tax_answer等）")
    limit: int = Field(default=10, ge=1, le=50, description="最大結果数")


class IndexStatsRequest(BaseModel):
    """インデックス統計情報リクエスト"""
    include_details: bool = Field(default=True, description="詳細統計を含むかどうか")


@app.tool(
    name="calculate_income_tax",
    description="年収、控除、家族構成に基づいて日本の所得税を計算します。給与所得控除は自動計算されますが、手動で指定することも可能です。",
)
@validate_and_sanitize(['annual_income'])
def calculate_income_tax(
    annual_income: int = Field(..., ge=0, description="年収（円）"),
    tax_year: int = Field(default=2025, ge=2020, le=2025, description="課税年度"),
    basic_deduction: int = Field(default=480000, ge=0, description="基礎控除（円）"),
    employment_income_deduction: Optional[int] = Field(default=None, ge=0, description="給与所得控除（円）。未指定の場合は自動計算"),
    dependents_count: int = Field(default=0, ge=0, le=20, description="扶養家族数"),
    spouse_deduction: int = Field(default=0, ge=0, description="配偶者控除（円）"),
    social_insurance_deduction: int = Field(default=0, ge=0, description="社会保険料控除（円）"),
    life_insurance_deduction: int = Field(default=0, ge=0, le=120000, description="生命保険料控除（円）"),
    earthquake_insurance_deduction: int = Field(default=0, ge=0, le=50000, description="地震保険料控除（円）"),
    medical_expense_deduction: int = Field(default=0, ge=0, description="医療費控除（円）"),
    donation_deduction: int = Field(default=0, ge=0, description="寄附金控除（円）"),
) -> Dict[str, Any]:
    """Calculate Japanese income tax based on income and deductions."""
    
    logger.info(
        "Income tax calculation requested",
        annual_income=annual_income,
        tax_year=tax_year,
        dependents_count=dependents_count,
    )
    
    try:
        # 監査ログ記録
        params = {
            'annual_income': annual_income,
            'tax_year': tax_year,
            'basic_deduction': basic_deduction,
            'employment_income_deduction': employment_income_deduction,
            'dependents_count': dependents_count,
            'spouse_deduction': spouse_deduction,
            'social_insurance_deduction': social_insurance_deduction,
            'life_insurance_deduction': life_insurance_deduction,
            'earthquake_insurance_deduction': earthquake_insurance_deduction,
            'medical_expense_deduction': medical_expense_deduction,
            'donation_deduction': donation_deduction
        }
        
        result = tax_calculator.calculate_income_tax(
            annual_income=annual_income,
            tax_year=tax_year,
            basic_deduction=basic_deduction,
            employment_income_deduction=employment_income_deduction,
            dependents_count=dependents_count,
            spouse_deduction=spouse_deduction,
            social_insurance_deduction=social_insurance_deduction,
            life_insurance_deduction=life_insurance_deduction,
            earthquake_insurance_deduction=earthquake_insurance_deduction,
            medical_expense_deduction=medical_expense_deduction,
            donation_deduction=donation_deduction,
        )
        
        audit_logger.log_api_call('calculate_income_tax', params, success=True)
        logger.info(
            "Income tax calculation completed",
            calculated_tax=result["income_tax"],
            effective_rate=result["effective_rate"],
        )
        
        return result
        
    except Exception as e:
        audit_logger.log_api_call('calculate_income_tax', params, success=False)
        logger.error("Income tax calculation failed", error=str(e))
        raise


@app.tool(
    name="get_consumption_tax_rate",
    description="指定された日付と商品カテゴリーに基づいて消費税率を取得します。標準税率と軽減税率に対応しています。",
)
@validate_and_sanitize(['date'])
def get_consumption_tax_rate(
    date: str = Field(..., description="税率を取得する日付（YYYY-MM-DD形式）"),
    category: str = Field(default="standard", description="税率カテゴリー（standard: 標準税率, reduced: 軽減税率）"),
) -> Dict[str, Any]:
    """Get consumption tax rate for a specific date and category."""
    
    logger.info(
        "Consumption tax rate requested",
        date=date,
        category=category,
    )
    
    try:
        # Validate category
        if category not in ["standard", "reduced"]:
            raise ValueError(f"Invalid category: {category}. Must be 'standard' or 'reduced'.")
        
        result = tax_calculator.get_consumption_tax_rate(date, category)
        
        logger.info(
            "Consumption tax rate retrieved",
            rate=result["consumption_tax_rate"],
            applicable_date=result["applicable_date"],
        )
        
        return result
        
    except Exception as e:
        logger.error("Consumption tax rate retrieval failed", error=str(e))
        raise


@app.tool(
    name="calculate_resident_tax",
    description="課税所得と都道府県に基づいて住民税を計算します。所得割と均等割の両方を含みます。",
)
@validate_and_sanitize(['taxable_income'])
def calculate_resident_tax(
    taxable_income: int = Field(..., ge=0, description="課税所得（円）"),
    prefecture: str = Field(default="東京都", description="都道府県名"),
    tax_year: int = Field(default=2025, ge=2020, le=2025, description="課税年度"),
) -> Dict[str, Any]:
    """Calculate resident tax based on taxable income and prefecture."""
    
    logger.info(
        "Resident tax calculation requested",
        taxable_income=taxable_income,
        prefecture=prefecture,
        tax_year=tax_year,
    )
    
    try:
        result = tax_calculator.calculate_resident_tax(
            taxable_income=taxable_income,
            prefecture=prefecture,
            tax_year=tax_year,
        )
        
        logger.info(
            "Resident tax calculation completed",
            total_tax=result["total_resident_tax"],
            prefecture=prefecture,
        )
        
        return result
        
    except Exception as e:
        logger.error("Resident tax calculation failed", error=str(e))
        raise


@app.tool(
    name="simulate_multi_year_taxes",
    description="複数年にわたる税額シミュレーションを実行します。年収の変化に応じた所得税と住民税の推移を計算できます。",
)
@validate_and_sanitize(['annual_incomes', 'start_year'])
def simulate_multi_year_taxes(
    annual_incomes: List[int] = Field(..., min_items=1, max_items=10, description="年収リスト（円）。最大10年分まで指定可能"),
    start_year: int = Field(default=2024, ge=2020, le=2030, description="シミュレーション開始年度"),
    prefecture: str = Field(default="東京都", description="都道府県名"),
    dependents_count: int = Field(default=0, ge=0, le=20, description="扶養家族数"),
    spouse_deduction: int = Field(default=0, ge=0, description="配偶者控除（円）"),
) -> Dict[str, Any]:
    """Simulate taxes for multiple years with varying incomes."""
    
    logger.info(
        "Multi-year tax simulation requested",
        years_count=len(annual_incomes),
        start_year=start_year,
        prefecture=prefecture,
    )
    
    try:
        # Validate that we don't exceed supported years
        end_year = start_year + len(annual_incomes) - 1
        if end_year > 2024:
            logger.warning(
                "Some years in simulation exceed supported range",
                end_year=end_year,
                max_supported=2024,
            )
        
        results = tax_calculator.simulate_multi_year_taxes(
            annual_incomes=annual_incomes,
            start_year=start_year,
            prefecture=prefecture,
            dependents_count=dependents_count,
            spouse_deduction=spouse_deduction,
        )
        
        # Calculate summary statistics
        total_income = sum(result["annual_income"] for result in results)
        total_tax = sum(result["total_tax"] for result in results)
        average_effective_rate = sum(result["effective_rate"] for result in results) / len(results)
        
        summary = {
            "simulation_years": len(annual_incomes),
            "start_year": start_year,
            "end_year": start_year + len(annual_incomes) - 1,
            "total_income": total_income,
            "total_tax": total_tax,
            "average_effective_rate": round(average_effective_rate, 2),
            "prefecture": prefecture,
        }
        
        logger.info(
            "Multi-year tax simulation completed",
            total_income=total_income,
            total_tax=total_tax,
            average_effective_rate=average_effective_rate,
        )
        
        return {
            "summary": summary,
            "yearly_results": results,
        }
        
    except Exception as e:
        logger.error("Multi-year tax simulation failed", error=str(e))
        raise


@app.tool(
    name="get_supported_prefectures",
    description="サポートされている都道府県のリストを取得します。住民税計算で使用可能な都道府県名を確認できます。",
)
def get_supported_prefectures() -> Dict[str, Any]:
    """Get list of supported prefectures for tax calculations."""
    
    logger.info("Supported prefectures list requested")
    
    # List of major prefectures supported
    supported_prefectures = [
        "東京都", "大阪府", "神奈川県", "愛知県", "埼玉県",
        "千葉県", "兵庫県", "北海道", "福岡県", "静岡県"
    ]
    
    return {
        "supported_prefectures": supported_prefectures,
        "total_count": len(supported_prefectures),
        "note": "その他の都道府県も標準税率で計算可能です",
    }


@app.tool(
    name="calculate_corporate_tax",
    description="法人の年間所得、資本金、控除に基づいて日本の法人税（法人税、地方法人税、事業税）を計算します。",
)
@validate_and_sanitize(['annual_income', 'capital'])
def calculate_corporate_tax(
    annual_income: int = Field(..., ge=0, description="年間所得（円）"),
    tax_year: int = Field(default=2025, ge=2020, le=2025, description="課税年度"),
    prefecture: str = Field(default="東京都", description="都道府県"),
    capital: int = Field(default=100000000, ge=1000000, description="資本金（円）"),
    deductions: int = Field(default=0, ge=0, description="各種控除の合計（円）"),
) -> Dict[str, Any]:
    """Calculate Japanese corporate tax based on income, capital, and deductions."""
    
    logger.info(
        "Corporate tax calculation requested",
        annual_income=annual_income,
        tax_year=tax_year,
        prefecture=prefecture,
        capital=capital,
    )
    
    try:
        # 監査ログ記録
        audit_logger.log_calculation_request(
            calculation_type="corporate_tax",
            parameters={
                "annual_income": annual_income,
                "tax_year": tax_year,
                "prefecture": prefecture,
                "capital": capital,
                "deductions": deductions,
            },
        )
        
        # 法人税計算実行
        result = corporate_tax_calculator.calculate_corporate_tax(
            annual_income=annual_income,
            tax_year=tax_year,
            prefecture=prefecture,
            capital=capital,
            deductions=deductions,
        )
        
        logger.info(
            "Corporate tax calculation completed",
            total_tax=result["total_tax"],
            effective_rate=result["effective_rate"],
        )
        
        return result
        
    except Exception as e:
        logger.error("Corporate tax calculation failed", error=str(e))
        raise


@app.tool(
    name="simulate_multi_year_corporate_taxes",
    description="複数年にわたる法人税のシミュレーションを実行します。年間所得の変化に応じた税負担の推移を分析できます。",
)
@validate_and_sanitize(['annual_incomes'])
def simulate_multi_year_corporate_taxes(
    annual_incomes: List[int] = Field(..., min_items=1, max_items=10, description="年間所得リスト（円）"),
    start_year: int = Field(default=2025, ge=2020, le=2030, description="開始年度"),
    prefecture: str = Field(default="東京都", description="都道府県"),
    capital: int = Field(default=100000000, ge=1000000, description="資本金（円）"),
    deductions: int = Field(default=0, ge=0, description="各種控除の合計（円）"),
) -> Dict[str, Any]:
    """Simulate corporate taxes for multiple years."""
    
    logger.info(
        "Multi-year corporate tax simulation requested",
        years_count=len(annual_incomes),
        start_year=start_year,
        prefecture=prefecture,
    )
    
    try:
        # 監査ログ記録
        audit_logger.log_calculation_request(
            calculation_type="multi_year_corporate_simulation",
            parameters={
                "annual_incomes": annual_incomes,
                "start_year": start_year,
                "prefecture": prefecture,
                "capital": capital,
                "deductions": deductions,
            },
        )
        
        # 複数年シミュレーション実行
        results = corporate_tax_calculator.simulate_multi_year_corporate_taxes(
            annual_incomes=annual_incomes,
            start_year=start_year,
            prefecture=prefecture,
            capital=capital,
            deductions=deductions,
        )
        
        # サマリー情報を計算
        total_income = sum(annual_incomes)
        total_tax = sum(result["total_tax"] for result in results)
        average_effective_rate = total_tax / total_income * 100 if total_income > 0 else 0
        
        simulation_summary = {
            "years_simulated": len(annual_incomes),
            "start_year": start_year,
            "end_year": start_year + len(annual_incomes) - 1,
            "total_income": total_income,
            "total_tax": total_tax,
            "average_effective_rate": round(average_effective_rate, 2),
            "prefecture": prefecture,
            "capital": capital,
            "yearly_results": results,
        }
        
        logger.info(
            "Multi-year corporate tax simulation completed",
            total_tax=total_tax,
            average_effective_rate=average_effective_rate,
        )
        
        return simulation_summary
        
    except Exception as e:
        logger.error("Multi-year corporate tax simulation failed", error=str(e))
        raise


@app.tool(
    name="get_tax_year_info",
    description="サポートされている課税年度の情報を取得します。各年度の税制改正内容も含まれます。",
)
def get_tax_year_info() -> Dict[str, Any]:
    """Get information about supported tax years and their features."""
    
    logger.info("Tax year information requested")
    
    tax_years_info = {
        "supported_years": [2020, 2021, 2022, 2023, 2024, 2025],
        "current_year": 2025,
        "year_details": {
            "2025": {
                "basic_deduction": 480000,
                "consumption_tax_standard": 0.10,
                "consumption_tax_reduced": 0.08,
                "notes": "現行税制"
            },
            "2024": {
                "basic_deduction": 480000,
                "consumption_tax_standard": 0.10,
                "consumption_tax_reduced": 0.08,
                "notes": "現行税制"
            },
            "2023": {
                "basic_deduction": 480000,
                "consumption_tax_standard": 0.10,
                "consumption_tax_reduced": 0.08,
                "notes": "2024年と同様の税制"
            },
        },
        "features": [
            "所得税の累進課税計算",
            "給与所得控除の自動計算",
            "各種所得控除の適用",
            "住民税計算（所得割・均等割）",
            "消費税率の履歴管理",
            "複数年シミュレーション",
            "法人税計算（法人税・地方法人税・事業税）",
            "法人税複数年シミュレーション",
            "大法人・中小法人の区分対応"
        ]
    }
    
    return tax_years_info


@app.tool(
    name="get_latest_tax_info",
    description="最新の税制情報を外部データソースから取得します。国税庁や財務省の公式情報を検索できます。",
)
async def get_latest_tax_info(request: TaxInfoRequest) -> Dict[str, Any]:
    """Get latest tax information from external data sources."""
    
    logger.info(
        "Latest tax information requested",
        query=request.query,
        category=request.category,
        tax_year=request.tax_year
    )
    
    try:
        # RAG統合を使用して最新の税制情報を取得
        tax_info_list = await rag_integration.get_latest_tax_info(
            query=request.query,
            category=request.category
        )
        
        # 結果を整理
        formatted_results = []
        for info in tax_info_list:
            formatted_results.append({
                "title": info.title,
                "source": info.source,
                "content": info.content[:200] + "..." if len(info.content) > 200 else info.content,
                "url": info.url,
                "category": info.category,
                "tax_year": info.tax_year,
                "relevance_score": info.relevance_score,
                "date_published": info.date_published.isoformat() if info.date_published else None
            })
        
        result = {
            "query": request.query,
            "category": request.category,
            "results_count": len(formatted_results),
            "results": formatted_results,
            "last_updated": datetime.now().isoformat(),
            "data_sources": [
                "財務省税制改正資料",
                "国税庁タックスアンサー"
            ]
        }
        
        logger.info(
            "Latest tax information retrieved",
            results_count=len(formatted_results)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to get latest tax information", error=str(e))
        raise


@app.tool(
    name="get_tax_rate_updates",
    description="指定年度の税率更新情報を取得します。税制改正による変更点を確認できます。",
)
async def get_tax_rate_updates(tax_year: int = 2025) -> Dict[str, Any]:
    """Get tax rate updates for specified year."""
    
    logger.info(
        "Tax rate updates requested",
        tax_year=tax_year
    )
    
    try:
        # RAG統合を使用して税率更新情報を取得
        rate_updates = await rag_integration.get_tax_rate_updates(tax_year)
        
        logger.info(
            "Tax rate updates retrieved",
            tax_year=tax_year,
            income_tax_changes=len(rate_updates['income_tax_changes']),
            corporate_tax_changes=len(rate_updates['corporate_tax_changes']),
            consumption_tax_changes=len(rate_updates['consumption_tax_changes'])
        )
        
        return rate_updates
        
    except Exception as e:
        logger.error("Failed to get tax rate updates", error=str(e))
        raise


@app.tool(
    name="search_legal_reference",
    description="法令参照検索を行います。法人税法の条文やタックスアンサー番号で検索できます。",
)
async def search_legal_reference(request: LegalReferenceRequest) -> Dict[str, Any]:
    """Search legal references including law articles and tax answers."""
    
    logger.info(
        "Legal reference search requested",
        reference=request.reference
    )
    
    try:
        # RAG統合を使用して法令参照検索
        results = await rag_integration.search_legal_reference(request.reference)
        
        # 結果をフォーマット
        formatted_results = []
        for info in results:
            formatted_results.append({
                "source": info.source,
                "title": info.title,
                "content": info.content[:500] + "..." if len(info.content) > 500 else info.content,
                "url": info.url,
                "category": info.category,
                "relevance_score": info.relevance_score
            })
        
        result = {
            "reference": request.reference,
            "results_count": len(formatted_results),
            "results": formatted_results,
            "search_timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            "Legal reference search completed",
            reference=request.reference,
            results_count=len(formatted_results)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to search legal reference", error=str(e))
        raise


@app.tool(
    name="search_enhanced_tax_info",
    description="SQLiteインデックスを活用した拡張税制情報検索"
)
async def search_enhanced_tax_info(request: EnhancedSearchRequest) -> dict:
    """SQLiteインデックスを活用した拡張税制情報検索"""
    logger.info(
        "Enhanced tax info search requested",
        query=request.query,
        category=request.category,
        tax_year=request.tax_year,
        document_type=request.document_type,
        limit=request.limit
    )
    
    try:
        # RAG統合からインデックス検索結果を取得
        search_results = await rag_integration.search_indexed_documents(
            query=request.query,
            category=request.category,
            tax_year=request.tax_year,
            document_type=request.document_type,
            limit=request.limit
        )
        
        # 拡張検索結果を取得（インデックス + リアルタイム検索）
        enhanced_results = await rag_integration.get_enhanced_tax_info(
            query=request.query,
            category=request.category,
            tax_year=request.tax_year
        )
        
        result = {
            "query": request.query,
            "filters": {
                "category": request.category,
                "tax_year": request.tax_year,
                "document_type": request.document_type
            },
            "indexed_results": search_results,
            "enhanced_results": enhanced_results,
            "total_results": len(search_results) + len(enhanced_results.get("additional_sources", [])),
            "search_timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            "Enhanced tax info search completed",
            query=request.query,
            indexed_count=len(search_results),
            enhanced_count=len(enhanced_results.get("additional_sources", []))
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to search enhanced tax info", error=str(e))
        raise


@app.tool(
    name="get_index_statistics",
    description="SQLiteインデックスの統計情報を取得"
)
async def get_index_statistics(request: IndexStatsRequest) -> dict:
    """SQLiteインデックスの統計情報を取得"""
    logger.info("Index statistics requested", include_details=request.include_details)
    
    try:
        # インデックス統計を取得
        stats = await rag_integration.get_index_statistics()
        
        result = {
            "statistics": stats,
            "include_details": request.include_details,
            "timestamp": datetime.now().isoformat()
        }
        
        if not request.include_details:
            # 詳細を含まない場合は基本統計のみ
            result["statistics"] = {
                "total_documents": stats.get("total_documents", 0),
                "total_searches": stats.get("total_searches", 0),
                "last_updated": stats.get("last_updated")
            }
        
        logger.info(
            "Index statistics retrieved",
            total_documents=stats.get("total_documents", 0),
            total_searches=stats.get("total_searches", 0)
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to get index statistics", error=str(e))
        raise


if __name__ == "__main__":
    logger.info(
        "Starting Japanese Tax Calculator MCP Server",
        version=settings.server_version,
    )
    
    # FastMCPはstdio経由で動作するため、run()にパラメータは不要
    app.run()