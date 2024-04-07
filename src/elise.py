from models import NetworkGraph, NetworkNode, ConfigData, NetworkOs
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import List

templates_dir = str(Path(__file__).parent)

class Fate():
    """
    Configuration generation, but without templates.
    """
    def __init__(self, node:NetworkNode,config_data : ConfigData) -> None:
        self.node = node
        self.config_data = config_data
    
    def generate_iosxe(self)->str:
        """"""
        cfg = []
        cfg.append(f"hostname {self.node.hostname}")
        cfg.extend(self._generate_generate_iosxe_interface_config())
        return "\n".join(cfg)

    def _generate_generate_iosxe_interface_config(self)->List[str]:
        interface_cfg = []
        for interface in self.node.interfaces:
            interface_cfg.append(f"interface {interface.name}")
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
                    print(f"configuration for {hostname} {node.os}")
                    if node.os == NetworkOs.IOSXE.value:

                        fate = Fate(node=node, config_data=self.ng.network.config_data)
                        result = fate.generate_iosxe()
                        print(result)


