# -------------------------------------------------------------------------------
# Copyright (c) 2022, Battelle Memorial Institute All rights reserved.
# Battelle Memorial Institute (hereinafter Battelle) hereby grants permission to any person or entity
# lawfully obtaining a copy of this software and associated documentation files (hereinafter the
# Software) to redistribute and use the Software in source and binary forms, with or without modification.
# Such person or entity may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and may permit others to do so, subject to the following conditions:
# Redistributions of source code must retain the above copyright notice, this list of conditions and the
# following disclaimers.
# Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
# the following disclaimer in the documentation and/or other materials provided with the distribution.
# Other than as used herein, neither the name Battelle Memorial Institute or Battelle may be used in any
# form whatsoever without the express written consent of Battelle.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
# BATTELLE OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
# General disclaimer for use with OSS licenses
#
# This material was prepared as an account of work sponsored by an agency of the United States Government.
# Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any
# of their employees, nor any jurisdiction or organization that has cooperated in the development of these
# materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for
# the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process
# disclosed, or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer,
# or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United
# States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed
# herein do not necessarily state or reflect those of the United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the
# UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
# -------------------------------------------------------------------------------
"""
Created on Feb 4, 2022
@author: Alexander Anderson, Rohit Jiniswale, Poorva Sharma, Robin Podmore
This service uses the LinkNet(TM) open-source power system model representation framework developed by IncSys Corp
"""

import os, json, time
from gridappsd import GridAPPSD, topics as t
from gridappsd.topics import service_input_topic, service_output_topic

from topology_processor.distributedtopology import DistributedTopology
from topology_processor.topologydictionary import TopologyDictionary
from topology_processor.networkmodel import NetworkModel

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
        
        self.log.info('Topology daemon started')

    
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
                'modelID': model_mrid,
                'feeders': Topology.Feeders,
                'islands': Topology.Islands,
                'connectivity': Topology.ConnNodeDict,
                'equipment': Topology.EquipDict
            }
            self.gapps.send(reply_to, message)
        
        elif message['requestType'] == 'GET_SNAPSHOT_TOPOLOGY':
            [Topology, timestamp] = self.get_snapshot_topology(model_mrid, message['simulationID'], message['timestamp'])
            message = {
                'modelID': model_mrid,
                'feeders': Topology.Feeders,
                'islands': Topology.Islands,
                'timestamp': timestamp
            }
            self.gapps.send(reply_to, message)
        else:
            message = "No valid requestType specified"
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
        EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine', 'PowerElectronicsConnection']
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
        import time
        counter=0
        while not influx_response['data'] and counter <5:
            influx_response = self.gapps.get_response(t.TIMESERIES, message) # Pass API call
            self.log.info('Waiting 10 seconds for data to be written to Timeseries Database')
            time.sleep(10)
            counter=counter+1
            if counter==5: self.log.info("No Timeseries data found. Returning default topology")

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
        
        return Topology, time
            
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
    