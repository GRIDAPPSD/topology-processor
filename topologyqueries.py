
def getallqueries(gapps,model_mrid):
    global Line_query,XfmrDict, XfmrKeys,SwitchDict, SwitchKeys,DG_query, Cap_query, Node_query
    Line_query=Linequery(gapps,model_mrid)
    [XfmrDict,XfmrKeys]=Transformerquery(gapps,model_mrid)
    [SwitchDict,SwitchKeys]=Switchquery(gapps,model_mrid)
    DG_query=DGQuery(gapps,model_mrid)
    Cap_query=CapQuery(gapps,model_mrid)
    Node_query=NodeQuery(gapps,model_mrid)


def Linequery(gapps,model_mrid):
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
    return Line_query

def Transformerquery(gapps,model_mrid):
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
    
    XfmrDict={}
    XfmrKeys=[]

    # Build dictionary of FROM-TO nodes for all transformers
    for i2 in range(len(Xfmr_query)):
        eqid=Xfmr_query[i2]['eqid']['value']

        seq=Xfmr_query[i2]['seq']['value']
        if eqid not in XfmrDict:
            XfmrDict[eqid]={}
            XfmrKeys.append(eqid)
        XfmrDict[eqid]['bus']=Xfmr_query[i2]['bus']['value']

        # Identify terminal sequence and create keys for new terminals
        if seq == '1' or seq == 1:
            # Primary winding
            XfmrDict[eqid]['bus1']=Xfmr_query[i2]['bus']['value']
            XfmrDict[eqid]['term1']=Xfmr_query[i2]['tid']['value']
            XfmrDict[eqid]['node1']=Xfmr_query[i2]['cnid']['value']
            XfmrDict[eqid]['tpnode1']=Xfmr_query[i2]['tpid']['value']
            XfmrDict[eqid]['tname1']=Xfmr_query[i2]['tname']['value']
            if 'ratedu' in Xfmr_query[i2]: XfmrDict[eqid]['volt1']=int(float(Xfmr_query[i2]['ratedu']['value']))
            else: XfmrDict[eqid]['volt1']=0
            if 'phs' in Xfmr_query[i2]: XfmrDict[eqid]['phase1']=Xfmr_query[i2]['phs']['value'] 
            else: XfmrDict[eqid]['phase1']={}

        elif seq == '2' or seq == 2:
            XfmrDict[eqid]['bus2']=Xfmr_query[i2]['bus']['value']
            XfmrDict[eqid]['term2']=Xfmr_query[i2]['tid']['value']
            XfmrDict[eqid]['node2']=Xfmr_query[i2]['cnid']['value']
            XfmrDict[eqid]['tpnode2']=Xfmr_query[i2]['tpid']['value']
            XfmrDict[eqid]['tname2']=Xfmr_query[i2]['tname']['value']
            if 'ratedu' in Xfmr_query[i2]: XfmrDict[eqid]['volt2']=int(float(Xfmr_query[i2]['ratedu']['value']))
            else: XfmrDict[eqid]['volt2']=0
            if 'phs' in Xfmr_query[i2]: XfmrDict[eqid]['phase2']=Xfmr_query[i2]['phs']['value'] 
            else: XfmrDict[eqid]['phase2']={}

        elif seq == '3' or seq == 3:
            XfmrDict[eqid]['bus3']=Xfmr_query[i2]['bus']['value']
            XfmrDict[eqid]['term3']=Xfmr_query[i2]['tid']['value']
            XfmrDict[eqid]['node3']=Xfmr_query[i2]['cnid']['value']
            XfmrDict[eqid]['tpnode3']=Xfmr_query[i2]['tpid']['value']
            XfmrDict[eqid]['tname3']=Xfmr_query[i2]['tname']['value']
            if 'ratedu' in Xfmr_query[i2]: XfmrDict[eqid]['volt3']=int(float(Xfmr_query[i2]['ratedu']['value']))
            else: XfmrDict[eqid]['volt3']=0
            if 'phs' in Xfmr_query[i2]: XfmrDict[eqid]['phase3']=Xfmr_query[i2]['phs']['value'] 
            else: XfmrDict[eqid]['phase3']={}
        else:
            raise ValueError('Unsupported transformer sequence value ', seq)
    return XfmrDict,XfmrKeys


