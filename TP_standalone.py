import argparse
from datetime import datetime
import json
import logging
import os
import math
import sys
import time as _time
import topologyqueries,linkedlist,update_topology,spanning_tree

from gridappsd import GridAPPSD, DifferenceBuilder, utils, topics as t
from gridappsd.topics import simulation_input_topic, simulation_log_topic, simulation_output_topic


def _main():
    
    # REQUIRED ARGUMENTS - MODEL MRID
    # OPTIONAL ARGUMENTS - SIMULATION ID AND TIMESTAMP FOR TOPOLOGY SNAPSHOT
    
    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_id",
                        help="Simulation id to use for responses on the message bus.")
    parser.add_argument("request",
                        help="Simulation Request")
    
    #########
    # REPLACE THIS SECTION WITH INPUT ARGUMENTS
    
    #model_mrid = sim_request["power_system_config"]["Line_name"]
    #model_mrid = "_C125761E-9C21-4CA9-9271-B168150DE276" #ieee13training
    model_mrid = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA" #final9500node
    #model_mrid = "_AAE94E4A-2465-6F5E-37B1-3E72183A4E44" #test9500
    #model_mrid = "_5B816B93-7A5F-B64C-8460-47C17D6E4B0F" #ieee13assets
    #model_mrid="_C1C3E687-6FFD-C753-582B-632A27E28507" # IEEE 123
    
    import Run9500NodeDemo as r
    simulation_id = r.simulation.simulation_id
    requestedTime=1570041125
    _time.sleep(15)
    print(simulation_id)
    
    
    
    ######
    
    global BaseConnDict,BaseTermDict,TermList, NodeList
    global XfmrKeys,XfmrDict,SwitchKeys,SwitchDict,DG_query
    
    
    gapps = GridAPPSD(simulation_id)
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

    
    # Build Linknet Lists from ACLineSegment,Transformers,DGs and Nodes
    [ConnNodeDict,TerminalsDict,TermList,NodeList]=linkedlist.build_linked_list(Line_query,XfmrDict,XfmrKeys,DG_query,Node_query)

    # Stash a copy of base dictionary
    BaseConnDict = json.dumps(ConnNodeDict)
    BaseTermDict = json.dumps(TerminalsDict)
    

    #IF SIMULATION ID IS SPECIFIED, GET TOPOLOGY FOR REQUESTED TIME FOR SPECIFIED TIMESTAMP

    equipment_dict = {}
    measurement_dict = {}
    meas_map={}

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
        
        ####### End of if simulation id is specified section #######
        
    # Process Switch Topology - run at each switch change - merges topology nodes across closed switches

    [TerminalsDict,ConnNodeDict]=update_topology.topology_update(BaseConnDict,BaseTermDict,SwitchDict,SwitchKeys,TermList)

    # Build Spanning Tree from Xfmrs & DGs

    [Tree,TotalNodes]=spanning_tree.generate_spanning_tree(XfmrKeys,XfmrDict,ConnNodeDict,TerminalsDict,TermList,NodeList,DG_query)
    
if __name__ == "__main__":
    _main()