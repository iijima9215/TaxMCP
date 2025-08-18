"""外部API統合モック

TaxMCPサーバーの外部API統合機能をモックするためのクラスと便利関数
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from .mock_response import MockResponse
from .mock_rag_integration import MockRAGIntegration
from .mock_security_manager import MockSecurityManager
from .mock_sqlite_indexer import MockSQLiteIndexer


class MockExternalAPIs:
    """外部API統合のモック"""
    
    @staticmethod
    def mock_mof_api():
        """財務省APIのモック"""
        return {
            "status": "success",
            "data": {
                "tax_rates": {
                    "income_tax": {
                        "basic_rate": 0.05,
                        "progressive_rates": [
                            {"threshold": 1950000, "rate": 0.05},
                            {"threshold": 3300000, "rate": 0.10},
                            {"threshold": 6950000, "rate": 0.20},
                            {"threshold": 9000000, "rate": 0.23},
                            {"threshold": 18000000, "rate": 0.33},
                            {"threshold": 40000000, "rate": 0.40},
                            {"threshold": float('inf'), "rate": 0.45}
                        ]
                    },
                    "consumption_tax": 0.10,
                    "corporate_tax": 0.23
                },
                "deductions": {
                    "basic_deduction": 480000,
                    "spouse_deduction": 380000,
                    "dependent_deduction": 380000
                },
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
    
    @staticmethod
    def mock_nta_api():
        """国税庁APIのモック"""
        return {
            "status": "success",
            "data": {
                "tax_forms": [
                    {
                        "form_id": "kakutei_shinkoku",
                        "name": "確定申告書",
                        "version": "2024",
                        "fields": [
                            {"field_id": "income", "name": "所得金額", "type": "number"},
                            {"field_id": "deductions", "name": "所得控除", "type": "number"},
                            {"field_id": "tax_amount", "name": "税額", "type": "number"}
                        ]
                    }
                ],
                "regulations": [
                    {
                        "regulation_id": "income_tax_law",
                        "title": "所得税法",
                        "articles": [
                            {"article": "第1条", "content": "所得税の課税対象"},
                            {"article": "第2条", "content": "所得の分類"}
                        ]
                    }
                ],
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
    
    @staticmethod
    def mock_egov_api():
        """e-Gov APIのモック"""
        return {
            "status": "success",
            "data": {
                "legal_documents": [
                    {
                        "document_id": "law_001",
                        "title": "所得税法",
                        "category": "税法",
                        "effective_date": "2024-01-01",
                        "content_summary": "所得税に関する基本的な規定"
                    },
                    {
                        "document_id": "law_002",
                        "title": "法人税法",
                        "category": "税法",
                        "effective_date": "2024-01-01",
                        "content_summary": "法人税に関する基本的な規定"
                    }
                ],
                "administrative_procedures": [
                    {
                        "procedure_id": "proc_001",
                        "name": "確定申告手続き",
                        "description": "個人の所得税確定申告に関する手続き",
                        "required_documents": ["源泉徴収票", "控除証明書"]
                    }
                ],
                "last_updated": "2024-01-01T00:00:00Z"
            }
        }
    
    @staticmethod
    def call_ministry_of_finance_api(data_type: str, **kwargs):
        """財務省API呼び出しのモック"""
        return {
            "status": "success",
            "data_type": data_type,
            "data": MockExternalAPIs.mock_mof_api()["data"],
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def call_national_tax_agency_api(data_type: str, **kwargs):
        """国税庁API呼び出しのモック"""
        return {
            "status": "success",
            "data_type": data_type,
            "data": MockExternalAPIs.mock_nta_api()["data"],
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def call_egov_api(data_type: str, **kwargs):
        """e-Gov API呼び出しのモック"""
        return {
            "status": "success",
            "data_type": data_type,
            "data": MockExternalAPIs.mock_egov_api()["data"],
            "timestamp": datetime.now().isoformat()
        }


class MockContextManager:
    """モックコンテキストマネージャー"""
    
    def __init__(self):
        self.patches = []
    
    def __enter__(self):
        # RAG統合のモック
        rag_patch = patch('rag_integration.RAGIntegration', MockRAGIntegration)
        self.patches.append(rag_patch)
        rag_patch.start()
        
        # SQLiteインデックスのモック
        sqlite_patch = patch('sqlite_indexer.SQLiteIndexer', MockSQLiteIndexer)
        self.patches.append(sqlite_patch)
        sqlite_patch.start()
        
        # セキュリティマネージャーのモック
        security_patch = patch('security.SecurityManager', MockSecurityManager)
        self.patches.append(security_patch)
        security_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for patch_obj in self.patches:
            patch_obj.stop()
        self.patches.clear()


# 便利な関数
def create_mock_response(status_code: int = 200, data: Any = None, error: str = None) -> MockResponse:
    """モックレスポンス作成
    
    Args:
        status_code: ステータスコード
        data: レスポンスデータ
        error: エラーメッセージ
        
    Returns:
        モックレスポンス
    """
    response_data = {
        "timestamp": datetime.now().isoformat(),
        "success": status_code < 400
    }
    
    if data is not None:
        response_data["data"] = data
    
    if error is not None:
        response_data["error"] = error
    
    return MockResponse(response_data, status_code)


def create_mock_http_client():
    """モックHTTPクライアント作成
    
    Returns:
        モックHTTPクライアント
    """
    mock_client = Mock()
    
    # GET リクエストのモック
    async def mock_get(url: str, **kwargs):
        if "mof.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_mof_api())
        elif "nta.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_nta_api())
        elif "e-gov.go.jp" in url:
            return create_mock_response(data=MockExternalAPIs.mock_egov_api())
        else:
            return create_mock_response(status_code=404, error="Not found")
    
    mock_client.get = AsyncMock(side_effect=mock_get)
    
    return mock_client