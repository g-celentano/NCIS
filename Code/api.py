from flask import Flask, request, jsonify
import threading
import logging


def start_api_server(mitigator, host="0.0.0.0", port=5000):
    app = Flask(__name__)
    logger = logging.getLogger("API")

    @app.route("/block", methods=["POST"])
    def block_flow():
        data = request.json
        flow_id = tuple(
            data.get(k)
            for k in [
                "eth_src",
                "eth_dst",
                "ipv4_src",
                "ipv4_dst",
                "udp_src",
                "udp_dst",
            ]
        )
        # Qui puoi aggiungere validazione dei parametri
        # Si assume che il controller abbia accesso a un datapath (es. il primo disponibile)
        datapath = next(iter(mitigator.controller.dps.values()), None)
        if not datapath:
            return jsonify({"error": "No datapath available"}), 400
        mitigator.apply_block(datapath, flow_id)
        logger.info(f"Blocco richiesto via API: {flow_id}")
        return jsonify({"status": "blocked", "flow_id": flow_id})

    @app.route("/unblock", methods=["POST"])
    def unblock_flow():
        data = request.json
        flow_id = tuple(
            data.get(k)
            for k in [
                "eth_src",
                "eth_dst",
                "ipv4_src",
                "ipv4_dst",
                "udp_src",
                "udp_dst",
            ]
        )
        with mitigator.lock:
            if flow_id in mitigator.blocked_flows:
                del mitigator.blocked_flows[flow_id]
                logger.info(f"Sblocco richiesto via API: {flow_id}")
                return jsonify({"status": "unblocked", "flow_id": flow_id})
            else:
                return jsonify({"error": "Flow not blocked"}), 404

    @app.route("/blocked", methods=["GET"])
    def get_blocked():
        with mitigator.lock:
            blocked = {str(k): v for k, v in mitigator.blocked_flows.items()}
        return jsonify(blocked)

    @app.route("/policy", methods=["POST"])
    def add_policy():
        """Add an external blocking policy."""
        data = request.json
        policy_id = data.get("policy_id")
        policy = data.get("policy", {})

        if not policy_id:
            return jsonify({"error": "policy_id is required"}), 400

        mitigator.add_external_policy(policy_id, policy)
        logger.info(f"Policy aggiunta via API: {policy_id}")
        return jsonify(
            {"status": "policy_added", "policy_id": policy_id, "policy": policy}
        )

    @app.route("/policy/<policy_id>", methods=["DELETE"])
    def remove_policy(policy_id):
        """Remove an external blocking policy."""
        if mitigator.remove_external_policy(policy_id):
            logger.info(f"Policy rimossa via API: {policy_id}")
            return jsonify({"status": "policy_removed", "policy_id": policy_id})
        else:
            return jsonify({"error": "Policy not found"}), 404

    @app.route("/policies", methods=["GET"])
    def get_policies():
        """Get all active policies."""
        policies = mitigator.get_all_policies()
        return jsonify(policies)

    @app.route("/shared-block", methods=["POST"])
    def add_shared_block():
        """Add a flow to the shared blocklist."""
        data = request.json
        flow_id = tuple(
            data.get(k)
            for k in [
                "eth_src",
                "eth_dst",
                "ipv4_src",
                "ipv4_dst",
                "udp_src",
                "udp_dst",
            ]
        )
        duration = data.get("duration", 3600)  # Default 1 hour
        source = data.get("source", "api")

        mitigator.add_to_shared_blocklist(flow_id, duration, source)
        logger.info(f"Blocco condiviso aggiunto via API: {flow_id}")
        return jsonify(
            {
                "status": "added_to_shared_blocklist",
                "flow_id": flow_id,
                "duration": duration,
            }
        )

    @app.route("/shared-unblock", methods=["POST"])
    def remove_shared_block():
        """Remove a flow from the shared blocklist."""
        data = request.json
        flow_id = tuple(
            data.get(k)
            for k in [
                "eth_src",
                "eth_dst",
                "ipv4_src",
                "ipv4_dst",
                "udp_src",
                "udp_dst",
            ]
        )

        if mitigator.remove_from_shared_blocklist(flow_id):
            logger.info(f"Blocco condiviso rimosso via API: {flow_id}")
            return jsonify(
                {"status": "removed_from_shared_blocklist", "flow_id": flow_id}
            )
        else:
            return jsonify({"error": "Flow not in shared blocklist"}), 404

    @app.route("/", methods=["GET"])
    def index():
        return "SDN Modular Controller REST API", 200

    # Avvia Flask in un thread separato
    threading.Thread(
        target=app.run, kwargs={"host": host, "port": port}, daemon=True
    ).start()
