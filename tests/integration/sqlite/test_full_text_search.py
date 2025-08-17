"""SQLite全文検索機能テスト

TaxMCPサーバーのSQLite全文検索機能をテストする
"""

import unittest
import sys
import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import PerformanceAssertions, DataAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestFullTextSearch(TaxMCPTestCase, PerformanceTestMixin):
    """SQLite全文検索機能テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
        
        # テスト用のSQLiteデータベース作成
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        self.connection = sqlite3.connect(self.test_db_path)
        
        # FTS5テーブルの作成
        self._create_fts_tables()
        
        # テストデータの挿入
        self._insert_test_data()
    
    def tearDown(self):
        """テストクリーンアップ"""
        if hasattr(self, 'connection'):
            self.connection.close()
        
        if hasattr(self, 'test_db_fd'):
            os.close(self.test_db_fd)
        
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        
        super().tearDown()
    
    def _create_fts_tables(self):
        """FTS5テーブルの作成"""
        cursor = self.connection.cursor()
        
        # 税法文書用FTSテーブル
        cursor.execute("""
            CREATE VIRTUAL TABLE tax_documents_fts USING fts5(
                title,
                content,
                category,
                tax_type,
                document_type,
                effective_date,
                content='tax_documents',
                content_rowid='id'
            )
        """)
        
        # 税法文書メタデータテーブル
        cursor.execute("""
            CREATE TABLE tax_documents (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                tax_type TEXT NOT NULL,
                document_type TEXT NOT NULL,
                effective_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 判例用FTSテーブル
        cursor.execute("""
            CREATE VIRTUAL TABLE legal_precedents_fts USING fts5(
                case_name,
                summary,
                full_text,
                court,
                decision_date,
                tax_issues,
                content='legal_precedents',
                content_rowid='id'
            )
        """)
        
        # 判例メタデータテーブル
        cursor.execute("""
            CREATE TABLE legal_precedents (
                id INTEGER PRIMARY KEY,
                case_name TEXT NOT NULL,
                summary TEXT NOT NULL,
                full_text TEXT NOT NULL,
                court TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                tax_issues TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 税務通達用FTSテーブル
        cursor.execute("""
            CREATE VIRTUAL TABLE tax_circulars_fts USING fts5(
                circular_number,
                title,
                content,
                issuing_authority,
                issue_date,
                subject_matter,
                content='tax_circulars',
                content_rowid='id'
            )
        """)
        
        # 税務通達メタデータテーブル
        cursor.execute("""
            CREATE TABLE tax_circulars (
                id INTEGER PRIMARY KEY,
                circular_number TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                issuing_authority TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                subject_matter TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.connection.commit()
    
    def _insert_test_data(self):
        """テストデータの挿入"""
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # 税法文書データ
        tax_documents = [
            {
                "title": "所得税法第84条（基礎控除）",
                "content": "居住者については、その者のその年分の総所得金額、退職所得金額及び山林所得金額の合計額から四十八万円を控除する。ただし、その者のその年分の合計所得金額が二千四百万円を超える場合には、次の各号に掲げる場合の区分に応じ、当該各号に定める金額を控除する。",
                "category": "所得税法",
                "tax_type": "所得税",
                "document_type": "法律",
                "effective_date": "2020-01-01"
            },
            {
                "title": "法人税法第22条（各事業年度の所得の金額の計算）",
                "content": "内国法人の各事業年度の所得の金額は、当該事業年度の益金の額から当該事業年度の損金の額を控除した金額とする。",
                "category": "法人税法",
                "tax_type": "法人税",
                "document_type": "法律",
                "effective_date": "1965-03-31"
            },
            {
                "title": "消費税法第4条（課税の対象）",
                "content": "国内において事業者が行った資産の譲渡等（特定資産の譲渡等に該当するものを除く。）には、この法律により、消費税を課する。",
                "category": "消費税法",
                "tax_type": "消費税",
                "document_type": "法律",
                "effective_date": "1988-12-30"
            },
            {
                "title": "地方税法第292条（個人の道府県民税の納税義務者等）",
                "content": "道府県は、次に掲げる者に対して個人の道府県民税を課する。一　当該道府県内に住所を有する個人　二　当該道府県内に事務所、事業所又は家屋敷を有する個人で当該道府県内に住所を有しない者",
                "category": "地方税法",
                "tax_type": "住民税",
                "document_type": "法律",
                "effective_date": "1950-07-31"
            },
            {
                "title": "相続税法第11条（相続税の納税義務者）",
                "content": "相続又は遺贈により財産を取得した個人で当該財産を取得した時において日本国内に住所を有するものは、当該相続又は遺贈により取得した財産の全部に対し、この法律により相続税を納める義務がある。",
                "category": "相続税法",
                "tax_type": "相続税",
                "document_type": "法律",
                "effective_date": "1958-04-01"
            }
        ]
        
        for doc in tax_documents:
            cursor.execute("""
                INSERT INTO tax_documents 
                (title, content, category, tax_type, document_type, effective_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["title"], doc["content"], doc["category"], doc["tax_type"],
                doc["document_type"], doc["effective_date"], current_time, current_time
            ))
        
        # 判例データ
        legal_precedents = [
            {
                "case_name": "最高裁平成15年2月25日判決（給与所得控除事件）",
                "summary": "給与所得控除の適用範囲に関する最高裁判決",
                "full_text": "給与所得者の必要経費の概算控除である給与所得控除は、給与所得者の勤務に関連して支出される費用の概算額として設けられたものであり、実際の必要経費の額にかかわらず適用される。",
                "court": "最高裁判所",
                "decision_date": "2003-02-25",
                "tax_issues": "給与所得控除,必要経費,所得税"
            },
            {
                "case_name": "東京高裁平成20年3月12日判決（法人税更正処分事件）",
                "summary": "法人税の損金算入に関する高等裁判所判決",
                "full_text": "法人が支出した費用が損金に算入されるためには、その支出が法人の事業の遂行上必要な費用であることが要求される。",
                "court": "東京高等裁判所",
                "decision_date": "2008-03-12",
                "tax_issues": "損金算入,必要経費,法人税"
            },
            {
                "case_name": "大阪地裁平成25年7月18日判決（消費税仕入税額控除事件）",
                "summary": "消費税の仕入税額控除に関する地方裁判所判決",
                "full_text": "消費税の仕入税額控除の適用を受けるためには、法定の要件を満たす請求書等の保存が必要である。",
                "court": "大阪地方裁判所",
                "decision_date": "2013-07-18",
                "tax_issues": "仕入税額控除,請求書等保存方式,消費税"
            }
        ]
        
        for precedent in legal_precedents:
            cursor.execute("""
                INSERT INTO legal_precedents 
                (case_name, summary, full_text, court, decision_date, tax_issues, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                precedent["case_name"], precedent["summary"], precedent["full_text"],
                precedent["court"], precedent["decision_date"], precedent["tax_issues"],
                current_time, current_time
            ))
        
        # 税務通達データ
        tax_circulars = [
            {
                "circular_number": "所基通2-1",
                "title": "基礎控除の適用について",
                "content": "所得税法第84条に規定する基礎控除の適用に当たっては、納税者の合計所得金額に応じて控除額が段階的に減額される。",
                "issuing_authority": "国税庁",
                "issue_date": "2020-04-01",
                "subject_matter": "基礎控除,所得税"
            },
            {
                "circular_number": "法基通2-1-1",
                "title": "益金の額の計算について",
                "content": "法人税法第22条第2項に規定する益金の額は、別段の定めがあるものを除き、資産の販売、有償又は無償による資産の譲渡又は役務の提供、無償による資産の譲受けその他の取引で資本等取引以外のものに係る当該法人の収益の額とする。",
                "issuing_authority": "国税庁",
                "issue_date": "1967-04-01",
                "subject_matter": "益金,法人税"
            },
            {
                "circular_number": "消基通5-1-1",
                "title": "課税の対象となる取引について",
                "content": "消費税法第4条第1項に規定する資産の譲渡等とは、事業として対価を得て行われる資産の譲渡及び貸付け並びに役務の提供をいう。",
                "issuing_authority": "国税庁",
                "issue_date": "1989-04-01",
                "subject_matter": "課税対象,消費税"
            }
        ]
        
        for circular in tax_circulars:
            cursor.execute("""
                INSERT INTO tax_circulars 
                (circular_number, title, content, issuing_authority, issue_date, subject_matter, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                circular["circular_number"], circular["title"], circular["content"],
                circular["issuing_authority"], circular["issue_date"], circular["subject_matter"],
                current_time, current_time
            ))
        
        # FTSインデックスの更新
        cursor.execute("INSERT INTO tax_documents_fts(tax_documents_fts) VALUES('rebuild')")
        cursor.execute("INSERT INTO legal_precedents_fts(legal_precedents_fts) VALUES('rebuild')")
        cursor.execute("INSERT INTO tax_circulars_fts(tax_circulars_fts) VALUES('rebuild')")
        
        self.connection.commit()
    
    def test_basic_full_text_search(self):
        """基本的な全文検索テスト"""
        print("\n=== 基本的な全文検索テスト ===")
        
        # 検索テストケース
        search_cases = [
            {
                "query": "基礎控除",
                "table": "tax_documents_fts",
                "expected_min_results": 1,
                "description": "基礎控除に関する文書検索"
            },
            {
                "query": "法人税",
                "table": "tax_documents_fts",
                "expected_min_results": 1,
                "description": "法人税に関する文書検索"
            },
            {
                "query": "消費税",
                "table": "tax_documents_fts",
                "expected_min_results": 1,
                "description": "消費税に関する文書検索"
            },
            {
                "query": "給与所得控除",
                "table": "legal_precedents_fts",
                "expected_min_results": 1,
                "description": "給与所得控除に関する判例検索"
            },
            {
                "query": "益金",
                "table": "tax_circulars_fts",
                "expected_min_results": 1,
                "description": "益金に関する通達検索"
            }
        ]
        
        for case in search_cases:
            print(f"\n--- {case['description']} ---")
            
            # パフォーマンス測定開始
            start_time = self.start_performance_measurement()
            
            # 全文検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, *
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 10
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            # パフォーマンス測定終了
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            print(f"検索時間: {performance_result['duration']:.3f}秒")
            
            # 結果数の確認
            self.assertGreaterEqual(
                len(results),
                case["expected_min_results"],
                f"期待される最小結果数以上: {len(results)} >= {case['expected_min_results']}"
            )
            
            # 検索結果の内容確認
            for i, result in enumerate(results[:3]):  # 上位3件を確認
                print(f"結果 {i+1}: rowid={result[0]}, rank={result[1]}")
                
                # ランクが有効な値であることを確認
                self.assertIsInstance(
                    result[1],
                    (int, float),
                    f"ランクが数値: {result[1]}"
                )
            
            # パフォーマンスの確認
            PerformanceAssertions.assert_response_time_acceptable(
                performance_result,
                max_duration=0.1  # 100ms以内
            )
            
            print(f"✓ {case['description']} 成功")
    
    def test_phrase_search(self):
        """フレーズ検索テスト"""
        print("\n=== フレーズ検索テスト ===")
        
        # フレーズ検索テストケース
        phrase_cases = [
            {
                "query": '"基礎控除"',
                "table": "tax_documents_fts",
                "description": "基礎控除の完全一致検索"
            },
            {
                "query": '"給与所得控除"',
                "table": "legal_precedents_fts",
                "description": "給与所得控除の完全一致検索"
            },
            {
                "query": '"資産の譲渡"',
                "table": "tax_documents_fts",
                "description": "資産の譲渡の完全一致検索"
            }
        ]
        
        for case in phrase_cases:
            print(f"\n--- {case['description']} ---")
            
            # フレーズ検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, *
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 5
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"フレーズ検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # フレーズ検索の結果確認
            if len(results) > 0:
                # 最上位の結果を詳細確認
                top_result = results[0]
                print(f"最上位結果: rowid={top_result[0]}, rank={top_result[1]}")
                
                # ランクが有効であることを確認
                self.assertIsInstance(
                    top_result[1],
                    (int, float),
                    f"ランクが数値: {top_result[1]}"
                )
            
            print(f"✓ {case['description']} 成功")
    
    def test_boolean_search(self):
        """ブール検索テスト"""
        print("\n=== ブール検索テスト ===")
        
        # ブール検索テストケース
        boolean_cases = [
            {
                "query": "所得税 AND 控除",
                "table": "tax_documents_fts",
                "description": "所得税かつ控除のAND検索"
            },
            {
                "query": "法人税 OR 消費税",
                "table": "tax_documents_fts",
                "description": "法人税または消費税のOR検索"
            },
            {
                "query": "税 NOT 相続",
                "table": "tax_documents_fts",
                "description": "税を含むが相続を含まないNOT検索"
            },
            {
                "query": "(所得税 OR 法人税) AND 控除",
                "table": "tax_documents_fts",
                "description": "複合ブール検索"
            }
        ]
        
        for case in boolean_cases:
            print(f"\n--- {case['description']} ---")
            
            # ブール検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, *
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 10
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"ブール検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # ブール検索の結果確認
            for i, result in enumerate(results[:3]):
                print(f"結果 {i+1}: rowid={result[0]}, rank={result[1]}")
            
            print(f"✓ {case['description']} 成功")
    
    def test_wildcard_search(self):
        """ワイルドカード検索テスト"""
        print("\n=== ワイルドカード検索テスト ===")
        
        # ワイルドカード検索テストケース
        wildcard_cases = [
            {
                "query": "控除*",
                "table": "tax_documents_fts",
                "description": "控除で始まる語の検索"
            },
            {
                "query": "*税",
                "table": "tax_documents_fts",
                "description": "税で終わる語の検索"
            },
            {
                "query": "法人*",
                "table": "tax_documents_fts",
                "description": "法人で始まる語の検索"
            }
        ]
        
        for case in wildcard_cases:
            print(f"\n--- {case['description']} ---")
            
            # ワイルドカード検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, *
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 10
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"ワイルドカード検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # ワイルドカード検索の結果確認
            for i, result in enumerate(results[:3]):
                print(f"結果 {i+1}: rowid={result[0]}, rank={result[1]}")
            
            print(f"✓ {case['description']} 成功")
    
    def test_column_specific_search(self):
        """カラム指定検索テスト"""
        print("\n=== カラム指定検索テスト ===")
        
        # カラム指定検索テストケース
        column_cases = [
            {
                "query": "title:基礎控除",
                "table": "tax_documents_fts",
                "description": "タイトルフィールドでの基礎控除検索"
            },
            {
                "query": "content:損金",
                "table": "tax_documents_fts",
                "description": "内容フィールドでの損金検索"
            },
            {
                "query": "tax_type:所得税",
                "table": "tax_documents_fts",
                "description": "税目フィールドでの所得税検索"
            },
            {
                "query": "court:最高裁判所",
                "table": "legal_precedents_fts",
                "description": "裁判所フィールドでの最高裁判所検索"
            }
        ]
        
        for case in column_cases:
            print(f"\n--- {case['description']} ---")
            
            # カラム指定検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, *
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 5
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"カラム指定検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # カラム指定検索の結果確認
            for i, result in enumerate(results):
                print(f"結果 {i+1}: rowid={result[0]}, rank={result[1]}")
            
            print(f"✓ {case['description']} 成功")
    
    def test_search_performance(self):
        """検索パフォーマンステスト"""
        print("\n=== 検索パフォーマンステスト ===")
        
        # パフォーマンステストケース
        performance_cases = [
            {
                "query": "税",
                "table": "tax_documents_fts",
                "description": "単一語検索パフォーマンス",
                "max_duration": 0.05  # 50ms
            },
            {
                "query": "所得税 AND 控除",
                "table": "tax_documents_fts",
                "description": "ブール検索パフォーマンス",
                "max_duration": 0.1  # 100ms
            },
            {
                "query": '"基礎控除"',
                "table": "tax_documents_fts",
                "description": "フレーズ検索パフォーマンス",
                "max_duration": 0.1  # 100ms
            },
            {
                "query": "控除*",
                "table": "tax_documents_fts",
                "description": "ワイルドカード検索パフォーマンス",
                "max_duration": 0.15  # 150ms
            }
        ]
        
        for case in performance_cases:
            print(f"\n--- {case['description']} ---")
            
            # 複数回実行して平均時間を測定
            execution_times = []
            
            for i in range(5):  # 5回実行
                start_time = self.start_performance_measurement()
                
                cursor = self.connection.cursor()
                cursor.execute(f"""
                    SELECT rowid, rank, *
                    FROM {case['table']}
                    WHERE {case['table']} MATCH ?
                    ORDER BY rank
                    LIMIT 10
                """, (case["query"],))
                
                results = cursor.fetchall()
                
                performance_result = self.end_performance_measurement(start_time)
                execution_times.append(performance_result['duration'])
            
            # 平均実行時間の計算
            avg_duration = sum(execution_times) / len(execution_times)
            min_duration = min(execution_times)
            max_duration = max(execution_times)
            
            print(f"検索クエリ: {case['query']}")
            print(f"平均実行時間: {avg_duration:.4f}秒")
            print(f"最小実行時間: {min_duration:.4f}秒")
            print(f"最大実行時間: {max_duration:.4f}秒")
            print(f"結果数: {len(results)}")
            
            # パフォーマンス要件の確認
            self.assertLessEqual(
                avg_duration,
                case["max_duration"],
                f"平均実行時間が要件を満たしている: {avg_duration:.4f}s <= {case['max_duration']}s"
            )
            
            print(f"✓ {case['description']} 成功")
    
    def test_search_ranking(self):
        """検索ランキングテスト"""
        print("\n=== 検索ランキングテスト ===")
        
        # ランキングテストケース
        ranking_cases = [
            {
                "query": "所得税",
                "table": "tax_documents_fts",
                "description": "所得税検索のランキング確認"
            },
            {
                "query": "控除",
                "table": "tax_documents_fts",
                "description": "控除検索のランキング確認"
            }
        ]
        
        for case in ranking_cases:
            print(f"\n--- {case['description']} ---")
            
            # ランキング付き検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, rank, title, 
                       snippet({case['table']}, 1, '<mark>', '</mark>', '...', 32) as snippet
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 5
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"ランキング検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # ランキングの確認
            previous_rank = None
            for i, result in enumerate(results):
                rowid, rank, title, snippet = result
                
                print(f"順位 {i+1}: rowid={rowid}, rank={rank:.4f}")
                print(f"  タイトル: {title}")
                print(f"  スニペット: {snippet}")
                
                # ランクが降順になっていることを確認
                if previous_rank is not None:
                    self.assertGreaterEqual(
                        previous_rank,
                        rank,
                        f"ランクが降順: {previous_rank} >= {rank}"
                    )
                
                previous_rank = rank
                
                # ランクが有効な値であることを確認
                self.assertIsInstance(
                    rank,
                    (int, float),
                    f"ランクが数値: {rank}"
                )
                
                self.assertGreater(
                    rank,
                    0,
                    f"ランクが正の値: {rank}"
                )
            
            print(f"✓ {case['description']} 成功")
    
    def test_search_highlighting(self):
        """検索ハイライトテスト"""
        print("\n=== 検索ハイライトテスト ===")
        
        # ハイライトテストケース
        highlight_cases = [
            {
                "query": "基礎控除",
                "table": "tax_documents_fts",
                "column_index": 1,  # title
                "description": "基礎控除のハイライト表示"
            },
            {
                "query": "法人税",
                "table": "tax_documents_fts",
                "column_index": 2,  # content
                "description": "法人税のハイライト表示"
            }
        ]
        
        for case in highlight_cases:
            print(f"\n--- {case['description']} ---")
            
            # ハイライト付き検索実行
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT rowid, 
                       snippet({case['table']}, {case['column_index']}, '<b>', '</b>', '...', 64) as highlighted_text
                FROM {case['table']}
                WHERE {case['table']} MATCH ?
                ORDER BY rank
                LIMIT 3
            """, (case["query"],))
            
            results = cursor.fetchall()
            
            print(f"ハイライト検索クエリ: {case['query']}")
            print(f"検索結果数: {len(results)}")
            
            # ハイライト結果の確認
            for i, result in enumerate(results):
                rowid, highlighted_text = result
                
                print(f"結果 {i+1}: rowid={rowid}")
                print(f"  ハイライトテキスト: {highlighted_text}")
                
                # ハイライトマーカーが含まれていることを確認
                self.assertIn(
                    "<b>",
                    highlighted_text,
                    "ハイライト開始マーカーが含まれている"
                )
                
                self.assertIn(
                    "</b>",
                    highlighted_text,
                    "ハイライト終了マーカーが含まれている"
                )
            
            print(f"✓ {case['description']} 成功")
    
    def test_index_maintenance(self):
        """インデックスメンテナンステスト"""
        print("\n=== インデックスメンテナンステスト ===")
        
        # インデックス統計の確認
        cursor = self.connection.cursor()
        
        # FTSテーブルの統計情報取得
        fts_tables = ["tax_documents_fts", "legal_precedents_fts", "tax_circulars_fts"]
        
        for table in fts_tables:
            print(f"\n--- {table} インデックス統計 ---")
            
            # インデックスサイズの確認
            cursor.execute(f"SELECT count(*) FROM {table}")
            doc_count = cursor.fetchone()[0]
            
            print(f"インデックス文書数: {doc_count}")
            
            # インデックスの整合性確認
            cursor.execute(f"INSERT INTO {table}({table}) VALUES('integrity-check')")
            
            print(f"✓ {table} インデックス整合性確認完了")
        
        # インデックス最適化テスト
        print("\n--- インデックス最適化 ---")
        
        start_time = self.start_performance_measurement()
        
        for table in fts_tables:
            cursor.execute(f"INSERT INTO {table}({table}) VALUES('optimize')")
        
        performance_result = self.end_performance_measurement(start_time)
        
        print(f"最適化時間: {performance_result['duration']:.3f}秒")
        
        # 最適化後の検索性能確認
        cursor.execute("""
            SELECT rowid, rank, *
            FROM tax_documents_fts
            WHERE tax_documents_fts MATCH '所得税'
            ORDER BY rank
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        self.assertGreater(
            len(results),
            0,
            "最適化後も検索が正常に動作する"
        )
        
        print("✓ インデックスメンテナンス成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)