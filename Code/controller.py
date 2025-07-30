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
        self.monitor = Monitor(self)
        self.detector = Detector(self)
        self.mitigator = Mitigator(self)
        self.running = True

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()

        # Start REST API server if available
        if start_api_server:
            self.api_thread = threading.Thread(target=start_api_server, args=(self.mitigator,), daemon=True)
            self.api_thread.start()

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.mitigator.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = self.monitor.parse_packet(msg.data)
        eth = pkt.get('eth', None)
        if not eth or eth['ethertype'] == 0x88cc:  # LLDP
            return

        src = eth['src']
        dst = eth['dst']
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

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

    def stop(self):
        self.running = False
        self.monitor.stop()
        if start_api_server:
            # Implement graceful API shutdown if needed
            pass




