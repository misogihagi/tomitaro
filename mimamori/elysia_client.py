import os
import requests
from typing import Dict, Any, Optional

class ElysiaClient:
    """
    Client for interacting with the Elysia API server.
    """
    def __init__(self, host: str, token: Optional[str] = None):
        """
        :param host: The host URL of the Elysia server (e.g. http://localhost:3000)
        :param token: The Bearer token for Basic auth credentials. 
                      Defaults to ELYSIA_AUTH_TOKEN or BASIC_AUTH_CREDENTIALS from environment.
        """
        self.host = host.rstrip('/')
        self.token = token or os.environ.get("ELYSIA_AUTH_TOKEN") or os.environ.get("BASIC_AUTH_CREDENTIALS")

    def post_measurement(self, data: Dict[str, Any]) -> bool:
        """
        Send measurement data to the Elysia server via POST request.
        """
        if not self.token:
            print("--- Elysiaアップロードエラー: 認証トークンが設定されていません (ELYSIA_AUTH_TOKEN) ---")
            return False

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        
        try:
            # treaty posts to the root URL or / depending on server setup.
            # Assuming '/' based on the treaty setup in client-cloudflare.
            response = requests.post(f"{self.host}/", json=data, headers=headers)
            response.raise_for_status()
            print(f"--- Elysiaアップロード成功: {response.status_code} ---")
            return True
        except requests.exceptions.RequestException as e:
            print(f"--- Elysiaアップロード失敗: {e} ---")
            if hasattr(e, 'response') and e.response is not None:
                print(f"レスポンス: {e.response.text}")
            return False
