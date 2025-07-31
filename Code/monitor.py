import time
import threading
from ryu.lib import hub
import logging  # <-- AGGIUNGI


class Monitor:
    def __init__(self, controller, interval=2):
        self.controller = controller
        self.interval = interval
        self.running = True
        self.stats = {
            "ports": {},
            "macs": {},
            "protocols": {},
        }
        self.lock = threading.Lock()
        self.logger = logging.getLogger("Monitor")  # <-- AGGIUNGI QUESTA RIGA

    def run(self):
        while self.running:
            self.collect_stats()
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def collect_stats(self):
        # Richiesta periodica delle statistiche agli switch
        for dp in getattr(self.controller, "dps", {}).values():
            parser = dp.ofproto_parser
            req = parser.OFPPortStatsRequest(dp, 0, dp.ofproto.OFPP_ANY)
            dp.send_msg(req)
            req = parser.OFPFlowStatsRequest(dp)
            dp.send_msg(req)

    def update_port_stats(self, dpid, stats):
        with self.lock:
            self.stats["ports"][dpid] = stats

    def update_flow_stats(self, dpid, stats):
        with self.lock:
            self.logger.info(f"Updating flow stats for dpid {dpid}: {len(stats)} flows")
            # Inizializza strutture se non esistono
            if dpid not in self.stats["macs"]:
                self.stats["macs"][dpid] = {}
            if dpid not in self.stats["protocols"]:
                self.stats["protocols"][dpid] = {}

            # Aggiorna throughput per MAC, IP, protocollo
            for stat in stats:
                match = getattr(stat, "match", {})
                byte_count = getattr(stat, "byte_count", 0)
                duration_sec = getattr(stat, "duration_sec", 1)
                if duration_sec == 0:
                    duration_sec = 1
                throughput = byte_count / duration_sec

                eth_src = match.get("eth_src")
                eth_dst = match.get("eth_dst")
                ipv4_src = match.get("ipv4_src")
                ipv4_dst = match.get("ipv4_dst")
                ip_proto = match.get("ip_proto")

                # Aggiorna statistiche per MAC
                if eth_src:
                    key = f"{eth_src}_{eth_dst}"
                    self.stats["macs"][dpid][key] = {"throughput": throughput}

                # Aggiorna statistiche per protocollo
                if ip_proto:
                    if ip_proto == 6:  # TCP
                        key = f"tcp_{ipv4_src}_{ipv4_dst}"
                    elif ip_proto == 17:  # UDP
                        key = f"udp_{ipv4_src}_{ipv4_dst}"
                    else:
                        key = f"ip_proto_{ip_proto}"
                    self.stats["protocols"][dpid][key] = {"throughput": throughput}

    def get_stats(self):
        with self.lock:
            return self.stats.copy()

    def parse_packet(self, data):
        # Funzione di utilità per estrarre info da un pacchetto
        from ryu.lib.packet import packet, ethernet, ipv4, udp, tcp

        pkt = packet.Packet(data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)
        tcp_pkt = pkt.get_protocol(tcp.tcp)
        return {
            "eth": {
                "src": eth.src if eth else None,
                "dst": eth.dst if eth else None,
                "ethertype": eth.ethertype if eth else None,
            },
            "ip": (
                {
                    "src": ip.src if ip else None,
                    "dst": ip.dst if ip else None,
                    "proto": ip.proto if ip else None,
                }
                if ip
                else None
            ),
            "udp": (
                {
                    "src_port": udp_pkt.src_port if udp_pkt else None,
                    "dst_port": udp_pkt.dst_port if udp_pkt else None,
                }
                if udp_pkt
                else None
            ),
            "tcp": (
                {
                    "src_port": tcp_pkt.src_port if tcp_pkt else None,
                    "dst_port": tcp_pkt.dst_port if tcp_pkt else None,
                }
                if tcp_pkt
                else None
            ),
        }
