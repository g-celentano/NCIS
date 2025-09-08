"""
External Security Module - Example
Demonstrates how external modules can contribute to blocking policies
"""

import time
import logging
import threading


class ExternalSecurityModule:
    """Example external module that can contribute blocking policies."""

    def __init__(self, mitigator):
        self.mitigator = mitigator
        self.logger = logging.getLogger("ExternalSecurityModule")
        self.running = True

        # Threat intelligence data (example)
        self.known_malicious_ips = [
            "192.168.1.100",  # Example malicious IP
            "10.0.0.50",  # Another example
        ]

        self.suspicious_mac_patterns = [
            "00:0c:29:",  # VMware MAC prefix - might be suspicious in some contexts
        ]

    def start(self):
        """Start the external security module."""
        self.logger.info("Starting External Security Module")

        # Add policies based on threat intelligence
        self._add_threat_intelligence_policies()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_threats, daemon=True
        )
        self.monitor_thread.start()

    def _add_threat_intelligence_policies(self):
        """Add policies based on known threats."""

        # Block known malicious IPs
        for ip in self.known_malicious_ips:
            policy = {
                "ipv4_src": ip,
                "description": f"Known malicious IP: {ip}",
                "severity": "high",
            }
            self.mitigator.add_external_policy(f"malicious_ip_{ip}", policy)

        # Block suspicious MAC patterns
        for i, mac_pattern in enumerate(self.suspicious_mac_patterns):
            policy = {
                "eth_src_pattern": mac_pattern,  # This would need pattern matching implementation
                "description": f"Suspicious MAC pattern: {mac_pattern}",
                "severity": "medium",
            }
            # For simplicity, we'll add a specific MAC that starts with this pattern
            specific_mac = mac_pattern + "00:00:01"
            policy_simple = {
                "eth_src": specific_mac,
                "description": f"Suspicious MAC: {specific_mac}",
                "severity": "medium",
            }
            self.mitigator.add_external_policy(f"suspicious_mac_{i}", policy_simple)

    def _monitor_threats(self):
        """Monitor for new threats and update policies."""
        while self.running:
            try:
                # Simulate checking for new threat intelligence
                self._check_for_new_threats()

                # Check for policy updates every 30 seconds
                time.sleep(30)

            except Exception as e:
                self.logger.error(f"Error in threat monitoring: {e}")
                time.sleep(5)

    def _check_for_new_threats(self):
        """Simulate checking external threat feeds."""
        # In a real implementation, this would:
        # - Check threat intelligence feeds
        # - Analyze recent attack patterns
        # - Update policies based on new information

        # Example: simulate finding a new malicious IP
        import random

        if random.random() < 0.1:  # 10% chance to "discover" new threat
            new_malicious_ip = f"192.168.1.{random.randint(200, 254)}"
            if new_malicious_ip not in self.known_malicious_ips:
                self.known_malicious_ips.append(new_malicious_ip)

                # Add policy for new threat
                policy = {
                    "ipv4_src": new_malicious_ip,
                    "description": f"Newly discovered malicious IP: {new_malicious_ip}",
                    "severity": "high",
                }
                self.mitigator.add_external_policy(
                    f"new_threat_{new_malicious_ip}", policy
                )
                self.logger.warning(f"Added policy for new threat: {new_malicious_ip}")

    def block_emergency_target(self, target_ip, duration=300):
        """Emergency blocking function for administrators."""
        flow_id = (None, None, target_ip, None, None, None)
        self.mitigator.add_to_shared_blocklist(
            flow_id, duration=duration, source="emergency_admin"
        )
        self.logger.critical(
            f"Emergency block applied to {target_ip} for {duration} seconds"
        )

    def add_admin_policy(self, policy_id, policy_config):
        """Allow administrators to add custom policies."""
        self.mitigator.add_external_policy(f"admin_{policy_id}", policy_config)
        self.logger.info(f"Administrator added policy: {policy_id}")

    def stop(self):
        """Stop the external security module."""
        self.running = False
        self.logger.info("External Security Module stopped")


# Example usage function
def integrate_external_module(controller):
    """Example of how to integrate the external module with the controller."""
    external_module = ExternalSecurityModule(controller.mitigator)
    external_module.start()

    # Example: simulate admin emergency action
    def simulate_admin_action():
        time.sleep(60)  # Wait 1 minute
        external_module.block_emergency_target("192.168.1.199", duration=600)

    admin_thread = threading.Thread(target=simulate_admin_action, daemon=True)
    admin_thread.start()

    return external_module
