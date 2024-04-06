import yaml
from models import NetworkNode, Endhost, Network, NetworkGraph


with open("db/network_1_nodes.yaml") as stream:
    network = yaml.safe_load(stream)


with open("db/network_1_connections.yaml") as stream:
    connections = yaml.safe_load(stream)

with open("db/network_1_endhosts.yaml") as stream:
    endhost_data = yaml.safe_load(stream)

network_model = Network(nodes={}, connections=connections)
for node in network:
    modeled_node = NetworkNode(**node)
    network_model.nodes[modeled_node.hostname] = modeled_node
for endhost in endhost_data:
    modeled_endhost = Endhost(**endhost)
    network_model.nodes[modeled_endhost.hostname] = modeled_endhost


ng = NetworkGraph(network=network_model)
#ng.display_network_nodes()
ng.display_nodes()
#ng.display_graph()
ng.display_links()
#ng.display_sub_graph(["switch-3", "switch-4"])
#ng.display_links("switch-2")
#ng.display_sub_graph(["spine-1", "spine-2", "leaf-1", "leaf-2", "leaf-3"])
