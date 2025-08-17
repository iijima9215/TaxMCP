"""監査ログセキュリティテスト

TaxMCPサーバーの監査ログ機能をテストする
"""

import unittest
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.utils.test_config import TaxMCPTestCase, SecurityTestMixin
from tests.utils.assertion_helpers import SecurityAssertions
from tests.utils.mock_external_apis import MockSecurityManager


class TestAuditLogging(TaxMCPTestCase, SecurityTestMixin):
    """監査ログセキュリティテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        super().setUp()
        self.setup_mocks()
        self.security_manager = MockSecurityManager()
        self.audit_logger = self.security_manager.get_audit_logger()
    
    def test_authentication_event_logging(self):
        """認証イベントログテスト"""
        print("\n=== 認証イベントログテスト ===")
        
        # 認証成功イベント
        print("\n--- 認証成功ログ ---")
        auth_success_event = {
            "event_type": "authentication_success",
            "user_id": "test_user_001",
            "api_key": "ak_test_12345",
            "ip_address": "192.168.1.100",
            "user_agent": "TaxMCP-Client/1.0",
            "timestamp": datetime.now().isoformat(),
            "session_id": "sess_abc123"
        }
        
        print(f"認証成功イベント: {auth_success_event}")
        
        # 認証成功ログ記録
        log_result = self.audit_logger.log_authentication_event(auth_success_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # 認証成功ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "認証成功イベントがログに記録されている")
        self.assertEqual(log_result["event_type"], "authentication_success")
        self.assertIn("log_id", log_result, "ログIDが生成されている")
        
        print("✓ 認証成功ログ記録成功")
        
        # 認証失敗イベント
        print("\n--- 認証失敗ログ ---")
        auth_failure_event = {
            "event_type": "authentication_failure",
            "attempted_user_id": "invalid_user",
            "api_key": "ak_invalid_key",
            "ip_address": "192.168.1.200",
            "user_agent": "Malicious-Client/1.0",
            "timestamp": datetime.now().isoformat(),
            "failure_reason": "invalid_api_key",
            "attempt_count": 3
        }
        
        print(f"認証失敗イベント: {auth_failure_event}")
        
        # 認証失敗ログ記録
        log_result = self.audit_logger.log_authentication_event(auth_failure_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # 認証失敗ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "認証失敗イベントがログに記録されている")
        self.assertEqual(log_result["event_type"], "authentication_failure")
        self.assertEqual(log_result["failure_reason"], "invalid_api_key")
        
        print("✓ 認証失敗ログ記録成功")
    
    def test_access_control_logging(self):
        """アクセス制御ログテスト"""
        print("\n=== アクセス制御ログテスト ===")
        
        # 権限不足アクセス試行
        print("\n--- 権限不足アクセス試行ログ ---")
        unauthorized_access_event = {
            "event_type": "unauthorized_access_attempt",
            "user_id": "limited_user_001",
            "requested_resource": "/admin/tax_rates",
            "required_permission": "admin_access",
            "user_permissions": ["basic_access", "tax_calculation"],
            "ip_address": "192.168.1.150",
            "timestamp": datetime.now().isoformat(),
            "session_id": "sess_def456"
        }
        
        print(f"権限不足アクセス試行: {unauthorized_access_event}")
        
        # アクセス制御ログ記録
        log_result = self.audit_logger.log_access_control_event(unauthorized_access_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # アクセス制御ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "権限不足アクセス試行がログに記録されている")
        self.assertEqual(log_result["event_type"], "unauthorized_access_attempt")
        self.assertEqual(log_result["requested_resource"], "/admin/tax_rates")
        
        print("✓ 権限不足アクセス試行ログ記録成功")
        
        # 権限昇格試行
        print("\n--- 権限昇格試行ログ ---")
        privilege_escalation_event = {
            "event_type": "privilege_escalation_attempt",
            "user_id": "standard_user_002",
            "attempted_action": "modify_tax_rates",
            "current_role": "tax_calculator",
            "attempted_role": "admin",
            "ip_address": "192.168.1.175",
            "timestamp": datetime.now().isoformat(),
            "method": "role_manipulation"
        }
        
        print(f"権限昇格試行: {privilege_escalation_event}")
        
        # 権限昇格ログ記録
        log_result = self.audit_logger.log_access_control_event(privilege_escalation_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # 権限昇格ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "権限昇格試行がログに記録されている")
        self.assertEqual(log_result["event_type"], "privilege_escalation_attempt")
        self.assertEqual(log_result["attempted_action"], "modify_tax_rates")
        
        print("✓ 権限昇格試行ログ記録成功")
    
    def test_data_access_logging(self):
        """データアクセスログテスト"""
        print("\n=== データアクセスログテスト ===")
        
        # 機密データアクセス
        print("\n--- 機密データアクセスログ ---")
        sensitive_data_access = {
            "event_type": "sensitive_data_access",
            "user_id": "auditor_001",
            "data_type": "personal_tax_records",
            "record_ids": ["tax_001", "tax_002", "tax_003"],
            "access_method": "database_query",
            "query": "SELECT * FROM tax_records WHERE user_id IN (...)",
            "ip_address": "192.168.1.50",
            "timestamp": datetime.now().isoformat(),
            "purpose": "annual_audit"
        }
        
        print(f"機密データアクセス: {sensitive_data_access}")
        
        # データアクセスログ記録
        log_result = self.audit_logger.log_data_access_event(sensitive_data_access)
        
        print(f"ログ記録結果: {log_result}")
        
        # データアクセスログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "機密データアクセスがログに記録されている")
        self.assertEqual(log_result["event_type"], "sensitive_data_access")
        self.assertEqual(log_result["data_type"], "personal_tax_records")
        
        print("✓ 機密データアクセスログ記録成功")
        
        # データ変更イベント
        print("\n--- データ変更ログ ---")
        data_modification_event = {
            "event_type": "data_modification",
            "user_id": "admin_001",
            "table_name": "tax_rates",
            "operation": "UPDATE",
            "record_id": "rate_2025_income",
            "old_values": {"rate": 0.20, "threshold": 1950000},
            "new_values": {"rate": 0.23, "threshold": 1950000},
            "ip_address": "192.168.1.10",
            "timestamp": datetime.now().isoformat(),
            "reason": "tax_law_update_2025"
        }
        
        print(f"データ変更イベント: {data_modification_event}")
        
        # データ変更ログ記録
        log_result = self.audit_logger.log_data_access_event(data_modification_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # データ変更ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "データ変更がログに記録されている")
        self.assertEqual(log_result["event_type"], "data_modification")
        self.assertEqual(log_result["operation"], "UPDATE")
        
        print("✓ データ変更ログ記録成功")
    
    def test_security_incident_logging(self):
        """セキュリティインシデントログテスト"""
        print("\n=== セキュリティインシデントログテスト ===")
        
        # SQLインジェクション攻撃検出
        print("\n--- SQLインジェクション攻撃ログ ---")
        sql_injection_incident = {
            "event_type": "security_incident",
            "incident_type": "sql_injection_attempt",
            "severity": "high",
            "user_id": "unknown",
            "ip_address": "203.0.113.100",
            "user_agent": "sqlmap/1.0",
            "attack_payload": "'; DROP TABLE users; --",
            "target_parameter": "income",
            "timestamp": datetime.now().isoformat(),
            "blocked": True,
            "detection_method": "input_validation"
        }
        
        print(f"SQLインジェクション攻撃: {sql_injection_incident}")
        
        # セキュリティインシデントログ記録
        log_result = self.audit_logger.log_security_incident(sql_injection_incident)
        
        print(f"ログ記録結果: {log_result}")
        
        # セキュリティインシデントログのアサーション
        SecurityAssertions.assert_security_incident_logged(log_result)
        self.assertTrue(log_result["logged"], "SQLインジェクション攻撃がログに記録されている")
        self.assertEqual(log_result["incident_type"], "sql_injection_attempt")
        self.assertEqual(log_result["severity"], "high")
        
        print("✓ SQLインジェクション攻撃ログ記録成功")
        
        # ブルートフォース攻撃検出
        print("\n--- ブルートフォース攻撃ログ ---")
        brute_force_incident = {
            "event_type": "security_incident",
            "incident_type": "brute_force_attack",
            "severity": "medium",
            "ip_address": "198.51.100.50",
            "target_endpoint": "/auth/login",
            "attempt_count": 50,
            "time_window": "5_minutes",
            "timestamp": datetime.now().isoformat(),
            "blocked": True,
            "detection_method": "rate_limiting"
        }
        
        print(f"ブルートフォース攻撃: {brute_force_incident}")
        
        # ブルートフォース攻撃ログ記録
        log_result = self.audit_logger.log_security_incident(brute_force_incident)
        
        print(f"ログ記録結果: {log_result}")
        
        # ブルートフォース攻撃ログのアサーション
        SecurityAssertions.assert_security_incident_logged(log_result)
        self.assertTrue(log_result["logged"], "ブルートフォース攻撃がログに記録されている")
        self.assertEqual(log_result["incident_type"], "brute_force_attack")
        self.assertEqual(log_result["attempt_count"], 50)
        
        print("✓ ブルートフォース攻撃ログ記録成功")
    
    def test_system_event_logging(self):
        """システムイベントログテスト"""
        print("\n=== システムイベントログテスト ===")
        
        # システム起動イベント
        print("\n--- システム起動ログ ---")
        system_startup_event = {
            "event_type": "system_event",
            "system_event_type": "server_startup",
            "server_version": "TaxMCP-1.0.0",
            "startup_time": datetime.now().isoformat(),
            "configuration": {
                "debug_mode": False,
                "log_level": "INFO",
                "database_url": "sqlite:///tax_data.db"
            },
            "host_info": {
                "hostname": "taxmcp-server-01",
                "os": "Linux",
                "python_version": "3.11.0"
            }
        }
        
        print(f"システム起動イベント: {system_startup_event}")
        
        # システムイベントログ記録
        log_result = self.audit_logger.log_system_event(system_startup_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # システムイベントログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "システム起動イベントがログに記録されている")
        self.assertEqual(log_result["system_event_type"], "server_startup")
        
        print("✓ システム起動ログ記録成功")
        
        # 設定変更イベント
        print("\n--- 設定変更ログ ---")
        config_change_event = {
            "event_type": "system_event",
            "system_event_type": "configuration_change",
            "user_id": "admin_001",
            "changed_settings": {
                "log_level": {"old": "INFO", "new": "DEBUG"},
                "rate_limit": {"old": 100, "new": 200}
            },
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.10",
            "reason": "troubleshooting_performance_issue"
        }
        
        print(f"設定変更イベント: {config_change_event}")
        
        # 設定変更ログ記録
        log_result = self.audit_logger.log_system_event(config_change_event)
        
        print(f"ログ記録結果: {log_result}")
        
        # 設定変更ログのアサーション
        SecurityAssertions.assert_audit_log_recorded(log_result)
        self.assertTrue(log_result["logged"], "設定変更イベントがログに記録されている")
        self.assertEqual(log_result["system_event_type"], "configuration_change")
        
        print("✓ 設定変更ログ記録成功")
    
    def test_log_integrity_verification(self):
        """ログ整合性検証テスト"""
        print("\n=== ログ整合性検証テスト ===")
        
        # 複数のログエントリを作成
        print("\n--- ログエントリ作成 ---")
        log_entries = []
        
        for i in range(5):
            log_entry = {
                "event_type": "test_event",
                "sequence_number": i + 1,
                "user_id": f"test_user_{i:03d}",
                "action": f"test_action_{i}",
                "timestamp": (datetime.now() + timedelta(seconds=i)).isoformat(),
                "data": f"test_data_{i}"
            }
            
            log_result = self.audit_logger.log_event(log_entry)
            log_entries.append(log_result)
            print(f"ログエントリ {i+1} 作成: {log_result['log_id']}")
        
        # ログチェーン整合性検証
        print("\n--- ログチェーン整合性検証 ---")
        integrity_check = self.audit_logger.verify_log_chain_integrity()
        
        print(f"整合性検証結果: {integrity_check}")
        
        # ログ整合性のアサーション
        SecurityAssertions.assert_log_integrity_valid(integrity_check)
        self.assertTrue(integrity_check["valid"], "ログチェーンの整合性が保たれている")
        self.assertEqual(integrity_check["verified_entries"], 5, "5つのエントリが検証されている")
        
        print("✓ ログチェーン整合性検証成功")
        
        # ログ改ざん検出テスト
        print("\n--- ログ改ざん検出テスト ---")
        
        # 意図的にログを改ざん
        tampered_log_id = log_entries[2]["log_id"]
        tamper_result = self.audit_logger.simulate_log_tampering(tampered_log_id)
        
        print(f"ログ改ざんシミュレーション: {tamper_result}")
        
        # 改ざん後の整合性検証
        tampered_integrity_check = self.audit_logger.verify_log_chain_integrity()
        
        print(f"改ざん後の整合性検証: {tampered_integrity_check}")
        
        # 改ざん検出のアサーション
        SecurityAssertions.assert_log_tampering_detected(tampered_integrity_check)
        self.assertFalse(tampered_integrity_check["valid"], "ログ改ざんが検出されている")
        self.assertIn(tampered_log_id, tampered_integrity_check["tampered_entries"])
        
        print("✓ ログ改ざん検出成功")
    
    def test_log_retention_and_archival(self):
        """ログ保持・アーカイブテスト"""
        print("\n=== ログ保持・アーカイブテスト ===")
        
        # 古いログエントリの作成
        print("\n--- 古いログエントリ作成 ---")
        old_log_entries = []
        
        # 1年前のログエントリ
        old_timestamp = datetime.now() - timedelta(days=365)
        for i in range(3):
            old_log_entry = {
                "event_type": "old_event",
                "user_id": f"old_user_{i:03d}",
                "action": f"old_action_{i}",
                "timestamp": (old_timestamp + timedelta(hours=i)).isoformat(),
                "data": f"old_data_{i}"
            }
            
            log_result = self.audit_logger.log_event(old_log_entry)
            old_log_entries.append(log_result)
            print(f"古いログエントリ {i+1} 作成: {log_result['log_id']}")
        
        # ログ保持ポリシー確認
        print("\n--- ログ保持ポリシー確認 ---")
        retention_policy = self.audit_logger.get_retention_policy()
        
        print(f"ログ保持ポリシー: {retention_policy}")
        
        # 保持ポリシーのアサーション
        SecurityAssertions.assert_retention_policy_valid(retention_policy)
        self.assertGreaterEqual(retention_policy["retention_days"], 365, "最低1年間の保持期間")
        self.assertTrue(retention_policy["archival_enabled"], "アーカイブ機能が有効")
        
        print("✓ ログ保持ポリシー確認成功")
        
        # ログアーカイブ実行
        print("\n--- ログアーカイブ実行 ---")
        archive_result = self.audit_logger.archive_old_logs(
            cutoff_date=datetime.now() - timedelta(days=300)
        )
        
        print(f"アーカイブ結果: {archive_result}")
        
        # アーカイブのアサーション
        SecurityAssertions.assert_log_archival_successful(archive_result)
        self.assertTrue(archive_result["success"], "ログアーカイブが成功している")
        self.assertGreater(archive_result["archived_count"], 0, "アーカイブされたログがある")
        
        print("✓ ログアーカイブ実行成功")
    
    def test_log_search_and_analysis(self):
        """ログ検索・分析テスト"""
        print("\n=== ログ検索・分析テスト ===")
        
        # 検索用のテストログを作成
        print("\n--- 検索用テストログ作成 ---")
        test_logs = [
            {
                "event_type": "authentication_failure",
                "user_id": "suspicious_user",
                "ip_address": "203.0.113.100",
                "timestamp": datetime.now().isoformat()
            },
            {
                "event_type": "security_incident",
                "incident_type": "sql_injection_attempt",
                "ip_address": "203.0.113.100",
                "timestamp": (datetime.now() + timedelta(minutes=5)).isoformat()
            },
            {
                "event_type": "unauthorized_access_attempt",
                "user_id": "suspicious_user",
                "ip_address": "203.0.113.100",
                "timestamp": (datetime.now() + timedelta(minutes=10)).isoformat()
            }
        ]
        
        for log_entry in test_logs:
            log_result = self.audit_logger.log_event(log_entry)
            print(f"テストログ作成: {log_result['log_id']}")
        
        # IPアドレスによる検索
        print("\n--- IPアドレス検索 ---")
        ip_search_result = self.audit_logger.search_logs_by_ip("203.0.113.100")
        
        print(f"IP検索結果: {ip_search_result}")
        
        # IP検索のアサーション
        SecurityAssertions.assert_log_search_successful(ip_search_result)
        self.assertGreaterEqual(ip_search_result["match_count"], 3, "3件以上のマッチ")
        
        print("✓ IPアドレス検索成功")
        
        # ユーザーIDによる検索
        print("\n--- ユーザーID検索 ---")
        user_search_result = self.audit_logger.search_logs_by_user("suspicious_user")
        
        print(f"ユーザー検索結果: {user_search_result}")
        
        # ユーザー検索のアサーション
        SecurityAssertions.assert_log_search_successful(user_search_result)
        self.assertGreaterEqual(user_search_result["match_count"], 2, "2件以上のマッチ")
        
        print("✓ ユーザーID検索成功")
        
        # セキュリティインシデント分析
        print("\n--- セキュリティインシデント分析 ---")
        incident_analysis = self.audit_logger.analyze_security_incidents(
            time_window=timedelta(hours=1)
        )
        
        print(f"インシデント分析結果: {incident_analysis}")
        
        # インシデント分析のアサーション
        SecurityAssertions.assert_incident_analysis_valid(incident_analysis)
        self.assertGreater(incident_analysis["total_incidents"], 0, "インシデントが検出されている")
        self.assertIn("203.0.113.100", incident_analysis["suspicious_ips"])
        
        print("✓ セキュリティインシデント分析成功")
    
    def test_real_time_log_monitoring(self):
        """リアルタイムログ監視テスト"""
        print("\n=== リアルタイムログ監視テスト ===")
        
        # ログ監視設定
        print("\n--- ログ監視設定 ---")
        monitoring_config = {
            "alert_rules": [
                {
                    "rule_name": "multiple_auth_failures",
                    "condition": "authentication_failure_count > 5",
                    "time_window": "5_minutes",
                    "severity": "high"
                },
                {
                    "rule_name": "sql_injection_detected",
                    "condition": "incident_type == 'sql_injection_attempt'",
                    "time_window": "immediate",
                    "severity": "critical"
                }
            ],
            "notification_channels": ["email", "slack", "sms"]
        }
        
        print(f"監視設定: {monitoring_config}")
        
        # 監視設定適用
        monitoring_setup = self.audit_logger.setup_real_time_monitoring(monitoring_config)
        
        print(f"監視設定結果: {monitoring_setup}")
        
        # 監視設定のアサーション
        SecurityAssertions.assert_monitoring_setup_successful(monitoring_setup)
        self.assertTrue(monitoring_setup["success"], "監視設定が成功している")
        self.assertEqual(len(monitoring_setup["active_rules"]), 2, "2つのルールが有効")
        
        print("✓ ログ監視設定成功")
        
        # アラート発生テスト
        print("\n--- アラート発生テスト ---")
        
        # 複数の認証失敗を生成してアラートをトリガー
        for i in range(6):
            auth_failure = {
                "event_type": "authentication_failure",
                "user_id": f"attacker_{i}",
                "ip_address": "198.51.100.200",
                "timestamp": (datetime.now() + timedelta(seconds=i*10)).isoformat()
            }
            
            log_result = self.audit_logger.log_event(auth_failure)
            print(f"認証失敗 {i+1} ログ: {log_result['log_id']}")
        
        # アラート確認
        time.sleep(1)  # アラート処理時間を待機
        alerts = self.audit_logger.get_triggered_alerts()
        
        print(f"発生したアラート: {alerts}")
        
        # アラートのアサーション
        SecurityAssertions.assert_alerts_triggered(alerts)
        self.assertGreater(len(alerts), 0, "アラートが発生している")
        
        # 複数認証失敗アラートの確認
        auth_failure_alerts = [
            alert for alert in alerts 
            if alert["rule_name"] == "multiple_auth_failures"
        ]
        self.assertGreater(len(auth_failure_alerts), 0, "認証失敗アラートが発生")
        
        print("✓ アラート発生テスト成功")


if __name__ == "__main__":
    unittest.main(verbosity=2)