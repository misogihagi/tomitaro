# adapter.py

from pymodbus.client import ModbusSerialClient
from typing import Optional, List, Tuple

class ModbusAdapter:
    """
    Modbusデバイスとの通信を扱うアダプタクラス。
    """
    def __init__(self, port: str, baudrate: int, unit_id: int = 1, timeout: int = 1):
        self.port = port
        self.baudrate = baudrate
        self.unit_id = unit_id
        self.timeout = timeout
        self.client: Optional[ModbusSerialClient] = None

    def __enter__(self):
        """コンテキストマネージャとして使用される際の接続処理"""
        self.client = ModbusSerialClient(
            baudrate=self.baudrate,
            port=self.port,
            timeout=self.timeout
        )
        if not self.client.connect():
            print("Modbusデバイスへの接続に失敗しました。ポート名や配線を確認してください。")
            self.client = None # 接続失敗時はNoneにしておく
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャ終了時の切断処理"""
        if self.client:
            self.client.close()

    def read_holding_registers(self, address: int, count: int) -> Optional[List[int]]:
        """
        指定されたアドレスと数だけHolding Registersを読み取る。
        成功した場合はレジスタのリストを、失敗した場合はNoneを返す。
        """
        if not self.client:
            return None

        try:
            # Holding Registersを一度に読み取る
            result = self.client.read_holding_registers(
                address=address,
                count=count,
                slave=self.unit_id
            )

            if result.isError():
                print(f"Modbus通信エラーが発生しました: {result}")
                return None
            
            if result.registers:
                return result.registers
            else:
                print("レジスタデータが取得できませんでした。")
                return None

        except Exception as e:
            print(f"Modbus通信中に予期せぬエラーが発生しました: {e}")
            return None
