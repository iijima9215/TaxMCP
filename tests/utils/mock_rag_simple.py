"""RAG統合テスト用の簡易モック

必要最小限のモック機能を提供する。
"""

from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import List, Dict, Any, Optional

# RAG統合モジュールのインポート
from rag_integration import TaxInformation, RAGCache


class MockRAGCache:
    """RAGキャッシュのモック"""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """キャッシュからデータを取得（モック）"""
        return self._cache.get(key)
    
    def set(self, key: str, data: Any) -> None:
        """データをキャッシュに保存（モック）"""
        self._cache[key] = data
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()


class MockTaxDataFetcher:
    """税制データ取得のモック"""
    
    def __init__(self):
        self.session = None
        self._sample_data = self._create_sample_data()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def _create_sample_data(self) -> List[TaxInformation]:
        """サンプルデータを作成"""
        return [
            TaxInformation(
                source="財務省",
                title="令和7年度税制改正の大綱",
                content="法人税率の見直し、所得税控除の変更等が含まれます",
                url="https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/20241213taikou.pdf",
                category="tax_reform",
                tax_year=2025,
                relevance_score=0.95
            ),
            TaxInformation(
                source="国税庁",
                title="法人税の計算",
                content="法人税の基本的な計算方法について説明します",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5759.htm",
                category="corporate_tax",
                relevance_score=0.9
            ),
            TaxInformation(
                source="国税庁タックスアンサー",
                title="給与所得控除",
                content="給与所得者の所得控除について",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1410.htm",
                category="income_tax",
                relevance_score=0.85
            )
        ]
    
    async def fetch_mof_tax_reform_data(self) -> List[TaxInformation]:
        """財務省税制改正データの取得（モック）"""
        return [data for data in self._sample_data if data.source == "財務省"]
    
    async def fetch_nta_tax_answer_data(self, query: str = "") -> List[TaxInformation]:
        """国税庁タックスアンサーデータの取得（モック）"""
        nta_data = [data for data in self._sample_data if "国税庁" in data.source]
        
        if query:
            # 簡単なクエリフィルタリング
            filtered_data = []
            query_lower = query.lower()
            for data in nta_data:
                if (query_lower in data.title.lower() or 
                    query_lower in data.content.lower() or
                    query_lower in (data.category or "").lower()):
                    filtered_data.append(data)
            return filtered_data
        
        return nta_data
    
    def search_relevant_info(self, query: str, tax_info_list: List[TaxInformation]) -> List[TaxInformation]:
        """関連情報検索（モック）"""
        if not query:
            return tax_info_list
        
        query_lower = query.lower()
        relevant_info = []
        
        for info in tax_info_list:
            score = 0.0
            
            # タイトルでの一致
            if query_lower in info.title.lower():
                score += 0.5
            
            # コンテンツでの一致
            if query_lower in info.content.lower():
                score += 0.3
            
            # カテゴリでの一致
            if query_lower in (info.category or "").lower():
                score += 0.2
            
            if score > 0:
                info.relevance_score = score
                relevant_info.append(info)
        
        # 関連度でソート
        relevant_info.sort(key=lambda x: x.relevance_score, reverse=True)
        return relevant_info[:10]


