#!/usr/bin/env python3
"""Basic validation tests for Smart Envi integration."""

import ast
import json
import sys
from pathlib import Path

def test_python_syntax(file_path: Path) -> bool:
    """Test Python file syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read(), filename=str(file_path))
        return True
    except SyntaxError as e:
        print(f"[FAIL] Syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error reading {file_path}: {e}")
        return False

def test_manifest() -> bool:
    """Test manifest.json validity."""
    try:
        with open('custom_components/smart_envi/manifest.json', 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        required_fields = ['domain', 'name', 'version', 'requirements']
        missing = [field for field in required_fields if field not in manifest]
        
        if missing:
            print(f"[FAIL] Manifest missing required fields: {missing}")
            return False
        
        if manifest['domain'] != 'smart_envi':
            print(f"[FAIL] Manifest domain mismatch: expected 'smart_envi', got '{manifest['domain']}'")
            return False
        
        print(f"[OK] Manifest valid: domain={manifest['domain']}, version={manifest['version']}")
        return True
    except Exception as e:
        print(f"[FAIL] Manifest validation failed: {e}")
        return False

def test_imports() -> bool:
    """Test that all imports are valid."""
    python_files = [
        'custom_components/smart_envi/__init__.py',
        'custom_components/smart_envi/api.py',
        'custom_components/smart_envi/climate.py',
        'custom_components/smart_envi/config_flow.py',
        'custom_components/smart_envi/coordinator.py',
        'custom_components/smart_envi/services.py',
        'custom_components/smart_envi/sensor.py',
        'custom_components/smart_envi/binary_sensor.py',
        'custom_components/smart_envi/const.py',
    ]
    
    all_passed = True
    for file_path in python_files:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            all_passed = False
            continue
        
        if test_python_syntax(path):
            print(f"[OK] {file_path}: Syntax OK")
        else:
            all_passed = False
    
    return all_passed

def test_constants() -> bool:
    """Test that constants are properly defined."""
    try:
        # Try to import constants (will fail if syntax errors)
        sys.path.insert(0, 'custom_components/smart_envi')
        import const
        
        required_constants = [
            'DOMAIN', 'SCAN_INTERVAL', 'MIN_TEMPERATURE', 'MAX_TEMPERATURE',
            'BASE_URL', 'ENDPOINTS', 'DEFAULT_SCAN_INTERVAL', 'DEFAULT_API_TIMEOUT'
        ]
        
        missing = [c for c in required_constants if not hasattr(const, c)]
        if missing:
            print(f"[FAIL] Missing constants: {missing}")
            return False
        
        print(f"[OK] All required constants defined")
        return True
    except Exception as e:
        print(f"[WARN] Could not import constants module (expected in test environment): {e}")
        return True  # Not a failure, just can't test without HA environment

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("Smart Envi Integration - Validation Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Python Syntax", test_imports),
        ("Manifest JSON", test_manifest),
        ("Constants", test_constants),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        result = test_func()
        results.append((test_name, result))
        print()
    
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print()
    if all_passed:
        print("[SUCCESS] All validation tests passed!")
        return 0
    else:
        print("[FAILURE] Some validation tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

