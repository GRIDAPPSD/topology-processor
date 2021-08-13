# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
"""
Created on July 15, 2021

@author: Gary Black, Rohit Jinsiwale
"""""

import sys
import os
import argparse
import json
import importlib
import numpy as np

from gridappsd import GridAPPSD

class Lineinfo:
    def __init__(self, name, bus1,bus2,id_line,term1,term2,node1,node2,phases,lineindex):
        self.name=name
        self.bus1=bus1
        self.bus2=bus2
        self.id_line=id_line
        self.term1=term1
        self.term2=term2
        self.node1=node1
        self.node2=node2
        self.phases=phases
        self.lineindex=lineindex

class ConnectivityNodes:
    def __init__(self,connectivity_node,name,node_index,list_t):
        self.connectivity_node=connectivity_node
        self.name=name
        self.node_index=node_index
        self.list_t=list_t

class Terminals:
    def __init__(self,terminal,term_id,next_ent,far,phases):
        self.terminal=terminal
        self.term_id=term_id
        self.next_ent=next_ent
        self.far=far
        self.phases=phases

def start(log_file, feeder_mrid, model_api_topic):
    global logfile
    logfile = log_file

    SPARQLManager = getattr(importlib.import_module('shared.sparql'), 'SPARQLManager')

    gapps = GridAPPSD()

    sparql_mgr = SPARQLManager(gapps, feeder_mrid, model_api_topic)

    bindings = sparql_mgr.nomv_query()
    '''print(bindings)'''



def AClinequery(log_file, feeder_mrid, model_api_topic):
    
    SPARQLManager = getattr(importlib.import_module('shared.sparql'), 'SPARQLManager')

    gapps = GridAPPSD()
    sparql_mgr = SPARQLManager(gapps, feeder_mrid, model_api_topic)
    Query_lines="""
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus1 ?bus2 ?id ?term1 ?term2 ?node1 ?node2 (group_concat(distinct ?phs;separator="") as ?phases) WHERE {
    SELECT ?name ?bus1 ?bus2 ?phs ?id ?term1 ?term2 ?node1 ?node2 WHERE {
    VALUES ?fdrid {"%s"}  # 13 bus
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?s r:type c:ACLineSegment.
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?id.
    ?t1 c:Terminal.ConductingEquipment ?s.
    ?t1 c:ACDCTerminal.sequenceNumber "1".
    ?t1 c:Terminal.ConnectivityNode ?cn1. 
    ?cn1 c:IdentifiedObject.name ?bus1.
    ?t2 c:Terminal.ConductingEquipment ?s.
    ?t2 c:ACDCTerminal.sequenceNumber "2".
    ?t2 c:Terminal.ConnectivityNode ?cn2. 
    ?cn2 c:IdentifiedObject.name ?bus2.
        bind(strafter(str(?t1), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?term1) 
        bind(strafter(str(?t2), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?term2)
        bind(strafter(str(?cn1), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?node1)
        bind(strafter(str(?cn2), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?node2)
            OPTIONAL {?acp c:ACLineSegmentPhase.ACLineSegment ?s.
            ?acp c:ACLineSegmentPhase.phase ?phsraw.
            bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    
    } ORDER BY ?name ?phs
    }
    GROUP BY ?name ?bus1 ?bus2 ?id ?term1 ?term2 ?node1 ?node2
    ORDER BY ?name
    """%sparql_mgr.feeder_mrid
    results=sparql_mgr.gad.query_data(Query_lines)
    bindings = results['data']['results']['bindings']
    '''print(results)
    print("\n")
    print(bindings[0])'''
    return bindings

