#!/usr/bin/env python3
"""
Test script to check which device controls/settings can be updated through the API.
"""

import asyncio
import json
import sys
from datetime import datetime
import uuid

import aiohttp


async def test_all_controls(username: str, password: str):
    """Test all device controls to see which can be updated."""
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
            
            print(f"\n{'='*70}")
            print("CURRENT DEVICE STATE:")
            print(f"{'='*70}")
            print(f"  Temperature: {current.get('current_temperature') or current.get('temperature')}")
            print(f"  State: {current.get('state')}")
            print(f"  Mode: {current.get('current_mode')}")
            print(f"  Freeze Protect: {current.get('freeze_protect_setting')}")
            print(f"  Child Lock: {current.get('child_lock_setting')}")
            print(f"  Notifications: {current.get('notification_setting')}")
            print(f"  Hold: {current.get('is_hold')}")
            print(f"  Permanent Hold: {current.get('permanent_hold')}")
            print(f"  Night Light: {current.get('night_light_setting')}")
            print(f"  Pilot Light: {current.get('pilot_light_setting')}")
            print(f"  Display Setting: {current.get('display_setting')}")
            
            # Store original values
            current_temp = current.get("current_temperature") or current.get("temperature")
            current_state = current.get("state", 1)
            current_freeze = current.get("freeze_protect_setting")
            current_child_lock = current.get("child_lock_setting")
            current_notification = current.get("notification_setting")
            current_hold = current.get("is_hold", False)
            current_permanent_hold = current.get("permanent_hold", False)
        
        # Test all controls on the update-temperature endpoint
        print(f"\n{'='*70}")
        print("TESTING CONTROLS ON: PATCH /device/update-temperature/{device_id}")
        print(f"{'='*70}")
        
        controls_to_test = [
            ("freeze_protect_setting", not current_freeze if isinstance(current_freeze, bool) else False, current_freeze),
            ("child_lock_setting", not current_child_lock if isinstance(current_child_lock, bool) else False, current_child_lock),
            ("notification_setting", not current_notification if isinstance(current_notification, bool) else False, current_notification),
            ("is_hold", not current_hold if isinstance(current_hold, bool) else False, current_hold),
            ("permanent_hold", not current_permanent_hold if isinstance(current_permanent_hold, bool) else False, current_permanent_hold),
        ]
        
        working_controls = []
        failed_controls = []
        
        for control_name, test_value, original_value in controls_to_test:
            print(f"\n--- Testing {control_name} ---")
            
            # Test with temperature + state + control
            payload = {
                "temperature": current_temp,
                "state": current_state,
                control_name: test_value
            }
            
            print(f"  Payload: {json.dumps(payload, indent=4)}")
            
            async with session.patch(
                f"{base_url}/device/update-temperature/{device_id}",
                headers=headers,
                json=payload
            ) as resp:
                status = resp.status
                try:
                    result = await resp.json()
                except:
                    result = {"text": await resp.text()}
                
                print(f"  Status: {status}")
                
                if status == 200:
                    print(f"  [SUCCESS] {control_name} CAN be updated!")
                    working_controls.append(control_name)
                    
                    # Restore original value
                    restore_payload = {
                        "temperature": current_temp,
                        "state": current_state,
                        control_name: original_value
                    }
                    async with session.patch(
                        f"{base_url}/device/update-temperature/{device_id}",
                        headers=headers,
                        json=restore_payload
                    ) as restore_resp:
                        if restore_resp.status == 200:
                            print(f"  [RESTORED] Original value restored")
                        else:
                            print(f"  [WARNING] Could not restore original value (status: {restore_resp.status})")
                elif status == 400:
                    error_msg = result.get("msg", "Bad Request")
                    print(f"  [FAIL] Bad Request: {error_msg}")
                    failed_controls.append((control_name, error_msg))
                else:
                    print(f"  [FAIL] Status {status}")
                    if isinstance(result, dict):
                        print(f"  Response: {json.dumps(result, indent=4)[:300]}")
                    failed_controls.append((control_name, f"Status {status}"))
        
        # Test other endpoints for failed controls
        if failed_controls:
            print(f"\n{'='*70}")
            print("TESTING ALTERNATIVE ENDPOINTS FOR FAILED CONTROLS:")
            print(f"{'='*70}")
            
            endpoint_patterns = [
                ("PATCH", f"device/{device_id}"),
                ("PUT", f"device/{device_id}"),
                ("PATCH", f"device/{device_id}/settings"),
                ("PUT", f"device/{device_id}/settings"),
                ("POST", f"device/{device_id}/settings"),
            ]
            
            for control_name, error_msg in failed_controls:
                print(f"\n--- Testing {control_name} on alternative endpoints ---")
                test_value = not current_freeze if control_name == "freeze_protect_setting" else False
                
                for method, endpoint in endpoint_patterns:
                    payload = {control_name: test_value}
                    print(f"  {method} {endpoint}")
                    
                    async with session.request(
                        method,
                        f"{base_url}/{endpoint}",
                        headers=headers,
                        json=payload
                    ) as resp:
                        status = resp.status
                        if status == 200:
                            print(f"    [SUCCESS] {method} {endpoint} works for {control_name}!")
                            working_controls.append(f"{control_name} ({method} {endpoint})")
                            break
                        elif status not in (404, 405):
                            try:
                                result = await resp.json()
                                error = result.get("msg", f"Status {status}")
                                print(f"    [FAIL] {error}")
                            except:
                                print(f"    [FAIL] Status {status}")
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY:")
        print(f"{'='*70}")
        if working_controls:
            print("\n[WORKING CONTROLS] - Can be updated through API:")
            for control in working_controls:
                print(f"  ✓ {control}")
        else:
            print("\n[NO WORKING CONTROLS] - None of the tested controls can be updated")
        
        if failed_controls:
            print("\n[FAILED CONTROLS] - Cannot be updated through API:")
            for control_name, error_msg in failed_controls:
                print(f"  ✗ {control_name}: {error_msg}")
        
        print(f"\n{'='*70}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_all_controls.py <username> <password>")
        sys.exit(1)
    
    asyncio.run(test_all_controls(sys.argv[1], sys.argv[2]))


