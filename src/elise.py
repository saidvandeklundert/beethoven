from models import NetworkGraph, NetworkNode, ConfigData, NetworkOs,InterfaceMode
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import List
from pydantic import BaseModel
templates_dir = str(Path(__file__).parent)


class JunosConstants(BaseModel):
    system:str="""set system no-redirects
set system arp aging-timer 5
set system internet-options path-mtu-discovery
set system authentication-order password
set system services ftp
set system services ssh
set system services netconf ssh port 830
set system syslog archive size 100k
set system syslog user * any emergency
set system syslog file messages any any
set system syslog file messages authorization none
set system syslog file messages interactive-commands none
set system syslog file messages match "!(.*not Juniper supported SFP.*|(.*Input IFL not found.*))"
set system syslog file messages explicit-priority
set system syslog file interactive-commands interactive-commands any
set system syslog file interactive-commands explicit-priority
set system syslog file login-attempts authorization any
set system syslog file login-attempts explicit-priority"""

    def systems_config(self)->List[str]:
        return self.system.splitlines()

JUNOS_CONSTANTS = JunosConstants()
class Fate():
    """
    Configuration generation, but without templates.
    """
    def __init__(self, node:NetworkNode,config_data : ConfigData) -> None:
        self.node = node
        self.config_data = config_data
    
    def generate_junos(self)->str:
        cfg = []
        cfg.append(f"set system host-name {self.node.hostname}")
        cfg.extend(self._generate_junos_system_config())
        cfg.extend(self._generate_junos_interface_config())
        return "\n".join(cfg)
    
    def _generate_junos_system_config(self)->List[str]:
        """
        Generate the system configuration for a Junos device
        """
        result = []
        result.extend(JUNOS_CONSTANTS.systems_config())
        for syslog_server in self.config_data.syslog_servers:
            result.append(f"set system syslog host {syslog_server} any notice")
        return result        

    def _generate_junos_interface_config(self)->List[str]:
        """
        Generate the interface configuration for Junos device.
        """
        interface_cfg = []
        for interface in self.node.interfaces:            
            if interface.interface_mode == InterfaceMode.TRUNK.value:                
                interface_cfg.append(f"set interfaces {interface.name} unit 0 family ethernet-switching interface-mode trunk")
                for vlan in interface.vlans:
                    interface_cfg.append(f"set interfaces  {interface.name} unit 0 family ethernet-switching vlan members {vlan.tag}")
            if interface.interface_mode == InterfaceMode.ACCESS.value:
                pass                  
            elif interface.interface_mode == InterfaceMode.ROUTED.value:
                if interface.ipv4_address:
                    interface_cfg.append(f"set interfaces {interface.name} unit 0 family inet address {interface.ipv4_address}")                    
                if interface.ipv6_address:
                    for ipv6_address in interface.ipv6_address:
                        interface_cfg.append(f"set interfaces  {interface.name} unit 0 family inet6 address {ipv6_address}")
        return interface_cfg

    def generate_iosxe(self)->str:
        """
        Generate an IOSXE configuration for an instance on 'Node'.
        """
        cfg = []
        cfg.append(f"hostname {self.node.hostname}")
        cfg.extend(self._generate_iosxe_system_settings())
        cfg.extend(self._generate_iosxe_interface_config())
        return "\n".join(cfg)

    def _generate_iosxe_system_settings(self)->List[str]:
        """Generate the system settings for an IOSXE device"""
        result = []
        result.append("logging buffered")
        for syslog_server in self.config_data.syslog_servers:
            result.append(f"logging {syslog_server}")
        return result

    
    def _generate_iosxe_interface_config(self)->List[str]:
        """
        Generate the interface configuration for Cisco IOSXE.
        """
        interface_cfg = []
        for interface in self.node.interfaces:
            interface_cfg.append(f"interface {interface.name}")
            if interface.interface_mode == InterfaceMode.TRUNK.value:
                interface_cfg.append(" switchport mode trunk")
                for vlan in interface.vlans:
                    interface_cfg.append(f" switchport trunk allowed vlan add {vlan.tag}")
            if interface.interface_mode == InterfaceMode.ACCESS.value:
                interface_cfg.append(" switchport mode access")
                interface_cfg.append(f" switchport access vlan {interface.vlans[0].tag}")                    
            elif interface.interface_mode == InterfaceMode.ROUTED.value:
                if interface.ipv4_address:
                    interface_cfg.append(f" ip address {interface.ipv4_address}")
                if interface.ipv6_address:
                    for ipv6_address in interface.ipv6_address:
                        interface_cfg.append(f" ipv6 address {ipv6_address}")

        return interface_cfg


class Elise():
    
    def __init__(self, ng: NetworkGraph) -> None:
          self.ng = ng
   
    def render_jinja_templates(self):
        """
        Given a network, produce the configuration.

        Contains the start of a Jinja implementation as well 
        as the start of a Python implementation.
        """    
        for hostname, node in self.ng.network:
            if isinstance(node, NetworkNode):
                print(hostname)
                file_loader = FileSystemLoader(templates_dir + "/templates")
                env = Environment(loader=file_loader)
                template = env.get_template("main.j2")
                output = template.render(node=node)
                if output:
                    output = "\n".join(
                        [line for line in output.splitlines() if line.strip()]
                    )
                    print(output)
                else:
                    raise RuntimeError("No template output!!")


    def build_configurations(self)->None:
            for hostname, node in self.ng.network:
                if isinstance(node, NetworkNode):
                    print(50*"-")
                    print(f"configuration for {hostname} {node.os}")
                    print(50*"-")
                    print("\n")
                    if node.os == NetworkOs.IOSXE.value:

                        fate = Fate(node=node, config_data=self.ng.network.config_data)
                        result = fate.generate_iosxe()
                        print(result)
                    elif node.os == NetworkOs.JUNOS.value:

                        fate = Fate(node=node, config_data=self.ng.network.config_data)
                        result = fate.generate_junos()
                        print(result)
                    else:
                        raise NotImplementedError(f"no implementation exists for {node.os}")                    


