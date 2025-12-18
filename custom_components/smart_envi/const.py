"""Constants for the Smart Envi integration."""
from datetime import timedelta

DOMAIN = "smart_envi"
OPTIONS_KEY = "smart_envi_options"

# Update interval: 30 seconds (balance between responsiveness and API load)
SCAN_INTERVAL = timedelta(seconds=30)

# Configuration defaults and limits
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_API_TIMEOUT = 15  # seconds
MIN_SCAN_INTERVAL = 10  # seconds - minimum to avoid API overload
MAX_SCAN_INTERVAL = 300  # seconds - 5 minutes max
MIN_API_TIMEOUT = 5  # seconds
MAX_API_TIMEOUT = 60  # seconds

# Temperature limits in Fahrenheit
MIN_TEMPERATURE = 50
MAX_TEMPERATURE = 86

# API Configuration
BASE_URL = "https://app-apis.enviliving.com/apis/v1"
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 30  # seconds

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
