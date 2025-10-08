import time
from cli import get_and_save_data
import schedule

if __name__ == "__main__":
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
