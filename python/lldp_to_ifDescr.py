from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import *
from junos import Junos_Configuration
import jcs
import sys
from lxml import etree
from jinja2 import Environment, BaseLoader

def main():

    usage = """
        on-box script to periodically scrape the lldp neighbor info and populates the respective interface descriptions.

        Interfaces to populate dynamic descriptions are identified by using the following config applied to target interfaces
        to ensure we don't overwrite interfaces where this behavior is not wanted. This is particularly useful for servers
        which participate in LLDP where manually configuring interface descriptions may be tedious.
        
        apply-macro ifdescr_from_lldp {
            true;
        }

    """

    with Device() as dev:
        dev.open()
        
        lldp_result = dev.rpc.get_lldp_neighbors_information()
        lldp_data = lldp_result.xpath("//lldp-neighbors-information")

        lldp_neighbors = {}
        # Loop through lldp neighbors and extract our info
        for neighbors in lldp_data:
            for neighbor in neighbors.getiterator(tag='lldp-neighbor-information'):
                local_port_id = neighbor.find('lldp-local-port-id').text
                remote_system_name = neighbor.find('lldp-remote-system-name').text
                remote_port_description = neighbor.find('lldp-remote-port-description').text

                lldp_neighbors[local_port_id] = { "remote_system_name": remote_system_name, "remote_port_description": remote_port_description }
        
        # Get configuration root object for interfaces only
        filter = '<configuration><interfaces/></configuration>'
        config_data = dev.rpc.get_config(filter_xml=filter)
        
        # debug output only to dump retrieved config
        # print(etree.tostring(config_data, encoding='unicode', pretty_print=True))
    
        # check for interfaces with the apply-macro 'ifdescr_from_lldp' == True for which we'll run the updates
        interface_list = config_data.xpath("./interfaces/interface[apply-macro[name='ifdescr_from_lldp']/data/name[text()='true']]/name")


        # build out list of scoped interfaces to get description updates
        interface_updates = []
        for i in interface_list:
            name = lldp_neighbors[i.text]
            description = f'INT::{lldp_neighbors[i.text]["remote_system_name"]}::{lldp_neighbors[i.text]["remote_port_description"]}'
            interface_updates.append( { "name": i.text, "description": lldp_neighbors[i.text]["remote_system_name"] } )

        print(f'Updating the following interfaces based on gathered LLDP information')
        print(interface_updates)
        


        # build our configuration snippet for description updates
        config_template = """
            <configuration>
                <interfaces>
                    {%- for interface in interface_list %}
                    <interface>
                        <name>{{ interface.name }}</name>
                        <description>{{ interface.description }}</description>
                    </interface>
                    {%- endfor %}
                </interfaces>
            </configuration>
        """
        
        # test only for data structure testing
        # interface_list = [ {"name":"xe-0/0/20", "description":"test_desc"}, {"name":"xe-0/0/21", "description":"test_desc2"} ]

        # load the jinja template to render our config
        rtemplate = Environment(loader=BaseLoader()).from_string(config_template)
        data = rtemplate.render(interface_list=interface_updates)

        # print(data)
        # <configuration>
        #     <interfaces>
        #         <interface>
        #             <name>xe-0/0/20</name>
        #             <description>test_desc</description>
        #         </interface>
        #         <interface>
        #             <name>xe-0/0/21</name>
        #             <description>test_desc2</description>
        #         </interface>
        #     </interfaces>
        # </configuration>

        # now we write these descriptions to the configuration
        dev.open()
        try:
            with Config(dev, mode="exclusive") as cu:
                print ("Loading and committing configuration changes")
                cu.load(data, format="xml", merge=True)
                cu.commit()

        except Exception as err:
            print (err)
            dev.close()
            return


if __name__ == "__main__":
    main()