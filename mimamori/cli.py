# cli.py

import time
from datetime import datetime
import schedule

# モジュールのインポート
from constants import DEFAULT_PORT_NAME, DEFAULT_BAUDRATE, DEFAULT_UNIT_ID, DB_NAME
from adapter import ModbusAdapter
from model import SensorModelSQLA

# --- サービスの初期化 ---
sensor_model = SensorModel(db_name=DB_NAME)
# ModbusAdapterは実行時にコンテキストマネージャで接続/切断を管理

def get_and_save_data():
    """
    データ取得、処理、保存の全体フローを実行する関数。
    scheduleライブラリによって定期実行される。
    """
    # データベースのセットアップを最初に行う
    sensor_model = SensorModelSQLA()
    sensor_model.setup_database()
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- データ取得処理開始 ---")
    
    # 1. Modbusアダプタの接続 (コンテキストマネージャを使用)
    modbus_adapter = ModbusAdapter(
        port=DEFAULT_PORT_NAME,
        baudrate=DEFAULT_BAUDRATE,
        unit_id=DEFAULT_UNIT_ID
    )

    with modbus_adapter as adapter:
        if adapter.client: # 接続に成功した場合のみ続行
            # 2. 読み取り範囲の取得
            start_address, register_count = sensor_model.get_modbus_read_range()

            # 3. Modbusデータの読み取り
            raw_registers = adapter.read_holding_registers(
                address=start_address,
                count=register_count
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

# --- メイン実行部 ---
def main():
    # スケジュール設定
    # 15分ごとに get_and_save_data 関数を実行するように設定
    schedule.every(15).minutes.do(get_and_save_data)
    
    print("\n==============================================")
    print("データ取得スケジューラーが起動しました。")
    print("15分ごとにデータ取得とSQLite保存を実行します。")
    print("停止するには Ctrl+C を押してください。")
    print("==============================================")
    
    # プログラムが終了しないように無限ループでスケジュールをチェック
    while True:
        schedule.run_pending()
        time.sleep(1) # スケジュールのチェック間隔 (1秒ごと)
