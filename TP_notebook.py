import time, json


StartTime = time.process_time()

# Establish connection to GridAPPS-D Platform:
from gridappsd import GridAPPSD


# Set environment variables - when developing, put environment variable in ~/.bashrc file or export in command line
# export GRIDAPPSD_USER=system
# export GRIDAPPSD_PASSWORD=manager

import os # Set username and password
os.environ['GRIDAPPSD_USER'] = 'tutorial_user'
os.environ['GRIDAPPSD_PASSWORD'] = '12345!'

# Connect to GridAPPS-D Platform
gapps = GridAPPSD()
assert gapps.connected

print("Established connection with GriAPPS-D in ", time.process_time() - StartTime, "seconds")

#model_mrid = "_C125761E-9C21-4CA9-9271-B168150DE276" #ieee13training
model_mrid = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA" #final9500node
#model_mrid = "_5B816B93-7A5F-B64C-8460-47C17D6E4B0F" #ieee13assets

#RUN SPARQL QUERIES - MOVE TO SPARQL_QUERIES.PY

StartTime = time.process_time()

QueryLines="""
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus1 ?bus2 ?id ?tname1 ?term1 ?tname2 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2 (group_concat(distinct ?phs;separator="") as ?phases) WHERE {
    SELECT ?name ?bus1 ?bus2 ?phs ?id ?tname1 ?term1 ?tname2 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2 WHERE {
    VALUES ?fdrid {"%s"}  
    ?fdr c:IdentifiedObject.mRID ?fdrid.
    ?s r:type c:ACLineSegment.
    ?s c:Equipment.EquipmentContainer ?fdr.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?id.
    ?t1 c:Terminal.ConductingEquipment ?s.
    ?t1 c:ACDCTerminal.sequenceNumber "1".
    ?t1 c:Terminal.ConnectivityNode ?cn1. 
    ?t1 c:IdentifiedObject.name ?tname1.
    ?cn1 c:IdentifiedObject.name ?bus1.
    ?cn1 c:ConnectivityNode.TopologicalNode ?tp1.
    ?t2 c:Terminal.ConductingEquipment ?s.
    ?t2 c:ACDCTerminal.sequenceNumber "2".
    ?t2 c:Terminal.ConnectivityNode ?cn2. 
    ?t2 c:IdentifiedObject.name ?tname2.
    ?cn2 c:ConnectivityNode.TopologicalNode ?tp2.
    ?cn2 c:IdentifiedObject.name ?bus2.

    bind(strafter(str(?t),"#") as ?tid).
        bind(strafter(str(?t1), "#") as ?term1) 
        bind(strafter(str(?t2), "#") as ?term2)
        bind(strafter(str(?cn1), "#") as ?node1)
        bind(strafter(str(?cn2), "#") as ?node2)
        bind(strafter(str(?tp1), "#") as ?tpnode1)
        bind(strafter(str(?tp2), "#") as ?tpnode2)
            OPTIONAL {?acp c:ACLineSegmentPhase.ACLineSegment ?s.
            ?acp c:ACLineSegmentPhase.phase ?phsraw.
            bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    
    } ORDER BY ?name ?phs
    }
    GROUP BY ?name ?bus1 ?bus2 ?id ?tname1 ?term1 ?tname2 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2
    ORDER BY ?name
    """%model_mrid

results = gapps.query_data(query = QueryLines, timeout = 60)
Line_query = results['data']['results']['bindings']

