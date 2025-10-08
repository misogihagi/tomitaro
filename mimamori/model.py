# model.py

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple

# --- 設定 ---
DB_NAME = "sensor_data.db"

# センサーデータのアドレスと処理の定義 (ビジネスロジックの一部)
SENSOR_MAP = {
    0: {'名前': 'temperature', 'サンプリング': 10},
    1: {'名前': 'humidness', 'サンプリング': 10},
    2: {'名前': 'EC_conductivity', 'サンプリング': 1},
    3: {'名前': 'PH', 'サンプリング': 10},
    4: {'名前': 'Nitrogen', 'サンプリング': 1},
    5: {'名前': 'Phosphorus', 'サンプリング': 1},
    6: {'名前': 'Potassium', 'サンプリング': 1}
}

class SensorModel:
    """
    センサーデータのモデルと処理ロジック、データベース操作を扱うクラス。
    """

    def __init__(self, db_name: str = DB_NAME, sensor_map: Dict[int, Dict[str, Any]] = SENSOR_MAP):
        self.db_name = db_name
        self.sensor_map = sensor_map

    def setup_database(self):
        """SQLiteデータベースとテーブルを初期設定する"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # テーブル定義のためのカラム名を動的に生成
        columns = ", ".join([f"{config['名前']} REAL" for config in self.sensor_map.values()])
        
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
        print(f"データベース {self.db_name} のセットアップが完了しました。")

    def process_raw_data(self, raw_registers: List[int]) -> Dict[str, float]:
        """
        生のModbusレジスタ値を受け取り、SENSOR_MAPに基づいて処理・変換する。
        """
        processed_data = {}
        start_address = min(self.sensor_map.keys())
        register_count = len(raw_registers)

        for offset in range(register_count):
            register_value = raw_registers[offset]
            current_address = start_address + offset
            config = self.sensor_map.get(current_address)
            
            if config:
                name = config['名前']
                sampling_rate = config['サンプリング']
                # データの変換ロジック
                processed_value = register_value / sampling_rate
                processed_data[name] = processed_value
                
        return processed_data

    def save_data(self, data: Dict[str, float]):
        """
        処理済みのセンサーデータをデータベースに保存する。
        """
        if not data:
            return

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        columns = "timestamp, " + ", ".join(data.keys())
        placeholders = "?, " + ", ".join(["?"] * len(data))
        values: List[Any] = [current_time] + list(data.values())
        
        insert_sql = f"""
        INSERT INTO measurements ({columns}) VALUES ({placeholders})
        """
        
        cursor.execute(insert_sql, values)
        conn.commit()
        conn.close()
        print(f"--- データベースに保存成功 ({current_time}) ---")

    def get_modbus_read_range(self) -> Tuple[int, int]:
        """Modbusアダプタが読み取るべき開始アドレスとレジスタ数を返す"""
        start_address = min(self.sensor_map.keys())
        register_count = max(self.sensor_map.keys()) - start_address + 1
        return start_address, register_count
