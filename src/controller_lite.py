import yaml
from models import NetworkNode, Endhost, Network, NetworkGraph, ConfigData
from pathlib import Path
from elise import Elise
import time


db_dir = str(Path(__file__).parent)
def get_network_model()->Network:
    with open(db_dir + "/db/network_1_nodes.yaml") as stream:
        network = yaml.safe_load(stream)


    with open(db_dir + "/db/network_1_connections.yaml") as stream:
        connections = yaml.safe_load(stream)

    with open(db_dir + "/db/network_1_endhosts.yaml") as stream:
        endhost_data = yaml.safe_load(stream)

    with open(db_dir + "/config_data/data.yaml") as stream:
        config_data = yaml.safe_load(stream)


    network_model = Network(
        nodes={}, connections=connections, config_data=ConfigData(**config_data)
    )
    for node in network:
        modeled_node = NetworkNode(**node)
        network_model.nodes[modeled_node.hostname] = modeled_node
    for endhost in endhost_data:
        modeled_endhost = Endhost(**endhost)
        network_model.nodes[modeled_endhost.hostname] = modeled_endhost
    return network_model

def generate_config():
    network_model = get_network_model()
    ng = NetworkGraph(network=network_model)
    elise = Elise(ng=ng)    
    elise.build_configurations(display_to_screen=False)


def main():
    while True:
        start = time.time()
        generate_config()
        end = time.time()
        print(end - start)
        
if __name__ == "__main__":
    main()