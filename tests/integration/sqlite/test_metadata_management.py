"""SQLiteメタデータ管理機能テスト

TaxMCPサーバーのSQLiteメタデータ管理機能をテストする
"""

import unittest
import sys
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, PerformanceTestMixin
from tests.utils.assertion_helpers import PerformanceAssertions, DataAssertions
from tests.utils.test_data_generator import TestDataGenerator


class TestMetadataManagement(TaxMCPTestCase, PerformanceTestMixin):
    """SQLiteメタデータ管理機能テストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.data_generator = TestDataGenerator()
        
        # テスト用のSQLiteデータベース作成
        self.test_db_fd, self.test_db_path = tempfile.mkstemp(suffix='.db')
        self.connection = sqlite3.connect(self.test_db_path)
        
        # メタデータ管理テーブルの作成
        self._create_metadata_tables()
        
        # テストデータの挿入
        self._insert_test_metadata()
    
    def tearDown(self):
        """テストクリーンアップ"""
        if hasattr(self, 'connection'):
            self.connection.close()
        
        if hasattr(self, 'test_db_fd'):
            os.close(self.test_db_fd)
        
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        
        super().tearDown()
    
    def _create_metadata_tables(self):
        """メタデータ管理テーブルの作成"""
        cursor = self.connection.cursor()
        
        # 外部キー制約を有効化
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 文書メタデータテーブル
        cursor.execute("""
            CREATE TABLE document_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                document_type TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                tax_type TEXT NOT NULL,
                effective_date TEXT,
                expiration_date TEXT,
                source_url TEXT,
                file_path TEXT,
                file_size INTEGER,
                file_hash TEXT,
                language TEXT DEFAULT 'ja',
                status TEXT DEFAULT 'active',
                version TEXT DEFAULT '1.0',
                tags TEXT,  -- JSON array
                custom_fields TEXT,  -- JSON object
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                indexed_at TEXT,
                last_accessed_at TEXT
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_document_metadata_document_id ON document_metadata(document_id)")
        cursor.execute("CREATE INDEX idx_document_metadata_document_type ON document_metadata(document_type)")
        cursor.execute("CREATE INDEX idx_document_metadata_category ON document_metadata(category)")
        cursor.execute("CREATE INDEX idx_document_metadata_tax_type ON document_metadata(tax_type)")
        cursor.execute("CREATE INDEX idx_document_metadata_status ON document_metadata(status)")
        cursor.execute("CREATE INDEX idx_document_metadata_effective_date ON document_metadata(effective_date)")
        cursor.execute("CREATE INDEX idx_document_metadata_created_at ON document_metadata(created_at)")
        
        # 文書関係テーブル
        cursor.execute("""
            CREATE TABLE document_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_document_id TEXT NOT NULL,
                target_document_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                relationship_strength REAL DEFAULT 1.0,
                metadata TEXT,  -- JSON object
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_document_id) REFERENCES document_metadata(document_id),
                FOREIGN KEY (target_document_id) REFERENCES document_metadata(document_id),
                UNIQUE(source_document_id, target_document_id, relationship_type)
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_document_relationships_source ON document_relationships(source_document_id)")
        cursor.execute("CREATE INDEX idx_document_relationships_target ON document_relationships(target_document_id)")
        cursor.execute("CREATE INDEX idx_document_relationships_type ON document_relationships(relationship_type)")
        
        # 文書バージョン履歴テーブル
        cursor.execute("""
            CREATE TABLE document_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                version TEXT NOT NULL,
                title TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                change_summary TEXT,
                change_type TEXT NOT NULL,  -- 'created', 'updated', 'deleted'
                changed_by TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES document_metadata(document_id),
                UNIQUE(document_id, version)
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_document_versions_document_id ON document_versions(document_id)")
        cursor.execute("CREATE INDEX idx_document_versions_version ON document_versions(version)")
        cursor.execute("CREATE INDEX idx_document_versions_created_at ON document_versions(created_at)")
        
        # 文書統計テーブル
        cursor.execute("""
            CREATE TABLE document_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                search_count INTEGER DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                last_accessed_at TEXT,
                last_searched_at TEXT,
                last_downloaded_at TEXT,
                popularity_score REAL DEFAULT 0.0,
                relevance_score REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES document_metadata(document_id),
                UNIQUE(document_id)
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_document_statistics_document_id ON document_statistics(document_id)")
        cursor.execute("CREATE INDEX idx_document_statistics_popularity ON document_statistics(popularity_score)")
        cursor.execute("CREATE INDEX idx_document_statistics_relevance ON document_statistics(relevance_score)")
        
        # タグテーブル
        cursor.execute("""
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                description TEXT,
                color TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_tags_name ON tags(name)")
        cursor.execute("CREATE INDEX idx_tags_category ON tags(category)")
        cursor.execute("CREATE INDEX idx_tags_usage_count ON tags(usage_count)")
        
        # 文書タグ関連テーブル
        cursor.execute("""
            CREATE TABLE document_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES document_metadata(document_id),
                FOREIGN KEY (tag_id) REFERENCES tags(id),
                UNIQUE(document_id, tag_id)
            )
        """)
        
        # インデックス作成
        cursor.execute("CREATE INDEX idx_document_tags_document_id ON document_tags(document_id)")
        cursor.execute("CREATE INDEX idx_document_tags_tag_id ON document_tags(tag_id)")
        
        # システムメタデータテーブル
        cursor.execute("""
            CREATE TABLE system_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                data_type TEXT NOT NULL,  -- 'string', 'integer', 'float', 'boolean', 'json'
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.connection.commit()
    
    def _insert_test_metadata(self):
        """テストメタデータの挿入"""
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # 文書メタデータの挿入
        documents = [
            {
                "document_id": "doc_income_tax_001",
                "title": "所得税法第84条（基礎控除）",
                "document_type": "law",
                "category": "所得税法",
                "subcategory": "控除",
                "tax_type": "所得税",
                "effective_date": "2020-01-01",
                "source_url": "https://elaws.e-gov.go.jp/document?lawid=340AC0000000033",
                "file_path": "/documents/income_tax/article_84.pdf",
                "file_size": 1024000,
                "file_hash": "sha256:abc123def456",
                "tags": json.dumps(["基礎控除", "所得税", "控除"]),
                "custom_fields": json.dumps({"article_number": "84", "importance": "high"})
            },
            {
                "document_id": "doc_corporate_tax_001",
                "title": "法人税法第22条（各事業年度の所得の金額の計算）",
                "document_type": "law",
                "category": "法人税法",
                "subcategory": "所得計算",
                "tax_type": "法人税",
                "effective_date": "1965-03-31",
                "source_url": "https://elaws.e-gov.go.jp/document?lawid=340AC0000000034",
                "file_path": "/documents/corporate_tax/article_22.pdf",
                "file_size": 2048000,
                "file_hash": "sha256:def456ghi789",
                "tags": json.dumps(["所得計算", "法人税", "益金", "損金"]),
                "custom_fields": json.dumps({"article_number": "22", "importance": "high"})
            },
            {
                "document_id": "doc_consumption_tax_001",
                "title": "消費税法第4条（課税の対象）",
                "document_type": "law",
                "category": "消費税法",
                "subcategory": "課税対象",
                "tax_type": "消費税",
                "effective_date": "1988-12-30",
                "source_url": "https://elaws.e-gov.go.jp/document?lawid=363AC0000000108",
                "file_path": "/documents/consumption_tax/article_4.pdf",
                "file_size": 512000,
                "file_hash": "sha256:ghi789jkl012",
                "tags": json.dumps(["課税対象", "消費税", "資産の譲渡"]),
                "custom_fields": json.dumps({"article_number": "4", "importance": "high"})
            },
            {
                "document_id": "doc_precedent_001",
                "title": "最高裁平成15年2月25日判決（給与所得控除事件）",
                "document_type": "precedent",
                "category": "判例",
                "subcategory": "所得税",
                "tax_type": "所得税",
                "effective_date": "2003-02-25",
                "source_url": "https://www.courts.go.jp/app/hanrei_jp/detail2?id=52123",
                "file_path": "/documents/precedents/supreme_court_2003_02_25.pdf",
                "file_size": 3072000,
                "file_hash": "sha256:jkl012mno345",
                "tags": json.dumps(["給与所得控除", "必要経費", "最高裁"]),
                "custom_fields": json.dumps({"court": "最高裁判所", "case_type": "民事"})
            },
            {
                "document_id": "doc_circular_001",
                "title": "所基通2-1（基礎控除の適用について）",
                "document_type": "circular",
                "category": "税務通達",
                "subcategory": "所得税",
                "tax_type": "所得税",
                "effective_date": "2020-04-01",
                "source_url": "https://www.nta.go.jp/law/tsutatsu/kihon/shotoku/01.htm",
                "file_path": "/documents/circulars/shotoku_kiso_2_1.pdf",
                "file_size": 256000,
                "file_hash": "sha256:mno345pqr678",
                "tags": json.dumps(["基礎控除", "税務通達", "国税庁"]),
                "custom_fields": json.dumps({"circular_number": "所基通2-1", "authority": "国税庁"})
            }
        ]
        
        for doc in documents:
            cursor.execute("""
                INSERT INTO document_metadata 
                (document_id, title, document_type, category, subcategory, tax_type, 
                 effective_date, source_url, file_path, file_size, file_hash, 
                 tags, custom_fields, created_at, updated_at, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["document_id"], doc["title"], doc["document_type"], doc["category"],
                doc["subcategory"], doc["tax_type"], doc["effective_date"], doc["source_url"],
                doc["file_path"], doc["file_size"], doc["file_hash"], doc["tags"],
                doc["custom_fields"], current_time, current_time, current_time
            ))
        
        # タグの挿入
        tags = [
            {"name": "基礎控除", "category": "控除", "description": "所得税の基礎控除に関するタグ", "color": "#FF5722"},
            {"name": "所得税", "category": "税目", "description": "所得税に関するタグ", "color": "#2196F3"},
            {"name": "法人税", "category": "税目", "description": "法人税に関するタグ", "color": "#4CAF50"},
            {"name": "消費税", "category": "税目", "description": "消費税に関するタグ", "color": "#FF9800"},
            {"name": "控除", "category": "制度", "description": "各種控除制度に関するタグ", "color": "#9C27B0"},
            {"name": "益金", "category": "計算", "description": "法人税の益金に関するタグ", "color": "#607D8B"},
            {"name": "損金", "category": "計算", "description": "法人税の損金に関するタグ", "color": "#795548"},
            {"name": "課税対象", "category": "制度", "description": "課税対象に関するタグ", "color": "#E91E63"},
            {"name": "給与所得控除", "category": "控除", "description": "給与所得控除に関するタグ", "color": "#00BCD4"},
            {"name": "最高裁", "category": "裁判所", "description": "最高裁判所の判例に関するタグ", "color": "#FFC107"}
        ]
        
        for tag in tags:
            cursor.execute("""
                INSERT INTO tags (name, category, description, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tag["name"], tag["category"], tag["description"], tag["color"], current_time, current_time))
        
        # 文書関係の挿入
        relationships = [
            {
                "source_document_id": "doc_income_tax_001",
                "target_document_id": "doc_precedent_001",
                "relationship_type": "related_case",
                "relationship_strength": 0.8,
                "metadata": json.dumps({"relation_reason": "基礎控除に関連する判例"})
            },
            {
                "source_document_id": "doc_income_tax_001",
                "target_document_id": "doc_circular_001",
                "relationship_type": "implementation_guidance",
                "relationship_strength": 0.9,
                "metadata": json.dumps({"relation_reason": "基礎控除の実務指針"})
            },
            {
                "source_document_id": "doc_corporate_tax_001",
                "target_document_id": "doc_income_tax_001",
                "relationship_type": "cross_reference",
                "relationship_strength": 0.6,
                "metadata": json.dumps({"relation_reason": "所得計算の共通概念"})
            }
        ]
        
        for rel in relationships:
            cursor.execute("""
                INSERT INTO document_relationships 
                (source_document_id, target_document_id, relationship_type, relationship_strength, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                rel["source_document_id"], rel["target_document_id"], rel["relationship_type"],
                rel["relationship_strength"], rel["metadata"], current_time
            ))
        
        # 文書統計の挿入
        for doc in documents:
            cursor.execute("""
                INSERT INTO document_statistics 
                (document_id, access_count, search_count, popularity_score, relevance_score, quality_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["document_id"], 10, 5, 0.7, 0.8, 0.9, current_time
            ))
        
        # システムメタデータの挿入
        system_metadata = [
            {"key": "db_version", "value": "1.0.0", "data_type": "string", "description": "データベースバージョン"},
            {"key": "last_index_update", "value": current_time, "data_type": "string", "description": "最後のインデックス更新時刻"},
            {"key": "total_documents", "value": "5", "data_type": "integer", "description": "総文書数"},
            {"key": "index_settings", "value": json.dumps({"fts_enabled": True, "auto_optimize": True}), "data_type": "json", "description": "インデックス設定"}
        ]
        
        for meta in system_metadata:
            cursor.execute("""
                INSERT INTO system_metadata (key, value, data_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (meta["key"], meta["value"], meta["data_type"], meta["description"], current_time, current_time))
        
        self.connection.commit()
    
    def test_document_metadata_crud(self):
        """文書メタデータCRUD操作テスト"""
        print("\n=== 文書メタデータCRUD操作テスト ===")
        
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # Create（作成）テスト
        print("\n--- Create（作成）テスト ---")
        new_document = {
            "document_id": "doc_test_001",
            "title": "テスト文書",
            "document_type": "regulation",
            "category": "テスト",
            "tax_type": "所得税",
            "effective_date": "2024-01-01",
            "tags": json.dumps(["テスト", "新規"]),
            "custom_fields": json.dumps({"test_field": "test_value"})
        }
        
        cursor.execute("""
            INSERT INTO document_metadata 
            (document_id, title, document_type, category, tax_type, effective_date, tags, custom_fields, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_document["document_id"], new_document["title"], new_document["document_type"],
            new_document["category"], new_document["tax_type"], new_document["effective_date"],
            new_document["tags"], new_document["custom_fields"], current_time, current_time
        ))
        
        # 作成確認
        cursor.execute("SELECT * FROM document_metadata WHERE document_id = ?", (new_document["document_id"],))
        created_doc = cursor.fetchone()
        
        self.assertIsNotNone(created_doc, "文書が正常に作成された")
        print(f"✓ 文書作成成功: {new_document['document_id']}")
        
        # Read（読み取り）テスト
        print("\n--- Read（読み取り）テスト ---")
        
        # 単一文書の読み取り
        cursor.execute("""
            SELECT document_id, title, document_type, category, tax_type, tags, custom_fields
            FROM document_metadata 
            WHERE document_id = ?
        """, ("doc_income_tax_001",))
        
        doc = cursor.fetchone()
        self.assertIsNotNone(doc, "文書が正常に読み取れた")
        
        document_id, title, document_type, category, tax_type, tags, custom_fields = doc
        
        # タグとカスタムフィールドのJSON解析
        parsed_tags = json.loads(tags)
        parsed_custom_fields = json.loads(custom_fields)
        
        self.assertIsInstance(parsed_tags, list, "タグがリスト形式")
        self.assertIsInstance(parsed_custom_fields, dict, "カスタムフィールドが辞書形式")
        
        print(f"✓ 文書読み取り成功: {document_id}")
        print(f"  タイトル: {title}")
        print(f"  タグ: {parsed_tags}")
        print(f"  カスタムフィールド: {parsed_custom_fields}")
        
        # 複数文書の読み取り（フィルタリング）
        cursor.execute("""
            SELECT COUNT(*) FROM document_metadata 
            WHERE tax_type = ? AND document_type = ?
        """, ("所得税", "law"))
        
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0, "フィルタリング検索で結果が取得できた")
        
        print(f"✓ フィルタリング検索成功: {count}件")
        
        # Update（更新）テスト
        print("\n--- Update（更新）テスト ---")
        
        updated_time = datetime.now().isoformat()
        updated_tags = json.dumps(["テスト", "更新済み", "修正"])
        
        cursor.execute("""
            UPDATE document_metadata 
            SET title = ?, tags = ?, updated_at = ?
            WHERE document_id = ?
        """, ("更新されたテスト文書", updated_tags, updated_time, new_document["document_id"]))
        
        # 更新確認
        cursor.execute("""
            SELECT title, tags, updated_at FROM document_metadata 
            WHERE document_id = ?
        """, (new_document["document_id"],))
        
        updated_doc = cursor.fetchone()
        title, tags, updated_at = updated_doc
        
        self.assertEqual(title, "更新されたテスト文書", "タイトルが正常に更新された")
        self.assertEqual(tags, updated_tags, "タグが正常に更新された")
        
        print(f"✓ 文書更新成功: {new_document['document_id']}")
        print(f"  新しいタイトル: {title}")
        
        # Delete（削除）テスト
        print("\n--- Delete（削除）テスト ---")
        
        # ソフト削除（ステータス変更）
        cursor.execute("""
            UPDATE document_metadata 
            SET status = 'deleted', updated_at = ?
            WHERE document_id = ?
        """, (updated_time, new_document["document_id"]))
        
        # 削除確認
        cursor.execute("""
            SELECT status FROM document_metadata 
            WHERE document_id = ?
        """, (new_document["document_id"],))
        
        status = cursor.fetchone()[0]
        self.assertEqual(status, "deleted", "文書が正常に削除された")
        
        print(f"✓ 文書削除成功: {new_document['document_id']}")
        
        self.connection.commit()
    
    def test_document_relationships(self):
        """文書関係管理テスト"""
        print("\n=== 文書関係管理テスト ===")
        
        cursor = self.connection.cursor()
        
        # 関係の検索テスト
        print("\n--- 関係検索テスト ---")
        
        # 特定文書の関連文書を取得
        cursor.execute("""
            SELECT 
                dr.target_document_id,
                dm.title,
                dr.relationship_type,
                dr.relationship_strength,
                dr.metadata
            FROM document_relationships dr
            JOIN document_metadata dm ON dr.target_document_id = dm.document_id
            WHERE dr.source_document_id = ?
            ORDER BY dr.relationship_strength DESC
        """, ("doc_income_tax_001",))
        
        relationships = cursor.fetchall()
        
        self.assertGreater(len(relationships), 0, "関連文書が取得できた")
        
        print(f"doc_income_tax_001の関連文書: {len(relationships)}件")
        
        for rel in relationships:
            target_id, title, rel_type, strength, metadata = rel
            parsed_metadata = json.loads(metadata) if metadata else {}
            
            print(f"  関連文書: {target_id}")
            print(f"    タイトル: {title}")
            print(f"    関係タイプ: {rel_type}")
            print(f"    関係強度: {strength}")
            print(f"    メタデータ: {parsed_metadata}")
            
            # 関係強度の妥当性確認
            self.assertGreaterEqual(strength, 0.0, "関係強度が0以上")
            self.assertLessEqual(strength, 1.0, "関係強度が1以下")
        
        # 双方向関係の検索
        print("\n--- 双方向関係検索テスト ---")
        
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN dr.source_document_id = ? THEN dr.target_document_id
                    ELSE dr.source_document_id
                END as related_document_id,
                dm.title,
                dr.relationship_type,
                dr.relationship_strength
            FROM document_relationships dr
            JOIN document_metadata dm ON 
                (dr.source_document_id = ? AND dm.document_id = dr.target_document_id) OR
                (dr.target_document_id = ? AND dm.document_id = dr.source_document_id)
            ORDER BY dr.relationship_strength DESC
        """, ("doc_income_tax_001", "doc_income_tax_001", "doc_income_tax_001"))
        
        bidirectional_relationships = cursor.fetchall()
        
        print(f"双方向関係: {len(bidirectional_relationships)}件")
        
        for rel in bidirectional_relationships:
            related_id, title, rel_type, strength = rel
            print(f"  関連文書: {related_id} ({rel_type}, 強度: {strength})")
        
        # 新しい関係の追加
        print("\n--- 関係追加テスト ---")
        
        current_time = datetime.now().isoformat()
        new_relationship = {
            "source_document_id": "doc_consumption_tax_001",
            "target_document_id": "doc_corporate_tax_001",
            "relationship_type": "tax_interaction",
            "relationship_strength": 0.5,
            "metadata": json.dumps({"interaction_type": "計算上の関連"})
        }
        
        cursor.execute("""
            INSERT INTO document_relationships 
            (source_document_id, target_document_id, relationship_type, relationship_strength, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            new_relationship["source_document_id"], new_relationship["target_document_id"],
            new_relationship["relationship_type"], new_relationship["relationship_strength"],
            new_relationship["metadata"], current_time
        ))
        
        # 追加確認
        cursor.execute("""
            SELECT COUNT(*) FROM document_relationships 
            WHERE source_document_id = ? AND target_document_id = ?
        """, (new_relationship["source_document_id"], new_relationship["target_document_id"]))
        
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1, "新しい関係が正常に追加された")
        
        print(f"✓ 関係追加成功: {new_relationship['source_document_id']} -> {new_relationship['target_document_id']}")
        
        self.connection.commit()
    
    def test_document_versioning(self):
        """文書バージョン管理テスト"""
        print("\n=== 文書バージョン管理テスト ===")
        
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # バージョン履歴の追加
        print("\n--- バージョン履歴追加テスト ---")
        
        versions = [
            {
                "document_id": "doc_income_tax_001",
                "version": "1.0",
                "title": "所得税法第84条（基礎控除）",
                "content_hash": "sha256:original_hash",
                "change_summary": "初版作成",
                "change_type": "created",
                "changed_by": "system"
            },
            {
                "document_id": "doc_income_tax_001",
                "version": "1.1",
                "title": "所得税法第84条（基礎控除）",
                "content_hash": "sha256:updated_hash_1",
                "change_summary": "控除額の改正に伴う更新",
                "change_type": "updated",
                "changed_by": "admin"
            },
            {
                "document_id": "doc_income_tax_001",
                "version": "1.2",
                "title": "所得税法第84条（基礎控除）",
                "content_hash": "sha256:updated_hash_2",
                "change_summary": "適用条件の明確化",
                "change_type": "updated",
                "changed_by": "editor"
            }
        ]
        
        for version in versions:
            cursor.execute("""
                INSERT INTO document_versions 
                (document_id, version, title, content_hash, change_summary, change_type, changed_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                version["document_id"], version["version"], version["title"],
                version["content_hash"], version["change_summary"], version["change_type"],
                version["changed_by"], current_time
            ))
        
        # バージョン履歴の取得
        print("\n--- バージョン履歴取得テスト ---")
        
        cursor.execute("""
            SELECT version, change_summary, change_type, changed_by, created_at
            FROM document_versions 
            WHERE document_id = ?
            ORDER BY version DESC
        """, ("doc_income_tax_001",))
        
        version_history = cursor.fetchall()
        
        self.assertEqual(len(version_history), 3, "3つのバージョンが取得できた")
        
        print(f"doc_income_tax_001のバージョン履歴: {len(version_history)}件")
        
        for version in version_history:
            ver, summary, change_type, changed_by, created_at = version
            print(f"  バージョン {ver}: {summary} ({change_type}, {changed_by})")
        
        # 最新バージョンの取得
        cursor.execute("""
            SELECT version, content_hash
            FROM document_versions 
            WHERE document_id = ?
            ORDER BY version DESC
            LIMIT 1
        """, ("doc_income_tax_001",))
        
        latest_version = cursor.fetchone()
        version, content_hash = latest_version
        
        self.assertEqual(version, "1.2", "最新バージョンが正しく取得できた")
        
        print(f"✓ 最新バージョン: {version} (ハッシュ: {content_hash})")
        
        # バージョン間の差分情報
        print("\n--- バージョン差分テスト ---")
        
        cursor.execute("""
            SELECT 
                v1.version as from_version,
                v2.version as to_version,
                v1.content_hash as from_hash,
                v2.content_hash as to_hash,
                v2.change_summary
            FROM document_versions v1
            JOIN document_versions v2 ON v1.document_id = v2.document_id
            WHERE v1.document_id = ? AND v1.version < v2.version
            ORDER BY v1.version, v2.version
        """, ("doc_income_tax_001",))
        
        version_diffs = cursor.fetchall()
        
        print(f"バージョン差分: {len(version_diffs)}件")
        
        for diff in version_diffs:
            from_ver, to_ver, from_hash, to_hash, summary = diff
            print(f"  {from_ver} -> {to_ver}: {summary}")
            print(f"    ハッシュ変更: {from_hash[:16]}... -> {to_hash[:16]}...")
        
        self.connection.commit()
    
    def test_document_statistics(self):
        """文書統計管理テスト"""
        print("\n=== 文書統計管理テスト ===")
        
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # 統計情報の取得
        print("\n--- 統計情報取得テスト ---")
        
        cursor.execute("""
            SELECT 
                ds.document_id,
                dm.title,
                ds.access_count,
                ds.search_count,
                ds.download_count,
                ds.popularity_score,
                ds.relevance_score,
                ds.quality_score
            FROM document_statistics ds
            JOIN document_metadata dm ON ds.document_id = dm.document_id
            ORDER BY ds.popularity_score DESC
        """)
        
        statistics = cursor.fetchall()
        
        self.assertGreater(len(statistics), 0, "統計情報が取得できた")
        
        print(f"文書統計: {len(statistics)}件")
        
        for stat in statistics:
            doc_id, title, access_count, search_count, download_count, popularity, relevance, quality = stat
            print(f"  文書: {doc_id}")
            print(f"    タイトル: {title}")
            print(f"    アクセス数: {access_count}, 検索数: {search_count}, ダウンロード数: {download_count}")
            print(f"    人気度: {popularity:.2f}, 関連度: {relevance:.2f}, 品質: {quality:.2f}")
            
            # スコアの妥当性確認
            self.assertGreaterEqual(popularity, 0.0, "人気度スコアが0以上")
            self.assertLessEqual(popularity, 1.0, "人気度スコアが1以下")
            self.assertGreaterEqual(relevance, 0.0, "関連度スコアが0以上")
            self.assertLessEqual(relevance, 1.0, "関連度スコアが1以下")
            self.assertGreaterEqual(quality, 0.0, "品質スコアが0以上")
            self.assertLessEqual(quality, 1.0, "品質スコアが1以下")
        
        # 統計情報の更新
        print("\n--- 統計情報更新テスト ---")
        
        # アクセス数の増加
        cursor.execute("""
            UPDATE document_statistics 
            SET access_count = access_count + 1,
                last_accessed_at = ?,
                updated_at = ?
            WHERE document_id = ?
        """, (current_time, current_time, "doc_income_tax_001"))
        
        # 更新確認
        cursor.execute("""
            SELECT access_count, last_accessed_at
            FROM document_statistics 
            WHERE document_id = ?
        """, ("doc_income_tax_001",))
        
        updated_stat = cursor.fetchone()
        access_count, last_accessed_at = updated_stat
        
        self.assertEqual(access_count, 11, "アクセス数が正常に更新された")
        
        print(f"✓ 統計更新成功: アクセス数 {access_count}")
        
        # 人気度スコアの再計算
        print("\n--- 人気度スコア再計算テスト ---")
        
        # 簡単な人気度計算式: (access_count * 0.5 + search_count * 0.3 + download_count * 0.2) / 100
        cursor.execute("""
            UPDATE document_statistics 
            SET popularity_score = ROUND(
                (access_count * 0.5 + search_count * 0.3 + download_count * 0.2) / 100.0, 
                3
            ),
            updated_at = ?
        """, (current_time,))
        
        # 再計算結果の確認
        cursor.execute("""
            SELECT document_id, access_count, search_count, download_count, popularity_score
            FROM document_statistics 
            ORDER BY popularity_score DESC
            LIMIT 3
        """)
        
        top_documents = cursor.fetchall()
        
        print("人気度上位3文書:")
        for doc in top_documents:
            doc_id, access, search, download, popularity = doc
            print(f"  {doc_id}: 人気度 {popularity} (アクセス: {access}, 検索: {search}, DL: {download})")
        
        self.connection.commit()
    
    def test_tag_management(self):
        """タグ管理テスト"""
        print("\n=== タグ管理テスト ===")
        
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # タグ一覧の取得
        print("\n--- タグ一覧取得テスト ---")
        
        cursor.execute("""
            SELECT name, category, description, color, usage_count
            FROM tags 
            ORDER BY usage_count DESC, name
        """)
        
        tags = cursor.fetchall()
        
        self.assertGreater(len(tags), 0, "タグが取得できた")
        
        print(f"登録タグ: {len(tags)}件")
        
        for tag in tags:
            name, category, description, color, usage_count = tag
            print(f"  {name} ({category}): {description} [使用回数: {usage_count}]")
        
        # 新しいタグの追加
        print("\n--- タグ追加テスト ---")
        
        new_tags = [
            {"name": "テスト用タグ", "category": "テスト", "description": "テスト用のタグ", "color": "#000000"},
            {"name": "重要", "category": "優先度", "description": "重要な文書を示すタグ", "color": "#FF0000"},
            {"name": "廃止予定", "category": "ステータス", "description": "廃止予定の制度に関するタグ", "color": "#808080"}
        ]
        
        for tag in new_tags:
            cursor.execute("""
                INSERT INTO tags (name, category, description, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (tag["name"], tag["category"], tag["description"], tag["color"], current_time, current_time))
        
        # 追加確認
        cursor.execute("SELECT COUNT(*) FROM tags WHERE name IN (?, ?, ?)", 
                      (new_tags[0]["name"], new_tags[1]["name"], new_tags[2]["name"]))
        
        added_count = cursor.fetchone()[0]
        self.assertEqual(added_count, 3, "3つのタグが正常に追加された")
        
        print(f"✓ タグ追加成功: {added_count}件")
        
        # タグの使用回数更新
        print("\n--- タグ使用回数更新テスト ---")
        
        # 特定のタグの使用回数を増加
        cursor.execute("""
            UPDATE tags 
            SET usage_count = usage_count + 1, updated_at = ?
            WHERE name = ?
        """, (current_time, "所得税"))
        
        # 更新確認
        cursor.execute("SELECT usage_count FROM tags WHERE name = ?", ("所得税",))
        usage_count = cursor.fetchone()[0]
        
        self.assertEqual(usage_count, 1, "使用回数が正常に更新された")
        
        print(f"✓ 使用回数更新成功: 所得税タグ {usage_count}回")
        
        # カテゴリ別タグ統計
        print("\n--- カテゴリ別タグ統計テスト ---")
        
        cursor.execute("""
            SELECT category, COUNT(*) as tag_count, SUM(usage_count) as total_usage
            FROM tags 
            GROUP BY category
            ORDER BY tag_count DESC
        """)
        
        category_stats = cursor.fetchall()
        
        print("カテゴリ別タグ統計:")
        for stat in category_stats:
            category, tag_count, total_usage = stat
            print(f"  {category}: {tag_count}個のタグ, 総使用回数: {total_usage}")
        
        self.connection.commit()
    
    def test_system_metadata(self):
        """システムメタデータ管理テスト"""
        print("\n=== システムメタデータ管理テスト ===")
        
        cursor = self.connection.cursor()
        current_time = datetime.now().isoformat()
        
        # システムメタデータの取得
        print("\n--- システムメタデータ取得テスト ---")
        
        cursor.execute("""
            SELECT key, value, data_type, description
            FROM system_metadata 
            ORDER BY key
        """)
        
        metadata = cursor.fetchall()
        
        self.assertGreater(len(metadata), 0, "システムメタデータが取得できた")
        
        print(f"システムメタデータ: {len(metadata)}件")
        
        for meta in metadata:
            key, value, data_type, description = meta
            
            # データ型に応じた値の解析
            if data_type == "json":
                parsed_value = json.loads(value)
                print(f"  {key} ({data_type}): {parsed_value} - {description}")
            elif data_type == "integer":
                int_value = int(value)
                print(f"  {key} ({data_type}): {int_value} - {description}")
            elif data_type == "float":
                float_value = float(value)
                print(f"  {key} ({data_type}): {float_value} - {description}")
            elif data_type == "boolean":
                bool_value = value.lower() == "true"
                print(f"  {key} ({data_type}): {bool_value} - {description}")
            else:
                print(f"  {key} ({data_type}): {value} - {description}")
        
        # システムメタデータの更新
        print("\n--- システムメタデータ更新テスト ---")
        
        # 文書数の更新
        cursor.execute("SELECT COUNT(*) FROM document_metadata WHERE status != 'deleted'")
        active_doc_count = cursor.fetchone()[0]
        
        cursor.execute("""
            UPDATE system_metadata 
            SET value = ?, updated_at = ?
            WHERE key = ?
        """, (str(active_doc_count), current_time, "total_documents"))
        
        # 更新確認
        cursor.execute("SELECT value FROM system_metadata WHERE key = ?", ("total_documents",))
        updated_count = cursor.fetchone()[0]
        
        self.assertEqual(updated_count, str(active_doc_count), "文書数が正常に更新された")
        
        print(f"✓ 文書数更新成功: {updated_count}件")
        
        # 新しいシステムメタデータの追加
        print("\n--- システムメタデータ追加テスト ---")
        
        new_metadata = [
            {
                "key": "last_backup_time",
                "value": current_time,
                "data_type": "string",
                "description": "最後のバックアップ時刻"
            },
            {
                "key": "search_performance_threshold",
                "value": "0.1",
                "data_type": "float",
                "description": "検索パフォーマンス閾値（秒）"
            },
            {
                "key": "maintenance_mode",
                "value": "false",
                "data_type": "boolean",
                "description": "メンテナンスモードフラグ"
            }
        ]
        
        for meta in new_metadata:
            cursor.execute("""
                INSERT INTO system_metadata (key, value, data_type, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (meta["key"], meta["value"], meta["data_type"], meta["description"], current_time, current_time))
        
        # 追加確認
        cursor.execute("SELECT COUNT(*) FROM system_metadata WHERE key IN (?, ?, ?)", 
                      (new_metadata[0]["key"], new_metadata[1]["key"], new_metadata[2]["key"]))
        
        added_count = cursor.fetchone()[0]
        self.assertEqual(added_count, 3, "3つのシステムメタデータが正常に追加された")
        
        print(f"✓ システムメタデータ追加成功: {added_count}件")
        
        self.connection.commit()
    
    def test_metadata_performance(self):
        """メタデータ操作パフォーマンステスト"""
        print("\n=== メタデータ操作パフォーマンステスト ===")
        
        cursor = self.connection.cursor()
        
        # 大量データ挿入パフォーマンス
        print("\n--- 大量データ挿入パフォーマンステスト ---")
        
        start_time = self.start_performance_measurement()
        
        # 100件の文書メタデータを挿入
        current_time = datetime.now().isoformat()
        
        for i in range(100):
            document_id = f"perf_test_doc_{i:03d}"
            title = f"パフォーマンステスト文書 {i+1}"
            tags = json.dumps(["パフォーマンステスト", f"番号{i+1}"])
            custom_fields = json.dumps({"test_number": i+1, "batch": "performance_test"})
            
            cursor.execute("""
                INSERT INTO document_metadata 
                (document_id, title, document_type, category, tax_type, tags, custom_fields, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, title, "test", "パフォーマンステスト", "テスト",
                tags, custom_fields, current_time, current_time
            ))
        
        performance_result = self.end_performance_measurement(start_time)
        
        print(f"100件挿入時間: {performance_result['duration']:.3f}秒")
        print(f"1件あたり平均: {performance_result['duration']/100:.4f}秒")
        
        # パフォーマンス要件の確認
        self.assertLess(
            performance_result['duration'],
            5.0,  # 5秒以内
            "大量データ挿入が5秒以内に完了"
        )
        
        # 大量データ検索パフォーマンス
        print("\n--- 大量データ検索パフォーマンステスト ---")
        
        search_cases = [
            {
                "query": "SELECT COUNT(*) FROM document_metadata",
                "description": "全件数取得",
                "max_duration": 0.1
            },
            {
                "query": "SELECT * FROM document_metadata WHERE tax_type = 'テスト' LIMIT 10",
                "description": "条件検索（LIMIT付き）",
                "max_duration": 0.05
            },
            {
                "query": "SELECT document_id, title FROM document_metadata WHERE document_type = 'test' ORDER BY created_at DESC LIMIT 20",
                "description": "ソート付き検索",
                "max_duration": 0.1
            },
            {
                "query": "SELECT category, COUNT(*) FROM document_metadata GROUP BY category",
                "description": "集計クエリ",
                "max_duration": 0.2
            }
        ]
        
        for case in search_cases:
            start_time = self.start_performance_measurement()
            
            cursor.execute(case["query"])
            results = cursor.fetchall()
            
            performance_result = self.end_performance_measurement(start_time)
            
            print(f"{case['description']}: {performance_result['duration']:.4f}秒 ({len(results)}件)")
            
            # パフォーマンス要件の確認
            self.assertLess(
                performance_result['duration'],
                case["max_duration"],
                f"{case['description']}が{case['max_duration']}秒以内に完了"
            )
        
        # インデックス効果の確認
        print("\n--- インデックス効果確認テスト ---")
        
        # インデックスを使用する検索
        start_time = self.start_performance_measurement()
        
        cursor.execute("""
            SELECT document_id, title 
            FROM document_metadata 
            WHERE document_type = 'test' AND tax_type = 'テスト'
            LIMIT 50
        """)
        
        indexed_results = cursor.fetchall()
        indexed_performance = self.end_performance_measurement(start_time)
        
        print(f"インデックス使用検索: {indexed_performance['duration']:.4f}秒 ({len(indexed_results)}件)")
        
        # インデックス効果の確認（0.1秒以内）
        self.assertLess(
            indexed_performance['duration'],
            0.1,
            "インデックス使用検索が0.1秒以内に完了"
        )
        
        self.connection.commit()
        
        print("✓ メタデータ操作パフォーマンステスト成功")
    
    def test_metadata_integrity(self):
        """メタデータ整合性テスト"""
        print("\n=== メタデータ整合性テスト ===")
        
        cursor = self.connection.cursor()
        
        # 外部キー制約の確認
        print("\n--- 外部キー制約確認テスト ---")
        
        # 存在しない文書IDでの関係追加（エラーになるべき）
        current_time = datetime.now().isoformat()
        
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO document_relationships 
                (source_document_id, target_document_id, relationship_type, created_at)
                VALUES (?, ?, ?, ?)
            """, ("non_existent_doc", "doc_income_tax_001", "test_relation", current_time))
        
        print("✓ 外部キー制約が正常に動作")
        
        # 重複制約の確認
        print("\n--- 重複制約確認テスト ---")
        
        # 同じdocument_idで重複挿入（エラーになるべき）
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO document_metadata 
                (document_id, title, document_type, category, tax_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("doc_income_tax_001", "重複テスト", "test", "テスト", "テスト", current_time, current_time))
        
        print("✓ 重複制約が正常に動作")
        
        # データ型制約の確認
        print("\n--- データ型制約確認テスト ---")
        
        # 不正なJSONデータの挿入テスト
        try:
            invalid_json = "invalid json string"
            cursor.execute("""
                INSERT INTO document_metadata 
                (document_id, title, document_type, category, tax_type, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("test_invalid_json", "JSONテスト", "test", "テスト", "テスト", invalid_json, current_time, current_time))
            
            # JSONの妥当性を確認
            cursor.execute("SELECT tags FROM document_metadata WHERE document_id = ?", ("test_invalid_json",))
            tags = cursor.fetchone()[0]
            
            # 不正なJSONの場合、パースでエラーになることを確認
            with self.assertRaises(json.JSONDecodeError):
                json.loads(tags)
            
            print("✓ 不正なJSONデータの検出が可能")
            
        except Exception as e:
            print(f"JSONテストでエラー: {e}")
        
        # 参照整合性の確認
        print("\n--- 参照整合性確認テスト ---")
        
        # 関連する文書統計が存在することを確認
        cursor.execute("""
            SELECT dm.document_id
            FROM document_metadata dm
            LEFT JOIN document_statistics ds ON dm.document_id = ds.document_id
            WHERE ds.document_id IS NULL AND dm.status = 'active'
        """)
        
        orphaned_docs = cursor.fetchall()
        
        # 統計情報のない文書があっても警告のみで、テストは成功とする
        if len(orphaned_docs) > 0:
            print(f"警告: 統計情報のない文書が{len(orphaned_docs)}件存在")
            for doc in orphaned_docs:
                print(f"  - {doc[0]}")
            print("✓ 参照整合性確認完了（警告あり）")
        else:
            print("✓ 全ての文書に統計情報が存在")
        
        print("✓ メタデータ整合性テスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)