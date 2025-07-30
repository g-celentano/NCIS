import time
import threading
from ryu.lib import hub

class Monitor:
    def __init__(self, controller, interval=2):
        self.controller = controller
        self.interval = interval
        self.running = True
        self.stats = {
            'ports': {},
            'macs': {},
            'protocols': {}
        }
        self.lock = threading.Lock()

    def run(self):
        while self.running:
            self.collect_stats()
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def collect_stats(self):
        # Richiesta periodica delle statistiche agli switch
        for dp in getattr(self.controller, 'dps', {}).values():
            parser = dp.ofproto_parser
            req = parser.OFPPortStatsRequest(dp, 0, dp.ofproto.OFPP_ANY)
            dp.send_msg(req)
            req = parser.OFPFlowStatsRequest(dp)
            dp.send_msg(req)

    def update_port_stats(self, dpid, stats):
        with self.lock:
            self.stats['ports'][dpid] = stats

    def update_flow_stats(self, dpid, stats):
        with self.lock:
            # Aggiorna throughput per MAC, IP, protocollo
            for stat in stats:
                match = getattr(stat, 'match', {})
                byte_count = getattr(stat, 'byte_count', 0)
                duration_sec = getattr(stat, 'duration_sec', 1)
                if duration_sec == 0:
                    duration_sec = 1
                throughput = byte_count / duration_sec

                eth_src = match.get('eth_src')
                eth_dst = match.get('eth_dst')
                ipv4_src = match.get('ipv4_src')
                ipv4_dst = match.get('ipv4_dst')
                ip_proto = match.get('ip_proto')
                udp_src = match.get('udp_src')
                udp_dst = match.get('udp_dst')
                tcp_src = match.get('tcp_src')
                tcp_dst = match.get('tcp_dst')

                # Per MAC
                if eth_src:
                    self.stats['macs'].setdefault(eth_src, {'throughput': 0})
                    self.stats['macs'][eth_src]['throughput'] += throughput
                if eth_dst:
                    self.stats['macs'].setdefault(eth_dst, {'throughput': 0})
                    self.stats['macs'][eth_dst]['throughput'] += throughput

                # Per IP
                if ipv4_src:
                    self.stats['macs'].setdefault(ipv4_src, {'throughput': 0})
                    self.stats['macs'][ipv4_src]['throughput'] += throughput
                if ipv4_dst:
                    self.stats['macs'].setdefault(ipv4_dst, {'throughput': 0})
                    self.stats['macs'][ipv4_dst]['throughput'] += throughput

                # Per protocollo
                proto_key = None
                if ip_proto == 6:
                    proto_key = f"TCP:{tcp_src}->{tcp_dst}"
                elif ip_proto == 17:
                    proto_key = f"UDP:{udp_src}->{udp_dst}"
                elif ip_proto:
                    proto_key = f"IP:{ip_proto}"
                if proto_key:
                    self.stats['protocols'].setdefault(proto_key, {'throughput': 0})
                    self.stats['protocols'][proto_key]['throughput'] += throughput

                # Salva anche throughput totale per dpid
                self.stats['ports'].setdefault(dpid, {'throughput': 0})
                self.stats['ports'][dpid]['throughput'] += throughput

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
            'eth': {
                'src': eth.src if eth else None,
                'dst': eth.dst if eth else None,
                'ethertype': eth.ethertype if eth else None
            },
            'ip': {
                'src': ip.src if ip else None,
                'dst': ip.dst if ip else None,
                'proto': ip.proto if ip else None
            } if ip else None,
            'udp': {
                'src_port': udp_pkt.src_port if udp_pkt else None,
                'dst_port': udp_pkt.dst_port if udp_pkt else None
            } if udp_pkt else None,
            'tcp': {
                'src_port': tcp_pkt.src_port if tcp_pkt else None,
                'dst_port': tcp_pkt.dst_port if tcp_pkt else None
            } if tcp_pkt else None
        }