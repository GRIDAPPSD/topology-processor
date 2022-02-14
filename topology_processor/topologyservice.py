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
Created on Feb 4, 2021
@author: Alexander Anderson, Rohit Jiniswale, Poorva Sharma
"""

import os, time, json, argparse
from gridappsd import GridAPPSD, topics as t
from gridappsd.topics import service_output_topic, simulation_input_topic, simulation_output_topic
from distributedtopology import DistributedTopology
from topologydictionary import TopologyDictionary
from networkmodel import NetworkModel

class TopologyService(GridAPPSD):
    
    def __init__(self, gapps, Topology, simulation_id, model_mrid, SwitchMeasDict):

        self.gapps = gapps
        self.publish_to_topic = service_output_topic('gridappsd-topology-processor', simulation_id)
        self.Topology = Topology
        self.SwitchMeasDict = SwitchMeasDict
        self.SwitchMeasKeys = list(self.SwitchMeasDict.keys())
        self.model_mrid = model_mrid
        self.log = self.gapps.get_logger()
        
    def on_message(self, headers, message):
        old_topo = False
        
        # Check if message received is simulation output message
        if "output" in headers["destination"]:
            timestamp = message["message"]["timestamp"]
            # Parse list of switch measurements
            
            for meas_id in self.SwitchMeasKeys:
                position = message["message"]["measurements"][meas_id]['value']
                eqid = self.SwitchMeasDict[meas_id]['eqid']
                eqtype = self.SwitchMeasDict[meas_id]['eqtype']
                # Check if any switch positions have changed
                if self.Topology.EquipDict[eqtype][eqid]['open'] != int(position):
                    self.Topology.EquipDict[eqtype][eqid]['open'] = int(position)
                    old_topo = True
                    if position == 0:
                        self.log.info('Detected switch ' + str(self.Topology.EquipDict[eqtype][eqid]['name']) + ' has opened at time ' + str(timestamp))
                    else:
                        self.log.info('Detected switch ' + str(self.Topology.EquipDict[eqtype][eqid]['name']) + ' has closed at time ' + str(timestamp))

        if old_topo:     

            self.Topology.update_switches()
            self.Topology.build_feeder_islands()
            message = {
                'feeder_id': self.model_mrid,
                'timestamp': timestamp,
                'feeders': json.dumps(self.Topology.Feeders),
                'islands': json.dumps(self.Topology.Islands)
            }
            self.gapps.send(self.publish_to_topic, message)
                
        
        
def _main():
    
      
    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_id",
                        help="Simulation id to use for responses on the message bus.")
    parser.add_argument("request",
                        help="Simulation Request")

    opts = parser.parse_args()
    
    # Authenticate with GridAPPS-D Platform
    os.environ['GRIDAPPSD_APPLICATION_ID'] = 'gridappsd-topology-service'
    os.environ['GRIDAPPSD_APPLICATION_STATUS'] = 'STARTED'
    os.environ['GRIDAPPSD_USER'] = 'system'
    os.environ['GRIDAPPSD_PASSWORD'] = 'manager'
    
    sim_request = json.loads(opts.request.replace("\'",""))
    model_mrid = sim_request["power_system_config"]["Line_name"]
    #model_mrid = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"
    
    simulation_id = opts.simulation_id
    
    gapps = GridAPPSD(simulation_id)
    assert gapps.connected
    
    sim_output_topic = simulation_output_topic(simulation_id)

    # Build Base Topology
    Topology = TopologyDictionary(gapps, model_mrid)
    network = NetworkModel(gapps)
    network.build_equip_dicts(model_mrid, Topology)
    EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine']
    Topology.build_linknet(EqTypes)
    Topology.update_switches()
    Topology.build_feeder_islands()

    # Query for switch position measurement mRIDs
    request = {"modelId": model_mrid,
               "requestType": "QUERY_OBJECT_MEASUREMENTS",
               "resultFormat": "JSON",
               "objectType": "LoadBreakSwitch"}
    meas_query = gapps.get_response(t.REQUEST_POWERGRID_DATA,request,timeout=15)

    # Iterate through measurements to identify switch position measurements
    SwitchMeasDict={}
    for measurement in meas_query["data"]:
        if measurement["type"] == "Pos":
            measid = measurement["measid"]
            SwitchMeasDict[measid] = {}
            SwitchMeasDict[measid]['eqtype'] = measurement['eqtype']
            SwitchMeasDict[measid]['eqid'] = measurement["eqid"]
            
    TopoService = TopologyService(gapps, Topology, simulation_id, model_mrid, SwitchMeasDict)
    gapps.subscribe(sim_output_topic, TopoService)
    while True:
        time.sleep(0.1)
        
if __name__ == "__main__":
    _main()
    