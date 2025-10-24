variable "cloudflare_account_id" {
  description = "CloudflareアカウントのID (UUID形式)"
  type        = string
}

variable "cloudflare_api_token" {
  description = "Cloudflare Providerが認証に使用するAPIトークン"
  type        = string
  sensitive   = true # トークンは機密情報として扱う
}

variable "d1_database_name" {
  description = "作成するD1データベースの名前"
  type        = string
  default     = "tomitaro-d1"
}

variable "d1_primary_location_hint" {
  description = "D1プライマリを作成するリージョン（wnam, enam, weur, eeur, apac, ocなど）。省略すると自動で決定される。"
  type        = string
  default     = null # デフォルトは指定なし
}
