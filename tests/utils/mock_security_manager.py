import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional


class MockSecurityManager:
    """セキュリティ機能のモック実装"""
    
    def __init__(self):
        """初期化"""
        self.tokens = {}  # トークンストレージ
        self.audit_logs = []  # 監査ログ
        self.secret_key = "test_secret_key_12345"
    
    # ===== トークン管理 =====
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """アクセストークンを作成"""
        token_id = secrets.token_urlsafe(32)
        expires_at = time.time() + 3600  # 1時間後に期限切れ
        
        self.tokens[token_id] = {
            "data": data,
            "expires_at": expires_at,
            "created_at": time.time()
        }
        
        return token_id
    
    def create_expired_token(self) -> str:
        """期限切れトークンを作成（テスト用）"""
        token_id = secrets.token_urlsafe(32)
        expires_at = time.time() - 3600  # 1時間前に期限切れ
        
        self.tokens[token_id] = {
            "data": {"user_id": "expired_user"},
            "expires_at": expires_at,
            "created_at": time.time() - 7200
        }
        
        return token_id
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証"""
        if not token or token not in self.tokens:
            return None
        
        token_data = self.tokens[token]
        
        # 期限切れチェック
        if time.time() > token_data["expires_at"]:
            return None
        
        return token_data["data"]
    
    # ===== 入力検証 =====
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, str]:
        """入力データの基本検証"""
        # 必須フィールドチェック
        for field in required_fields:
            if field not in data:
                return False, f"Required field '{field}' is missing"
        
        # 数値フィールドの検証
        for key, value in data.items():
            if key.endswith('_income') or key == 'amount':
                if isinstance(value, str):
                    return False, f"Field '{key}' must be a valid number"
                if isinstance(value, (int, float)) and value < 0:
                    return False, f"Field '{key}' must be non-negative"
        
        return True, "Valid"
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データのサニタイズ"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # 文字列のトリムと長さ制限
                sanitized[key] = value.strip()[:1000]
            elif isinstance(value, (int, float)):
                # 数値の範囲制限
                if key == 'amount':
                    sanitized[key] = min(value, 100000000)  # 1億円上限
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    def validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データ型の検証"""
        type_violations = []
        
        for key, value in data.items():
            if key == 'income' and not isinstance(value, (int, float)):
                type_violations.append(key)
            elif key == 'tax_year' and isinstance(value, str):
                # 文字列だが数値に変換可能な場合は許可
                try:
                    int(value)
                except ValueError:
                    type_violations.append(key)
            elif key == 'married' and not isinstance(value, bool):
                type_violations.append(key)
        
        return {
            "valid": len(type_violations) == 0,
            "type_violations": type_violations
        }
    
    def validate_input_length(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力長の検証"""
        length_violations = []
        
        for key, value in data.items():
            if isinstance(value, str):
                if key == 'user_name' and len(value) > 1000:
                    length_violations.append(key)
                elif key == 'description' and len(value) > 5000:
                    length_violations.append(key)
        
        return {
            "valid": len(length_violations) == 0,
            "length_violations": length_violations
        }
    
    # ===== APIキー管理 =====
    
    def generate_api_key(self) -> str:
        """APIキーを生成"""
        return f"taxmcp_{secrets.token_urlsafe(32)}"
    
    def hash_api_key(self, api_key: str) -> str:
        """APIキーをハッシュ化"""
        return hashlib.sha256(f"{api_key}{self.secret_key}".encode()).hexdigest()
    
    # ===== 監査ログ =====
    
    def log_api_call(self, tool_name: str, params: Dict[str, Any], 
                     client_id: str, success: bool) -> Dict[str, Any]:
        """API呼び出しをログ記録"""
        log_entry = {
            "log_id": secrets.token_urlsafe(16),
            "event_type": "api_call",
            "tool_name": tool_name,
            "params": params,
            "client_id": client_id,
            "success": success,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        }
        
        self.audit_logs.append(log_entry)
        
        return {
            "logged": True,
            "log_id": log_entry["log_id"],
            "event_type": log_entry["event_type"]
        }
    
    def log_security_event(self, event_type: str, details: str, 
                          client_id: str) -> Dict[str, Any]:
        """セキュリティイベントをログ記録"""
        log_entry = {
            "log_id": secrets.token_urlsafe(16),
            "event_type": event_type,
            "details": details,
            "client_id": client_id,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat()
        }
        
        self.audit_logs.append(log_entry)
        
        return {
            "logged": True,
            "log_id": log_entry["log_id"],
            "event_type": log_entry["event_type"]
        }
    
    def search_audit_logs(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """監査ログを検索"""
        filtered_logs = []
        
        for log in self.audit_logs:
            # イベントタイプでフィルタ
            if "event_type" in criteria:
                if log["event_type"] != criteria["event_type"]:
                    continue
            
            # 時間範囲でフィルタ
            if "time_range" in criteria:
                time_range = criteria["time_range"]
                if log["timestamp"] < time_range["start"] or log["timestamp"] > time_range["end"]:
                    continue
            
            filtered_logs.append(log)
        
        return {
            "logs": filtered_logs,
            "total_count": len(filtered_logs)
        }