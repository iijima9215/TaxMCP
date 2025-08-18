"""モックレスポンスクラス

TaxMCPサーバーのAPIレスポンスをモックするためのクラス
"""

from typing import Dict, Any


class MockResponse:
    """APIレスポンスをモックするクラス"""
    
    def __init__(self, data: Dict[str, Any], status_code: int = 200):
        self._data = data
        self.status_code = status_code
        self.headers = {'Content-Type': 'application/json'}
    
    def json(self) -> Dict[str, Any]:
        """JSONデータを返す"""
        return self._data
    
    def __getitem__(self, key):
        """辞書のようにアクセスできるようにする"""
        if key == 'status_code':
            return self.status_code
        return self._data[key]
    
    def __contains__(self, key):
        """in演算子をサポート"""
        if key == 'status_code':
            return True
        return key in self._data
    
    def get(self, key, default=None):
        """辞書のgetメソッドをサポート"""
        if key == 'status_code':
            return self.status_code
        return self._data.get(key, default)
    
    def keys(self):
        """辞書のkeysメソッドをサポート"""
        keys = list(self._data.keys())
        keys.append('status_code')
        return keys
    
    def items(self):
        """辞書のitemsメソッドをサポート"""
        items = list(self._data.items())
        items.append(('status_code', self.status_code))
        return items
    
    def __len__(self):
        """len()関数をサポート"""
        return len(self._data)
    
    def __iter__(self):
        """イテレーションをサポート"""
        return iter(self._data)
    
    def __setitem__(self, key, value):
        """辞書のように値を設定できるようにする"""
        if key == 'status_code':
            self.status_code = value
        else:
            self._data[key] = value
    
    def __repr__(self):
        """文字列表現"""
        return f"MockResponse(data={self._data}, status_code={self.status_code})"
    
    def __str__(self):
        """文字列表現"""
        return str(self._data)