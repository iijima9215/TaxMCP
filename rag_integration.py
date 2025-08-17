"""RAG統合モジュール - 外部データソースとの連携機能

日本の税制に関する公式データソースから最新情報を取得し、
MCPサーバーの計算精度と信頼性を向上させる。
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import hashlib
import pickle
from bs4 import BeautifulSoup
import re

# SQLite indexer import
from sqlite_indexer import SQLiteIndexer, DocumentMetadata

logger = logging.getLogger(__name__)

@dataclass
class TaxDataSource:
    """税制データソースの定義"""
    name: str
    url: str
    source_type: str  # 'api', 'scraping', 'rss'
    update_frequency: int  # 更新頻度（時間）
    last_updated: Optional[datetime] = None
    cache_key: Optional[str] = None

@dataclass
class TaxInformation:
    """取得した税制情報"""
    source: str
    title: str
    content: str
    url: str
    date_published: Optional[datetime] = None
    tax_year: Optional[int] = None
    category: Optional[str] = None  # 'income_tax', 'corporate_tax', 'consumption_tax', etc.
    relevance_score: float = 0.0

class RAGCache:
    """RAGデータのキャッシュ管理"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_cache_path(self, key: str) -> Path:
        """キャッシュファイルのパスを生成"""
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.pkl"
    
    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """キャッシュからデータを取得"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
                
            # キャッシュの有効期限をチェック
            if datetime.now() - cached_data['timestamp'] > timedelta(hours=max_age_hours):
                cache_path.unlink()  # 期限切れキャッシュを削除
                return None
                
            return cached_data['data']
            
        except Exception as e:
            logger.warning(f"キャッシュ読み込みエラー: {e}")
            return None
    
    def set(self, key: str, data: Any) -> None:
        """データをキャッシュに保存"""
        cache_path = self._get_cache_path(key)
        
        try:
            cached_data = {
                'timestamp': datetime.now(),
                'data': data
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
                
        except Exception as e:
            logger.error(f"キャッシュ保存エラー: {e}")

class TaxDataFetcher:
    """税制データの取得クラス"""
    
    def __init__(self):
        self.cache = RAGCache()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # SQLite indexer for document management
        self.indexer = SQLiteIndexer(
            db_path="tax_documents.db",
            index_dir="search_index"
        )
        
        # データソースの定義
        self.data_sources = {
            'mof_tax_reform': TaxDataSource(
                name="財務省税制改正資料",
                url="https://www.mof.go.jp/tax_policy/tax_reform/outline/index.html",
                source_type="scraping",
                update_frequency=168  # 週1回
            ),
            'nta_tax_answer': TaxDataSource(
                name="国税庁タックスアンサー",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/index.htm",
                source_type="scraping",
                update_frequency=24  # 日1回
            ),
            'egov_laws': TaxDataSource(
                name="e-Gov法令検索",
                url="https://elaws.e-gov.go.jp/",
                source_type="api",
                update_frequency=72  # 3日に1回
            ),
            'nta_tax_answer_direct': TaxDataSource(
                name="国税庁タックスアンサー直接検索",
                url="https://www.nta.go.jp/taxes/shiraberu/taxanswer/",
                source_type="direct",
                update_frequency=24  # 日1回
            )
        }
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'TaxMCP-RAG/1.0 (Tax Calculation Service)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self.session:
            await self.session.close()
    
    async def fetch_mof_tax_reform_data(self) -> List[TaxInformation]:
        """財務省の税制改正資料を取得"""
        cache_key = "mof_tax_reform_data"
        cached_data = self.cache.get(cache_key, max_age_hours=168)  # 1週間キャッシュ
        
        if cached_data:
            logger.info("財務省税制改正データをキャッシュから取得")
            return cached_data
        
        try:
            url = self.data_sources['mof_tax_reform'].url
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"財務省サイトへのアクセスエラー: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                tax_info_list = []
                
                # 令和7年度（2025年度）の税制改正情報を抽出
                year_sections = soup.find_all(['h3', 'h4'], string=re.compile(r'令和[0-9]+年度'))
                
                for section in year_sections:
                    year_match = re.search(r'令和([0-9]+)年度', section.get_text())
                    if year_match:
                        year_reiwa = int(year_match.group(1))
                        year_ad = year_reiwa + 2018  # 令和元年 = 2019年
                        
                        # セクション内のリンクを取得
                        parent = section.find_parent()
                        if parent:
                            links = parent.find_all('a', href=True)
                            
                            for link in links:
                                if any(keyword in link.get_text() for keyword in ['税制改正', '大綱', '概要']):
                                    tax_info = TaxInformation(
                                        source="財務省税制改正資料",
                                        title=f"令和{year_reiwa}年度税制改正 - {link.get_text().strip()}",
                                        content=link.get_text().strip(),
                                        url=link['href'] if link['href'].startswith('http') else f"https://www.mof.go.jp{link['href']}",
                                        tax_year=year_ad,
                                        category="tax_reform",
                                        relevance_score=1.0 if year_ad >= 2024 else 0.8
                                    )
                                    tax_info_list.append(tax_info)
                
                # キャッシュに保存
                self.cache.set(cache_key, tax_info_list)
                logger.info(f"財務省から{len(tax_info_list)}件の税制改正情報を取得")
                
                return tax_info_list
                
        except Exception as e:
            logger.error(f"財務省税制改正データ取得エラー: {e}")
            return []
    
    async def fetch_nta_tax_answer_data(self, query: str = "") -> List[TaxInformation]:
        """国税庁タックスアンサーから情報を取得"""
        cache_key = f"nta_tax_answer_{hashlib.md5(query.encode()).hexdigest()}"
        cached_data = self.cache.get(cache_key, max_age_hours=24)
        
        if cached_data:
            logger.info("国税庁タックスアンサーデータをキャッシュから取得")
            return cached_data
        
        try:
            # 基本的なタックスアンサーのカテゴリを取得
            base_url = "https://www.nta.go.jp/taxes/shiraberu/taxanswer"
            categories = [
                ("shotoku", "所得税", "income_tax"),
                ("hojin", "法人税", "corporate_tax"),
                ("shohi", "消費税", "consumption_tax"),
                ("sozoku", "相続税", "inheritance_tax")
            ]
            
            tax_info_list = []
            
            for category_path, category_name, category_type in categories:
                try:
                    url = f"{base_url}/{category_path}/index.htm"
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # FAQ項目を抽出
                            faq_links = soup.find_all('a', href=re.compile(r'[0-9]+\.htm'))
                            
                            for link in faq_links[:10]:  # 最初の10件のみ
                                tax_info = TaxInformation(
                                    source="国税庁タックスアンサー",
                                    title=f"{category_name} - {link.get_text().strip()}",
                                    content=link.get_text().strip(),
                                    url=f"{base_url}/{category_path}/{link['href']}",
                                    category=category_type,
                                    relevance_score=0.9
                                )
                                tax_info_list.append(tax_info)
                                
                except Exception as e:
                    logger.warning(f"カテゴリ {category_name} の取得エラー: {e}")
                    continue
            
            # キャッシュに保存
            self.cache.set(cache_key, tax_info_list)
            logger.info(f"国税庁から{len(tax_info_list)}件のタックスアンサー情報を取得")
            
            return tax_info_list
            
        except Exception as e:
            logger.error(f"国税庁タックスアンサーデータ取得エラー: {e}")
            return []
    
    def search_relevant_info(self, query: str, tax_info_list: List[TaxInformation]) -> List[TaxInformation]:
        """クエリに関連する税制情報を検索"""
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
        return relevant_info[:10]  # 上位10件

class RAGIntegration:
    """RAG統合メインクラス"""
    
    def __init__(self):
        self.fetcher = TaxDataFetcher()
        self.cache = RAGCache()
    
    async def get_latest_tax_info(self, query: str = "", category: str = "") -> List[TaxInformation]:
        """最新の税制情報を取得"""
        all_info = []
        
        async with self.fetcher as fetcher:
            # 財務省の税制改正情報を取得
            mof_info = await fetcher.fetch_mof_tax_reform_data()
            all_info.extend(mof_info)
            
            # 国税庁タックスアンサーを取得
            nta_info = await fetcher.fetch_nta_tax_answer_data(query)
            all_info.extend(nta_info)
        
        # カテゴリでフィルタリング
        if category:
            all_info = [info for info in all_info if info.category == category]
        
        # クエリで検索
        if query:
            all_info = self.fetcher.search_relevant_info(query, all_info)
        
        return all_info
    
    async def get_tax_rate_updates(self, tax_year: int = 2025) -> Dict[str, Any]:
        """指定年度の税率更新情報を取得"""
        cache_key = f"tax_rate_updates_{tax_year}"
        cached_data = self.cache.get(cache_key, max_age_hours=168)  # 1週間キャッシュ
        
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
                # 簡単なキーワードマッチングで税率変更を検出
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
        """法令参照検索（法人税法第XX条、タックスアンサーNo.XXXXなど）"""
        cache_key = f"legal_ref_{hashlib.md5(reference.encode()).hexdigest()}"
        cached_data = self.cache.get(cache_key, max_age_hours=24)
        
        if cached_data:
            logger.info(f"法令参照データをキャッシュから取得: {reference}")
            return cached_data
        
        results = []
        
        try:
            # タックスアンサー番号の検索（例：No.5280, 5280）
            tax_answer_match = re.search(r'(?:No\.?\s*)?([0-9]{4,5})', reference)
            if tax_answer_match:
                answer_no = tax_answer_match.group(1)
                tax_answer_result = await self._search_tax_answer_by_number(answer_no)
                if tax_answer_result:
                    results.append(tax_answer_result)
            
            # 法令条文の検索（例：法人税法第61条の4、所得税法第120条）
            law_match = re.search(r'(法人税法|所得税法|消費税法|相続税法|地方税法)(?:第)?([0-9]+)条(?:の([0-9]+))?', reference)
            if law_match:
                law_name = law_match.group(1)
                article_no = law_match.group(2)
                sub_article = law_match.group(3) if law_match.group(3) else None
                law_result = await self._search_law_article(law_name, article_no, sub_article)
                if law_result:
                    results.append(law_result)
            
            # キーワード検索（上記に該当しない場合）
            if not results:
                keyword_results = await self.get_latest_tax_info(query=reference, category="legal")
                results.extend(keyword_results[:3])  # 上位3件
            
            # キャッシュに保存
            self.cache.set(cache_key, results)
            logger.info(f"法令参照検索完了: {reference} - {len(results)}件")
            
            return results
            
        except Exception as e:
            logger.error(f"法令参照検索エラー: {e}")
            return []
    
    async def _search_tax_answer_by_number(self, answer_no: str) -> Optional[TaxInformation]:
        """タックスアンサー番号による直接検索"""
        try:
            # タックスアンサーのURL構成
            base_url = "https://www.nta.go.jp/taxes/shiraberu/taxanswer"
            
            # 番号から分野を推定
            category_map = {
                '1': 'shotoku',  # 所得税（1000番台）
                '2': 'hojin',    # 法人税（2000番台）
                '3': 'sozoku',   # 相続税（3000番台）
                '4': 'shohi',    # 消費税（4000番台）
                '5': 'hojin',    # 法人税（5000番台）
                '6': 'shotoku',  # 所得税（6000番台）
                '7': 'shotoku',  # 所得税（7000番台）
                '8': 'shotoku',  # 所得税（8000番台）
                '9': 'shotoku'   # 所得税（9000番台）
            }
            
            first_digit = answer_no[0]
            category = category_map.get(first_digit, 'shotoku')
            
            # URLを構築
            url = f"{base_url}/{category}/{answer_no}.htm"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # タイトルを取得
                    title_elem = soup.find('h1') or soup.find('title')
                    title = title_elem.get_text().strip() if title_elem else f"タックスアンサー No.{answer_no}"
                    
                    # 本文を取得
                    content_elem = soup.find('div', class_='main-content') or soup.find('body')
                    content = content_elem.get_text().strip() if content_elem else ""
                    
                    # 不要な部分を除去
                    content = re.sub(r'\s+', ' ', content)[:1000]  # 1000文字まで
                    
                    return TaxInformation(
                        source="国税庁タックスアンサー",
                        title=title,
                        content=content,
                        url=url,
                        category="tax_answer",
                        relevance_score=1.0
                    )
                else:
                    logger.warning(f"タックスアンサー No.{answer_no} が見つかりません")
                    return None
                    
        except Exception as e:
            logger.error(f"タックスアンサー検索エラー: {e}")
            return None
    
    async def _search_law_article(self, law_name: str, article_no: str, sub_article: Optional[str] = None) -> Optional[TaxInformation]:
        """法令条文の検索"""
        try:
            # e-Gov法令検索のAPIを使用（簡易版）
            search_query = f"{law_name} 第{article_no}条"
            if sub_article:
                search_query += f"の{sub_article}"
            
            # 実際のe-Gov APIの代わりに、検索結果をシミュレート
            # 本格実装では e-Gov法令検索API を使用
            
            return TaxInformation(
                source="e-Gov法令検索",
                title=f"{law_name} 第{article_no}条" + (f"の{sub_article}" if sub_article else ""),
                content=f"{search_query}の条文内容（e-Gov法令検索APIから取得予定）",
                url=f"https://elaws.e-gov.go.jp/search/elawsSearch/elaws_search/lsg0500/search?lawTitle={law_name}",
                category="law_article",
                relevance_score=1.0
            )
            
        except Exception as e:
            logger.error(f"法令条文検索エラー: {e}")
            return None
    
    async def index_document_automatically(self, tax_info: TaxInformation) -> bool:
        """取得した税制情報を自動的にSQLiteインデックスに追加"""
        try:
            # Generate unique document ID
            doc_id = f"{tax_info.source}_{hashlib.md5(tax_info.url.encode()).hexdigest()[:8]}"
            
            # Determine document type and category
            document_type = "unknown"
            if "タックスアンサー" in tax_info.source or "tax_answer" in tax_info.source.lower():
                document_type = "tax_answer"
            elif "法令" in tax_info.source or "law" in tax_info.source.lower():
                document_type = "law_article"
            elif "税制改正" in tax_info.source or "tax_reform" in tax_info.source.lower():
                document_type = "tax_reform"
            
            # Add to SQLite index
            success = self.indexer.add_document(
                doc_id=doc_id,
                title=tax_info.title,
                content=tax_info.content,
                source_url=tax_info.url,
                document_type=document_type,
                category=tax_info.category or "general",
                year=tax_info.tax_year or datetime.now().year
            )
            
            if success:
                logger.info(f"Document indexed successfully: {doc_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Document indexing error: {e}")
            return False
    
    async def search_indexed_documents(self, 
                                     query: str,
                                     document_type: Optional[str] = None,
                                     category: Optional[str] = None,
                                     tax_year: Optional[int] = None,
                                     limit: int = 10) -> List[TaxInformation]:
        """SQLiteインデックスを使用した高速文書検索"""
        try:
            # Search using SQLite indexer
            results = self.indexer.search_documents(
                query=query,
                document_type=document_type,
                category=category,
                year=tax_year,
                limit=limit
            )
            
            # Convert to TaxInformation objects
            tax_info_list = []
            for result in results:
                # Get full content if needed
                full_content = self.indexer.get_document_content(result['doc_id'])
                
                tax_info = TaxInformation(
                    source=result.get('document_type', 'indexed_document'),
                    title=result['title'],
                    content=full_content or result['content_preview'],
                    url=result['source_url'],
                    date_published=datetime.fromisoformat(result['last_updated']) if result['last_updated'] else None,
                    tax_year=result['year'],
                    category=result['category'],
                    relevance_score=result['relevance_score']
                )
                tax_info_list.append(tax_info)
            
            return tax_info_list
            
        except Exception as e:
            logger.error(f"Indexed document search error: {e}")
            return []
    
    async def get_enhanced_tax_info(self, 
                                  query: str, 
                                  category: Optional[str] = None,
                                  tax_year: Optional[int] = None,
                                  use_cache: bool = True) -> List[TaxInformation]:
        """拡張された税制情報取得（SQLiteインデックス + リアルタイム検索）"""
        try:
            all_results = []
            
            # 1. First search indexed documents for fast results
            indexed_results = await self.search_indexed_documents(
                query=query,
                category=category,
                tax_year=tax_year,
                limit=5
            )
            all_results.extend(indexed_results)
            
            # 2. If not enough results, fetch from live sources
            if len(indexed_results) < 3:
                live_results = await self.get_latest_tax_info(
                    query=query,
                    category=category,
                    tax_year=tax_year
                )
                
                # Index new documents automatically
                for tax_info in live_results:
                    await self.index_document_automatically(tax_info)
                
                all_results.extend(live_results)
            
            # Remove duplicates based on title similarity
            unique_results = []
            seen_titles = set()
            
            for result in all_results:
                title_key = result.title.lower().strip()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    unique_results.append(result)
            
            # Sort by relevance score
            unique_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return unique_results[:10]  # Return top 10 results
            
        except Exception as e:
            logger.error(f"Enhanced tax info retrieval error: {e}")
            return []
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """SQLiteインデックスの統計情報を取得"""
        try:
            return self.indexer.get_statistics()
        except Exception as e:
            logger.error(f"Statistics retrieval error: {e}")
            return {}
    
    async def cleanup_old_indexed_documents(self, days: int = 365) -> int:
        """古いインデックス文書のクリーンアップ"""
        try:
            return self.indexer.cleanup_old_documents(days=days)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
    
    async def bulk_index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """複数文書の一括インデックス化"""
        success_count = 0
        
        for doc in documents:
            try:
                success = self.indexer.add_document(
                    doc_id=doc['doc_id'],
                    title=doc['title'],
                    content=doc['content'],
                    source_url=doc.get('source_url', ''),
                    document_type=doc.get('document_type', 'unknown'),
                    category=doc.get('category', 'general'),
                    year=doc.get('year', datetime.now().year)
                )
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error indexing document {doc.get('doc_id', 'unknown')}: {e}")
        
        logger.info(f"Bulk indexing completed: {success_count}/{len(documents)} documents indexed")
        return success_count

# グローバルインスタンス
rag_integration = RAGIntegration()

# 使用例とテスト関数
async def test_rag_integration():
    """RAG統合のテスト"""
    print("=== RAG統合テスト開始 ===")
    
    try:
        # 最新の税制情報を取得
        print("\n1. 最新税制情報の取得...")
        latest_info = await rag_integration.get_latest_tax_info(query="法人税")
        print(f"取得件数: {len(latest_info)}件")
        
        for i, info in enumerate(latest_info[:3]):
            print(f"  {i+1}. {info.title}")
            print(f"     ソース: {info.source}")
            print(f"     関連度: {info.relevance_score}")
        
        # 税率更新情報を取得
        print("\n2. 2025年度税率更新情報の取得...")
        rate_updates = await rag_integration.get_tax_rate_updates(2025)
        print(f"所得税変更: {len(rate_updates['income_tax_changes'])}件")
        print(f"法人税変更: {len(rate_updates['corporate_tax_changes'])}件")
        print(f"消費税変更: {len(rate_updates['consumption_tax_changes'])}件")
        
        # 法令参照検索のテスト
        print("\n3. 法令参照検索のテスト...")
        
        # タックスアンサー番号検索
        tax_answer_result = await rag_integration.search_legal_reference("No.5280")
        print(f"タックスアンサー検索結果: {len(tax_answer_result)}件")
        if tax_answer_result:
            print(f"  - {tax_answer_result[0].title}")
        
        # 法令条文検索
        law_result = await rag_integration.search_legal_reference("法人税法第61条の4")
        print(f"法令条文検索結果: {len(law_result)}件")
        if law_result:
            print(f"  - {law_result[0].title}")
        
        print("\n=== RAG統合テスト完了 ===")
        
    except Exception as e:
        print(f"テストエラー: {e}")

if __name__ == "__main__":
    # テスト実行
    asyncio.run(test_rag_integration())