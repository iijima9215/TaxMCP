#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Indexer for Tax Documents

This module provides SQLite-based indexing and full-text search capabilities
for Ministry of Finance documents and other tax-related materials.
"""

import sqlite3
import os
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import re

# Third-party imports
import jieba
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.analysis import StandardAnalyzer
from whoosh.qparser import QueryParser
from whoosh.query import Term, And, Or

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DocumentMetadata:
    """Document metadata structure"""
    doc_id: str
    title: str
    source_url: str
    content_hash: str
    document_type: str  # 'tax_reform', 'law_article', 'tax_answer', etc.
    category: str  # 'income_tax', 'corporate_tax', 'consumption_tax', etc.
    year: int
    last_updated: datetime
    keywords: List[str]
    content_preview: str  # First 200 characters
    file_size: int
    language: str = 'ja'

class SQLiteIndexer:
    """SQLite-based document indexer with full-text search capabilities"""
    
    def __init__(self, db_path: str = "tax_documents.db", index_dir: str = "search_index"):
        self.db_path = db_path
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Initialize Whoosh index
        self._init_search_index()
        
        # Configure jieba for Japanese text segmentation
        jieba.initialize()
        
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_url TEXT,
                    content_hash TEXT UNIQUE,
                    document_type TEXT,
                    category TEXT,
                    year INTEGER,
                    last_updated TIMESTAMP,
                    keywords TEXT,  -- JSON array
                    content_preview TEXT,
                    file_size INTEGER,
                    language TEXT DEFAULT 'ja'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_content (
                    doc_id TEXT PRIMARY KEY,
                    full_content TEXT,
                    processed_content TEXT,  -- Segmented for search
                    FOREIGN KEY (doc_id) REFERENCES documents (doc_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_stats (
                    query TEXT,
                    result_count INTEGER,
                    search_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_year ON documents(year)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_updated ON documents(last_updated)")
            
            conn.commit()
            
    def _init_search_index(self):
        """Initialize Whoosh full-text search index"""
        schema = Schema(
            doc_id=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=StandardAnalyzer()),
            content=TEXT(analyzer=StandardAnalyzer()),
            processed_content=TEXT(analyzer=StandardAnalyzer()),
            document_type=KEYWORD(stored=True),
            category=KEYWORD(stored=True),
            year=KEYWORD(stored=True),
            keywords=KEYWORD(stored=True, commas=True),
            last_updated=DATETIME(stored=True)
        )
        
        if not index.exists_in(self.index_dir):
            self.search_index = index.create_in(self.index_dir, schema)
        else:
            self.search_index = index.open_dir(self.index_dir)
            
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for duplicate detection"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _segment_japanese_text(self, text: str) -> str:
        """Segment Japanese text using jieba for better search"""
        # Use jieba to segment the text
        segments = jieba.cut(text, cut_all=False)
        return ' '.join(segments)
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[str]:
        """Extract keywords from text using TF-IDF-like approach"""
        # Simple keyword extraction - can be enhanced with more sophisticated methods
        # Remove common Japanese particles and conjunctions
        stop_words = {'の', 'に', 'は', 'を', 'が', 'で', 'と', 'から', 'まで', 'より', 'について', 'による', 'として'}
        
        # Segment text and filter
        words = jieba.cut(text, cut_all=False)
        keywords = []
        
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stop_words and not word.isdigit():
                keywords.append(word)
        
        # Count frequency and return top keywords
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    def add_document(self, 
                    doc_id: str,
                    title: str,
                    content: str,
                    source_url: str = "",
                    document_type: str = "unknown",
                    category: str = "general",
                    year: int = None) -> bool:
        """Add or update a document in the index"""
        try:
            content_hash = self._calculate_content_hash(content)
            
            # Check if document already exists with same content
            with sqlite3.connect(self.db_path) as conn:
                existing = conn.execute(
                    "SELECT doc_id FROM documents WHERE content_hash = ?",
                    (content_hash,)
                ).fetchone()
                
                if existing and existing[0] != doc_id:
                    logger.info(f"Document with same content already exists: {existing[0]}")
                    return False
            
            # Process content
            processed_content = self._segment_japanese_text(content)
            keywords = self._extract_keywords(content)
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            if year is None:
                year = datetime.now().year
            
            # Create metadata
            metadata = DocumentMetadata(
                doc_id=doc_id,
                title=title,
                source_url=source_url,
                content_hash=content_hash,
                document_type=document_type,
                category=category,
                year=year,
                last_updated=datetime.now(),
                keywords=keywords,
                content_preview=content_preview,
                file_size=len(content.encode('utf-8')),
                language='ja'
            )
            
            # Store in SQLite
            with sqlite3.connect(self.db_path) as conn:
                # Insert/update document metadata
                conn.execute("""
                    INSERT OR REPLACE INTO documents 
                    (doc_id, title, source_url, content_hash, document_type, category, 
                     year, last_updated, keywords, content_preview, file_size, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata.doc_id, metadata.title, metadata.source_url,
                    metadata.content_hash, metadata.document_type, metadata.category,
                    metadata.year, metadata.last_updated, json.dumps(metadata.keywords),
                    metadata.content_preview, metadata.file_size, metadata.language
                ))
                
                # Insert/update document content
                conn.execute("""
                    INSERT OR REPLACE INTO document_content 
                    (doc_id, full_content, processed_content)
                    VALUES (?, ?, ?)
                """, (doc_id, content, processed_content))
                
                conn.commit()
            
            # Add to Whoosh index
            writer = self.search_index.writer()
            writer.update_document(
                doc_id=doc_id,
                title=title,
                content=content,
                processed_content=processed_content,
                document_type=document_type,
                category=category,
                year=str(year),
                keywords=','.join(keywords),
                last_updated=metadata.last_updated
            )
            writer.commit()
            
            logger.info(f"Successfully indexed document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document {doc_id}: {e}")
            return False
    
    def search_documents(self, 
                        query: str,
                        document_type: Optional[str] = None,
                        category: Optional[str] = None,
                        year: Optional[int] = None,
                        limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents using full-text search"""
        start_time = datetime.now()
        
        try:
            with self.search_index.searcher() as searcher:
                # Build query
                query_parts = []
                
                # Main text query
                if query.strip():
                    # Search in both title and content
                    title_parser = QueryParser("title", self.search_index.schema)
                    content_parser = QueryParser("processed_content", self.search_index.schema)
                    
                    title_query = title_parser.parse(query)
                    content_query = content_parser.parse(query)
                    
                    text_query = Or([title_query, content_query])
                    query_parts.append(text_query)
                
                # Filter by document type
                if document_type:
                    query_parts.append(Term("document_type", document_type))
                
                # Filter by category
                if category:
                    query_parts.append(Term("category", category))
                
                # Filter by year
                if year:
                    query_parts.append(Term("year", str(year)))
                
                # Combine all query parts
                if query_parts:
                    final_query = And(query_parts) if len(query_parts) > 1 else query_parts[0]
                else:
                    # If no query, return recent documents
                    final_query = None
                
                # Execute search
                if final_query:
                    results = searcher.search(final_query, limit=limit)
                else:
                    results = searcher.documents()
                
                # Format results
                formatted_results = []
                for result in results:
                    doc_id = result['doc_id']
                    
                    # Get additional metadata from SQLite
                    with sqlite3.connect(self.db_path) as conn:
                        metadata = conn.execute("""
                            SELECT title, source_url, document_type, category, year,
                                   last_updated, keywords, content_preview
                            FROM documents WHERE doc_id = ?
                        """, (doc_id,)).fetchone()
                        
                        if metadata:
                            formatted_results.append({
                                'doc_id': doc_id,
                                'title': metadata[0],
                                'source_url': metadata[1],
                                'document_type': metadata[2],
                                'category': metadata[3],
                                'year': metadata[4],
                                'last_updated': metadata[5],
                                'keywords': json.loads(metadata[6]) if metadata[6] else [],
                                'content_preview': metadata[7],
                                'relevance_score': result.score if hasattr(result, 'score') else 1.0
                            })
                
                # Log search statistics
                search_time = (datetime.now() - start_time).total_seconds()
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO search_stats (query, result_count, search_time) VALUES (?, ?, ?)",
                        (query, len(formatted_results), search_time)
                    )
                    conn.commit()
                
                return formatted_results
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_document_content(self, doc_id: str) -> Optional[str]:
        """Retrieve full content of a document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute(
                    "SELECT full_content FROM document_content WHERE doc_id = ?",
                    (doc_id,)
                ).fetchone()
                
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error retrieving document content: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing and search statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Document statistics
                doc_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(DISTINCT document_type) as document_types,
                        COUNT(DISTINCT category) as categories,
                        MIN(year) as earliest_year,
                        MAX(year) as latest_year,
                        SUM(file_size) as total_size
                    FROM documents
                """).fetchone()
                
                # Search statistics
                search_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_searches,
                        AVG(search_time) as avg_search_time,
                        AVG(result_count) as avg_results
                    FROM search_stats
                    WHERE timestamp > datetime('now', '-30 days')
                """).fetchone()
                
                # Category breakdown
                category_stats = conn.execute("""
                    SELECT category, COUNT(*) as count
                    FROM documents
                    GROUP BY category
                    ORDER BY count DESC
                """).fetchall()
                
                return {
                    'total_documents': doc_stats[0] or 0,
                    'document_types': doc_stats[1] or 0,
                    'categories': doc_stats[2] or 0,
                    'year_range': f"{doc_stats[3] or 'N/A'}-{doc_stats[4] or 'N/A'}",
                    'total_size_mb': round((doc_stats[5] or 0) / 1024 / 1024, 2),
                    'total_searches_30d': search_stats[0] or 0,
                    'avg_search_time_ms': round((search_stats[1] or 0) * 1000, 2),
                    'avg_results_per_search': round(search_stats[2] or 0, 1),
                    'category_breakdown': dict(category_stats)
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_documents(self, days: int = 365) -> int:
        """Remove documents older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                # Get documents to remove
                old_docs = conn.execute(
                    "SELECT doc_id FROM documents WHERE last_updated < ?",
                    (cutoff_date,)
                ).fetchall()
                
                # Remove from database
                conn.execute(
                    "DELETE FROM document_content WHERE doc_id IN (SELECT doc_id FROM documents WHERE last_updated < ?)",
                    (cutoff_date,)
                )
                conn.execute(
                    "DELETE FROM documents WHERE last_updated < ?",
                    (cutoff_date,)
                )
                
                # Remove from search index
                writer = self.search_index.writer()
                for doc_id, in old_docs:
                    writer.delete_by_term('doc_id', doc_id)
                writer.commit()
                
                conn.commit()
                
                logger.info(f"Cleaned up {len(old_docs)} old documents")
                return len(old_docs)
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

# Test function
if __name__ == "__main__":
    # Example usage
    indexer = SQLiteIndexer()
    
    # Add a sample document
    sample_content = """
    令和7年度税制改正について
    
    所得税の基礎控除額が480,000円から500,000円に引き上げられます。
    また、給与所得控除の見直しも行われ、年収850万円超の場合の控除額が調整されます。
    
    法人税については、中小企業の軽減税率が維持され、
    研究開発税制の拡充も継続されます。
    """
    
    indexer.add_document(
        doc_id="tax_reform_2025_001",
        title="令和7年度税制改正の概要",
        content=sample_content,
        source_url="https://www.mof.go.jp/tax_policy/tax_reform/outline/fy2025/",
        document_type="tax_reform",
        category="income_tax",
        year=2025
    )
    
    # Search example
    results = indexer.search_documents("基礎控除", category="income_tax")
    print(f"Found {len(results)} documents")
    for result in results:
        print(f"- {result['title']} (Score: {result['relevance_score']:.2f})")
    
    # Get statistics
    stats = indexer.get_statistics()
    print(f"\nIndex Statistics: {stats}")