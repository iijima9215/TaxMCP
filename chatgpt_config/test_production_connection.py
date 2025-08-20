#!/usr/bin/env python3
"""
TaxMCP本番環境接続テストスクリプト
https://taxmcp.ami-j2.comサーバーとの接続をテストします。
"""

import requests
import json
import sys
import time
from urllib.parse import urljoin

# 設定
BASE_URL = "https://taxmcp.ami-j2.com"
TIMEOUT = 30
VERIFY_SSL = True

def test_connection():
    """基本的な接続テスト"""
    print(f"TaxMCP本番環境接続テスト開始: {BASE_URL}")
    print("=" * 50)
    
    try:
        # ヘルスチェック
        print("1. ヘルスチェック...")
        response = requests.get(
            urljoin(BASE_URL, "/health"),
            timeout=TIMEOUT,
            verify=VERIFY_SSL
        )
        
        if response.status_code == 200:
            print("✓ ヘルスチェック成功")
            print(f"  レスポンス: {response.json()}")
        else:
            print(f"✗ ヘルスチェック失敗: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 接続エラー: {e}")
        return False
    
    try:
        # 簡単な税務計算テスト
        print("\n2. 税務計算テスト...")
        test_data = {
            "income": 5000000,
            "deductions": {
                "basic": 480000,
                "dependent": 760000
            },
            "tax_year": 2024,
            "prefecture": "東京都"
        }
        
        response = requests.post(
            urljoin(BASE_URL, "/calculate_income_tax"),
            json=test_data,
            timeout=TIMEOUT,
            verify=VERIFY_SSL,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✓ 税務計算テスト成功")
            result = response.json()
            print(f"  計算結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        else:
            print(f"✗ 税務計算テスト失敗: {response.status_code}")
            print(f"  エラー内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 税務計算テストエラー: {e}")
        return False
    
    print("\n✓ 全てのテストが成功しました！")
    print(f"TaxMCP本番環境 ({BASE_URL}) は正常に動作しています。")
    return True

def test_mcp_compatibility():
    """MCP互換性テスト"""
    print("\n3. MCP互換性テスト...")
    
    try:
        # MCPエンドポイントの確認
        response = requests.get(
            urljoin(BASE_URL, "/mcp/info"),
            timeout=TIMEOUT,
            verify=VERIFY_SSL
        )
        
        if response.status_code == 200:
            print("✓ MCP互換性確認成功")
            info = response.json()
            print(f"  MCPバージョン: {info.get('version', 'N/A')}")
            print(f"  利用可能なツール数: {len(info.get('tools', []))}")
        else:
            print(f"✗ MCP互換性確認失敗: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ MCP互換性テストエラー: {e}")
        return False
    
    return True

def main():
    """メイン実行関数"""
    print("TaxMCP本番環境接続テストツール")
    print(f"対象サーバー: {BASE_URL}")
    print(f"タイムアウト: {TIMEOUT}秒")
    print(f"SSL検証: {'有効' if VERIFY_SSL else '無効'}")
    print()
    
    # 基本接続テスト
    if not test_connection():
        print("\n❌ 基本接続テストに失敗しました。")
        sys.exit(1)
    
    # MCP互換性テスト
    if not test_mcp_compatibility():
        print("\n⚠️  MCP互換性テストに失敗しました。")
        print("基本的な税務計算は動作しますが、ChatGPT連携に問題がある可能性があります。")
        sys.exit(1)
    
    print("\n🎉 全てのテストが成功しました！")
    print("ChatGPTとの連携設定を行ってください。")

if __name__ == "__main__":
    main()