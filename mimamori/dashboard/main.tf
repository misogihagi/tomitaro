terraform {
  required_providers {
    grafana = {
      source = "grafana/grafana"
      version = "4.10.0"
    }
  }
}

provider "grafana" {
  url  = "YOUR_GRAFANA_URL" 
  auth = "YOUR_API_KEY_OR_BASIC_AUTH" 
}

resource "grafana_data_source" "sqlite_sensor_data" {
  name = "SQLite Sensor Data"
  type = "franmar-sqlite-datasource" # 使用するプラグインのtypeに置き換えてください
  uid  = "sqlite_sensor_ds"
  
  # SQLiteファイルへのパスを指定
  json_data = jsonencode({
    path = "/path/to/your/sensor_data.db" # データベースファイルへのフルパス
  })
  
  # 任意のバージョン（プラグインに依存）
  # version = 1 
  
  is_default = false
}

## Grafanaダッシュボードの定義 (JSON)
locals {
  # SQLクエリ: 'timestamp'を時間軸、'temperature'を値として取得
  # timestampはdatetime型またはUnixエポックタイムである必要があります。
  sqlite_query = <<-EOT
    SELECT
      strftime('%s', timestamp) AS time,
      temperature
    FROM measurements
    ORDER BY timestamp
  EOT
  
  # ダッシュボードJSONの定義
  dashboard_json = jsonencode({
    title = "Sensor Data Dashboard"
    panels = [
      {
        title  = "Temperature over Time"
        type   = "timeseries"
        gridPos = {
          h = 9
          w = 12
          x = 0
          y = 0
        }
        datasource = "${grafana_data_source.sqlite_sensor_data.uid}"
        targets = [
          {
            refId = "A"
            query = local.sqlite_query
            # プラグインに依存するその他の設定（例: formatAsTimeSeriesなど）
          }
        ]
        options = {}
      }
    ]
    # その他のダッシュボード設定...
  })
}

## Grafanaダッシュボードの作成
resource "grafana_dashboard" "sensor_dashboard" {
  config_json = local.dashboard_json
  # ダッシュボードのフォルダIDを指定することもできます。
  # folder_uid = "general" 
}
