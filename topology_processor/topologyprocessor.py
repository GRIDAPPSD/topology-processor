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
        self.log = self.gapps.get_logger()

    
    # GridAPPS-D service
    def on_message(self, headers, message):
        model_mrid = message['model_id']
        reply_to = headers['reply-to']
        
        if message['requestType'] == 'GET_SWITCH_AREAS':
            message = self.get_switch_areas(model_mrid)
            self.gapps.send(reply_to, message)
            
        elif message['requestType'] == 'GET_BASE_TOPOLOGY':
            Topology = self.get_base_topology(model_mrid)
            message = {
                'feeder_id': model_mrid,
                'feeders': json.dumps(Topology.Feeders),
                'islands': json.dumps(Topology.Islands),
                'connectivity': json.dumps(Topology.ConnNodeDict),
                'equipment': json.dumps(Topology.EquipDict)
            }
            self.gapps.send(reply_to, message)
        
        elif message['requestType'] == 'GET_SNAPSHOT_TOPOLOGY':
            Topology = self.get_snapshot_topology(model_mrid, message['simulation_id'], message['timestamp'])
            message = {
                'feeder_id': model_mrid,
                'feeders': json.dumps(Topology.Feeders),
                'islands': json.dumps(Topology.Islands)
            }
            self.gapps.send(reply_to, message)
            
        
    def get_switch_areas(self, model_mrid):
        self.log.info('Building switch areas for ' + str(model_mrid))
        DistTopo = DistributedTopology(self.gapps, model_mrid)
        message = DistTopo.create_switch_areas(model_mrid)
        return message
        
    def get_base_topology(self, model_mrid):
        self.log.info('Building base topology for ' + str(model_mrid))
        Topology = TopologyDictionary(self.gapps, model_mrid)
        network = NetworkModel(self.gapps)
        network.build_equip_dicts(model_mrid, Topology)
        EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine']
        Topology.build_linknet(EqTypes)
        Topology.update_switches()
        Topology.build_feeder_islands()
        return Topology     


        
    def get_snapshot_topology(self, model_mrid, simulation_id, timestamp):
        self.log.info('Building snapshot topology for ' + str(model_mrid))
        Topology = TopologyDictionary(self.gapps, model_mrid)
        network = NetworkModel(self.gapps)
        network.build_equip_dicts(model_mrid, Topology)
        EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine']
        Topology.build_linknet(EqTypes)
        
         #Query for switch position measurement mRIDs
        request = {"modelId": model_mrid,
                   "requestType": "QUERY_OBJECT_MEASUREMENTS",
                   "resultFormat": "JSON",
                   "objectType": "LoadBreakSwitch"
                   }

        response = self.gapps.get_response(t.REQUEST_POWERGRID_DATA,request,timeout=15)
        
        equipment_dict = {}
        measurement_dict = {}
        meas_map={}

        for measurement in response["data"]:
            if measurement["type"] == "Pos":
                measid = measurement["measid"]
                meas_map[measid] = {}
                meas_map[measid]['eqtype'] = measurement['eqtype']
                meas_map[measid]['eqid'] = measurement["eqid"]



        # Query for switch measurments
        message = {
            "queryMeasurement":"simulation",
            "queryFilter":{"simulation_id": str(simulation_id),
                "startTime": str(round(int(timestamp)-1)),
                "endTime": str(round(int(timestamp)+3)),
                "measurement_mrid": list(measurement_dict.keys())
                          },
                "responseFormat":"JSON" }


        influx_response = self.gapps.get_response(t.TIMESERIES, message) # Pass API call

        counter=0
        while not influx_response['data'] and counter <5:
            influx_response = gapps.get_response(t.TIMESERIES, message) # Pass API call
            self.log.debug('Waiting 10 seconds for data to be written to Timeseries Database')
            _time.sleep(10)
            counter=counter+1
            if counter==5: self.log.debug("No Timeseries data found. Returning default topology")

        # Parse timeseries data for current switch positions
        for measurement in influx_response["data"]:
            measid = measurement["measurement_mrid"]
            time = measurement["time"]
            if measid in meas_map:
                eqid = meas_map[measid]['eqid']
                eqtype = meas_map[measid]['eqtype']
                Topology.EquipDict[eqtype][eqid]["open"] = measurement['value']
                
        Topology.update_switches()
        Topology.build_feeder_islands()
        
        return Topology
            
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
    