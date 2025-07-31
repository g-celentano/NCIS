# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import threading
import logging
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3

from monitor import Monitor
from detector import Detector
from mitigator import Mitigator

try:
    from api import start_api_server
except ImportError:
    start_api_server = None


class ModularController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ModularController, self).__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.mac_to_port = {}
        self.dps = {}  # <-- AGGIUNGI per tenere traccia degli switch
        self.monitor = Monitor(self)
        self.detector = Detector(self, interval=5)  # <-- AGGIUNGI interval
        self.mitigator = Mitigator(self)
        self.running = True

        # Start threads
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()

        self.detector_thread = threading.Thread(
            target=self.detector.run, daemon=True
        )  # <-- AGGIUNGI
        self.detector_thread.start()

        self.mitigator_thread = threading.Thread(
            target=self.mitigator.run, daemon=True
        )  # <-- AGGIUNGI
        self.mitigator_thread.start()

        # Start API
        if start_api_server:
            self.api_thread = threading.Thread(
                target=start_api_server, args=(self.mitigator,), daemon=True
            )
            self.api_thread.start()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.dps[datapath.id] = datapath  # <-- AGGIUNGI per tracciare gli switch
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.mitigator.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match["in_port"]
        pkt = self.monitor.parse_packet(msg.data)
        eth = pkt.get("eth", None)
        if not eth or eth["ethertype"] == 0x88CC:
            return

        src = eth["src"]
        dst = eth["dst"]
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        # AGGIUNGI: Detection semplice basata su frequenza
        self._check_dos_patterns(pkt, datapath, in_port)

        # Check for mitigation actions
        block_action = self.mitigator.should_block(pkt, datapath, in_port)
        if block_action:
            self.logger.info(f"Blocking flow: {block_action}")
            self.mitigator.apply_block(datapath, block_action)
            return

        # Normal forwarding
        out_port = self.mac_to_port[dpid].get(dst, datapath.ofproto.OFPP_FLOOD)
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
        self.mitigator.forward_packet(msg, datapath, in_port, actions, src, dst)

    def _check_dos_patterns(self, pkt, datapath, in_port):
        eth = pkt.get("eth", {})
        ip = pkt.get("ip", {})
        udp = pkt.get("udp", {})
        tcp = pkt.get("tcp", {})
        src = eth.get("src")
        dst = eth.get("dst")

        if not src or not dst:
            return

        # IGNORA traffico di sistema
        if (
            dst.startswith("33:33:")
            or dst == "ff:ff:ff:ff:ff:ff"
            or dst.startswith("01:00:5e:")
        ):
            return
        if udp and (udp.get("dst_port") == 5353 or udp.get("src_port") == 68):
            return
        if eth.get("ethertype") == 0x88CC:
            return

        import time

        now = time.time()

        if not hasattr(self, "_traffic_profiles"):
            self._traffic_profiles = {}
            self._last_cleanup = now

        # Pulizia periodica (ogni 60 secondi)
        if now - self._last_cleanup > 60:
            old_hosts = [
                h
                for h, data in self._traffic_profiles.items()
                if now - data["last_update"] > 30
            ]
            for h in old_hosts:
                del self._traffic_profiles[h]
            self._last_cleanup = now

        # Inizializza/aggiorna profilo del traffico
        if src not in self._traffic_profiles:
            self._traffic_profiles[src] = {
                "first_seen": now,
                "last_update": now,
                "packet_history": [],
                "tcp_syn_count": 0,
                "ping_count": 0,
                "udp_count": 0,
                "rate_history": [],
                "targets": set(),
                "block_count": 0,
                "is_likely_legitimate": False,
            }

        profile = self._traffic_profiles[src]
        profile["last_update"] = now
        profile["packet_history"].append(now)
        profile["targets"].add(dst)

        # Limita la storia a ultimi 20 secondi
        profile["packet_history"] = [
            t for t in profile["packet_history"] if now - t < 20
        ]

        # Classifica tipo di pacchetto
        if tcp:
            if hasattr(tcp, "bits") and tcp.bits == 2:  # SYN
                profile["tcp_syn_count"] += 1
        elif ip and ip.get("proto") == 1:  # ICMP
            profile["ping_count"] += 1
        elif udp:
            profile["udp_count"] += 1

        # Calcola rate attuale (pacchetti/secondo)
        time_window = min(20, now - profile["first_seen"])
        if time_window > 0:
            current_rate = len(profile["packet_history"]) / time_window
            profile["rate_history"].append(current_rate)
            # Mantieni solo ultime 5 misurazioni
            if len(profile["rate_history"]) > 5:
                profile["rate_history"].pop(0)

        # Se il profilo esiste da almeno 10 secondi, valuta il suo comportamento
        host_age = now - profile["first_seen"]
        if host_age < 10:
            return  # Aspetta per avere dati sufficienti

        # DETECTION basata su profili comportamentali
        is_dos = False
        reason = ""

        # 1. Alta percentuale di SYN (tipico di SYN flood)
        total_pkts = len(profile["packet_history"])
        if total_pkts > 20 and profile["tcp_syn_count"] > total_pkts * 0.8:
            is_dos = True
            reason = f"SYN flood: {profile['tcp_syn_count']}/{total_pkts} SYN packets"

        # 2. Burst estremi (>100 pkt/s)
        elif current_rate > 100:
            is_dos = True
            reason = f"Extreme rate: {current_rate:.1f} pkts/s"

        # 3. Aumento rapido del rate (>4x in pochi secondi)
        elif (
            len(profile["rate_history"]) > 2
            and profile["rate_history"][-1] > 4 * profile["rate_history"][0]
            and profile["rate_history"][-1] > 50
        ):
            is_dos = True
            reason = f"Rate spike: {profile['rate_history'][0]:.1f} to {profile['rate_history'][-1]:.1f} pkts/s"

        # 4. Rate sostenuto alto (>60 pkt/s per >15s)
        elif (
            current_rate > 60 and host_age > 15 and len(profile["packet_history"]) > 200
        ):
            is_dos = True
            reason = (
                f"Sustained high rate: {current_rate:.1f} pkts/s for {host_age:.1f}s"
            )

        # Log periodico per debug
        if total_pkts % 30 == 0:
            self.logger.info(
                f"Profile {src}: {current_rate:.1f} pkts/s, {len(profile['targets'])} targets, "
                f"{profile['tcp_syn_count']} SYNs, {profile['ping_count']} pings, age={host_age:.1f}s"
            )

        if is_dos:
            profile["block_count"] += 1
            self.logger.info(f"*** DoS DETECTED from {src}: {reason} ***")
            flow_id = self.mitigator._flow_id(pkt)
            self.mitigator.apply_block(datapath, flow_id)
            # Reset contatori
            profile["packet_history"] = []
            profile["tcp_syn_count"] = 0

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        self.logger.info(f"Received flow stats from switch {ev.msg.datapath.id}")
        self.monitor.update_flow_stats(ev.msg.datapath.id, ev.msg.body)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        self.logger.info(f"Received port stats from switch {ev.msg.datapath.id}")
        self.monitor.update_port_stats(ev.msg.datapath.id, ev.msg.body)

    def stop(self):
        self.running = False
        self.monitor.stop()
        if start_api_server:
            # Implement graceful API shutdown if needed
            pass

    def _reset_counters(self):
        # Da chiamare periodicamente
        if hasattr(self, "_packet_count"):
            self._packet_count.clear()
            self.logger.info("Packet counters reset")
