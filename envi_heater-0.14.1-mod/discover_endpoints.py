#!/usr/bin/env python3
"""
Comprehensive endpoint discovery script to find all possible API endpoints.
"""

import asyncio
import json
import sys
from datetime import datetime
import uuid

import aiohttp


async def discover_all_endpoints(username: str, password: str):
    """Comprehensive endpoint discovery."""
    base_url = "https://app-apis.enviliving.com/apis/v1"
    
    async with aiohttp.ClientSession() as session:
        # Authenticate
        print("Authenticating...")
        device_id = f"discover_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        auth_payload = {
            "username": username,
            "password": password,
            "login_type": 1,
            "device_id": device_id,
            "device_type": "discover",
        }
        
        async with session.post(f"{base_url}/auth/login", json=auth_payload) as resp:
            if resp.status != 200:
                print(f"Auth failed: {resp.status}")
                return
            data = await resp.json()
            token = data["data"]["token"]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        # Get device list
        async with session.get(f"{base_url}/device/list", headers=headers) as resp:
            device_list = await resp.json()
            if "data" in device_list and isinstance(device_list["data"], list):
                device_ids = [str(d["id"]) for d in device_list["data"] if "id" in d]
            else:
                print("No devices found")
                return
        
        test_device_id = str(device_ids[0])
        print(f"\nUsing device ID: {test_device_id} for testing")
        
        # Get current device state for reference
        async with session.get(f"{base_url}/device/{test_device_id}", headers=headers) as resp:
            device_data = await resp.json()
            current = device_data["data"]
            current_temp = current.get("current_temperature") or current.get("temperature")
            current_state = current.get("state", 1)
            current_freeze = current.get("freeze_protect_setting")
        
        print(f"\n{'='*70}")
        print("COMPREHENSIVE ENDPOINT DISCOVERY")
        print(f"{'='*70}")
        
        # Test payloads for settings
        test_settings = {
            "freeze_protect_setting": not current_freeze if isinstance(current_freeze, bool) else False,
            "child_lock_setting": not current.get("child_lock_setting", False) if isinstance(current.get("child_lock_setting"), bool) else True,
            "notification_setting": not current.get("notification_setting", False) if isinstance(current.get("notification_setting"), bool) else False,
            "is_hold": not current.get("is_hold", False) if isinstance(current.get("is_hold"), bool) else True,
        }
        
        # Comprehensive endpoint patterns to test
        endpoint_patterns = [
            # Direct device endpoints
            ("PATCH", f"device/{test_device_id}"),
            ("PUT", f"device/{test_device_id}"),
            ("POST", f"device/{test_device_id}"),
            
            # Settings endpoints
            ("PATCH", f"device/{test_device_id}/settings"),
            ("PUT", f"device/{test_device_id}/settings"),
            ("POST", f"device/{test_device_id}/settings"),
            ("PATCH", f"device/settings/{test_device_id}"),
            ("PUT", f"device/settings/{test_device_id}"),
            ("POST", f"device/settings/{test_device_id}"),
            
            # Control endpoints
            ("PATCH", f"device/{test_device_id}/control"),
            ("PUT", f"device/{test_device_id}/control"),
            ("POST", f"device/{test_device_id}/control"),
            ("PATCH", f"device/control/{test_device_id}"),
            ("PUT", f"device/control/{test_device_id}"),
            ("POST", f"device/control/{test_device_id}"),
            
            # Update endpoints
            ("PATCH", f"device/{test_device_id}/update"),
            ("PUT", f"device/{test_device_id}/update"),
            ("POST", f"device/{test_device_id}/update"),
            ("PATCH", f"device/update/{test_device_id}"),
            ("PUT", f"device/update/{test_device_id}"),
            ("POST", f"device/update/{test_device_id}"),
            
            # Configure endpoints
            ("PATCH", f"device/{test_device_id}/configure"),
            ("PUT", f"device/{test_device_id}/configure"),
            ("POST", f"device/{test_device_id}/configure"),
            ("PATCH", f"device/configure/{test_device_id}"),
            
            # Settings-specific endpoints
            ("PATCH", f"device/{test_device_id}/settings/freeze_protect"),
            ("POST", f"device/{test_device_id}/settings/freeze_protect"),
            ("PATCH", f"device/{test_device_id}/settings/child_lock"),
            ("POST", f"device/{test_device_id}/settings/child_lock"),
            ("PATCH", f"device/{test_device_id}/settings/notification"),
            ("POST", f"device/{test_device_id}/settings/notification"),
            ("PATCH", f"device/{test_device_id}/settings/hold"),
            ("POST", f"device/{test_device_id}/settings/hold"),
            
            # Alternative patterns
            ("PATCH", f"device/{test_device_id}/set"),
            ("POST", f"device/{test_device_id}/set"),
            ("PATCH", f"device/set/{test_device_id}"),
            ("POST", f"device/set/{test_device_id}"),
            
            # API v2 patterns (if exists)
            ("PATCH", f"v2/device/{test_device_id}"),
            ("POST", f"v2/device/{test_device_id}"),
            ("PATCH", f"v2/device/{test_device_id}/settings"),
            ("POST", f"v2/device/{test_device_id}/settings"),
            
            # RESTful resource patterns
            ("POST", f"device/{test_device_id}/freeze_protect"),
            ("POST", f"device/{test_device_id}/child_lock"),
            ("POST", f"device/{test_device_id}/notification"),
            ("POST", f"device/{test_device_id}/hold"),
            ("PUT", f"device/{test_device_id}/freeze_protect"),
            ("PUT", f"device/{test_device_id}/child_lock"),
            
            # Action-based patterns (common in IoT APIs)
            ("POST", f"device/{test_device_id}/actions/freeze_protect"),
            ("POST", f"device/{test_device_id}/actions/child_lock"),
            ("POST", f"device/{test_device_id}/actions/notification"),
            ("POST", f"device/{test_device_id}/actions/hold"),
            ("POST", f"device/{test_device_id}/action"),
            
            # Command patterns
            ("POST", f"device/{test_device_id}/command"),
            ("POST", f"device/command/{test_device_id}"),
            ("POST", f"device/{test_device_id}/commands"),
            
            # Property update patterns
            ("PATCH", f"device/{test_device_id}/properties"),
            ("PUT", f"device/{test_device_id}/properties"),
            ("POST", f"device/{test_device_id}/properties"),
            
            # Config patterns
            ("PATCH", f"device/{test_device_id}/config"),
            ("PUT", f"device/{test_device_id}/config"),
            ("POST", f"device/{test_device_id}/config"),
            
            # Preferences patterns
            ("PATCH", f"device/{test_device_id}/preferences"),
            ("PUT", f"device/{test_device_id}/preferences"),
            ("POST", f"device/{test_device_id}/preferences"),
        ]
        
        working_endpoints = []
        failed_endpoints = []
        
        print(f"\nTesting {len(endpoint_patterns)} endpoint patterns...")
        print(f"Testing with freeze_protect_setting as example\n")
        
        for method, endpoint in endpoint_patterns:
            # Try with just the setting
            payload1 = {"freeze_protect_setting": test_settings["freeze_protect_setting"]}
            
            # Try with temperature + state + setting
            payload2 = {
                "temperature": current_temp,
                "state": current_state,
                "freeze_protect_setting": test_settings["freeze_protect_setting"]
            }
            
            for payload_name, payload in [("setting only", payload1), ("with temp+state", payload2)]:
                try:
                    async with session.request(
                        method,
                        f"{base_url}/{endpoint}",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        status = resp.status
                        
                        if status == 200:
                            try:
                                result = await resp.json()
                                print(f"✓ {method:6} {endpoint:50} [{payload_name:15}] -> 200 SUCCESS!")
                                print(f"  Response: {json.dumps(result, indent=2)[:200]}")
                                working_endpoints.append((method, endpoint, payload_name, result))
                                
                                # Restore original
                                restore_payload = {
                                    "temperature": current_temp,
                                    "state": current_state,
                                    "freeze_protect_setting": current_freeze
                                }
                                async with session.request(
                                    method,
                                    f"{base_url}/{endpoint}",
                                    headers=headers,
                                    json=restore_payload,
                                    timeout=aiohttp.ClientTimeout(total=5)
                                ) as restore_resp:
                                    if restore_resp.status == 200:
                                        print(f"  [Restored original value]")
                                break  # Found working endpoint, move to next
                            except:
                                pass
                        elif status == 400:
                            try:
                                result = await resp.json()
                                error_msg = result.get("msg", "Bad Request")
                                if "not allowed" not in error_msg.lower():
                                    # Different error might mean endpoint exists but payload wrong
                                    print(f"? {method:6} {endpoint:50} [{payload_name:15}] -> 400 ({error_msg[:50]})")
                            except:
                                pass
                        elif status == 404:
                            # Endpoint doesn't exist, skip
                            break
                        elif status == 405:
                            # Method not allowed, skip
                            break
                except asyncio.TimeoutError:
                    # Timeout, skip
                    break
                except Exception as e:
                    # Other error, skip
                    break
        
        # Also try discovering endpoints by looking at response headers/links
        print(f"\n{'='*70}")
        print("CHECKING FOR ENDPOINT HINTS IN RESPONSES")
        print(f"{'='*70}")
        
        # Check device detail response for any endpoint hints
        async with session.get(f"{base_url}/device/{test_device_id}", headers=headers) as resp:
            device_detail = await resp.json()
            print("\nDevice detail response keys:")
            print(f"  {list(device_detail.keys())}")
            if "data" in device_detail:
                print("\nDevice data keys:")
                print(f"  {list(device_detail['data'].keys())[:20]}...")
            
            # Check headers for any hints
            print("\nResponse headers:")
            for header, value in resp.headers.items():
                if any(hint in header.lower() for hint in ['link', 'endpoint', 'api', 'url']):
                    print(f"  {header}: {value}")
        
        # Try OPTIONS to see allowed methods
        print(f"\n{'='*70}")
        print("CHECKING ALLOWED METHODS WITH OPTIONS")
        print(f"{'='*70}")
        
        options_endpoints = [
            f"device/{test_device_id}",
            f"device/{test_device_id}/settings",
            f"device/{test_device_id}/control",
            f"device/update-temperature/{test_device_id}",
        ]
        
        for endpoint in options_endpoints:
            try:
                async with session.options(
                    f"{base_url}/{endpoint}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    allowed_methods = resp.headers.get("Allow", "")
                    if allowed_methods:
                        print(f"  {endpoint:50} -> Allowed: {allowed_methods}")
            except:
                pass
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        
        if working_endpoints:
            print("\n[FOUND WORKING ENDPOINTS]:")
            for method, endpoint, payload_type, result in working_endpoints:
                print(f"  ✓ {method} {endpoint} (payload: {payload_type})")
                print(f"    Response: {json.dumps(result, indent=4)[:300]}")
        else:
            print("\n[NO WORKING ENDPOINTS FOUND]")
            print("  All tested endpoints either:")
            print("    - Return 404 (endpoint doesn't exist)")
            print("    - Return 405 (method not allowed)")
            print("    - Return 400 with 'not allowed' error")
            print("\n  This suggests these settings are truly read-only through the API.")
            print("  They can only be changed through the Envi mobile app.")
        
        print(f"\n{'='*70}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python discover_endpoints.py <username> <password>")
        sys.exit(1)
    
    asyncio.run(discover_all_endpoints(sys.argv[1], sys.argv[2]))

