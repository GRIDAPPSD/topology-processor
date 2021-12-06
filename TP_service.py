# -------------------------------------------------------------------------------
# Copyright (c) 2021, Battelle Memorial Institute All rights reserved.
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
Created on Oct 20, 2021
@author: Alexander Anderson, Rohit Jiniswale, Poorva Sharma
"""

import argparse
from datetime import datetime
import json
import logging
import os
import math
import sys
import time
import topologyqueries,linkedlist,update_topology,spanning_tree

from gridappsd import GridAPPSD, DifferenceBuilder, utils, topics
from gridappsd.topics import simulation_input_topic, simulation_log_topic, simulation_output_topic

# Set environment variables - when developing, put environment variable in ~/.bashrc file or export in command line
# Set username and password
os.environ['GRIDAPPSD_USER'] = 'app_user'
os.environ['GRIDAPPSD_PASSWORD'] = '1234App'
global simulation_id
simulation_id='707758295'


class SimulationSubscriber(object):
    """ A simple class that handles publishing forward and reverse differences
    The object should be used as a callback from a GridAPPSD object so that the
    on_message function will get called each time a message from the simulator.  During
    the execution of on_meessage the `CapacitorToggler` object will publish a
    message to the simulation_input_topic with the forward and reverse difference specified.
    """

    def __init__(self, simulation_id, gapps_obj, measurement_dict, meas_eq_map):

        self.gapps = gapps_obj
        self.publish_to_topic = topics.service_output_topic('topologyprocessor',simulation_id)
        self.measurement_dict = measurement_dict
        self.meas_map = meas_eq_map
        self.measurement_value = {}
        self.processsed = False

    def on_message(self, headers, message):
        """ Handle incoming messages on the simulation_output_topic for the simulation_id
        Parameters
        ----------
        headers: dict
            A dictionary of headers that could be used to determine topic of origin and
            other attributes.
        message: object
            A data structure following the protocol defined in the message structure
            of ``GridAPPSD``.  Most message payloads will be serialized dictionaries, but that is
            not a requirement.
        """
        old_topo = False
        
        # Check if message received is simulation output message
        if "output" in headers["destination"]:
            timestamp = message["message"]["timestamp"]
            
            # Parse list of measurements
            for measurement in self.measurement_dict:
                position = message["message"]["measurements"][measurement]['value']
                eqid = self.meas_map[measurement]
                # Check if any switch positions have changed
                if SwitchDict[eqid]['open'] != int(position):
                    if position == 0:
                        print('Detected switch ', SwitchDict[eqid]['name'], ' has opened at time ', timestamp)
                    else:
                        print('Detected switch ', SwitchDict[eqid]['name'], ' has closed at time ', timestamp)
                    SwitchDict[eqid]['open'] = position
                    old_topo = True


            if old_topo:                            
                # Process Switch Topology - run at each switch change - merges topology nodes across closed switches
                [TerminalsDict,ConnNodeDict]=update_topology.topology_update(BaseConnDict,BaseTermDict,SwitchDict,SwitchKeys,TermList)

                # Build Spanning Tree from Xfmrs & DGs
                [Tree,TotalNodes]=spanning_tree.generate_spanning_tree(XfmrKeys, XfmrDict, ConnNodeDict, TerminalsDict, TermList, NodeList, DG_query)

                # Publish updated topology
                output = {}
                output['timestamp'] = timestamp
                output['ConnNodeDict'] = ConnNodeDict
                output['TopologyTree'] = Tree
                self.gapps.send(self.publish_to_topic, json.dumps(output))
                        

class Logger(object):
    
    def __init__(self, simulation_id, gridappsd_obj, sim_log_topic):
        self.simulationId = simulation_id
        self.gapps = gridappsd_obj
        self.sim_log_topic = sim_log_topic
        
    
    def log(self, logLevel, message, processStatus):
        t_now = datetime.utcnow()
        message = {
            "source": os.path.basename(__file__),
            "processId": self.simulationId,
            "timestamp": int(time.mktime(t_now.timetuple()))*1000,
            "processStatus": processStatus,
            "logMessage": message,
            "logLevel": logLevel,
            "storeToDb": True
            }
        self.gapps.send(self.sim_log_topic, json.dumps(message))
    
    
def _main():
    
      
    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_id",
                        help="Simulation id to use for responses on the message bus.")
    parser.add_argument("request",
                        help="Simulation Request")
    # These are now set through the docker container interface via env variables or defaulted to
    # proper values.
    #
    # parser.add_argument("-u", "--user", default="system",
    #                     help="The username to authenticate with the message bus.")
    # parser.add_argument("-p", "--password", default="manager",
    #                     help="The password to authenticate with the message bus.")
    # parser.add_argument("-a", "--address", default="127.0.0.1",
    #                     help="tcp address of the mesage bus.")
    # parser.add_argument("--port", default=61613, type=int,
    #                     help="the stomp port on the message bus.")
    #
    #opts = parser.parse_args()
    
    global BaseConnDict,BaseTermDict,TermList, NodeList
    global XfmrKeys,XfmrDict,SwitchKeys,SwitchDict,DG_query
    
    
    sim_output_topic = simulation_output_topic(simulation_id)
    sim_input_topic = simulation_input_topic(simulation_id)
    sim_log_topic = simulation_log_topic(simulation_id)
    #sim_request = json.loads(opts.request.replace("\'",""))
    #model_mrid = sim_request["power_system_config"]["Line_name"]
    #model_mrid = "_C125761E-9C21-4CA9-9271-B168150DE276" #ieee13training
    model_mrid = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA" #final9500node
    #model_mrid = "_AAE94E4A-2465-6F5E-37B1-3E72183A4E44" #test9500
    #model_mrid = "_5B816B93-7A5F-B64C-8460-47C17D6E4B0F" #ieee13assets
    #model_mrid="_C1C3E687-6FFD-C753-582B-632A27E28507" # IEEE 123
    gapps = GridAPPSD(simulation_id)
    logger = Logger(simulation_id, gapps, sim_log_topic)

    assert gapps.connected

    # Query for ACLineSegment, Transformerend, Switches, Breakers, Reclosers, Fuses, Sectionalisers,SynchronousMachine,TopologicalNode
    topologyqueries.getallqueries(gapps,model_mrid)
    Line_query=topologyqueries.Line_query
    XfmrDict=topologyqueries.XfmrDict
    XfmrKeys=topologyqueries.XfmrKeys
    SwitchDict=topologyqueries.SwitchDict
    SwitchKeys=topologyqueries.SwitchKeys
    DG_query=topologyqueries.DG_query
    Node_query=topologyqueries.Node_query
    #print(Switch_query)
    
    # Build Linknet Lists from ACLineSegment,Transformers,DGs and Nodes
    [ConnNodeDict,TerminalsDict,TermList,NodeList]=linkedlist.build_linked_list(Line_query,XfmrDict,XfmrKeys,DG_query,Node_query)

    # Stash a copy of base dictionary
    BaseConnDict = json.dumps(ConnNodeDict)
    BaseTermDict = json.dumps(TerminalsDict)

    # Process Switch Topology - run at each switch change - merges topology nodes across closed switches

    [TerminalsDict,ConnNodeDict]=update_topology.topology_update(BaseConnDict,BaseTermDict,SwitchDict,SwitchKeys,TermList)

    # Build Spanning Tree from Xfmrs & DGs

    [Tree,TotalNodes]=spanning_tree.generate_spanning_tree(XfmrKeys,XfmrDict,ConnNodeDict,TerminalsDict,TermList,NodeList,DG_query)

    try: 
          
        equipment_dict = {}
        measurement_dict = {}
        meas_map = {}
        #Query for switch position measurement mRIDs
        request = {"modelId": model_mrid,
                   "requestType": "QUERY_OBJECT_MEASUREMENTS",
                   "resultFormat": "JSON",
                   "objectType": "LoadBreakSwitch"
                   }
        
        response = gapps.get_response("goss.gridappsd.process.request.data.powergridmodel",request,timeout=15)
        for measurement in response["data"]:
            if measurement["type"] == "Pos":
                measid = measurement["measid"]
                measurement_dict[measid] = measurement
                meas_map[measid] = measurement["eqid"]
                SwitchDict[measurement["eqid"]]["measid"] = measid
    
        #print(capacitors_meas_dict)
        #print(switches_meas_dict)
        meas_eq_map = {}
        eq_phases_map = {}
        for measurement in measurement_dict:
            for equipment in equipment_dict:
                if equipment == measurement_dict[measurement]['eqid']:
                    if equipment in eq_phases_map:
                        eq_phases_map[equipment] = eq_phases_map[equipment] + measurement_dict[measurement]['phases']
                    else:
                        eq_phases_map[equipment] = measurement_dict[measurement]['phases']
                    meas_eq_map[measurement] = equipment
        

    except Exception as e:
        logger.log("ERROR", e , "ERROR")
    #logger.log("DEBUG","Subscribing to simulation","RUNNING")
    subscriber = SimulationSubscriber(simulation_id, gapps, measurement_dict, meas_map)
    gapps.subscribe(sim_input_topic, subscriber)
    gapps.subscribe(sim_output_topic, subscriber)
    #logger.log("DEBUG","Service Initialized","RUNNING")
    while True:
        time.sleep(0.1)


if __name__ == "__main__":
    _main()