QueryXfmrs="""
# list all the terminals connected to a TransformerEnd for CIMWriter
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/CIM100#>
SELECT ?endclass ?eqid ?endid ?tname ?tid ?bus ?cnid ?tpid ?seq ?phs ?ratedu WHERE {
 VALUES ?fdrid {"%s"} 
 ?fdr c:IdentifiedObject.mRID ?fdrid.
 {?pxf c:Equipment.EquipmentContainer ?fdr.
  ?end c:PowerTransformerEnd.PowerTransformer ?pxf.
  ?end c:PowerTransformerEnd.ratedU ?ratedu.
  ?pxf c:IdentifiedObject.mRID ?eqid.
}
  UNION
 {?tank c:Equipment.EquipmentContainer ?fdr.
  ?end c:TransformerTankEnd.TransformerTank ?tank.
  ?tank c:IdentifiedObject.mRID ?eqid.
  ?end c:TransformerTankEnd.phases ?ph.
 }
 ?end c:TransformerEnd.Terminal ?t.

 ?t c:Terminal.ConnectivityNode ?cn. 
 ?t c:IdentifiedObject.name ?tname.
  
 ?cn c:ConnectivityNode.TopologicalNode ?tp.
 ?cn c:IdentifiedObject.name ?bus.
 ?t c:ACDCTerminal.sequenceNumber ?seq.
 bind(strafter(str(?end),"#") as ?endid).
 bind(strafter(str(?t),"#") as ?tid).
 bind(strafter(str(?cn),"#") as ?cnid).
 bind(strafter(str(?tp),"#") as ?tpid).
 bind(strafter(str(?ph),"e.") as ?phs).
 ?end a ?classraw.
 bind(strafter(str(?classraw),"CIM100#") as ?endclass)
}
ORDER by ?endclass ?eqid ?tname ?endid ?bus ?cnid ?tpid ?seq ?phs ?ratedu
"""%model_mrid

results = gapps.query_data(query = QueryXfmrs, timeout = 60)
Xfmr_query = results['data']['results']['bindings']

QuerySwitches="""
# list nodes for Breakers, Reclosers, LoadBreakSwitches, Fuses, Sectionalisers in a selected feeder
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/CIM100#>
SELECT ?cimtype ?name ?id ?bus1 ?bus2 ?term1 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2 ?open (group_concat(distinct ?phs;separator="") as ?phases) WHERE {
  SELECT ?cimtype ?name ?id ?bus1 ?bus2 ?term1 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2 ?phs ?open WHERE {
 VALUES ?fdrid {"%s"}  # 13 bus
 VALUES ?cimraw {c:LoadBreakSwitch c:Recloser c:Breaker c:Fuse c:Sectionaliser}
 ?fdr c:IdentifiedObject.mRID ?fdrid.
 ?s r:type ?cimraw.
  bind(strafter(str(?cimraw),"#") as ?cimtype)
 ?s c:Equipment.EquipmentContainer ?fdr.
 ?s c:IdentifiedObject.name ?name.
 ?s c:IdentifiedObject.mRID ?id.
 ?s c:Switch.normalOpen ?open.
 ?t1 c:Terminal.ConductingEquipment ?s.
 ?t1 c:ACDCTerminal.sequenceNumber "1".
 ?t1 c:Terminal.ConnectivityNode ?cn1. 
 ?cn1 c:ConnectivityNode.TopologicalNode ?tp1.
 ?cn1 c:IdentifiedObject.name ?bus1.
 ?t2 c:Terminal.ConductingEquipment ?s.
 ?t2 c:ACDCTerminal.sequenceNumber "2".
 ?t2 c:Terminal.ConnectivityNode ?cn2. 
 ?cn2 c:ConnectivityNode.TopologicalNode ?tp2.
 ?cn2 c:IdentifiedObject.name ?bus2
    OPTIONAL {?swp c:SwitchPhase.Switch ?s.
    ?swp c:SwitchPhase.phaseSide1 ?phsraw.
    bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
    bind(strafter(str(?t1), "#") as ?term1) 
    bind(strafter(str(?t2), "#") as ?term2)
    bind(strafter(str(?cn1), "#") as ?node1)
    bind(strafter(str(?cn2), "#") as ?node2)
    bind(strafter(str(?tp1), "#") as ?tpnode1)
    bind(strafter(str(?tp2), "#") as ?tpnode2)
 } ORDER BY ?name ?phs
}
GROUP BY ?cimtype ?name ?id ?bus1 ?bus2 ?term1 ?term2 ?node1 ?node2 ?tpnode1 ?tpnode2 ?open
ORDER BY ?cimtype ?name
"""%model_mrid

results = gapps.query_data(query = QuerySwitches, timeout = 60)
Switch_query = results['data']['results']['bindings']

