#!/usr/bin/python
from mininet.log import setLogLevel, info
from mininet.net import Mininet, CLI
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink

class ComplexEnvironment(object):
    def __init__(self):
        "Create a complex mesh/tree-like network with up to 10 switches and multiple hosts."
        self.net = Mininet(controller=RemoteController, link=TCLink)
        info("*** Starting controller\n")
        c1 = self.net.addController('c1', controller=RemoteController)
        c1.start()
        info("*** Adding hosts and switches\n")
        # Add hosts (1 target, 4 attackers, 2 legittimi)
        hosts = []
        for i in range(1, 8):
            hosts.append(self.net.addHost(f'h{i}', mac=f'00:00:00:00:00:0{i}', ip=f'10.0.0.{i}'))
        # Add switches
        switches = []
        for i in range(1, 11):
            switches.append(self.net.addSwitch(f's{i}', cls=OVSKernelSwitch))
        info("*** Adding links\n")
        # Connect hosts to switches (distribuiti)
        self.net.addLink(hosts[0], switches[0], bw=10)  # h1 (attacker) -> s1
        self.net.addLink(hosts[1], switches[1], bw=10)  # h2 (attacker) -> s2
        self.net.addLink(hosts[2], switches[2], bw=10)  # h3 (attacker) -> s3
        self.net.addLink(hosts[3], switches[3], bw=10)  # h4 (attacker) -> s4
        self.net.addLink(hosts[4], switches[4], bw=10)  # h5 (legit) -> s5
        self.net.addLink(hosts[5], switches[5], bw=10)  # h6 (legit) -> s6
        self.net.addLink(hosts[6], switches[9], bw=10)  # h7 (target) -> s10

        # Mesh/tree inter-switch links
        # Tree backbone: s1,s2,s3,s4 -> s7 -> s8 -> s9 -> s10
        self.net.addLink(switches[0], switches[6], bw=5)
        self.net.addLink(switches[1], switches[6], bw=5)
        self.net.addLink(switches[2], switches[6], bw=5)
        self.net.addLink(switches[3], switches[6], bw=5)
        self.net.addLink(switches[6], switches[7], bw=5)
        self.net.addLink(switches[7], switches[8], bw=5)
        self.net.addLink(switches[8], switches[9], bw=5)
        # Collegamenti multipli (mesh)
        self.net.addLink(switches[4], switches[7], bw=5)
        self.net.addLink(switches[5], switches[8], bw=5)
        self.net.addLink(switches[2], switches[5], bw=5)
        self.net.addLink(switches[1], switches[4], bw=5)
        info("*** Starting network\n")
        self.net.build()
        self.net.start()

if __name__ == '__main__':
    setLogLevel('info')
    info('starting the complex environment\n')
    env = ComplexEnvironment()
    info("*** Running CLI\n")
    CLI(env.net)