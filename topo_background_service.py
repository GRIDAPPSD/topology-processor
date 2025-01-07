import os
import json
import time
import logging
from gridappsd import GridAPPSD
from gridappsd.topics import service_input_topic, service_output_topic
from cimgraph.databases import ConnectionParameters, BlazegraphConnection

from topology_processor.utils import DistributedTopologyMessage
import cimgraph.data_profile.cimhub_2023 as cim

class TopologyProcessor(GridAPPSD):
    
    def __init__(self):
        os.environ['GRIDAPPSD_APPLICATION_ID'] = 'topology-background-service'
        os.environ['GRIDAPPSD_APPLICATION_STATUS'] = 'STARTED'
        os.environ['GRIDAPPSD_USER'] = 'app_user'
        os.environ['GRIDAPPSD_PASSWORD'] = '1234App'
        gapps = GridAPPSD()
        assert gapps.connected
        self.gapps = gapps
        self.log = self.gapps.get_logger()
        params = ConnectionParameters(url = "http://localhost:8889/bigdata/namespace/kb/sparql", cim_profile='cimhub_2023', iec61970_301=8)
        self.blazegraph = BlazegraphConnection(params)

        
        self.log.info('Topology Background Service Started')

    
    # GridAPPS-D service
    def on_message(self, headers, message):
        model_mrid = message['mRID']
        reply_to = headers['reply-to']
        
        
        if message['requestType'] == 'GET_DISTRIBUTED_AREAS':
            
            self.log.info(f'Building Distributed Areas for {model_mrid}')
            
            topo_message = DistributedTopologyMessage()
            container = self.blazegraph.get_object(mrid=model_mrid)

            if isinstance(container, cim.Feeder):
                topo_message.get_context_from_feeder(container, self.blazegraph)

            elif isinstance(container, cim.FeederArea):
                topo_message.get_context_from_feeder_area(container, self.blazegraph)
                
            elif isinstance(container, cim.DistributionArea):
                topo_message.get_context_from_distribution_area(container, self.blazegraph)

            return_message = json.dumps(topo_message.message, indent=4)
            del topo_message
            self.gapps.send(reply_to, return_message)
            
        elif message['requestType'] == 'GET_BASE_TOPOLOGY':
            Topology = self.get_base_topology(model_mrid)
            return_message = {  
                "response": "not yet supported"
                # 'modelID': model_mrid,
                # 'feeders': Topology.Feeders,
                # 'islands': Topology.Islands,
                # 'connectivity': Topology.ConnNodeDict,
                # 'equipment': Topology.EquipDict
            }
            self.gapps.send(reply_to, message)
        
        elif message['requestType'] == 'GET_SNAPSHOT_TOPOLOGY':
            # [Topology, timestamp] = self.get_snapshot_topology(model_mrid, message['simulationID'], message['timestamp'])
            message = {
                "response": "not yet supported"
                # 'modelID': model_mrid,
                # 'feeders': Topology.Feeders,
                # 'islands': Topology.Islands,
                # 'timestamp': timestamp
            }
            self.gapps.send(reply_to, message)
        else:
            message = "No valid requestType specified"
            self.gapps.send(reply_to, message)
        
    def get_switch_areas(self, model_mrid):
        self.log.info('Building switch areas for ' + str(model_mrid))
        # DistTopo = DistributedTopology(self.gapps, model_mrid)
        # message = DistTopo.create_switch_areas(model_mrid)
        # return message
        
      


     
            
def _main():
    topic = "goss.gridappsd.request.data.cimtopology"
    os.environ['GRIDAPPSD_USER'] = 'app_user'
    os.environ['GRIDAPPSD_PASSWORD'] = '1234App'
    gapps = GridAPPSD()
    assert gapps.connected
    topology = TopologyProcessor()
    gapps.subscribe(topic, topology)
    while True:
        time.sleep(0.1)
        
if __name__ == "__main__":
    _main()