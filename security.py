import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from config import settings
import logging
import jwt

logger = logging.getLogger(__name__)

class SecurityManager:
    """セキュリティ管理クラス"""
    
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.token_expire_minutes = settings.access_token_expire_minutes
        
    def generate_api_key(self) -> str:
        """APIキーを生成"""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """APIキーをハッシュ化"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """アクセストークンを作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token validation failed: {e}")
            return None
    
    def validate_input(self, data: Dict[str, Any], required_fields: list) -> tuple[bool, str]:
        """入力データを検証"""
        # 必須フィールドの確認
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Required field '{field}' is missing"
        
        # 数値フィールドの検証
        numeric_fields = ['annual_income', 'basic_deduction', 'spouse_deduction', 
                         'dependent_deduction', 'social_insurance_deduction',
                         'life_insurance_deduction', 'earthquake_insurance_deduction',
                         'medical_deduction', 'donation_deduction', 'taxable_income',
                         'purchase_amount', 'start_year', 'end_year', 'years']
        
        for field in numeric_fields:
            if field in data:
                try:
                    value = float(data[field])
                    if value < 0:
                        return False, f"Field '{field}' must be non-negative"
                    if field in ['annual_income', 'taxable_income'] and value > 100000000:  # 1億円上限
                        return False, f"Field '{field}' exceeds maximum allowed value"
                except (ValueError, TypeError):
                    return False, f"Field '{field}' must be a valid number"
        
        # 年度の検証
        if 'tax_year' in data:
            try:
                year = int(data['tax_year'])
                current_year = datetime.now().year
                if year < 2020 or year > current_year + 1:
                    return False, f"Tax year must be between 2020 and {current_year + 1}"
            except (ValueError, TypeError):
                return False, "Tax year must be a valid integer"
        
        # 都道府県コードの検証
        if 'prefecture_code' in data:
            try:
                code = int(data['prefecture_code'])
                if code < 1 or code > 47:
                    return False, "Prefecture code must be between 1 and 47"
            except (ValueError, TypeError):
                return False, "Prefecture code must be a valid integer"
        
        return True, "Validation passed"
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データをサニタイズ"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # 文字列の場合、危険な文字を除去
                sanitized[key] = value.strip()[:1000]  # 長さ制限
            elif isinstance(value, (int, float)):
                # 数値の場合、範囲チェック
                sanitized[key] = max(0, min(value, 100000000))  # 0以上1億以下
            else:
                sanitized[key] = value
        
        return sanitized

    def validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データのデータ型を検証"""
        validation_result = {"valid": True, "type_violations": {}, "expected_types": {}}
        
        type_mappings = {
            "income": float,
            "tax_year": int,
            "deductions": float,
            "married": bool,
            "birth_date": date  # datetime.date型を期待
        }

        for field, expected_type in type_mappings.items():
            if field in data:
                value = data[field]
                is_valid = True
                
                if expected_type == float:
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        is_valid = False
                elif expected_type == int:
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        is_valid = False
                elif expected_type == bool:
                    if not isinstance(value, bool):
                        is_valid = False
                elif expected_type == date:
                    if not isinstance(value, str):
                        is_valid = False
                    else:
                        try:
                            datetime.strptime(value, "%Y-%m-%d").date()
                        except ValueError:
                            is_valid = False

                if not is_valid:
                    validation_result["valid"] = False
                    validation_result["type_violations"][field] = f"Expected {expected_type.__name__}, got {type(value).__name__}"
                    validation_result["expected_types"][field] = expected_type.__name__

        return validation_result

    def validate_input_length(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """入力データの長さを検証"""
        validation_result = {"valid": True, "length_violations": {}}
        
        length_constraints = {
            "user_name": 1000,
            "description": 5000,
            "api_key": 256,
            "query": 2000
        }

        for field, max_length in length_constraints.items():
            if field in data and isinstance(data[field], str):
                if len(data[field]) > max_length:
                    validation_result["valid"] = False
                    validation_result["length_violations"][field] = f"Exceeded max length of {max_length}"

        return validation_result

class AuditLogger:
    """監査ログクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        
    def log_api_call(self, tool_name: str, params: Dict[str, Any], 
                    client_id: Optional[str] = None, success: bool = True):
        """API呼び出しをログ記録"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'tool_name': tool_name,
            'client_id': client_id or 'anonymous',
            'success': success,
            'params_hash': hashlib.md5(str(params).encode()).hexdigest()[:8]
        }
        
        if success:
            self.logger.info(f"API call successful: {log_data}")
        else:
            self.logger.warning(f"API call failed: {log_data}")
    
    def log_security_event(self, event_type: str, details: str, 
                          client_id: Optional[str] = None):
        """セキュリティイベントをログ記録"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'client_id': client_id or 'anonymous'
        }
        
        self.logger.warning(f"Security event: {log_data}")

# グローバルインスタンス
security_manager = SecurityManager()
audit_logger = AuditLogger()

def require_auth(f):
    """認証が必要な関数のデコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 開発環境では認証をスキップ
        if settings.DEBUG:
            return f(*args, **kwargs)
        
        # 本番環境では認証チェックを実装
        # ここでは簡単な実装例
        auth_header = kwargs.get('auth_header')
        if not auth_header:
            audit_logger.log_security_event('AUTH_MISSING', 'No authentication header provided')
            raise ValueError("Authentication required")
        
        token = auth_header.replace('Bearer ', '')
        payload = security_manager.verify_token(token)
        if not payload:
            audit_logger.log_security_event('AUTH_INVALID', 'Invalid authentication token')
            raise ValueError("Invalid authentication token")
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_and_sanitize(required_fields: list):
    """入力検証とサニタイズのデコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # パラメータから入力データを取得
            if args and isinstance(args[0], dict):
                data = args[0]
            elif 'data' in kwargs:
                data = kwargs['data']
            else:
                data = kwargs
            
            # 入力検証
            is_valid, message = security_manager.validate_input(data, required_fields)
            if not is_valid:
                audit_logger.log_security_event('VALIDATION_FAILED', message)
                raise ValueError(f"Validation failed: {message}")
            
            # 入力サニタイズ
            sanitized_data = security_manager.sanitize_input(data)
            
            # サニタイズされたデータで関数を実行
            if args and isinstance(args[0], dict):
                return f(sanitized_data, *args[1:], **kwargs)
            elif 'data' in kwargs:
                kwargs['data'] = sanitized_data
                return f(*args, **kwargs)
            else:
                return f(*args, **{**kwargs, **sanitized_data})
        
        return decorated_function
    return decorator