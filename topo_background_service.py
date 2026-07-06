import os
import json
import time
from gridappsd import GridAPPSD
from cimgraph.databases.blazegraph import BlazegraphConnection

from topology_processor.utils import DistributedTopologyMessage
import cimgraph.data_profile.cimhub_2023 as cim
from dotenv import load_dotenv

# Uncomment and set following environment variables if testing outside GridAPPS-D container
#os.environ["GRIDAPPSD_ADDRESS"] = ''
#os.environ["GRIDAPPSD_PORT"] = ''
#os.environ["GRIDAPPSD_USER"] = ''
#os.environ["GRIDAPPSD_PASSWORD"] = ''
#os.environ['CIMG_HOST'] = ''
#os.environ['CIMG_PORT'] = ''
#os.environ['CIMG_NAMESPACE'] = ''

os.environ['CIMG_CIM_PROFILE'] = 'cimhub_2023'
os.environ['CIMG_URL'] = 'http://blazegraph:8080/bigdata/namespace/kb/sparql'
os.environ['CIMG_IEC61970_301'] = '8'


class TopologyProcessor(GridAPPSD):
    
    def __init__(self):
        gapps = GridAPPSD()
        assert gapps.connected
        self.gapps = gapps
        self.log = self.gapps.get_logger()
        self.blazegraph = BlazegraphConnection()
        self.log.info('Topology Background Service Started')
        self.return_message = {}

    
    # GridAPPS-D service
    def on_message(self, headers, message):
        model_mrid = message['mRID']
        reply_to = headers['reply-to']
        
        
        if message['requestType'] == 'GET_DISTRIBUTED_AREAS':
            
            print(f'Building Distributed Areas for {model_mrid}')

            if model_mrid in self.return_message and self.return_message[model_mrid] is not None:
                print('Distributed Areas already built, sending cached message on '+reply_to)
                self.gapps.send(reply_to, self.return_message[model_mrid])
            
            else:
            
                topo_message = DistributedTopologyMessage()
                container = self.blazegraph.get_object(mRID=model_mrid)

                if isinstance(container, cim.Feeder):
                    topo_message.get_context_from_feeder(container, self.blazegraph)

                elif isinstance(container, cim.FeederArea):
                    topo_message.get_context_from_feeder_area(container, self.blazegraph)
                    
                elif isinstance(container, cim.DistributionArea):
                    topo_message.get_context_from_distribution_area(container, self.blazegraph)

                self.return_message[model_mrid] = json.dumps(topo_message.message, indent=4)
                del topo_message
                self.gapps.send(reply_to, self.return_message[model_mrid])

        elif message['requestType'] == 'GET_BASE_TOPOLOGY':
            #Topology = self.get_base_topology(model_mrid)
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

    load_dotenv()
        
    topic = "goss.gridappsd.request.data.cimtopology"
    gapps = GridAPPSD()
    assert gapps.connected
    topology = TopologyProcessor()
    gapps.subscribe(topic, topology)
    while True:
        time.sleep(0.1)
        
if __name__ == "__main__":
    _main()
