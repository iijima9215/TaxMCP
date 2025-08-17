"""外部API モックユーティリティ

TaxMCPサーバーの外部API連携をモックするためのユーティリティ
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date


class MockRAGIntegration:
    """RAG統合機能のモック"""
    
    def __init__(self):
        self.cache = {}
        self.call_count = 0
    
    async def get_latest_tax_info(self, query: str, category: str = "general") -> List[Dict[str, Any]]:
        """最新税制情報取得のモック
        
        Args:
            query: 検索クエリ
            category: カテゴリ
            
        Returns:
            モック検索結果
        """
        self.call_count += 1
        
        # クエリに基づくモックレスポンス
        mock_responses = {
            "基礎控除": [
                {
                    "title": "基礎控除の概要",
                    "content": "2025年度の基礎控除額は48万円です。",
                    "source": "国税庁",
                    "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1199.htm",
                    "last_updated": "2024-12-01",
                    "relevance_score": 0.95
                }
            ],
            "法人税率": [
                {
                    "title": "法人税率の改正",
                    "content": "中小法人の税率は15%、大法人は23%です。",
                    "source": "財務省",
                    "url": "https://www.mof.go.jp/tax_policy/",
                    "last_updated": "2024-11-15",
                    "relevance_score": 0.92
                }
            ],
            "消費税": [
                {
                    "title": "消費税率について",
                    "content": "標準税率10%、軽減税率8%が適用されます。",
                    "source": "国税庁",
                    "url": "https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/",
                    "last_updated": "2024-10-01",
                    "relevance_score": 0.98
                }
            ]
        }
        
        # 部分マッチで検索
        results = []
        for key, value in mock_responses.items():
            if key in query or query in key:
                results.extend(value)
        
        # デフォルトレスポンス
        if not results:
            results = [{
                "title": f"検索結果: {query}",
                "content": f"'{query}'に関する情報が見つかりました。",
                "source": "モックデータ",
                "url": "https://example.com/mock",
                "last_updated": datetime.now().isoformat(),
                "relevance_score": 0.5
            }]
        
        return results
    
    async def get_tax_rate_updates(self, year: Optional[int] = None) -> Dict[str, Any]:
        """税率更新情報取得のモック
        
        Args:
            year: 対象年度
            
        Returns:
            モック税率更新情報
        """
        self.call_count += 1
        
        return {
            "year": year or 2025,
            "updates": [
                {
                    "type": "income_tax",
                    "description": "基礎控除額の調整",
                    "effective_date": "2025-01-01",
                    "details": {
                        "old_value": 480000,
                        "new_value": 480000,
                        "change_reason": "据え置き"
                    }
                },
                {
                    "type": "corporate_tax",
                    "description": "中小法人税率の維持",
                    "effective_date": "2025-04-01",
                    "details": {
                        "small_company_rate": 0.15,
                        "large_company_rate": 0.23
                    }
                }
            ],
            "last_updated": datetime.now().isoformat()
        }
    
    async def search_legal_reference(self, query: str, law_type: str = "income_tax") -> List[Dict[str, Any]]:
        """法令参照検索のモック
        
        Args:
            query: 検索クエリ
            law_type: 法令種別
            
        Returns:
            モック法令検索結果
        """
        self.call_count += 1
        
        mock_laws = {
            "income_tax": [
                {
                    "law_name": "所得税法",
                    "article": "第1条",
                    "content": "この法律は、所得税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000033"
                }
            ],
            "corporate_tax": [
                {
                    "law_name": "法人税法",
                    "article": "第1条",
                    "content": "この法律は、法人税について定めるものとする。",
                    "url": "https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/detail?lawId=340AC0000000034"
                }
            ]
        }
        
        return mock_laws.get(law_type, [])


class MockSQLiteIndexer:
    """SQLiteインデックス機能のモック"""
    
    def __init__(self):
        self.documents = []
        self.index_built = False
    
    async def add_document(self, title: str, content: str, metadata: Dict[str, Any]) -> bool:
        """ドキュメント追加のモック
        
        Args:
            title: ドキュメントタイトル
            content: ドキュメント内容
            metadata: メタデータ
            
        Returns:
            追加成功フラグ
        """
        doc = {
            "id": len(self.documents) + 1,
            "title": title,
            "content": content,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        self.documents.append(doc)
        return True
    
    async def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """ドキュメント検索のモック
        
        Args:
            query: 検索クエリ
            limit: 結果数制限
            
        Returns:
            モック検索結果
        """
        results = []
        for doc in self.documents:
            if query.lower() in doc["title"].lower() or query.lower() in doc["content"].lower():
                results.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"][:200] + "...",
                    "metadata": doc["metadata"],
                    "score": 0.8
                })
                if len(results) >= limit:
                    break
        return results
    
    async def build_index(self) -> bool:
        """インデックス構築のモック
        
        Returns:
            構築成功フラグ
        """
        self.index_built = True
        return True
    
    async def get_statistics(self) -> Dict[str, Any]:
        """統計情報取得のモック
        
        Returns:
            モック統計情報
        """
        return {
            "total_documents": len(self.documents),
            "index_size": len(self.documents) * 1024,  # 仮のサイズ
            "last_updated": datetime.now().isoformat(),
            "index_built": self.index_built
        }


class MockSecurityManager:
    """セキュリティマネージャーのモック"""
    
    def __init__(self):
        self.auth_attempts = []
        self.audit_logs = []
    
    async def authenticate_request(self, token: str) -> Dict[str, Any]:
        """リクエスト認証のモック
        
        Args:
            token: 認証トークン
            
        Returns:
            認証結果
        """
        self.auth_attempts.append({
            "token": token,
            "timestamp": datetime.now().isoformat(),
            "success": token == "valid_token"
        })
        
        if token == "valid_token":
            return {
                "authenticated": True,
                "user_id": "test_user",
                "permissions": ["read", "write"]
            }
        else:
            return {
                "authenticated": False,
                "error": "Invalid token"
            }
    
    async def validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力検証のモック
        
        Args:
            data: 入力データ
            
        Returns:
            検証結果
        """
        errors = []
        
        # 基本的な検証ルール
        if "annual_income" in data:
            if not isinstance(data["annual_income"], (int, float)) or data["annual_income"] < 0:
                errors.append("annual_income must be a positive number")
        
        if "tax_year" in data:
            if not isinstance(data["tax_year"], int) or data["tax_year"] < 2020 or data["tax_year"] > 2030:
                errors.append("tax_year must be between 2020 and 2030")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized_data": data
        }
    
    async def log_audit_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """監査ログ記録のモック
        
        Args:
            event_type: イベント種別
            details: イベント詳細
            
        Returns:
            記録成功フラグ
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self.audit_logs.append(log_entry)
        return True


class MockExternalAPIs:
    """外部API群のモック"""
    
    @staticmethod
    def mock_mof_api():
        """財務省APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "tax_reforms": [
                    {
                        "year": 2025,
                        "title": "令和7年度税制改正大綱",
                        "url": "https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                        "summary": "基礎控除額の据え置き等"
                    }
                ]
            }
        }
    
    @staticmethod
    def mock_nta_api():
        """国税庁APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "tax_answers": [
                    {
                        "id": "1199",
                        "title": "基礎控除",
                        "content": "基礎控除は、すべての納税者に適用される控除です。",
                        "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1199.htm"
                    }
                ]
            }
        }
    
    @staticmethod
    def mock_egov_api():
        """e-Gov法令検索APIのモック
        
        Returns:
            モックレスポンス
        """
        return {
            "status": 200,
            "data": {
                "laws": [
                    {
                        "law_id": "340AC0000000033",
                        "law_name": "所得税法",
                        "articles": [
                            {
                                "article_number": "第1条",
                                "content": "この法律は、所得税について定めるものとする。"
                            }
                        ]
                    }
                ]
            }
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
def create_mock_response(status_code: int = 200, data: Any = None, error: str = None) -> Dict[str, Any]:
    """モックレスポンス作成
    
    Args:
        status_code: ステータスコード
        data: レスポンスデータ
        error: エラーメッセージ
        
    Returns:
        モックレスポンス
    """
    response = {
        "status_code": status_code,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if error is not None:
        response["error"] = error
    
    return response


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