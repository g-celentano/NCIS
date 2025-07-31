import threading
import logging
import time


class Mitigator:
    def handle_anomaly(self, anomaly):
        # Riceve una segnalazione di anomalia dal detector e applica il blocco
        # Si assume che anomaly['key'] sia compatibile con _flow_id
        # Puoi personalizzare la logica di mapping qui
        flow_id = anomaly.get("key")
        # Trova un datapath disponibile
        datapath = next(iter(self.controller.dps.values()), None)
        if datapath and flow_id:
            self.apply_block(datapath, flow_id)
            self.logger.info(f"Blocco automatico per anomalia: {flow_id}")

    def run(self, interval=5):
        # Thread per lo sblocco progressivo
        while getattr(self, "running", True):
            self.unblock_flows()
            time.sleep(interval)

    def stop(self):
        self.running = False

    def __init__(self, controller):
        self.controller = controller
        self.lock = threading.Lock()
        self.blocked_flows = {}
        self.logger = logging.getLogger("Mitigator")

    def _flow_id(self, pkt):
        # Identificatore granulare: MAC/IP/UDP port
        eth = pkt.get("eth", {})
        ip = pkt.get("ip", {}) if pkt.get("ip") else {}
        udp = pkt.get("udp", {}) if pkt.get("udp") else {}
        tcp = pkt.get("tcp", {}) if pkt.get("tcp") else {}
        return (
            eth.get("src"),
            eth.get("dst"),
            ip.get("src"),
            ip.get("dst"),
            udp.get("src_port"),
            udp.get("dst_port"),
        )

    def should_block(self, pkt, datapath, in_port):
        flow_id = self._flow_id(pkt)
        now = time.time()
        with self.lock:
            block_info = self.blocked_flows.get(flow_id)
            if block_info and block_info["until"] > now:
                return flow_id
        # Qui puoi aggiungere logica per decidere se bloccare in base a segnali dal Detector
        return None

    def apply_block(self, datapath, flow_id):
        with self.lock:
            info = self.blocked_flows.get(flow_id, {"count": 0})
            info["count"] += 1

            # Limita il block_time a un massimo di 1 ora (3600 secondi)
            # invece di raddoppiare indefinitamente
            count = min(info["count"], 8)  # Limita a 2^7 = 128 moltiplicatore
            block_time = 30 * (2 ** (count - 1))
            block_time = min(block_time, 3600)  # Max 1 ora

            info["until"] = time.time() + block_time
            self.blocked_flows[flow_id] = info
            self.logger.info(
                f"Blocca flow {flow_id} per {block_time} secondi (count={info['count']})"
            )

        # Costruisci OFPMatch solo con valori non-None
        parser = datapath.ofproto_parser
        match_kwargs = {}

        if flow_id[0]:  # eth_src
            match_kwargs["eth_src"] = flow_id[0]
        if flow_id[1]:  # eth_dst
            match_kwargs["eth_dst"] = flow_id[1]
        if flow_id[2]:  # ipv4_src
            match_kwargs["eth_type"] = 0x0800  # IPv4
            match_kwargs["ipv4_src"] = flow_id[2]
        if flow_id[3]:  # ipv4_dst
            match_kwargs["eth_type"] = 0x0800  # IPv4
            match_kwargs["ipv4_dst"] = flow_id[3]
        if flow_id[4]:  # udp_src
            match_kwargs["ip_proto"] = 17  # UDP
            match_kwargs["udp_src"] = flow_id[4]
        if flow_id[5]:  # udp_dst
            match_kwargs["ip_proto"] = 17  # UDP
            match_kwargs["udp_dst"] = flow_id[5]

        match = parser.OFPMatch(**match_kwargs)
        actions = []  # Nessuna azione = drop
        self.add_flow(datapath, 10, match, actions)

    def forward_packet(self, msg, datapath, in_port, actions, src, dst):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None,
        )
        datapath.send_msg(out)

    def add_flow(self, datapath, priority, match, actions):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def unblock_flows(self):
        # Da chiamare periodicamente per sbloccare i flussi scaduti
        now = time.time()
        with self.lock:
            expired = [
                fid for fid, info in self.blocked_flows.items() if info["until"] <= now
            ]
            for fid in expired:
                del self.blocked_flows[fid]
                self.logger.info(f"Sblocco flow {fid}")
