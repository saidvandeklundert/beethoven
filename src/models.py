from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
import uuid
from uuid import UUID
from typing import List, Optional, Union, Dict
from enum import Enum
import ipaddress
import networkx as nx
import matplotlib.pyplot as plt


class Vlan(BaseModel):
    """
    A Virtual Local Area Network.
    """

    tag: int
    name: Optional[str] = None

    def __hash__(self):
        return hash(str(self.tag))


class InterfaceMode(Enum):
    """
    The mode that the interface is operating in.
    """

    ACCESS = "access"
    TRUNK = "trunk"
    ROUTED = "routed"


class InterfaceType(Enum):
    """
    The interface type.
    """

    PHYSICAL = "physical"
    AGGREGRATE = "aggregate"
    VIRTUAL = "virtual"
    SUB_INTERFACE = "sub_interface"


class Interface(BaseModel):
    """
    The interface and all of its properties
    """

    _id: UUID = uuid.uuid4()
    name: str
    parent: str  # hostname of the device or parent interface
    ipv4_address: Optional[ipaddress.IPv4Interface] = None
    ipv6_address: Optional[List[ipaddress.IPv6Interface]] = None
    interface_mode: InterfaceMode
    interface_type: InterfaceType
    vlans: List[Vlan] = []
    sub_interfaces: List[Interface] = []
    aggregate_members: Optional[List[str]] = None

    class Config:
        use_enum_values = True

    def __hash__(self):
        return hash(str(self._id))

    def __str__(self) -> str:
        return f"{self.name}"

class Role(Enum):
    """
    The role of the device
    """

    SPINE = "spine"
    LEAF = "leaf"
    ACCESS_SWITCH = "acc-sw"
    DISTRIBUTION_SWITCH = "dis-sw"


class Vendor(Enum):
    """
    The Network vendor.
    """

    CISCO = "cisco"
    JUNIPER = "juniper"
    ARISTA = "arista"
    UNKNOWN = "unknown"


class NetworkOs(Enum):
    """
    The network OS in use.
    """
    IOS = "IOS"
    IOSXE = "IOSXE"
    IOSXR = "IOSXR"
    JUNOS = "JUNOS"
    EOS = "EOS"
    UNKNOWN = "unknown"


class NetworkNode(BaseModel, use_enum_values=True):
    """
    A node in the network. Can be a switch, router, etc.
    """

    hostname: str
    vendor: Vendor = Vendor.CISCO
    role: Role
    os: NetworkOs = NetworkOs.IOSXE
    interfaces: List[Interface]


    def __hash__(self):
        return hash(self.hostname)

    def __str__(self) -> str:
        return self.hostname

    def __iter__(self):
        return iter(self.interfaces)

    def __getitem__(self, interface_idx: int):
        return self.interfaces[interface_idx]

    

class EndhostType(Enum):
    WIRELESS_AP = "wireless access point"
    SERVER = "server"


class Endhost(BaseModel, use_enum_values=True):
    """
    Non-networked devices or device not part of
     a wired network.
    """

    hostname: str
    host_type: EndhostType = EndhostType.SERVER
    interfaces: List[Interface]

    def __hash__(self):
        return hash(self.hostname)

    def __str__(self) -> str:
        return self.hostname

    def __iter__(self):
        return iter(self.interfaces)

    def __getitem__(self, interface_idx: int):
        return self.interfaces[interface_idx]


class Endhosts(BaseModel, use_enum_values=True):
    """ """

    nodes: List[Endhost]

    def __iter__(self):
        return iter(self.nodes)

class ConfigData(BaseModel):
    syslog_servers:List[ipaddress.IPv4Address] 
    dns_servers:List[ipaddress.IPv4Address] 

class Network(BaseModel, use_enum_values=True):
    """
    A Network.
    """

    nodes: Dict[str, Union[NetworkNode, Endhost]]
    connections: List
    config_data : ConfigData

    def __iter__(self):
        return iter(self.nodes.items())

    def __getitem__(self, node: str):
        return self.nodes[node]