def _main():
    # for loading modules
    if (os.path.isdir('shared')):
        sys.path.append('.')
    elif (os.path.isdir('../shared')):
        sys.path.append('..')

    parser = argparse.ArgumentParser()
    parser.add_argument("--request", help="Simulation Request")

    opts = parser.parse_args()
    sim_request = json.loads(opts.request.replace("\'",""))
    feeder_mrid = sim_request["power_system_config"]["Line_name"]

    model_api_topic = "goss.gridappsd.process.request.data.powergridmodel"
    log_file = open('topology_processor.log', 'w')

    start(log_file, feeder_mrid, model_api_topic)
    Line_query=AClinequery(log_file, feeder_mrid, model_api_topic)
    # parse each line to estbalish connectivty nodes list

    Lineinfotable=[]
    ConnectivityNodeList=[]
    TerminalsList=[]
    File_connectivitynode=open('Debugnodes.txt','w')
    File_terminals=open('DebugTerminals.txt','w')
    #print(Line_query[0]['bus1']['value'])
    for i in range(len(Line_query)):
        name=Line_query[i]['name']['value']
        bus1=Line_query[i]['bus1']['value']
        bus2=Line_query[i]['bus2']['value']
        id_line=Line_query[i]['id']['value']
        term1=Line_query[i]['term1']['value']
        term2=Line_query[i]['term2']['value']
        node1=Line_query[i]['node1']['value']
        node2=Line_query[i]['node2']['value']
        phases=Line_query[i]['phases']['value']
        lineindex=i
        lineobject=Lineinfo(name,bus1,bus2,id_line,term1,term2,node1,node2,phases,lineindex)
        Lineinfotable.append(lineobject)
        print(Lineinfotable[i].name,' ',Lineinfotable[i].bus1,' ',Lineinfotable[i].bus2,' ',Lineinfotable[i].id_line,' ')
        print(Lineinfotable[i].term1,' ',Lineinfotable[i].term2,' ',Lineinfotable[i].node1,' ',Lineinfotable[i].node2,' ')
        print(Lineinfotable[i].phases,' ',Lineinfotable[i].lineindex)
        print('\n')
        
    # Start Line by line process to build linked list
    for i in range(len(Lineinfotable)):
        if(i==0):
            N1=ConnectivityNodes(Lineinfotable[i].node1,Lineinfotable[i].bus1,1,0)
            N2=ConnectivityNodes(Lineinfotable[i].node2,Lineinfotable[i].bus2,2,0)
            ConnectivityNodeList.append(N1)
            ConnectivityNodeList.append(N2)
            index1=0
            index2=1
        else:
            #write code to check if node exists and append
            node1name=Lineinfotable[i].node1
            node2name=Lineinfotable[i].node2
            index1=-1
            index2=-1
            for j in range(len(ConnectivityNodeList)):
                # check if node1 or node 2 alreaydy exist and record indices
                if(node1name==ConnectivityNodeList[j].connectivity_node):
                    index1=j
                if(node2name==ConnectivityNodeList[j].connectivity_node):
                    index2=j
            # check if indices are still -1 and decide which ones to append
            if(index1==-1 and index2>-1):
                index1=len(ConnectivityNodeList)
                N1=ConnectivityNodes(Lineinfotable[i].node1,Lineinfotable[i].bus1,index1+1,0)
                ConnectivityNodeList.append(N1)
            if(index2==-1 and index1>-1):
                index2=len(ConnectivityNodeList)
                N2=ConnectivityNodes(Lineinfotable[i].node2,Lineinfotable[i].bus2,index2+1,0)
                ConnectivityNodeList.append(N2)
            if(index1==-1 and index2==-1):
                index1=len(ConnectivityNodeList)
                index2=len(ConnectivityNodeList)+1
                N1=ConnectivityNodes(Lineinfotable[i].node1,Lineinfotable[i].bus1,index1+1,0)
                N2=ConnectivityNodes(Lineinfotable[i].node2,Lineinfotable[i].bus2,index2+1,0)
                ConnectivityNodeList.append(N1)
                ConnectivityNodeList.append(N2)
        # Fill terminal table (no aliasing so just append)
        T1=Terminals(Lineinfotable[i].term1,2*i+1,0,0,Lineinfotable[i].phases)
        T2=Terminals(Lineinfotable[i].term2,2*i+2,0,0,Lineinfotable[i].phases)
        TerminalsList.append(T1)
        TerminalsList.append(T2)
        # identify relevent node indices in 
        # Start Linking process
        # 1. Move node list variables to terinal next
        lengthofTerminalslist=len(TerminalsList)
        TerminalsList[lengthofTerminalslist-2].next_ent=ConnectivityNodeList[index1].list_t
        TerminalsList[lengthofTerminalslist-1].next_ent=ConnectivityNodeList[index2].list_t
        TerminalsList[lengthofTerminalslist-2].far=ConnectivityNodeList[index2].node_index
        TerminalsList[lengthofTerminalslist-1].far=ConnectivityNodeList[index1].node_index
        ConnectivityNodeList[index1].list_t=TerminalsList[lengthofTerminalslist-2].term_id
        ConnectivityNodeList[index2].list_t=TerminalsList[lengthofTerminalslist-1].term_id
        
        for k in range(len(ConnectivityNodeList)):
            str1=ConnectivityNodeList[k].connectivity_node+' '+ConnectivityNodeList[k].name+' '+str(ConnectivityNodeList[k].node_index)+' '+str(ConnectivityNodeList[k].list_t)
            File_connectivitynode.write(str1+'\n')
        File_connectivitynode.write('\n')
        File_connectivitynode.write('\n')
        for k in range(len(TerminalsList)):
            str2=TerminalsList[k].terminal+' '+str(TerminalsList[k].term_id)+' '+str(TerminalsList[k].next_ent)+' '+str(TerminalsList[k].far)+' '+str(TerminalsList[k].phases)
            File_terminals.write(str2+'\n')
        File_terminals.write('\n')
        File_terminals.write('\n')
    File_connectivitynode.close()
    File_terminals.close()


    
        

        
    
    



if __name__ == "__main__":
    _main()

