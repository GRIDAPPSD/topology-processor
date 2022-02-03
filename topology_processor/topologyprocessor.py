import os, json, time
from gridappsd import GridAPPSD, topics as t
from gridappsd.topics import service_input_topic, service_output_topic
from distributedtopology import DistributedTopology
from topologydictionary import TopologyDictionary
from networkmodel import NetworkModel

class TopologyProcessor(GridAPPSD):
    
    def __init__(self):
        os.environ['GRIDAPPSD_APPLICATION_ID'] = 'gridappsd-topology-processor'
        os.environ['GRIDAPPSD_APPLICATION_STATUS'] = 'STARTED'
        os.environ['GRIDAPPSD_USER'] = 'app_user'
        os.environ['GRIDAPPSD_PASSWORD'] = '1234App'
        gapps = GridAPPSD()
        assert gapps.connected
        self.gapps = gapps

    
    # GridAPPS-D service
    def on_message(self, headers, message):
        model_mrid = message['modelID']
        reply_to = headers['reply-to']
        
        if message['requestType'] == 'GET_SWITCH_AREAS':
            message = self.get_switch_areas(model_mrid)
            self.gapps.send(reply_to, message)
            
        elif message['requestType'] == 'GET_BASE_TOPOLOGY':
            Topology = self.get_base_topology(model_mrid)
            message = {
                'feeder_id': model_mrid,
                'feeders': Topology.Feeders,
                'islands': Topology.Islands,
                'connectivity_model': Topology.ConnNodeDict
            }
            self.gapps.send(reply_to, message)
        
        elif message['requestType'] == 'GET_SNAPSHOT_TOPOLOGY':
            simulation_id = message['simulation_id']
            timestamp = message['time']
            message = self.get_snapshot_topology(model_mrid, simulation_id, timestamp)
            self.gapps.send(reply_to, message)
            
        
    def get_switch_areas(self, model_mrid):
        DistTopo = DistributedTopology(self.gapps, model_mrid)
        message = DistTopo.create_switch_areas(model_mrid)
        return message
        
    def get_base_topology(self, model_mrid):
        Topology = TopologyDictionary(self.gapps, model_mrid)
        network = NetworkModel(self.gapps)
        network.build_equip_dicts(model_mrid, Topology)
        EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine']
        Topology.build_linknet(EqTypes)
        Topology.update_switches()
        Topology.build_feeder_islands()
        return Topology     


        
    def get_snapshot_topology(self, model_mrid, sim_id, timestamp):
        Topology = TopologyDictionary(self.gapps, model_mrid)
        
        
         #Query for switch position measurement mRIDs
        request = {"modelId": model_mrid,
                   "requestType": "QUERY_OBJECT_MEASUREMENTS",
                   "resultFormat": "JSON",
                   "objectType": "LoadBreakSwitch"
                   }

        response = gapps.get_response(t.REQUEST_POWERGRID_DATA,request,timeout=15)

        for measurement in response["data"]:
            if measurement["type"] == "Pos":
                measid = measurement["measid"]
                measurement_dict[measid] = measurement
                meas_map[measid] = measurement["eqid"]
                SwitchDict[measurement["eqid"]]["measid"] = measid


        # Query for switch measurments
        message = {
            "queryMeasurement":"simulation",
            "queryFilter":{"simulation_id": str(simulation_id),
                "startTime": str(round(requestedTime-1)),
                "endTime": str(round(requestedTime+3)),
                "measurement_mrid": list(measurement_dict.keys())
                          },
                "responseFormat":"JSON" }


        influx_response = gapps.get_response(t.TIMESERIES, message) # Pass API call

        counter=0
        while not influx_response['data'] and counter <5:
            influx_response = gapps.get_response(t.TIMESERIES, message) # Pass API call
            print('Waiting 10 seconds for data to be written to Timeseries Database')
            _time.sleep(10)
            counter=counter+1
            if counter==5: print("No Timeseries data found. Returning default topology")

        # Parse timeseries data for current switch positions
        for measurement in influx_response["data"]:
            measid = measurement["measurement_mrid"]
            time = measurement["time"]
            eqid = meas_map[measid]
            SwitchDict[eqid]["open"] = measurement['value']
            
def _main():
    topic = "goss.gridappsd.request.data.topology"
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
    