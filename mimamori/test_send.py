import os
import sys
from datetime import datetime
from elysia_client import ElysiaClient
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む（ELYSIA_AUTH_TOKENなどに必要）
load_dotenv()

def main():
    """
    Elysiaのサーバーにテストデータを送信するスクリプト
    使用方法: python test_send.py [http://localhost:3000]
    """
    host = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    
    print(f"ElysiaClientのテスト送信を開始します...")
    print(f"送信先ホスト: {host}")
    
    client = ElysiaClient(host=host)

    # サーバー側が期待するデータ構造に基づくテストデータ
    test_data = {
        "timestamp": '2000-10-10T10:00:00Z',
        "site": "Test-Greenhouse",
        "temperature": 25.5,
        "humidness": 60.2,
        "EC_conductivity": 1.5,
        "PH": 6.8,
        "Nitrogen": 140.0,
        "Phosphorus": 50.0,
        "Potassium": 200.0
    }
    
    print(f"送信データ: {test_data}")

    # 送信処理
    success = client.post_measurement(test_data)
    
    if success:
        print("✅ テスト送信に成功しました。")
    else:
        print("❌ テスト送信に失敗しました。")
        print("環境変数(ELYSIA_AUTH_TOKEN または BASIC_AUTH_CREDENTIALS) やホスト名が正しいか確認してください。")

if __name__ == "__main__":
    main()
