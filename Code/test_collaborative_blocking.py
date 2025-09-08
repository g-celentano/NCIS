#!/usr/bin/env python3
"""
Test Script for Collaborative Blocking Decisions
Demonstrates the new shared policy functionality
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:5000"


def test_policy_management():
    """Test adding, retrieving, and removing policies."""
    print("=== Testing Policy Management ===")

    # Test adding a policy
    policy_data = {
        "policy_id": "test_malicious_ip",
        "policy": {
            "ipv4_src": "192.168.1.100",
            "description": "Test malicious IP",
            "severity": "high",
        },
    }

    try:
        response = requests.post(f"{API_BASE}/policy", json=policy_data)
        print(f"Add policy response: {response.status_code} - {response.json()}")
    except requests.RequestException as e:
        print(f"Error adding policy: {e}")
        return False

    # Test retrieving all policies
    try:
        response = requests.get(f"{API_BASE}/policies")
        print(f"Get policies response: {response.status_code}")
        if response.status_code == 200:
            policies = response.json()
            print(f"Current policies: {json.dumps(policies, indent=2)}")
    except requests.RequestException as e:
        print(f"Error getting policies: {e}")

    # Test removing the policy
    try:
        response = requests.delete(f"{API_BASE}/policy/test_malicious_ip")
        print(f"Remove policy response: {response.status_code} - {response.json()}")
    except requests.RequestException as e:
        print(f"Error removing policy: {e}")

    return True


def test_shared_blocklist():
    """Test shared blocklist functionality."""
    print("\n=== Testing Shared Blocklist ===")

    # Test adding to shared blocklist
    block_data = {
        "ipv4_src": "192.168.1.200",
        "duration": 300,  # 5 minutes
        "source": "test_script",
    }

    try:
        response = requests.post(f"{API_BASE}/shared-block", json=block_data)
        print(f"Add shared block response: {response.status_code} - {response.json()}")
    except requests.RequestException as e:
        print(f"Error adding shared block: {e}")
        return False

    # Test removing from shared blocklist
    try:
        response = requests.post(
            f"{API_BASE}/shared-unblock", json={"ipv4_src": "192.168.1.200"}
        )
        print(
            f"Remove shared block response: {response.status_code} - {response.json()}"
        )
    except requests.RequestException as e:
        print(f"Error removing shared block: {e}")

    return True


def test_complex_policy():
    """Test a complex policy with multiple criteria."""
    print("\n=== Testing Complex Policy ===")

    complex_policy = {
        "policy_id": "complex_attack_pattern",
        "policy": {
            "ipv4_src": "10.0.0.50",
            "ipv4_dst": "192.168.1.1",
            "tcp_dst": 80,
            "description": "Complex attack pattern: specific source targeting web server",
            "severity": "critical",
        },
    }

    try:
        response = requests.post(f"{API_BASE}/policy", json=complex_policy)
        print(
            f"Add complex policy response: {response.status_code} - {response.json()}"
        )

        # Wait a moment then remove it
        time.sleep(2)
        response = requests.delete(f"{API_BASE}/policy/complex_attack_pattern")
        print(
            f"Remove complex policy response: {response.status_code} - {response.json()}"
        )

    except requests.RequestException as e:
        print(f"Error with complex policy: {e}")

    return True


def test_emergency_scenario():
    """Simulate an emergency blocking scenario."""
    print("\n=== Testing Emergency Scenario ===")

    # Simulate multiple threat sources requiring immediate blocking
    emergency_blocks = [
        {"ipv4_src": "192.168.1.150", "duration": 600, "source": "emergency_admin"},
        {"eth_src": "aa:bb:cc:dd:ee:ff", "duration": 300, "source": "security_team"},
        {
            "ipv4_dst": "192.168.1.10",
            "udp_dst": 53,
            "duration": 1800,
            "source": "dns_protection",
        },
    ]

    for i, block in enumerate(emergency_blocks):
        try:
            response = requests.post(f"{API_BASE}/shared-block", json=block)
            print(
                f"Emergency block {i+1} response: {response.status_code} - {response.json()}"
            )
        except requests.RequestException as e:
            print(f"Error with emergency block {i+1}: {e}")

    # Check current state
    try:
        response = requests.get(f"{API_BASE}/policies")
        if response.status_code == 200:
            policies = response.json()
            shared_count = len(policies.get("shared_blocklist", {}))
            print(f"Total shared blocks active: {shared_count}")
    except requests.RequestException as e:
        print(f"Error checking emergency state: {e}")

    return True


def main():
    """Run all tests."""
    print("Collaborative Blocking Decisions - Test Script")
    print("=" * 50)

    # Check if API is available
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code != 200:
            print(f"API not available at {API_BASE}")
            sys.exit(1)
        print(f"API available: {response.text}")
    except requests.RequestException:
        print(f"Cannot connect to API at {API_BASE}")
        print("Make sure the NCIS controller is running with API enabled")
        sys.exit(1)

    # Run tests
    tests = [
        test_policy_management,
        test_shared_blocklist,
        test_complex_policy,
        test_emergency_scenario,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Brief pause between tests
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{len(tests)} tests")

    if passed == len(tests):
        print("All tests passed! Collaborative blocking is working correctly.")
    else:
        print("Some tests failed. Check the controller logs for details.")


if __name__ == "__main__":
    main()