QueryDGs="""
# SynchronousMachine - DistSyncMachine
# SynchronousMachine - DistSyncMachine
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/CIM100#>
SELECT ?name ?eqid ?term ?bus ?node ?tpid WHERE {
   VALUES ?fdrid {"%s"}  # 123 bus with PV
 ?s r:type c:SynchronousMachine.
 ?s c:IdentifiedObject.name ?name.
 ?s c:Equipment.EquipmentContainer ?fdr.
 ?fdr c:IdentifiedObject.mRID ?fdrid. 
 bind(strafter(str(?s),"#_") as ?eqid).
 OPTIONAL {?smp c:SynchronousMachinePhase.SynchronousMachine ?s.
 ?smp c:SynchronousMachinePhase.phase ?phsraw.
   bind(strafter(str(?phsraw),"SinglePhaseKind.") as ?phs) }
 ?t c:Terminal.ConductingEquipment ?s.
 ?t c:Terminal.ConnectivityNode ?cn. 
 ?cn c:ConnectivityNode.TopologicalNode ?tp.
 ?cn c:IdentifiedObject.name ?bus
 bind(strafter(str(?cn),"#") as ?node).
 bind(strafter(str(?s),"#") as ?term).
 bind(strafter(str(?tp),"#") as ?tpid)
}
GROUP by ?name ?eqid ?term ?bus ?node ?tpid
ORDER by ?name
"""%model_mrid

results = gapps.query_data(query = QueryDGs, timeout = 60)
DG_query = results['data']['results']['bindings']

QueryNodes="""
# list all the connectivity node, topology node, base voltages
PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX c:  <http://iec.ch/TC57/CIM100#>
SELECT DISTINCT ?busname ?cnid ?tpnid ?nomv WHERE {
VALUES ?fdrid {"%s"}  # 13 bus
 ?fdr c:IdentifiedObject.mRID ?fdrid.
 ?bus c:ConnectivityNode.ConnectivityNodeContainer ?fdr.
 ?bus c:ConnectivityNode.TopologicalNode ?tp.
 ?bus r:type c:ConnectivityNode.
 ?bus c:IdentifiedObject.name ?busname.
 ?bus c:IdentifiedObject.mRID ?cnid.
 ?fdr c:IdentifiedObject.name ?feeder.
 ?trm c:Terminal.ConnectivityNode ?bus.
 ?trm c:Terminal.ConductingEquipment ?ce.
 ?ce  c:ConductingEquipment.BaseVoltage ?bv.
 ?bv  c:BaseVoltage.nominalVoltage ?nomv.
 bind(strafter(str(?tp), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?tpnid)
}
ORDER by ?busname ?tpnid ?nomv
"""%model_mrid

results = gapps.query_data(query = QueryNodes, timeout = 60)
Node_query = results['data']['results']['bindings']

print("Queried for all lines, transformers, switches, and DGs", time.process_time() - StartTime, "seconds")


# BUILD LINKNET STRUCTURE - MOVE TO LINKNET.PY

index=0
ConnNodeDict = {}
TerminalsDict = {}
NodeList = []
TermList = []
StartTime = time.process_time()

