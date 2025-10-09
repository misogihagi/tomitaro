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
