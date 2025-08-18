"""SQLiteインデックス機能モック

TaxMCPサーバーのSQLiteインデックス機能をモックするためのクラス
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .mock_response import MockResponse


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
    
    async def search_documents(self, query: str, limit: int = 10) -> MockResponse:
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
        return MockResponse({
            "results": results,
            "total_results": len(results),
            "success": True
        }, 200)
    
    async def build_index(self) -> bool:
        """インデックス構築のモック
        
        Returns:
            構築成功フラグ
        """
        self.index_built = True
        return True
    
    async def get_statistics(self) -> MockResponse:
        """統計情報取得のモック
        
        Returns:
            モック統計情報
        """
        return MockResponse({
            "total_documents": len(self.documents),
            "index_size": len(self.documents) * 1024,  # 仮のサイズ
            "last_updated": datetime.now().isoformat(),
            "index_built": self.index_built,
            "success": True
        }, 200)