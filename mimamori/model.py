# model_sqlalchemy.py

from datetime import datetime
from typing import Dict, Any, List, Tuple

from sqlalchemy import create_engine, Column, Float, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import MetaData, Table

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

# ORMのためのベースクラス
Base = declarative_base()

# センサーマップに基づいて動的にモデルクラスを生成
def create_measurement_model(sensor_map: Dict[int, Dict[str, Any]]):
    """SENSOR_MAPに基づいてMeasurementモデルクラスを動的に生成する"""
    
    # 共通のカラム
    attrs = {
        '__tablename__': 'measurements',
        'timestamp': Column(String, primary_key=True),
        # 'id': Column(Integer, primary_key=True, autoincrement=True), # Auto-incrementing IDが必要な場合はこちら
    }

    # SENSOR_MAPからカラムを動的に追加
    for config in sensor_map.values():
        column_name = config['名前']
        # SQLiteのREALに対応するFloat型を使用
        attrs[column_name] = Column(Float)
        
    # クラス定義 (ORMマッピング)
    Measurement = type('Measurement', (Base,), attrs)
    return Measurement

Measurement = create_measurement_model(SENSOR_MAP)

class SensorModelSQLA:
    """
    センサーデータのモデルと処理ロジック、データベース操作を扱うクラス (SQLAlchemy版)。
    """

    def __init__(self, db_name: str = DB_NAME, sensor_map: Dict[int, Dict[str, Any]] = SENSOR_MAP):
        self.db_name = db_name
        self.sensor_map = sensor_map
        # SQLAlchemyエンジンとセッションを初期化
        # SQLiteの場合、`sqlite:///` に続けてファイルパスを指定
        self.engine = create_engine(f'sqlite:///{self.db_name}')
        self.Session = sessionmaker(bind=self.engine)

    def setup_database(self):
        """データベースとテーブルを初期設定する (SQLAlchemy ORMを使用)"""
        # Baseのサブクラス (Measurement) に関連付けられたテーブルを作成
        Base.metadata.create_all(self.engine)
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
        処理済みのセンサーデータをデータベースに保存する (SQLAlchemy ORMを使用)。
        """
        if not data:
            return

        session = self.Session()
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Measurementオブジェクトを動的に作成
            measurement_data = {'timestamp': current_time, **data}
            measurement = Measurement(**measurement_data)
            
            # セッションに追加してコミット
            session.add(measurement)
            session.commit()
            print(f"--- データベースに保存成功 ({current_time}) ---")
        except Exception as e:
            session.rollback()
            print(f"--- データベース保存失敗: {e} ---")
        finally:
            session.close()

    def get_modbus_read_range(self) -> Tuple[int, int]:
        """Modbusアダプタが読み取るべき開始アドレスとレジスタ数を返す"""
        start_address = min(self.sensor_map.keys())
        register_count = max(self.sensor_map.keys()) - start_address + 1
        return start_address, register_count
