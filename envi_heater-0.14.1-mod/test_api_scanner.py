#!/usr/bin/env python3
"""
Envi API Scanner - Test utility to explore and scan the Envi API endpoints.

This tool helps discover available endpoints, test authentication,
and explore the API structure beyond what's currently implemented.
"""

import asyncio
import base64
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientTimeout


class EnviApiScanner:
    """Scanner for exploring Envi API endpoints."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.base_url = "https://app-apis.enviliving.com/apis/v1"
        self.token: Optional[str] = None
        self.token_expires: Optional[datetime] = None
        self.timeout = ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def authenticate(self) -> bool:
        """Authenticate and get JWT token."""
        print("\n[AUTH] Authenticating...")
        fresh_device_id = f"scanner_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": self.username,
            "password": self.password,
            "login_type": 1,
            "device_id": fresh_device_id,
            "device_type": "scanner",
        }
        url = f"{self.base_url}/auth/login"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "EnviAPI-Scanner/1.0",
        }

        try:
            async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as resp:
                resp_text = await resp.text()
                print(f"   Status: {resp.status}")
                
                if resp.status != 200:
                    print(f"   [FAIL] Login failed: {resp_text[:200]}")
                    return False

                data = json.loads(resp_text)
                if data.get("status") != "success":
                    print(f"   [FAIL] Login rejected: {data.get('msg', 'unknown error')}")
                    return False

                self.token = data["data"]["token"]
                self.token_expires = self._parse_jwt_expiry(self.token)
                
                print(f"   [OK] Authentication successful!")
                print(f"   Token: {self.token[:50]}...")
                if self.token_expires:
                    print(f"   Expires: {self.token_expires.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                return True
        except Exception as e:
            print(f"   [FAIL] Authentication error: {e}")
            return False

    def _parse_jwt_expiry(self, token: str) -> Optional[datetime]:
        """Extract expiry from JWT token."""
        try:
            payload_part = token.split(".")[1]
            payload_part += "=" * (-len(payload_part) % 4)
            claims = json.loads(base64.urlsafe_b64decode(payload_part))
            exp = claims.get("exp")
            if exp:
                return datetime.fromtimestamp(int(exp), tz=timezone.utc)
        except Exception:
            pass
        return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request."""
        if not self.token:
            await self.authenticate()

        headers = kwargs.pop("headers", {}) or {}
        headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        })
        kwargs["headers"] = headers
        url = f"{self.base_url}/{endpoint}"

        async with self.session.request(method.upper(), url, timeout=self.timeout, **kwargs) as resp:
            resp_text = await resp.text()
            try:
                data = json.loads(resp_text) if resp_text else {}
            except json.JSONDecodeError:
                data = {"raw_response": resp_text}

            return {
                "status_code": resp.status,
                "headers": dict(resp.headers),
                "data": data,
                "raw_text": resp_text[:500] if len(resp_text) > 500 else resp_text,
            }

    async def test_known_endpoints(self) -> None:
        """Test all known endpoints from the codebase."""
        print("\n" + "="*70)
        print("[LIST] TESTING KNOWN ENDPOINTS")
        print("="*70)

        # Test device/list
        print("\n1. GET /device/list")
        result = await self._request("GET", "device/list")
        self._print_result(result)
        
        device_ids = []
        if result["status_code"] == 200 and isinstance(result["data"].get("data"), list):
            device_ids = [d.get("id") for d in result["data"]["data"] if d.get("id")]
            print(f"   Found {len(device_ids)} device(s): {device_ids}")

        # Test device/{id} for each device
        if device_ids:
            for device_id in device_ids[:3]:  # Limit to first 3 devices
                print(f"\n2. GET /device/{device_id}")
                result = await self._request("GET", f"device/{device_id}")
                self._print_result(result)

    async def scan_common_endpoints(self) -> None:
        """Try common REST API endpoint patterns."""
        print("\n" + "="*70)
        print("[SCAN] SCANNING COMMON ENDPOINT PATTERNS")
        print("="*70)

        # Get a device ID first
        device_list = await self._request("GET", "device/list")
        device_ids = []
        if device_list["status_code"] == 200 and isinstance(device_list["data"].get("data"), list):
            device_ids = [d.get("id") for d in device_list["data"]["data"] if d.get("id")]
        
        if not device_ids:
            print("   [WARN] No devices found. Skipping device-specific scans.")
            return

        device_id = device_ids[0]
        print(f"   Using device ID: {device_id}")

        # Common endpoint patterns to try
        patterns = [
            # Device endpoints
            ("GET", "device"),
            ("GET", f"device/{device_id}/status"),
            ("GET", f"device/{device_id}/state"),
            ("GET", f"device/{device_id}/info"),
            ("GET", f"device/{device_id}/details"),
            ("GET", f"device/{device_id}/schedule"),
            ("GET", f"device/{device_id}/schedules"),
            ("GET", f"device/{device_id}/settings"),
            ("GET", f"device/{device_id}/config"),
            ("GET", f"device/{device_id}/history"),
            ("GET", f"device/{device_id}/stats"),
            
            # Alternative update endpoints
            ("PATCH", f"device/{device_id}"),
            ("PUT", f"device/{device_id}"),
            ("POST", f"device/{device_id}/update"),
            ("POST", f"device/{device_id}/control"),
            
            # User/Account endpoints
            ("GET", "user"),
            ("GET", "user/profile"),
            ("GET", "user/info"),
            ("GET", "account"),
            
            # Other common patterns
            ("GET", "devices"),
            ("GET", "heaters"),
            ("GET", "status"),
            ("GET", "health"),
        ]

        found_endpoints = []
        for method, endpoint in patterns:
            result = await self._request(method, endpoint)
            if result["status_code"] not in (404, 405):
                found_endpoints.append((method, endpoint, result))
                print(f"\n   [OK] {method} {endpoint} -> {result['status_code']}")
                if result["status_code"] == 200:
                    self._print_result(result, indent="      ")
            else:
                print(f"   [FAIL] {method} {endpoint} -> {result['status_code']}")

        if found_endpoints:
            print(f"\n   [STATS] Found {len(found_endpoints)} additional endpoints!")

    async def discover_unknown_endpoints(self) -> None:
        """Advanced discovery of unknown endpoints using multiple strategies."""
        print("\n" + "="*70)
        print("[DISCOVER] ADVANCED ENDPOINT DISCOVERY")
        print("="*70)

        device_list = await self._request("GET", "device/list")
        device_ids = []
        if device_list["status_code"] == 200 and isinstance(device_list["data"].get("data"), list):
            device_ids = [d.get("id") for d in device_list["data"]["data"] if d.get("id")]

        if not device_ids:
            print("   [WARN] No devices found. Skipping discovery.")
            return

        device_id = device_ids[0]
        print(f"   Using device ID: {device_id}")

        found_endpoints = []

        # Get schedule_id from device data first
        device_detail = await self._request("GET", f"device/{device_id}")
        schedule_id = None
        if device_detail["status_code"] == 200:
            schedule_data = device_detail["data"].get("data", {}).get("schedule", {})
            schedule_id = schedule_data.get("schedule_id") if isinstance(schedule_data, dict) else None

        # Strategy 1: Based on fields we saw in device detail response
        print("\n   Strategy 1: Endpoints based on device data fields...")
        field_based_endpoints = [
            # Schedule related (we found schedule/list works!)
            ("GET", f"schedule/{device_id}"),
            ("GET", f"schedule/list"),
            ("GET", f"schedules"),
            ("GET", f"device/{device_id}/schedule/list"),
            ("GET", f"schedule/{schedule_id}" if schedule_id else None),  # Get specific schedule
            ("POST", f"schedule/create"),
            ("POST", f"schedule/update"),
            ("PUT", f"schedule/{schedule_id}" if schedule_id else None),
            ("PATCH", f"schedule/{schedule_id}" if schedule_id else None),
            # Note: DELETE was tested but actually deletes - skipping for safety
            
            # Settings endpoints
            ("GET", f"device/{device_id}/settings/night-light"),
            ("PATCH", f"device/{device_id}/settings/night-light"),
            ("GET", f"device/{device_id}/settings/pilot-light"),
            ("PATCH", f"device/{device_id}/settings/pilot-light"),
            ("GET", f"device/{device_id}/settings/display"),
            ("PATCH", f"device/{device_id}/settings/display"),
            
            # Mode endpoints
            ("POST", f"device/{device_id}/mode"),
            ("POST", f"device/{device_id}/set-mode"),
            ("POST", f"device/update-mode/{device_id}"),
            
            # State/Control endpoints
            ("POST", f"device/{device_id}/turn-on"),
            ("POST", f"device/{device_id}/turn-off"),
            ("POST", f"device/{device_id}/toggle"),
            
            # Hold endpoints (we saw is_hold field)
            ("POST", f"device/{device_id}/hold"),
            ("POST", f"device/{device_id}/hold/clear"),
            ("POST", f"device/{device_id}/permanent-hold"),
            
            # Geofence (we saw is_geofence_active)
            ("GET", f"geofence"),
            ("GET", f"geofence/list"),
            ("GET", f"device/{device_id}/geofence"),
            
            # Temperature endpoints (variations)
            ("POST", f"device/{device_id}/temperature"),
            ("PUT", f"device/{device_id}/temperature"),
            ("POST", f"device/set-temperature/{device_id}"),
            
            # Additional patterns based on known endpoint structure
            ("POST", f"device/update-state/{device_id}"),
            ("POST", f"device/update/{device_id}"),
        ]

        for method, endpoint in field_based_endpoints:
            if endpoint is None:  # Skip None endpoints (when schedule_id not available)
                continue
            result = await self._request(method, endpoint)
            if result["status_code"] not in (404, 405):
                found_endpoints.append((method, endpoint, result))
                print(f"   [OK] {method} {endpoint} -> {result['status_code']}")
                if result["status_code"] in (200, 201, 204):
                    self._print_result(result, indent="      ")
            # Don't print failures for this section to reduce noise

        # Strategy 2: Different HTTP methods on known endpoints
        print("\n   Strategy 2: Testing different HTTP methods on known endpoints...")
        known_endpoints = [
            "device/list",
            f"device/{device_id}",
            f"device/update-temperature/{device_id}",
        ]
        
        methods_to_try = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        for endpoint in known_endpoints:
            for method in methods_to_try:
                # Skip if we already know this method works
                if endpoint == "device/list" and method == "GET":
                    continue
                if endpoint == f"device/{device_id}" and method == "GET":
                    continue
                if endpoint == f"device/update-temperature/{device_id}" and method == "PATCH":
                    continue
                
                result = await self._request(method, endpoint)
                if result["status_code"] not in (404, 405):
                    found_endpoints.append((method, endpoint, result))
                    print(f"   [OK] {method} {endpoint} -> {result['status_code']}")
                    if result["status_code"] in (200, 201, 204):
                        self._print_result(result, indent="      ")

        # Strategy 3: API documentation and version endpoints
        print("\n   Strategy 3: API documentation and version endpoints...")
        doc_endpoints = [
            ("GET", "docs"),
            ("GET", "api-docs"),
            ("GET", "swagger"),
            ("GET", "swagger.json"),
            ("GET", "openapi.json"),
            ("GET", "api/v1"),
            ("GET", "api/v2"),
            ("GET", "v2/device/list"),
            ("GET", "version"),
            ("GET", "info"),
        ]
        
        for method, endpoint in doc_endpoints:
            result = await self._request(method, endpoint)
            if result["status_code"] not in (404, 405):
                found_endpoints.append((method, endpoint, result))
                print(f"   [OK] {method} {endpoint} -> {result['status_code']}")
                if result["status_code"] == 200:
                    self._print_result(result, indent="      ")

        # Strategy 4: User/Account related endpoints
        print("\n   Strategy 4: User and account endpoints...")
        user_endpoints = [
            ("GET", "user/profile"),
            ("GET", "user/info"),
            ("GET", "user/devices"),
            ("GET", "account/info"),
            ("GET", "account/settings"),
            ("GET", "me"),
            ("GET", "profile"),
        ]
        
        for method, endpoint in user_endpoints:
            result = await self._request(method, endpoint)
            if result["status_code"] not in (404, 405):
                found_endpoints.append((method, endpoint, result))
                print(f"   [OK] {method} {endpoint} -> {result['status_code']}")
                if result["status_code"] == 200:
                    self._print_result(result, indent="      ")

        # Strategy 5: Check response headers for hints
        print("\n   Strategy 5: Analyzing response headers for endpoint hints...")
        test_result = await self._request("GET", "device/list")
        headers = test_result.get("headers", {})
        interesting_headers = ["Link", "X-API-Version", "X-Endpoints", "Allow", "Access-Control-Allow-Methods"]
        print("   Response headers that might contain hints:")
        for header in interesting_headers:
            if header in headers:
                print(f"      {header}: {headers[header]}")

        # Strategy 6: Try OPTIONS on known endpoints (might reveal allowed methods)
        print("\n   Strategy 6: OPTIONS requests to discover allowed methods...")
        for endpoint in ["device/list", f"device/{device_id}", "schedule/list"]:
            result = await self._request("OPTIONS", endpoint)
            if result["status_code"] in (200, 204):
                allow_header = result.get("headers", {}).get("Allow", "")
                if allow_header:
                    print(f"   [OK] OPTIONS {endpoint} -> Allowed methods: {allow_header}")
                    found_endpoints.append(("OPTIONS", endpoint, result))

        # Strategy 7: Explore schedule endpoints more deeply
        print("\n   Strategy 7: Deep dive into schedule endpoints...")
        schedule_endpoints = [
            ("GET", "schedule/list"),
            ("GET", f"schedule/device/{device_id}"),
            ("POST", "schedule/create"),
            ("POST", "schedule/add"),
            ("PUT", f"schedule/{schedule_id}" if schedule_id else None),
            ("PATCH", f"schedule/{schedule_id}" if schedule_id else None),
            ("GET", f"schedule/{schedule_id}" if schedule_id else None),
        ]
        
        for method, endpoint in schedule_endpoints:
            if endpoint is None:
                continue
            result = await self._request(method, endpoint)
            if result["status_code"] not in (404, 405):
                # Check if we already found this
                if not any(e[0] == method and e[1] == endpoint for e in found_endpoints):
                    found_endpoints.append((method, endpoint, result))
                    print(f"   [OK] {method} {endpoint} -> {result['status_code']}")
                    if result["status_code"] in (200, 201):
                        self._print_result(result, indent="      ")

        # Summary
        print("\n" + "-"*70)
        if found_endpoints:
            print(f"   [STATS] Discovered {len(found_endpoints)} new endpoints!")
            print("\n   Summary of discovered endpoints:")
            for method, endpoint, result in found_endpoints:
                print(f"      {method:6} {endpoint:50} -> {result['status_code']}")
        else:
            print("   [INFO] No additional endpoints discovered.")
        print("-"*70)

    async def test_update_endpoints(self) -> None:
        """Test various update/control endpoints."""
        print("\n" + "="*70)
        print("[CTRL] TESTING UPDATE/CONTROL ENDPOINTS")
        print("="*70)

        device_list = await self._request("GET", "device/list")
        device_ids = []
        if device_list["status_code"] == 200 and isinstance(device_list["data"].get("data"), list):
            device_ids = [d.get("id") for d in device_list["data"]["data"] if d.get("id")]

        if not device_ids:
            print("   [WARN] No devices found. Skipping update tests.")
            return

        device_id = device_ids[0]
        print(f"   Using device ID: {device_id}")

        # Get current state first
        current_state = await self._request("GET", f"device/{device_id}")
        print(f"\n   Current device state:")
        if current_state["status_code"] == 200:
            self._print_result(current_state, indent="      ")

        # Test known update endpoint
        print(f"\n   Testing PATCH /device/update-temperature/{device_id}")
        print("   (This will NOT actually change settings - just testing endpoint)")
        
        # Try to get current temp first to restore it
        current_temp = None
        if current_state["status_code"] == 200:
            data = current_state["data"].get("data", {})
            current_temp = data.get("current_temperature") or data.get("temperature")

        # Test with current temp (should be safe)
        if current_temp:
            test_payload = {"temperature": current_temp}
            result = await self._request("PATCH", f"device/update-temperature/{device_id}", json=test_payload)
            print(f"   Status: {result['status_code']}")
            if result["status_code"] != 200:
                self._print_result(result, indent="      ")

        # Test other update patterns
        update_patterns = [
            ("PATCH", f"device/{device_id}", {"state": 0}),
            ("PUT", f"device/{device_id}", {"state": 0}),
            ("POST", f"device/{device_id}/control", {"action": "status"}),
        ]

        for method, endpoint, payload in update_patterns:
            print(f"\n   Testing {method} {endpoint}")
            result = await self._request(method, endpoint, json=payload)
            if result["status_code"] not in (404, 405):
                print(f"   Status: {result['status_code']}")
                self._print_result(result, indent="      ")

    async def explore_response_structures(self) -> None:
        """Deep dive into response structures."""
        print("\n" + "="*70)
        print("[EXPLORE] EXPLORING RESPONSE STRUCTURES")
        print("="*70)

        # Device list structure
        print("\n1. Device List Structure:")
        result = await self._request("GET", "device/list")
        if result["status_code"] == 200:
            data = result["data"]
            print(f"   Top-level keys: {list(data.keys())}")
            if "data" in data and isinstance(data["data"], list) and data["data"]:
                device = data["data"][0]
                print(f"   Device object keys: {list(device.keys())}")
                print(f"   Sample device: {json.dumps(device, indent=6)}")

        # Device detail structure
        device_list = await self._request("GET", "device/list")
        device_ids = []
        if device_list["status_code"] == 200 and isinstance(device_list["data"].get("data"), list):
            device_ids = [d.get("id") for d in device_list["data"]["data"] if d.get("id")]

        if device_ids:
            print(f"\n2. Device Detail Structure (device_id: {device_ids[0]}):")
            result = await self._request("GET", f"device/{device_ids[0]}")
            if result["status_code"] == 200:
                data = result["data"]
                print(f"   Top-level keys: {list(data.keys())}")
                if "data" in data:
                    device_data = data["data"]
                    print(f"   Device data keys: {list(device_data.keys())}")
                    print(f"   Full structure: {json.dumps(device_data, indent=6)}")

    def _print_result(self, result: Dict[str, Any], indent: str = "   ") -> None:
        """Pretty print API result."""
        status = result["status_code"]
        data = result["data"]

        if status == 200:
            print(f"{indent}[OK] Status: {status}")
        elif status in (401, 403):
            print(f"{indent}[LOCK] Status: {status} (Auth required)")
        elif status == 404:
            print(f"{indent}[FAIL] Status: {status} (Not found)")
        elif status == 405:
            print(f"{indent}[WARN] Status: {status} (Method not allowed)")
        else:
            print(f"{indent}[WARN] Status: {status}")

        if isinstance(data, dict):
            if "status" in data:
                print(f"{indent}   API Status: {data['status']}")
            if "msg" in data:
                print(f"{indent}   Message: {data['msg']}")
            if "data" in data:
                data_content = data["data"]
                if isinstance(data_content, dict):
                    print(f"{indent}   Data keys: {list(data_content.keys())[:10]}")
                elif isinstance(data_content, list):
                    print(f"{indent}   Data: List with {len(data_content)} items")
                    if data_content:
                        print(f"{indent}   First item keys: {list(data_content[0].keys())[:10] if isinstance(data_content[0], dict) else 'N/A'}")

        # Show sample of response
        if isinstance(data, dict) and data:
            sample = json.dumps(data, indent=6)[:500]
            print(f"{indent}   Sample: {sample}...")

    async def test_settings_updates(self) -> None:
        """Test different payload formats for settings updates."""
        print("\n" + "="*70)
        print("[SETTINGS] TESTING SETTINGS UPDATE PAYLOADS")
        print("="*70)

        device_list = await self._request("GET", "device/list")
        device_ids = []
        if device_list["status_code"] == 200 and isinstance(device_list["data"].get("data"), list):
            device_ids = [d.get("id") for d in device_list["data"]["data"] if d.get("id")]

        if not device_ids:
            print("   [WARN] No devices found. Skipping settings tests.")
            return

        device_id = device_ids[0]
        print(f"   Using device ID: {device_id}")

        # Get current device state
        current_state = await self._request("GET", f"device/{device_id}")
        if current_state["status_code"] != 200:
            print("   [FAIL] Could not fetch current device state")
            return

        device_data = current_state["data"].get("data", {})
        current_temp = device_data.get("current_temperature") or device_data.get("temperature")
        current_state_val = device_data.get("state", 1)
        current_freeze_protect = device_data.get("freeze_protect_setting")
        current_child_lock = device_data.get("child_lock_setting")

        print(f"\n   Current device state:")
        print(f"      Temperature: {current_temp}")
        print(f"      State: {current_state_val}")
        print(f"      Freeze Protect: {current_freeze_protect}")
        print(f"      Child Lock: {current_child_lock}")

        # Test different payload formats for freeze_protect_setting
        print(f"\n   Testing freeze_protect_setting updates:")
        test_payloads = [
            # Format 1: Just the setting
            {"freeze_protect_setting": not current_freeze_protect if isinstance(current_freeze_protect, bool) else False},
            
            # Format 2: Setting + temperature
            {"temperature": current_temp, "freeze_protect_setting": not current_freeze_protect if isinstance(current_freeze_protect, bool) else False},
            
            # Format 3: Setting + temperature + state
            {"temperature": current_temp, "state": current_state_val, "freeze_protect_setting": not current_freeze_protect if isinstance(current_freeze_protect, bool) else False},
            
            # Format 4: Try with inverted value (since API seems inverted)
            {"temperature": current_temp, "state": current_state_val, "freeze_protect_setting": current_freeze_protect},
        ]

        for i, payload in enumerate(test_payloads, 1):
            print(f"\n   Test {i}: {json.dumps(payload, indent=6)}")
            result = await self._request("PATCH", f"device/update-temperature/{device_id}", json=payload)
            print(f"      Status: {result['status_code']}")
            if result["status_code"] == 200:
                print(f"      [SUCCESS] Payload format {i} works!")
                self._print_result(result, indent="         ")
                # Restore original value
                restore_payload = {"temperature": current_temp, "state": current_state_val, "freeze_protect_setting": current_freeze_protect}
                await self._request("PATCH", f"device/update-temperature/{device_id}", json=restore_payload)
                break
            elif result["status_code"] == 400:
                print(f"      [FAIL] Bad Request - payload format rejected")
                if "data" in result and result["data"]:
                    error_msg = result["data"].get("msg") or str(result["data"])
                    print(f"      Error: {error_msg[:200]}")
            else:
                print(f"      [FAIL] Status {result['status_code']}")
                self._print_result(result, indent="         ")

        # Test child_lock_setting
        print(f"\n   Testing child_lock_setting updates:")
        test_payloads_lock = [
            {"temperature": current_temp, "state": current_state_val, "child_lock_setting": not current_child_lock if isinstance(current_child_lock, bool) else False},
            {"temperature": current_temp, "state": current_state_val, "child_lock_setting": current_child_lock},
        ]

        for i, payload in enumerate(test_payloads_lock, 1):
            print(f"\n   Test {i}: {json.dumps(payload, indent=6)}")
            result = await self._request("PATCH", f"device/update-temperature/{device_id}", json=payload)
            print(f"      Status: {result['status_code']}")
            if result["status_code"] == 200:
                print(f"      [SUCCESS] Payload format {i} works!")
                self._print_result(result, indent="         ")
                # Restore original value
                restore_payload = {"temperature": current_temp, "state": current_state_val, "child_lock_setting": current_child_lock}
                await self._request("PATCH", f"device/update-temperature/{device_id}", json=restore_payload)
                break
            elif result["status_code"] == 400:
                print(f"      [FAIL] Bad Request")
                if "data" in result and result["data"]:
                    error_msg = result["data"].get("msg") or str(result["data"])
                    print(f"      Error: {error_msg[:200]}")

        print("\n" + "-"*70)

    async def run_full_scan(self) -> None:
        """Run complete API scan."""
        print("\n" + "="*70)
        print("[START] ENVI API SCANNER")
        print("="*70)
        print(f"Base URL: {self.base_url}")
        print(f"Username: {self.username}")

        if not await self.authenticate():
            print("\n[FAIL] Authentication failed. Cannot proceed.")
            return

        await self.test_known_endpoints()
        await self.explore_response_structures()
        await self.scan_common_endpoints()
        await self.discover_unknown_endpoints()
        await self.test_update_endpoints()
        await self.test_settings_updates()

        print("\n" + "="*70)
        print("[OK] SCAN COMPLETE")
        print("="*70)


async def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python test_api_scanner.py <username> <password>")
        print("\nExample:")
        print("  python test_api_scanner.py user@example.com mypassword")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    async with EnviApiScanner(username, password) as scanner:
        await scanner.run_full_scan()


if __name__ == "__main__":
    asyncio.run(main())