class NetworkGraph:
    def __init__(self, network: Network):
        self.network = network
        self.graph = nx.Graph()
        self._add_nodes_to_graph()
        self._connect_nodes_to_interfaces()
        self._connect_interfaces()
        self._validate_graph()

    def _add_nodes_to_graph(self):
        """
        Add all the nodes to the graph
        """
        for _, node in self.network:
            self.graph.add_node(node)

    def _connect_nodes_to_interfaces(self):
        """
        Setup the network nodes and the connections to their interfaces
        """
        for _, node in self.network:
            for interface in node:
                self.graph.add_edge(node, interface)

    def _connect_interfaces(self):
        """
        Connect all the interfaces together.
        """
        for c in self.network.connections:
            self.graph.add_edge(self.network[c[0]][c[1]], self.network[c[2]][c[3]])

    def display_network_nodes(self):
        """
        Print all the Network nodes in the network.
        """
        for node in list(self.graph.nodes):
            if isinstance(node, NetworkNode):
                print(node)

    def display_nodes(self):
        """
        Print all the nodes in the network.
        """
        for node in list(self.graph.nodes):
            print(node)

    def display_graph(self):
        """
        Draw the entire graph on screen.
        """
        pos = nx.circular_layout(self.graph)
        nx.draw(self.graph, pos, with_labels=True)
        nx.draw_networkx_edges(self.graph, pos, arrowstyle="<|-", style="dashed")
        plt.show()

    def display_graph_test(self):
        """
        Draw the entire graph on screen.
        """
        pos = nx.circular_layout(self.graph)
        nx.draw_kamada_kawai(self.graph, )
        nx.draw_networkx_edges(self.graph, pos, arrowstyle="<|-", style="dashed",width=0.5)
        plt.show()


    def display_sub_graph(self, nodes: List[str]):
        """
        Draw a portion of the graph on screen.
        """
        relevant_items = []
        for node in nodes:
            relevant_items.append(self.network[node])
            for interface in self.network[node].interfaces:
                relevant_items.append(interface)
        sub_graph = self.graph.subgraph(nodes=relevant_items)
        pos = nx.circular_layout(sub_graph)
        nx.draw(sub_graph, pos, with_labels=True)
        nx.draw_networkx_edges(sub_graph, pos, arrowstyle="<|-", style="dashed")
        plt.show()

    def display_links(self, node_name: Optional[str] = None):
        """
        Print all the links in a given network in the following format:

        >>> switch-3 GigabitEthernet0/0/1 < -- > GigabitEthernet0/0/1 switch-4
        """
        for link in list(self.graph.edges):
            if isinstance(link[0], Interface) and isinstance(link[1], Interface):
                a_side = link[0]
                b_side = link[1]
                link_str = f"{a_side.parent} {a_side.name} < -- > {b_side.name} {b_side.parent}"
                if node_name:
                    if node_name in link_str:
                        print(link_str)
                else:
                    print(link_str)

    def _validate_mode(self, a_side: Interface, b_side: Interface) -> bool:
        """
        Validate whether or not the mode of the interface on both ends
        is compatible.
        """
        a_mode = a_side.interface_mode
        b_mode = b_side.interface_mode
        if a_mode == b_mode:
            return True
        if a_mode == InterfaceMode.ACCESS and b_mode == InterfaceMode.ROUTED:
            return True
        if b_mode == InterfaceMode.ACCESS and a_mode == InterfaceMode.ROUTED:
            return True
        else:
            return False

    def validate_links(self, node_name: Optional[str] = None):
        """
        Iterate the grap edges and ensure that the links on both ends are
        compatible.
        """
        for link in list(self.graph.edges):
            if isinstance(link[0], Interface) and isinstance(link[1], Interface):
                a_side: Interface = link[0]
                b_side: Interface = link[1]

                a_side.interface_type
                link_str = f"{a_side.parent} {a_side.name} < -- > {b_side.name} {b_side.parent}"
                if node_name and node_name not in link_str:
                    continue
                result = self._validate_mode(a_side=a_side, b_side=b_side)
                if result == False:
                    raise ValueError(
                        f"Invalid mode combination for {link_str}: {a_side.interface_mode} {b_side.interface_mode}"
                    )

    def _validate_graph(self):
        """
        Run validations on the graph that was just build.
        """
        self.validate_links()