def Switchquery(gapps,model_mrid):
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
    
    SwitchDict={}
    SwitchKeys=[]
    for i5 in range(len(Switch_query)):
        mrid=Switch_query[i5]['id']['value']
        SwitchDict[mrid]={}
        SwitchKeys.append(mrid)
        SwitchDict[mrid]['name']=Switch_query[i5]['name']['value']
        SwitchDict[mrid]['bus1']=Switch_query[i5]['bus1']['value']
        SwitchDict[mrid]['bus2']=Switch_query[i5]['bus2']['value']
        SwitchDict[mrid]['term1']=Switch_query[i5]['term1']['value']
        SwitchDict[mrid]['term2']=Switch_query[i5]['term2']['value']
        SwitchDict[mrid]['node1']=Switch_query[i5]['node1']['value']
        SwitchDict[mrid]['node2']=Switch_query[i5]['node2']['value']
        SwitchDict[mrid]['tpnode1']=Switch_query[i5]['tpnode1']['value']
        SwitchDict[mrid]['tpnode2']=Switch_query[i5]['tpnode2']['value']


        # If switch closed, merge nodes
        if Switch_query[i5]['open']['value'] == 'false':
            SwitchDict[mrid]['open'] = 1
        else:
            SwitchDict[mrid]['open'] = 0
        
    return SwitchDict,SwitchKeys

def DGQuery(gapps,model_mrid):
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
    return DG_query

def CapQuery(gapps,model_mrid):
    QueryCaps="""
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT 

    ?name ?id ?nomu ?node ?term ?fdrid WHERE {
     ?s r:type c:LinearShuntCompensator.

    VALUES ?fdrid {"%s"}
     ?s c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
     ?s c:IdentifiedObject.name ?name.
     ?s c:ConductingEquipment.BaseVoltage ?bv.
     ?bv c:BaseVoltage.nominalVoltage ?basev.
     ?s c:ShuntCompensator.nomU ?nomu. 
     ?s c:IdentifiedObject.mRID ?id. 
     ?t c:Terminal.ConductingEquipment ?s.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?cn c:IdentifiedObject.name ?bus
     bind(strafter(str(?cn),"#") as ?node).
     bind(strafter(str(?s),"#") as ?term).
    }
    ORDER by ?name
    """%model_mrid
    results = gapps.query_data(query = QueryCaps, timeout = 60)
    Cap_query = results['data']['results']['bindings']
    return Cap_query

def NodeQuery(gapps,model_mrid):
    QueryNodes="""
        PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX c:  <http://iec.ch/TC57/CIM100#>
        SELECT DISTINCT ?busname ?cnid ?tpnid  WHERE {
          VALUES ?fdrid {"%s"}
        ?fdr c:IdentifiedObject.mRID ?fdrid.
        ?bus c:ConnectivityNode.ConnectivityNodeContainer ?fdr.
        ?bus c:ConnectivityNode.TopologicalNode ?tp.
        ?bus r:type c:ConnectivityNode.
        ?bus c:IdentifiedObject.name ?busname.
        ?bus c:IdentifiedObject.mRID ?cnid.
        ?fdr c:IdentifiedObject.name ?feeder.
        ?trm c:Terminal.ConnectivityNode ?bus.
        ?trm c:Terminal.ConductingEquipment ?ce.
        
        OPTIONAL {
        ?ce  c:ConductingEquipment.BaseVoltage ?bv.
        ?bv  c:BaseVoltage.nominalVoltage ?nomv.
          }
        bind(strafter(str(?tp), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?tpnid)
        }
        GROUP by ?busname ?cnid ?tpnid
        ORDER by ?busname
        """%model_mrid

    results = gapps.query_data(query = QueryNodes, timeout = 60)
    Node_query = results['data']['results']['bindings']
    return Node_query