class MockRAGIntegration:
    """RAG統合のモック"""
    
    def __init__(self):
        self.fetcher = MockTaxDataFetcher()
        self.cache = MockRAGCache()
        self._sample_tax_answers = self._create_sample_tax_answers()
        self._sample_law_articles = self._create_sample_law_articles()
    
    def _create_sample_tax_answers(self) -> Dict[str, TaxInformation]:
        """サンプルタックスアンサーを作成"""
        return {
            "5280": TaxInformation(
                source="国税庁タックスアンサー",
                title="タックスアンサー No.5280 法人税の計算",
                content="法人税の基本的な計算方法について詳しく説明します",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/hojin/5280.htm",
                category="tax_answer",
                relevance_score=1.0
            ),
            "1410": TaxInformation(
                source="国税庁タックスアンサー",
                title="タックスアンサー No.1410 給与所得控除",
                content="給与所得者の所得控除について説明します",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1410.htm",
                category="tax_answer",
                relevance_score=1.0
            )
        }
    
    def _create_sample_law_articles(self) -> Dict[str, TaxInformation]:
        """サンプル法令条文を作成"""
        return {
            "法人税法_61_4": TaxInformation(
                source="e-Gov法令検索",
                title="法人税法 第61条の4",
                content="法人税法第61条の4の条文内容（e-Gov法令検索APIから取得予定）",
                url="https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/search?lawTitle=法人税法",
                category="law_article",
                relevance_score=1.0
            ),
            "所得税法_120": TaxInformation(
                source="e-Gov法令検索",
                title="所得税法 第120条",
                content="所得税法第120条の条文内容（e-Gov法令検索APIから取得予定）",
                url="https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/search?lawTitle=所得税法",
                category="law_article",
                relevance_score=1.0
            )
        }
    
    async def get_latest_tax_info(self, query: str = "", category: str = "") -> List[TaxInformation]:
        """最新税制情報取得（モック）"""
        all_info = []
        
        # 財務省の税制改正情報を取得
        mof_info = await self.fetcher.fetch_mof_tax_reform_data()
        all_info.extend(mof_info)
        
        # 国税庁タックスアンサーを取得
        nta_info = await self.fetcher.fetch_nta_tax_answer_data(query)
        all_info.extend(nta_info)
        
        # カテゴリでフィルタリング
        if category:
            all_info = [info for info in all_info if info.category == category]
        
        # クエリで検索
        if query:
            all_info = self.fetcher.search_relevant_info(query, all_info)
        
        return all_info
    
    async def get_tax_rate_updates(self, tax_year: int = 2025) -> Dict[str, Any]:
        """税率更新情報取得（モック）"""
        cache_key = f"tax_rate_updates_{tax_year}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        # 税制改正情報から税率変更を抽出
        tax_info = await self.get_latest_tax_info(category="tax_reform")
        
        rate_updates = {
            'tax_year': tax_year,
            'income_tax_changes': [],
            'corporate_tax_changes': [],
            'consumption_tax_changes': [],
            'last_updated': datetime.now().isoformat()
        }
        
        for info in tax_info:
            if info.tax_year == tax_year:
                content_lower = info.content.lower()
                
                if any(keyword in content_lower for keyword in ['所得税', '税率', '控除']):
                    rate_updates['income_tax_changes'].append({
                        'title': info.title,
                        'url': info.url,
                        'source': info.source
                    })
                
                if any(keyword in content_lower for keyword in ['法人税', '税率']):
                    rate_updates['corporate_tax_changes'].append({
                        'title': info.title,
                        'url': info.url,
                        'source': info.source
                    })
                
                if any(keyword in content_lower for keyword in ['消費税', '軽減税率']):
                    rate_updates['consumption_tax_changes'].append({
                        'title': info.title,
                        'url': info.url,
                        'source': info.source
                    })
        
        # キャッシュに保存
        self.cache.set(cache_key, rate_updates)
        
        return rate_updates
    
    async def search_legal_reference(self, reference: str) -> List[TaxInformation]:
        """法令参照検索（モック）"""
        cache_key = f"legal_ref_{reference}"
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        results = []
        
        # タックスアンサー番号の検索
        import re
        tax_answer_match = re.search(r'(?:No\.?\s*)?([0-9]{4,5})', reference)
        if tax_answer_match:
            answer_no = tax_answer_match.group(1)
            if answer_no in self._sample_tax_answers:
                results.append(self._sample_tax_answers[answer_no])
        
        # 法令条文の検索
        law_match = re.search(r'(法人税法|所得税法|消費税法|相続税法|地方税法)(?:第)?([0-9]+)条(?:の([0-9]+))?', reference)
        if law_match:
            law_name = law_match.group(1)
            article_no = law_match.group(2)
            sub_article = law_match.group(3) if law_match.group(3) else None
            
            key = f"{law_name}_{article_no}"
            if sub_article:
                key += f"_{sub_article}"
            
            if key in self._sample_law_articles:
                results.append(self._sample_law_articles[key])
        
        # キャッシュに保存
        self.cache.set(cache_key, results)
        
        return results
    
    async def _search_tax_answer_by_number(self, answer_no: str) -> Optional[TaxInformation]:
        """タックスアンサー番号による検索（モック）"""
        return self._sample_tax_answers.get(answer_no)
    
    async def _search_law_article(self, law_name: str, article_no: str, sub_article: Optional[str] = None) -> Optional[TaxInformation]:
        """法令条文検索（モック）"""
        key = f"{law_name}_{article_no}"
        if sub_article:
            key += f"_{sub_article}"
        
        return self._sample_law_articles.get(key)


def create_mock_rag_integration() -> MockRAGIntegration:
    """モックRAG統合インスタンスを作成"""
    return MockRAGIntegration()


def create_sample_tax_information() -> List[TaxInformation]:
    """サンプル税制情報を作成"""
    return [
        TaxInformation(
            source="国税庁",
            title="法人税率の改正について",
            content="令和7年度税制改正により法人税率が変更されます",
            url="https://www.nta.go.jp/test",
            category="corporate_tax",
            tax_year=2025,
            relevance_score=0.9
        ),
        TaxInformation(
            source="財務省",
            title="所得税控除額の見直し",
            content="基礎控除額が48万円に変更されます",
            url="https://www.mof.go.jp/test",
            category="income_tax",
            tax_year=2025,
            relevance_score=0.8
        ),
        TaxInformation(
            source="国税庁タックスアンサー",
            title="消費税の軽減税率制度",
            content="軽減税率の対象品目について説明します",
            url="https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/index.htm",
            category="consumption_tax",
            relevance_score=0.75
        )
    ]