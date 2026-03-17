# mimamori (土壌モニタリングシステム)

`mimamori` は、Raspberry Pi と各種センサーを使用して土壌の状態（水分量、温度など）をリアルタイムで監視し、Cloudflare 経由でデータの保存・通知を行い、Grafana で可視化するシステムです。

## 1. システム構成

- **データ取得 (Raspberry Pi)**: 5分間隔で Modbus センサーからデータを取得し、ローカルの SQLite および Cloudflare D1 に保存します。
- **データ保存 (Cloudflare D1 / KV)**: クラウド上での時系列データの保持。
- **通知 (Slack)**: データ取得の成功や異常を Slack に通知。
- **可視化 (Grafana)**: 収集したデータをダッシュボードでグラフ表示。

## 2. ディレクトリ構成

```text
.
├── main.py              # メインエントリポイント（スケジューラ起動）
├── cli.py               # データ取得・保存のメインロジック
├── adapter.py           # Modbus 通信アダプタ
├── model.py             # データモデルとデータベース操作（SQLite/D1）
├── constants.py         # 定数設定（Modbus設定、DB名など）
├── bot/                 # Cloudflare Workers (Slack Bot) 関連
├── dashboard/           # Grafana (Docker Compose / Terraform) 関連
├── database/            # データベース基盤 (Terraform) 関連
└── docs/                # 仕様書・ドキュメント
```

## 3. セットアップ手順

### 3.1. Raspberry Pi 側の準備

#### 依存関係のインストール
このプロジェクトは `uv` または `pip` を使用して管理できます。

```bash
# uv を使用する場合
uv sync

# pip を使用する場合
pip install -r requirements.txt
```
※ `pyproject.toml` に基づき、`pymodbus`, `schedule`, `sqlalchemy`, `python-dotenv`, `requests` などが必要です。

#### 環境設定 (.env)
プロジェクトルートに `.env` ファイルを作成し、以下の情報を設定します。

```env
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_DATABASE_ID=your_database_id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

#### Modbus センサーの接続
`constants.py` でポート名やボーレートを確認・設定してください。デフォルトは `/dev/ttyACM0` です。

### 3.2. Cloudflare / Slack 側の準備

1. **Slack App の作成**: `bot/manifest.json` を使用して Slack App を作成し、Webhook URL を取得します。
2. **Cloudflare D1 の作成**: データベースを作成し、ID を `.env` に設定します。
3. **Workers のデプロイ**: `bot/` ディレクトリで `wrangler deploy` を実行します（※ソースコードの実装が必要です）。

### 3.3. Grafana 側の準備

1. **Docker Compose の起動**:
   ```bash
   cd dashboard
   docker-compose up -d
   ```
2. **Terraform による設定**:
   `dashboard/main.tf` を編集して Grafana の URL や認証情報を設定し、実行します。
   ```bash
   terraform init
   terraform apply
   ```

## 4. 使い方

### データ取得の開始 (Raspberry Pi)

以下のコマンドを実行すると、スケジューラが起動し、5分ごとにデータ取得が始まります。

```bash
python main.py
```

ログには以下のように表示されます：
- データ取得の成否
- ローカル SQLite への保存
- Cloudflare D1 への保存
- エラー発生時の Slack 通知

### ダッシュボードの確認
`http://localhost:3000` にアクセスし、Grafana でデータの推移を確認できます。

## 5. 開発者向け情報

- **センサーの追加**: `model.py` の `SENSOR_MAP` を編集することで、取得する項目を増やすことができます。
- **保存先の変更**: `model.py` の `SensorModelSQLA` クラスをカスタマイズしてください。
