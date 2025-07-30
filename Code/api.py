from flask import Flask, request, jsonify
import threading
import logging

def start_api_server(mitigator, host='0.0.0.0', port=5000):
    app = Flask(__name__)
    logger = logging.getLogger("API")

    @app.route('/block', methods=['POST'])
    def block_flow():
        data = request.json
        flow_id = tuple(data.get(k) for k in ['eth_src', 'eth_dst', 'ipv4_src', 'ipv4_dst', 'udp_src', 'udp_dst'])
        # Qui puoi aggiungere validazione dei parametri
        # Si assume che il controller abbia accesso a un datapath (es. il primo disponibile)
        datapath = next(iter(mitigator.controller.dps.values()), None)
        if not datapath:
            return jsonify({'error': 'No datapath available'}), 400
        mitigator.apply_block(datapath, flow_id)
        logger.info(f"Blocco richiesto via API: {flow_id}")
        return jsonify({'status': 'blocked', 'flow_id': flow_id})

    @app.route('/unblock', methods=['POST'])
    def unblock_flow():
        data = request.json
        flow_id = tuple(data.get(k) for k in ['eth_src', 'eth_dst', 'ipv4_src', 'ipv4_dst', 'udp_src', 'udp_dst'])
        with mitigator.lock:
            if flow_id in mitigator.blocked_flows:
                del mitigator.blocked_flows[flow_id]
                logger.info(f"Sblocco richiesto via API: {flow_id}")
                return jsonify({'status': 'unblocked', 'flow_id': flow_id})
            else:
                return jsonify({'error': 'Flow not blocked'}), 404

    @app.route('/blocked', methods=['GET'])
    def get_blocked():
        with mitigator.lock:
            blocked = {str(k): v for k, v in mitigator.blocked_flows.items()}
        return jsonify(blocked)

    # Avvia Flask in un thread separato
    threading.Thread(target=app.run, kwargs={'host': host, 'port': port}, daemon=True).start()