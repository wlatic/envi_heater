#!/usr/bin/env python3
"""
Quick test script to find the correct endpoint for settings updates.
"""

import asyncio
import json
import sys
from datetime import datetime
import uuid

import aiohttp


async def test_settings_updates(username: str, password: str):
    """Test different endpoints for settings updates."""
    base_url = "https://app-apis.enviliving.com/apis/v1"
    
    async with aiohttp.ClientSession() as session:
        # Authenticate
        print("Authenticating...")
        device_id = f"test_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        auth_payload = {
            "username": username,
            "password": password,
            "login_type": 1,
            "device_id": device_id,
            "device_type": "test",
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
            # The API returns: {"status": "success", "data": [{"id": ...}, ...]}
            if "data" in device_list and isinstance(device_list["data"], list):
                device_ids = [str(d["id"]) for d in device_list["data"] if "id" in d]
            else:
                print(f"Unexpected response structure: {json.dumps(device_list, indent=2)}")
                return
            
            if not device_ids:
                print("No devices found")
                return
        
        device_id = str(device_ids[0])
        print(f"\nUsing device ID: {device_id}")
        
        # Get current state
        async with session.get(f"{base_url}/device/{device_id}", headers=headers) as resp:
            device_data = await resp.json()
            current = device_data["data"]
            current_temp = current.get("current_temperature") or current.get("temperature")
            current_state = current.get("state", 1)
            current_freeze = current.get("freeze_protect_setting")
            
            print(f"\nCurrent state:")
            print(f"  Temperature: {current_temp}")
            print(f"  State: {current_state}")
            print(f"  Freeze Protect: {current_freeze} (type: {type(current_freeze).__name__})")
        
        # Test different endpoints for settings
        print(f"\n{'='*70}")
        print("Testing different endpoints for settings updates:")
        print(f"{'='*70}")
        
        # Determine target value (toggle it)
        if isinstance(current_freeze, bool):
            target_value = not current_freeze
        else:
            target_value = False
        
        # Try different endpoint patterns
        endpoint_patterns = [
            ("PATCH", f"device/{device_id}", {"freeze_protect_setting": target_value}),
            ("PUT", f"device/{device_id}", {"freeze_protect_setting": target_value}),
            ("PATCH", f"device/{device_id}/settings", {"freeze_protect_setting": target_value}),
            ("PUT", f"device/{device_id}/settings", {"freeze_protect_setting": target_value}),
            ("PATCH", f"device/settings/{device_id}", {"freeze_protect_setting": target_value}),
            ("PUT", f"device/settings/{device_id}", {"freeze_protect_setting": target_value}),
            ("PATCH", f"device/{device_id}/update", {"freeze_protect_setting": target_value}),
            ("PUT", f"device/{device_id}/update", {"freeze_protect_setting": target_value}),
            ("POST", f"device/{device_id}/settings", {"freeze_protect_setting": target_value}),
        ]
        
        for method, endpoint, payload in endpoint_patterns:
            print(f"\n   Testing {method} {endpoint}")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            async with session.request(
                method,
                f"{base_url}/{endpoint}",
                headers=headers,
                json=payload
            ) as resp:
                status = resp.status
                try:
                    result = await resp.json()
                except:
                    result = {"text": await resp.text()}
                
                print(f"   Status: {status}")
                if status == 200:
                    print(f"   [SUCCESS] This endpoint works!")
                    print(f"   Response: {json.dumps(result, indent=2)}")
                    # Restore original
                    restore = {"freeze_protect_setting": current_freeze}
                    async with session.request(
                        method,
                        f"{base_url}/{endpoint}",
                        headers=headers,
                        json=restore
                    ) as restore_resp:
                        print(f"   Restored original value")
                    break
                elif status == 400:
                    print(f"   [FAIL] Bad Request")
                    if "msg" in result:
                        print(f"   Error: {result['msg']}")
                    else:
                        print(f"   Response: {json.dumps(result, indent=2)[:200]}")
                elif status == 404:
                    print(f"   [SKIP] Endpoint not found")
                elif status == 405:
                    print(f"   [SKIP] Method not allowed")
                else:
                    print(f"   [FAIL] Status {status}")
                    if isinstance(result, dict):
                        print(f"   Response: {json.dumps(result, indent=2)[:200]}")
        
        print(f"\n{'='*70}")
        print("Conclusion:")
        print(f"{'='*70}")
        print("If all endpoints returned 400/404/405, these settings may be:")
        print("  1. Read-only through the API")
        print("  2. Require a different authentication method")
        print("  3. Only changeable through the mobile app")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_settings_endpoint.py <username> <password>")
        sys.exit(1)
    
    asyncio.run(test_settings_updates(sys.argv[1], sys.argv[2]))
