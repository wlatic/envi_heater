"""Constants for the Smart Envi integration."""
from datetime import timedelta

DOMAIN = "smart_envi"
OPTIONS_KEY = "smart_envi_options"

# Update interval: 30 seconds (balance between responsiveness and API load)
SCAN_INTERVAL = timedelta(seconds=30)

# Temperature limits in Fahrenheit
MIN_TEMPERATURE = 50
MAX_TEMPERATURE = 86

# API Configuration
BASE_URL = "https://app-apis.enviliving.com/apis/v1"

# API Endpoints
ENDPOINTS = {
    "auth_login": "auth/login",
    "device_list": "device/list",
    "device_get": "device/{device_id}",
    "device_update": "device/update-temperature/{device_id}",
    "schedule_list": "schedule/list",
    "schedule_add": "schedule/add",
    "schedule_get": "schedule/{schedule_id}",
    "schedule_update": "schedule/{schedule_id}",
    "schedule_delete": "schedule/{schedule_id}",
}
