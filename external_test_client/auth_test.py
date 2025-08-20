#!/usr/bin/env python3
"""
外部テスト環境用認証テストクライアント
JWT認証とAPI Key認証をテストします。
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
import jwt
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 現在のディレクトリから.envを読み込み
load_dotenv()

class AuthTestClient:
    """認証テスト用クライアント"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://taxmcp.ami-j2.com')
        self.api_version = os.getenv('API_VERSION', 'v1')
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        
        # 認証情報
        self.api_key = os.getenv('API_KEY')
        self.jwt_secret = os.getenv('JWT_SECRET_KEY')
        self.test_username = os.getenv('TEST_USERNAME', 'test_user')
        self.test_password = os.getenv('TEST_PASSWORD', 'test_password_123')
        self.test_user_id = os.getenv('TEST_USER_ID', 'test_user_001')
        
        # ログ設定
        self.setup_logging()
        
        # セッション
        self.session = None
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auth_test.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        connector = aiohttp.TCPConnector(ssl=self.ssl_verify)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()
    
    def generate_jwt_token(self, user_id: str, expires_in_hours: int = 24) -> str:
        """JWTトークン生成"""
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEYが設定されていません")
        
        payload = {
            "user_id": user_id,
            "username": self.test_username,
            "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
            "iat": datetime.utcnow(),
            "iss": "taxmcp-test-client"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    def generate_expired_jwt_token(self, user_id: str) -> str:
        """期限切れJWTトークン生成（テスト用）"""
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET_KEYが設定されていません")
        
        payload = {
            "user_id": user_id,
            "username": self.test_username,
            "exp": datetime.utcnow() - timedelta(hours=1),  # 1時間前に期限切れ
            "iat": datetime.utcnow() - timedelta(hours=2),
            "iss": "taxmcp-test-client"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    def get_headers(self, auth_type: str = "none", token: str = None) -> Dict[str, str]:
        """認証ヘッダー付きリクエストヘッダーを取得"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TaxMCP-Auth-Test-Client/1.0'
        }
        
        if auth_type == "api_key" and self.api_key:
            headers['X-API-Key'] = self.api_key
        elif auth_type == "jwt" and token:
            headers['Authorization'] = f'Bearer {token}'
        elif auth_type == "invalid_api_key":
            headers['X-API-Key'] = "invalid-api-key-12345"
        elif auth_type == "invalid_jwt":
            headers['Authorization'] = "Bearer invalid.jwt.token"
        
        return headers
    
    async def test_no_auth_access(self) -> Dict[str, Any]:
        """認証なしアクセステスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("認証なしアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("none")
            ) as response:
                result = {
                    "test_name": "no_auth_access",
                    "status_code": response.status,
                    "success": response.status in [200, 401, 403],  # 期待される応答
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status == 200:
                    result["message"] = "認証なしでアクセス可能（セキュリティ警告）"
                    result["security_issue"] = True
                elif response.status in [401, 403]:
                    result["message"] = "認証なしアクセスが正しく拒否されました"
                    result["security_issue"] = False
                else:
                    result["message"] = f"予期しないステータスコード: {response.status}"
                    result["security_issue"] = True
                
                return result
                
        except Exception as e:
            return {
                "test_name": "no_auth_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_valid_api_key_access(self) -> Dict[str, Any]:
        """有効なAPI Keyアクセステスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("有効なAPI Keyアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("api_key")
            ) as response:
                result = {
                    "test_name": "valid_api_key_access",
                    "status_code": response.status,
                    "success": response.status == 200,
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status == 200:
                    response_data = await response.json()
                    result["message"] = "API Key認証成功"
                    result["response_data"] = response_data
                else:
                    error_text = await response.text()
                    result["message"] = f"API Key認証失敗: {error_text}"
                
                return result
                
        except Exception as e:
            return {
                "test_name": "valid_api_key_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_invalid_api_key_access(self) -> Dict[str, Any]:
        """無効なAPI Keyアクセステスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("無効なAPI Keyアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("invalid_api_key")
            ) as response:
                result = {
                    "test_name": "invalid_api_key_access",
                    "status_code": response.status,
                    "success": response.status in [401, 403],
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status in [401, 403]:
                    result["message"] = "無効なAPI Keyが正しく拒否されました"
                else:
                    result["message"] = f"無効なAPI Keyが受け入れられました（セキュリティ問題）"
                    result["security_issue"] = True
                
                return result
                
        except Exception as e:
            return {
                "test_name": "invalid_api_key_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_valid_jwt_access(self) -> Dict[str, Any]:
        """有効なJWTアクセステスト"""
        try:
            # JWTトークン生成
            jwt_token = self.generate_jwt_token(self.test_user_id)
            
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("有効なJWTアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("jwt", jwt_token)
            ) as response:
                result = {
                    "test_name": "valid_jwt_access",
                    "status_code": response.status,
                    "success": response.status == 200,
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status == 200:
                    response_data = await response.json()
                    result["message"] = "JWT認証成功"
                    result["response_data"] = response_data
                else:
                    error_text = await response.text()
                    result["message"] = f"JWT認証失敗: {error_text}"
                
                return result
                
        except Exception as e:
            return {
                "test_name": "valid_jwt_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_expired_jwt_access(self) -> Dict[str, Any]:
        """期限切れJWTアクセステスト"""
        try:
            # 期限切れJWTトークン生成
            expired_jwt_token = self.generate_expired_jwt_token(self.test_user_id)
            
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("期限切れJWTアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("jwt", expired_jwt_token)
            ) as response:
                result = {
                    "test_name": "expired_jwt_access",
                    "status_code": response.status,
                    "success": response.status in [401, 403],
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status in [401, 403]:
                    result["message"] = "期限切れJWTが正しく拒否されました"
                else:
                    result["message"] = f"期限切れJWTが受け入れられました（セキュリティ問題）"
                    result["security_issue"] = True
                
                return result
                
        except Exception as e:
            return {
                "test_name": "expired_jwt_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_invalid_jwt_access(self) -> Dict[str, Any]:
        """無効なJWTアクセステスト"""
        try:
            url = f"{self.base_url}/api/{self.api_version}/calculate/individual"
            test_data = {
                "income": 5000000,
                "deductions": 480000,
                "tax_year": 2025,
                "prefecture": "東京都",
                "city": "新宿区"
            }
            
            self.logger.info("無効なJWTアクセステスト")
            
            async with self.session.post(
                url, 
                json=test_data, 
                headers=self.get_headers("invalid_jwt")
            ) as response:
                result = {
                    "test_name": "invalid_jwt_access",
                    "status_code": response.status,
                    "success": response.status in [401, 403],
                    "timestamp": datetime.now().isoformat()
                }
                
                if response.status in [401, 403]:
                    result["message"] = "無効なJWTが正しく拒否されました"
                else:
                    result["message"] = f"無効なJWTが受け入れられました（セキュリティ問題）"
                    result["security_issue"] = True
                
                return result
                
        except Exception as e:
            return {
                "test_name": "invalid_jwt_access",
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_auth_tests(self) -> Dict[str, Any]:
        """認証テスト実行"""
        self.logger.info("=== 認証テスト開始 ===")
        self.logger.info(f"テスト対象: {self.base_url}")
        
        test_functions = [
            self.test_no_auth_access,
            self.test_valid_api_key_access,
            self.test_invalid_api_key_access,
            self.test_valid_jwt_access,
            self.test_expired_jwt_access,
            self.test_invalid_jwt_access
        ]
        
        results = []
        security_issues = []
        
        for test_func in test_functions:
            self.logger.info(f"実行中: {test_func.__name__}")
            
            try:
                result = await test_func()
                results.append(result)
                
                if result["success"]:
                    self.logger.info(f"✓ {result['test_name']} 成功")
                else:
                    self.logger.error(f"✗ {result['test_name']} 失敗")
                
                # セキュリティ問題の検出
                if result.get("security_issue"):
                    security_issues.append(result)
                
            except Exception as e:
                error_result = {
                    "test_name": test_func.__name__,
                    "status_code": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
                self.logger.error(f"✗ {test_func.__name__} エラー: {e}")
            
            # テスト間の遅延
            await asyncio.sleep(1)
        
        # 結果サマリー
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r["success"])
        
        summary = {
            "start_time": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "security_issues": len(security_issues),
            "results": results,
            "security_issues_detail": security_issues
        }
        
        # レポート生成
        self.generate_auth_report(summary)
        
        return summary
    
    def generate_auth_report(self, summary: Dict[str, Any]):
        """認証テストレポート生成"""
        self.logger.info("\n=== 認証テスト結果サマリー ===")
        self.logger.info(f"総テスト数: {summary['total_tests']}")
        self.logger.info(f"成功テスト数: {summary['successful_tests']}")
        self.logger.info(f"失敗テスト数: {summary['failed_tests']}")
        self.logger.info(f"成功率: {summary['success_rate']:.1f}%")
        self.logger.info(f"セキュリティ問題: {summary['security_issues']}件")
        
        # セキュリティ問題の詳細
        if summary['security_issues_detail']:
            self.logger.warning("\n⚠️ セキュリティ問題が検出されました:")
            for issue in summary['security_issues_detail']:
                self.logger.warning(f"- {issue['test_name']}: {issue['message']}")
        else:
            self.logger.info("\n✓ セキュリティ問題は検出されませんでした")
        
        # 結果をファイルに保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"auth_test_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"\n詳細結果を保存: {results_file}")

async def main():
    """メイン関数"""
    try:
        async with AuthTestClient() as client:
            results = await client.run_auth_tests()
            return results
    except KeyboardInterrupt:
        print("\nテストが中断されました")
        return None
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())