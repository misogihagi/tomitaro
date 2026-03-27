import time
import argparse
from datetime import datetime
import schedule
import requests
import json
import os
import traceback
from dotenv import load_dotenv

# モジュールのインポート
from constants import (
    DEFAULT_RS485_PORT_NAME,
    DEFAULT_USB_PORT_NAME,
    DEFAULT_BAUDRATE,
    DEFAULT_UNIT_ID,
)
from adapter import ModbusAdapter
from model import SensorModelSQLA


def get_and_save_data(site, port):
    """
    データ取得、処理、保存の全体フローを実行する関数。
    scheduleライブラリによって定期実行される。
    """
    # データベースのセットアップを最初に行う
    sensor_model = SensorModelSQLA(site=site)
    sensor_model.setup_database()

    print(
        f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- データ取得処理開始 ---"
    )

    # 1. Modbusアダプタの接続 (コンテキストマネージャを使用)
    modbus_adapter = ModbusAdapter(
        port=port, baudrate=DEFAULT_BAUDRATE, unit_id=DEFAULT_UNIT_ID, site=site
    )

    with modbus_adapter as adapter:
        if adapter.client:  # 接続に成功した場合のみ続行
            try:
                # 2. 読み取り範囲の取得
                start_address, register_count = sensor_model.get_modbus_read_range()

                # 3. Modbusデータの読み取り
                raw_registers = adapter.read_holding_registers(
                    address=start_address, count=register_count
                )

                if raw_registers:
                    # 4. 取得データの処理 (model.pyのロジックを使用)
                    processed_data = sensor_model.process_raw_data(raw_registers)

                    # 取得データを表示
                    for name, value in processed_data.items():
                        print(f"  {name}: {value}")

                    # 5. データをデータベースに保存 (model.pyのロジックを使用)
                    sensor_model.save_data(processed_data)
                else:
                    print("データ取得に失敗したため、処理を中断します。")
            # adapter.__exit__によって接続は自動的に閉じられる
            except Exception as e:
                load_dotenv(dotenv_path)
                webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
                error_traceback = traceback.format_exc()

                # 一応標準出力にも
                print(error_traceback)

                # 通知送信
                payload = {"text": error_traceback}
                response = requests.post(
                    webhook_url,
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    print(f"Error: {response.status_code}, {response.text}")
                else:
                    print("Notification sent successfully!")


# --- メイン実行部 ---
def main():
    parser = argparse.ArgumentParser(description="土壌状態を監視します")

    parser.add_argument(
        "--site", type=str, help="対象となるサイトや場所の名前を指定してください"
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=["standalone", "networked"],
        help="自己完結か他己完結か",
    )

    parser.add_argument(
        "--sensor",
        type=str,
        choices=["usb", "rs485"],
        help="USB接続かRS485接続か",
    )
    parser.add_argument("--host", type=str, help="送信するリクエストの宛先")

    args = parser.parse_args()

    site = args.site or ""
    sensor = args.sensor or "rs485"

    if sensor == "usb":
        port = DEFAULT_USB_PORT_NAME
    else:
        port = DEFAULT_RS485_PORT_NAME

    if args.mode == "networked":
        if not arg.host:
            raise ("他己完結モードの時は宛先を指定してください")

    schedule.every(5).minutes.do(lambda: get_and_save_data(site=site, port=port))

    print("\n==============================================")
    print("データ取得スケジューラーが起動しました。")
    print("5分ごとにデータ取得とSQLite保存を実行します。")
    print("停止するには Ctrl+C を押してください。")
    print("==============================================")

    # プログラムが終了しないように無限ループでスケジュールをチェック
    while True:
        schedule.run_pending()
        time.sleep(1)  # スケジュールのチェック間隔 (1秒ごと)