for i1 in range(len(Line_query)):
    name=Line_query[i1]['name']['value']
    bus1=Line_query[i1]['bus1']['value']
    bus2=Line_query[i1]['bus2']['value']
    id_line=Line_query[i1]['id']['value']
    tname1=Line_query[i1]['tname1']['value']
    tname2=Line_query[i1]['tname2']['value']
    term1=Line_query[i1]['term1']['value']
    term2=Line_query[i1]['term2']['value']
    node1=Line_query[i1]['node1']['value']
    node2=Line_query[i1]['node2']['value']
    phases=Line_query[i1]['phases']['value']
    tpnode1=Line_query[i1]['tpnode1']['value']
    tpnode2=Line_query[i1]['tpnode2']['value']
    
    # Create keys for new terminals
    TerminalsDict[term1] = {}
    TerminalsDict[term2] = {}
    TerminalsDict[term1]['term'] = 2*i1+1
    TerminalsDict[term2]['term'] = 2*i1+2
    TermList.append(term1)
    TermList.append(term2)
    #TerminalsDict[term1]['phases'] = phases
    #TerminalsDict[term2]['phases'] = phases
    
    # If node1 or node2 not in dict, create new keys
    if not node1 in ConnNodeDict.keys():
        ConnNodeDict[node1] = {}
        ConnNodeDict[node1]['name'] = bus1
        ConnNodeDict[node1]['node'] = index+1
        ConnNodeDict[node1]['list'] = 0
        ConnNodeDict[node1]['tpid'] = tpnode1
        index = index+1
        NodeList.append(node1)

    if not node2 in ConnNodeDict.keys(): 
        ConnNodeDict[node2] = {}
        ConnNodeDict[node2]['name'] = bus2
        ConnNodeDict[node2]['node'] = index+1
        ConnNodeDict[node2]['list'] = 0
        ConnNodeDict[node2]['tpid'] = tpnode2
        index = index+1
        NodeList.append(node2)
    
    # 1. Move node list variables to terinal next    
    TerminalsDict[term1]['name'] = tname1
    TerminalsDict[term2]['name'] = tname2
    TerminalsDict[term1]['bus'] = bus1
    TerminalsDict[term2]['bus'] = bus2
    TerminalsDict[term1]['next'] = ConnNodeDict[node1]['list']
    TerminalsDict[term2]['next'] = ConnNodeDict[node2]['list']

    # 2. Populate Terminal list far field with nodes
    TerminalsDict[term1]['far'] = ConnNodeDict[node2]['node']
    TerminalsDict[term2]['far'] = ConnNodeDict[node1]['node']
    
    # 3. Populate Connectivity nodes list with terminals
    ConnNodeDict[node1]['list'] = TerminalsDict[term1]['term']
    ConnNodeDict[node2]['list'] = TerminalsDict[term2]['term']
    
print("Processed ", i1, "line objects in ", time.process_time() - StartTime, "seconds")

Xfmr_dict={}
XfmrKeys=[]
i1=i1+1

StartTime = time.process_time()

# Build dictionary of FROM-TO nodes for all transformers
for i2 in range(len(Xfmr_query)):
    eqid=Xfmr_query[i2]['eqid']['value']
    
    seq=Xfmr_query[i2]['seq']['value']
    if eqid not in Xfmr_dict:
        Xfmr_dict[eqid]={}
        XfmrKeys.append(eqid)
    Xfmr_dict[eqid]['bus']=Xfmr_query[i2]['bus']['value']
    
    # Identify terminal sequence and create keys for new terminals
    if seq == '1' or seq == 1:
        # Primary winding
        Xfmr_dict[eqid]['bus1']=Xfmr_query[i2]['bus']['value']
        Xfmr_dict[eqid]['term1']=Xfmr_query[i2]['tid']['value']
        Xfmr_dict[eqid]['node1']=Xfmr_query[i2]['cnid']['value']
        Xfmr_dict[eqid]['tpnode1']=Xfmr_query[i2]['tpid']['value']
        Xfmr_dict[eqid]['tname1']=Xfmr_query[i2]['tname']['value']
        if 'ratedu' in Xfmr_query[i2]: Xfmr_dict[eqid]['volt1']=int(float(Xfmr_query[i2]['ratedu']['value']))
        else: Xfmr_dict[eqid]['volt1']=0
        if 'phs' in Xfmr_query[i2]: Xfmr_dict[eqid]['phase1']=Xfmr_query[i2]['phs']['value'] 
        else: Xfmr_dict[eqid]['phase1']={}
            
    elif seq == '2' or seq == 2:
        Xfmr_dict[eqid]['bus2']=Xfmr_query[i2]['bus']['value']
        Xfmr_dict[eqid]['term2']=Xfmr_query[i2]['tid']['value']
        Xfmr_dict[eqid]['node2']=Xfmr_query[i2]['cnid']['value']
        Xfmr_dict[eqid]['tpnode2']=Xfmr_query[i2]['tpid']['value']
        Xfmr_dict[eqid]['tname2']=Xfmr_query[i2]['tname']['value']
        if 'ratedu' in Xfmr_query[i2]: Xfmr_dict[eqid]['volt2']=int(float(Xfmr_query[i2]['ratedu']['value']))
        else: Xfmr_dict[eqid]['volt2']=0
        if 'phs' in Xfmr_query[i2]: Xfmr_dict[eqid]['phase2']=Xfmr_query[i2]['phs']['value'] 
        else: Xfmr_dict[eqid]['phase2']={}
        
    elif seq == '3' or seq == 3:
        Xfmr_dict[eqid]['bus3']=Xfmr_query[i2]['bus']['value']
        Xfmr_dict[eqid]['term3']=Xfmr_query[i2]['tid']['value']
        Xfmr_dict[eqid]['node3']=Xfmr_query[i2]['cnid']['value']
        Xfmr_dict[eqid]['tpnode3']=Xfmr_query[i2]['tpid']['value']
        Xfmr_dict[eqid]['tname3']=Xfmr_query[i2]['tname']['value']
        if 'ratedu' in Xfmr_query[i2]: Xfmr_dict[eqid]['volt3']=int(float(Xfmr_query[i2]['ratedu']['value']))
        else: Xfmr_dict[eqid]['volt3']=0
        if 'phs' in Xfmr_query[i2]: Xfmr_dict[eqid]['phase3']=Xfmr_query[i2]['phs']['value'] 
        else: Xfmr_dict[eqid]['phase3']={}
    else:
        raise ValueError('Unsupported transformer sequence value ', seq)
   

