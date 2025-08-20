#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部エンドポイント診断ツール (HTTPS専用)
リバースプロキシ環境での接続診断を行います。
"""

import os
import sys
import json
import time
import socket
import ssl
import requests
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

class HTTPSDiagnosticTool:
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://taxmcp.ami-j2.com')
        self.secret_key = os.getenv('SECRET_KEY')
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'diagnostics': {}
        }
        
    def log(self, message, level='INFO'):
        """ログ出力"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
        
    def test_dns_resolution(self):
        """DNS解決テスト"""
        self.log("DNS解決テストを開始")
        parsed_url = urlparse(self.base_url)
        hostname = parsed_url.hostname
        
        try:
            ip_addresses = socket.gethostbyname_ex(hostname)[2]
            self.results['diagnostics']['dns'] = {
                'status': 'success',
                'hostname': hostname,
                'ip_addresses': ip_addresses,
                'message': f'DNS解決成功: {hostname} -> {ip_addresses}'
            }
            self.log(f"DNS解決成功: {hostname} -> {ip_addresses}")
            return True
        except socket.gaierror as e:
            self.results['diagnostics']['dns'] = {
                'status': 'failed',
                'hostname': hostname,
                'error': str(e),
                'message': f'DNS解決失敗: {hostname}'
            }
            self.log(f"DNS解決失敗: {hostname} - {e}", 'ERROR')
            return False
            
    def test_tcp_connection(self):
        """TCP接続テスト"""
        self.log("TCP接続テストを開始")
        parsed_url = urlparse(self.base_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443  # HTTPS default port
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                self.results['diagnostics']['tcp'] = {
                    'status': 'success',
                    'hostname': hostname,
                    'port': port,
                    'message': f'TCP接続成功: {hostname}:{port}'
                }
                self.log(f"TCP接続成功: {hostname}:{port}")
                return True
            else:
                self.results['diagnostics']['tcp'] = {
                    'status': 'failed',
                    'hostname': hostname,
                    'port': port,
                    'error_code': result,
                    'message': f'TCP接続失敗: {hostname}:{port}'
                }
                self.log(f"TCP接続失敗: {hostname}:{port} (エラーコード: {result})", 'ERROR')
                return False
        except Exception as e:
            self.results['diagnostics']['tcp'] = {
                'status': 'failed',
                'hostname': hostname,
                'port': port,
                'error': str(e),
                'message': f'TCP接続エラー: {hostname}:{port}'
            }
            self.log(f"TCP接続エラー: {hostname}:{port} - {e}", 'ERROR')
            return False
            
    def test_ssl_certificate(self):
        """SSL証明書テスト"""
        self.log("SSL証明書テストを開始")
        parsed_url = urlparse(self.base_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 443
        
        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
            self.results['diagnostics']['ssl'] = {
                'status': 'success',
                'hostname': hostname,
                'subject': dict(x[0] for x in cert['subject']),
                'issuer': dict(x[0] for x in cert['issuer']),
                'version': cert['version'],
                'not_before': cert['notBefore'],
                'not_after': cert['notAfter'],
                'message': 'SSL証明書検証成功'
            }
            self.log(f"SSL証明書検証成功: {cert['subject']}")
            return True
        except ssl.SSLError as e:
            self.results['diagnostics']['ssl'] = {
                'status': 'failed',
                'hostname': hostname,
                'error': str(e),
                'message': 'SSL証明書検証失敗'
            }
            self.log(f"SSL証明書検証失敗: {e}", 'ERROR')
            return False
        except Exception as e:
            self.results['diagnostics']['ssl'] = {
                'status': 'failed',
                'hostname': hostname,
                'error': str(e),
                'message': 'SSL接続エラー'
            }
            self.log(f"SSL接続エラー: {e}", 'ERROR')
            return False
            
    def test_https_endpoints(self):
        """HTTPS エンドポイントテスト"""
        self.log("HTTPSエンドポイントテストを開始")
        
        endpoints = [
            '/health',
            '/api/health',
            '/api/v1/health',
            '/status',
            '/ping'
        ]
        
        headers = {}
        if self.secret_key:
            headers['Authorization'] = f'Bearer {self.secret_key}'
            headers['X-API-Key'] = self.secret_key
            
        endpoint_results = {}
        
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                self.log(f"テスト中: {url}")
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=10,
                    verify=True  # SSL証明書を検証
                )
                
                endpoint_results[endpoint] = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'response_time': response.elapsed.total_seconds(),
                    'content_length': len(response.content),
                    'message': f'HTTP {response.status_code}'
                }
                
                self.log(f"{endpoint}: HTTP {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
                
            except requests.exceptions.SSLError as e:
                endpoint_results[endpoint] = {
                    'error': 'SSL_ERROR',
                    'message': str(e)
                }
                self.log(f"{endpoint}: SSL エラー - {e}", 'ERROR')
                
            except requests.exceptions.ConnectionError as e:
                endpoint_results[endpoint] = {
                    'error': 'CONNECTION_ERROR',
                    'message': str(e)
                }
                self.log(f"{endpoint}: 接続エラー - {e}", 'ERROR')
                
            except requests.exceptions.Timeout as e:
                endpoint_results[endpoint] = {
                    'error': 'TIMEOUT',
                    'message': str(e)
                }
                self.log(f"{endpoint}: タイムアウト - {e}", 'ERROR')
                
            except Exception as e:
                endpoint_results[endpoint] = {
                    'error': 'UNKNOWN_ERROR',
                    'message': str(e)
                }
                self.log(f"{endpoint}: 不明なエラー - {e}", 'ERROR')
                
        self.results['diagnostics']['https_endpoints'] = endpoint_results
        
    def test_reverse_proxy_headers(self):
        """リバースプロキシヘッダーテスト"""
        self.log("リバースプロキシヘッダーテストを開始")
        
        url = f"{self.base_url}/"
        headers = {}
        if self.secret_key:
            headers['Authorization'] = f'Bearer {self.secret_key}'
            
        try:
            response = requests.head(
                url, 
                headers=headers, 
                timeout=10,
                verify=True
            )
            
            proxy_headers = {}
            for header, value in response.headers.items():
                if any(keyword in header.lower() for keyword in 
                      ['server', 'proxy', 'via', 'x-forwarded', 'x-real-ip', 'x-nginx']):
                    proxy_headers[header] = value
                    
            self.results['diagnostics']['reverse_proxy'] = {
                'status': 'success',
                'status_code': response.status_code,
                'proxy_headers': proxy_headers,
                'all_headers': dict(response.headers),
                'message': f'リバースプロキシ検出: {proxy_headers}'
            }
            
            self.log(f"リバースプロキシヘッダー検出: {proxy_headers}")
            
        except Exception as e:
            self.results['diagnostics']['reverse_proxy'] = {
                'status': 'failed',
                'error': str(e),
                'message': 'リバースプロキシヘッダーテスト失敗'
            }
            self.log(f"リバースプロキシヘッダーテスト失敗: {e}", 'ERROR')
            
    def run_diagnostics(self):
        """全診断テストを実行"""
        self.log("=== HTTPS診断テスト開始 ===")
        self.log(f"対象URL: {self.base_url}")
        self.log(f"SECRET_KEY設定: {'あり' if self.secret_key else 'なし'}")
        
        # 各テストを順次実行
        tests = [
            ('DNS解決', self.test_dns_resolution),
            ('TCP接続', self.test_tcp_connection),
            ('SSL証明書', self.test_ssl_certificate),
            ('HTTPSエンドポイント', self.test_https_endpoints),
            ('リバースプロキシ', self.test_reverse_proxy_headers)
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name}テスト ---")
            try:
                test_func()
            except Exception as e:
                self.log(f"{test_name}テストでエラー: {e}", 'ERROR')
                self.results['diagnostics'][test_name.lower()] = {
                    'status': 'failed',
                    'error': str(e),
                    'message': f'{test_name}テスト実行エラー'
                }
                
        self.log("\n=== 診断テスト完了 ===")
        
    def save_results(self):
        """結果をJSONファイルに保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'diagnostic_results_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            self.log(f"診断結果を保存: {filename}")
        except Exception as e:
            self.log(f"結果保存エラー: {e}", 'ERROR')
            
    def print_summary(self):
        """診断結果サマリーを表示"""
        self.log("\n=== 診断結果サマリー ===")
        
        for test_name, result in self.results['diagnostics'].items():
            status = result.get('status', 'unknown')
            message = result.get('message', 'メッセージなし')
            
            if status == 'success':
                self.log(f"✓ {test_name}: {message}")
            else:
                self.log(f"✗ {test_name}: {message}", 'ERROR')
                
if __name__ == '__main__':
    diagnostic = HTTPSDiagnosticTool()
    
    try:
        diagnostic.run_diagnostics()
        diagnostic.save_results()
        diagnostic.print_summary()
    except KeyboardInterrupt:
        diagnostic.log("\n診断テストが中断されました", 'WARNING')
    except Exception as e:
        diagnostic.log(f"診断テスト実行エラー: {e}", 'ERROR')
        sys.exit(1)