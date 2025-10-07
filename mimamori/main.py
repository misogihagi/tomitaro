from pymodbus.client import ModbusSerialClient
import sqlite3
import time
from datetime import datetime
import schedule # スケジュール実行のためのライブラリ

# --- Modbus通信設定 ---
PORT_NAME = "/dev/ttyACM0"
BAUDRATE  = 9600
UNIT_ID   = 1

# --- データベース設定 ---
DB_NAME = "sensor_data.db"

# センサーデータのアドレスと処理の定義
SENSOR_MAP = {
    0: {'名前': 'temperature', 'サンプリング': 10},
    1: {'名前': 'humidness',   'サンプリング': 10},
    2: {'名前': 'EC_conductivity', 'サンプリング': 1},
    3: {'名前': 'PH', 'サンプリング': 10},
    4: {'名前': 'Nitrogen', 'サンプリング': 1},
    5: {'名前': 'Phosphorus', 'サンプリング': 1},
    6: {'名前': 'Potassium', 'サンプリング': 1}
}

def setup_database():
    """SQLiteデータベースとテーブルを初期設定する"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # テーブル定義のためのカラム名を動的に生成
    columns = ", ".join([f"{config['名前']} REAL" for config in SENSOR_MAP.values()])
    
    # measurementsテーブルを作成
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS measurements (
        timestamp TEXT PRIMARY KEY,
        {columns}
    );
    """
    cursor.execute(create_table_sql)
    conn.commit()
    conn.close()
    print(f"データベース {DB_NAME} のセットアップが完了しました。")

def get_and_save_data():
    """Modbusからデータを取得し、SQLiteに保存する処理"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- データ取得処理開始 ---")
    
    # 1. データベース接続
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 2. Modbusクライアント接続
    client = ModbusSerialClient(
        baudrate=BAUDRATE,
        port=PORT_NAME,
        timeout=1
    )

    if client.connect():
        start_address = min(SENSOR_MAP.keys())
        register_count = max(SENSOR_MAP.keys()) - start_address + 1 # 7レジスタ

        try:
            # Holding Registersを一度に読み取る
            result = client.read_holding_registers(
                address=start_address,
                count=register_count,
            )

            if result.isError():
                print(f"Modbus通信エラーが発生しました: {result}")
                return

            if result.registers:
                processed_data = {}
                
                # 3. 取得データの処理
                for offset in range(register_count):
                    register_value = result.registers[offset]
                    current_address = start_address + offset
                    config = SENSOR_MAP.get(current_address)
                    
                    if config:
                        name = config['名前']
                        sampling_rate = config['サンプリング']
                        processed_value = register_value / sampling_rate
                        processed_data[name] = processed_value
                        print(f"  {name}: {processed_value}") # 取得データを表示

                # 4. データをデータベースに保存
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                columns = "timestamp, " + ", ".join(processed_data.keys())
                placeholders = "?, " + ", ".join(["?"] * len(processed_data))
                values = [current_time] + list(processed_data.values())
                
                insert_sql = f"""
                INSERT INTO measurements ({columns}) VALUES ({placeholders})
                """
                
                cursor.execute(insert_sql, values)
                conn.commit()
                print(f"--- データベースに保存成功 ({current_time}) ---")

            else:
                print("レジスタデータが取得できませんでした。")

        except Exception as e:
            print(f"処理中に予期せぬエラーが発生しました: {e}")

        finally:
            client.close()
    else:
        print("Modbusデバイスへの接続に失敗しました。ポート名や配線を確認してください。")
    
    # 5. データベース接続を閉じる
    conn.close()

# --- メイン実行部 ---
if __name__ == "__main__":
    # データベースのセットアップを最初に行う
    setup_database()
    
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