for i3 in range(len(XfmrKeys)):
    
    bus1=Xfmr_dict[XfmrKeys[i3]]['bus1']
    bus2=Xfmr_dict[XfmrKeys[i3]]['bus2']
    term1=Xfmr_dict[XfmrKeys[i3]]['term1']
    term2=Xfmr_dict[XfmrKeys[i3]]['term2']
    tname1=Xfmr_dict[XfmrKeys[i3]]['tname1']
    tname2=Xfmr_dict[XfmrKeys[i3]]['tname2']
    node1=Xfmr_dict[XfmrKeys[i3]]['node1']
    node2=Xfmr_dict[XfmrKeys[i3]]['node2']
    tpnode1=Xfmr_dict[XfmrKeys[i3]]['tpnode1']
    tpnode2=Xfmr_dict[XfmrKeys[i3]]['tpnode2']
    
    # THIS CODE IS EXACT SAME AS ABOVE FOR LINES, COULD PUT INTO FUNCTION OR CLASS THAT CAN BE CALLED
    
    # Create keys for new terminals
    TerminalsDict[term1] = {}
    TerminalsDict[term2] = {}
    TerminalsDict[term1]['term'] = 2*(i3+i1)+1 #updated index, need to add to end of dict
    TerminalsDict[term2]['term'] = 2*(i3+i1)+2
    TermList.append(term1)
    TermList.append(term2)
    #TerminalsDict[term1]['phases'] = phases
    #TerminalsDict[term2]['phases'] = phases
    
    # If node1 or node2 not in dict, create new keys
    if not node1 in ConnNodeDict.keys():
        ConnNodeDict[node1] = {}
        ConnNodeDict[node1]['name'] = bus1
        ConnNodeDict[node1]['node'] = index+1
        ConnNodeDict[node1]['list'] = 0
        ConnNodeDict[node1]['tpid'] = tpnode1
        index = index+1
        NodeList.append(node1)

    if not node2 in ConnNodeDict.keys(): 
        ConnNodeDict[node2] = {}
        ConnNodeDict[node2]['name'] = bus2
        ConnNodeDict[node2]['node'] = index+1
        ConnNodeDict[node2]['list'] = 0
        ConnNodeDict[node2]['tpid'] = tpnode2
        index = index+1
        NodeList.append(node2)
    
    # 1. Move node list variables to terinal next    
    TerminalsDict[term1]['name'] = tname1
    TerminalsDict[term2]['name'] = tname2
    TerminalsDict[term1]['bus'] = bus1
    TerminalsDict[term2]['bus'] = bus2
    TerminalsDict[term1]['next'] = ConnNodeDict[node1]['list']
    TerminalsDict[term2]['next'] = ConnNodeDict[node2]['list']

    # 2. Populate Terminal list far field with nodes
    TerminalsDict[term1]['far'] = ConnNodeDict[node2]['node']
    TerminalsDict[term2]['far'] = ConnNodeDict[node1]['node']
    
    # 3. Populate Connectivity nodes list with terminals
    ConnNodeDict[node1]['list'] = TerminalsDict[term1]['term']
    ConnNodeDict[node2]['list'] = TerminalsDict[term2]['term']
    
    #NEED TO INSERT LOGIC TO HANDLE THREE-WINDING SUBSTATION XFMR
    
print("Processed ", i2, "transformer objects in ", time.process_time() - StartTime, "seconds")


StartTime = time.process_time()

for i4 in range(len(DG_query)):
    node=DG_query[i4]['node']['value']
    term=DG_query[i4]['term']['value']
    


    if node not in ConnNodeDict.keys():
        
        TerminalsDict[term] = {}
        TerminalsDict[term]['term'] = i4+2*(i3+i1+1)+1 #updated index, need to add to end of dict
        TerminalsDict[term]['next'] = 0
        TerminalsDict[term]['far'] = index+1
        TerminalsDict[term]['name'] = DG_query[i4]['bus']['value']
        TermList.append(term)
        
        ConnNodeDict[node] = {}
        ConnNodeDict[node]['name'] = DG_query[i4]['bus']['value']
        ConnNodeDict[node]['node'] = index+1
        ConnNodeDict[node]['list'] = TerminalsDict[term]['term']
        ConnNodeDict[node]['tpid'] = DG_query[i4]['tpid']['value']
        index = index+1
        NodeList.append(node)
        
print("Processed ", i4, "generator objects in ", time.process_time() - StartTime, "seconds")

StartTime = time.process_time()
old_index = index
for i4 in range(len(Node_query)):
    node=Node_query[i4]['cnid']['value']

    if node not in ConnNodeDict.keys():
        ConnNodeDict[node] = {}
        ConnNodeDict[node]['name'] = Node_query[i4]['busname']['value']
        ConnNodeDict[node]['node'] = index+1
        ConnNodeDict[node]['list'] = 0
        ConnNodeDict[node]['tpid'] = Node_query[i4]['tpnid']['value']
        index = index+1
        NodeList.append(node1)
        
print("Processed ", index-old_index, "missing nodes in ", time.process_time() - StartTime, "seconds")


# Stash a copy of base dictionary
BaseConnDict = json.dumps(ConnNodeDict)
BaseTermDict = json.dumps(TerminalsDict)

# Pull base topology Dictionary
ConnNodeDict = json.loads(BaseConnDict)
TerminalsDict = json.loads(BaseTermDict)

StartTime = time.process_time()

for i5 in range(len(Switch_query)):
    #bus1=Switch_query[i5]['bus1']['value']
    #bus2=Switch_query[i5]['bus2']['value']
    #term1=Switch_query[i5]['term1']['value']
    #term2=Switch_query[i5]['term2']['value']
    node1=Switch_query[i5]['node1']['value']
    node2=Switch_query[i5]['node2']['value']
    #tpnode1=Switch_query[i5]['tpnode1']['value']
    #tpnode2=Switch_query[i5]['tpnode2']['value']
    
    # If switch closed, merge nodes
    if Switch_query[i5]['open']['value'] == 'false':
        
        # Merge topology Nodes
        #ConnNodeDict[node1]['tpid'] = tpnode1
        ConnNodeDict[node2]['tpid'] = ConnNodeDict[node1]['tpid'] #tpnode1
        #TopoNodeDict[tpnode1] = [node1, node2] # not implemented
        #TopoNodeDict[tpnode2] = [node2, node1]
        
        # Update Linked Lists
        if ConnNodeDict[node2]['list'] > ConnNodeDict[node1]['list']:
            term2 = TermList[ConnNodeDict[node2]['list']-1]
            next2 = TerminalsDict[term2]['next']
            while next2 != 0:
                term2 = TermList[next2-1]
                next2 = TerminalsDict[term2]['next']
            TerminalsDict[term2]['next'] = ConnNodeDict[node1]['list']
            ConnNodeDict[node1]['list'] = ConnNodeDict[node2]['list']
        else:
            term1 = TermList[ConnNodeDict[node1]['list']-1]
            next1 = TerminalsDict[term1]['next']
            while next1 != 0:
                term1 = TermList[next1-1]
                next1 = TerminalsDict[term1]['next']
            TerminalsDict[term1]['next'] = ConnNodeDict[node2]['list']
            ConnNodeDict[node2]['list'] = ConnNodeDict[node1]['list']
            
print("Processed ", i5, "switch objects in ", time.process_time() - StartTime, "seconds")

Tree={}
TotalNodes=0
StartTime = time.process_time()

# Iterate through all substation transformers
for i6 in range(len(XfmrKeys)):
    
    # Identify if distribution substation transformer
    if (int(Xfmr_dict[XfmrKeys[i6]]['volt1']) >= 34000 and 34000 >= int(Xfmr_dict[XfmrKeys[i6]]['volt2']) > 1000) or (int(Xfmr_dict[XfmrKeys[i6]]['volt2']) >= 34000 and 34000 >= int(Xfmr_dict[XfmrKeys[i6]]['volt1']) > 1000):
        # Create Tree starting from this transformer
        FirstNode = 1 
        LastNode = 2
        # Set as rootnode 
        # assuming node1 is high and node2 is low - need to verify will work otherwise
        Tree[XfmrKeys[i6]]=[Xfmr_dict[XfmrKeys[i6]]['node1'], Xfmr_dict[XfmrKeys[i6]]['node2']]

        while LastNode != FirstNode:
            NextTerm = ConnNodeDict[Tree[XfmrKeys[i6]][FirstNode]]['list']
            FirstNode = FirstNode + 1
            while NextTerm != 0:
                # Get next node and terminal for current node
                NextNode = TerminalsDict[TermList[NextTerm-1]]['far']
                NextTerm = TerminalsDict[TermList[NextTerm-1]]['next']
                # Add to tree if not there already
                if NodeList[NextNode-1] not in Tree[XfmrKeys[i6]]:
                    Tree[XfmrKeys[i6]].append(NodeList[NextNode-1])
                    LastNode = LastNode + 1
                    
        NodesInTree=len(Tree[XfmrKeys[i6]])
        print("Processed topology from substation transformer ", Xfmr_dict[XfmrKeys[i6]]['tname1'], " with ", NodesInTree, " buses")
        TotalNodes=TotalNodes+NodesInTree
            
print("Processed ", len(Tree.keys()), "topology trees containing ", TotalNodes, " buses in ", time.process_time() - StartTime, "seconds")

Subs=list(Tree.keys())
TotalNodes = 0
StartTime = time.process_time()


# Iterate through all SynchronousMachine
for i7 in range(len(DG_query)):
    node=DG_query[i7]['node']['value']
    term=DG_query[i7]['term']['value']
    islanded = True
    
    # Identify if DER is really islanded
    for i8 in range(len(Subs)):
        if node in Tree[Subs[i8]]:
            islanded = False
        
    if islanded == True:
        # Create Tree starting from this transformer
        FirstNode = 0 
        LastNode = 1
        # Set as rootnode 
        # assuming node1 is high and node2 is low - need to verify will work otherwise
        Tree[node]=[node]

        while LastNode != FirstNode:
            NextTerm = ConnNodeDict[Tree[node][FirstNode]]['list']
            FirstNode = FirstNode + 1
            while NextTerm != 0:
                # Get next node and terminal for current node
                NextNode = TerminalsDict[TermList[NextTerm-1]]['far']
                NextTerm = TerminalsDict[TermList[NextTerm-1]]['next']
                # Add to tree if not there already
                if NodeList[NextNode-1] not in Tree[node]:
                    Tree[node].append(NodeList[NextNode-1])
                    LastNode = LastNode + 1
                    
        NodesInTree=len(Tree[node])
        TotalNodes=TotalNodes+NodesInTree
            
print("Processed ", len(Tree.keys())-len(Subs), " more islands containing ", TotalNodes, " buses in ", time.process_time() - StartTime, "seconds")