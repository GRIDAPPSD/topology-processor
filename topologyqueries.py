
def getallqueries(gapps,model_mrid):
    global Line_query,Xfmr_query,Switch_query,DG_query, Node_query
    Line_query=Linequery(gapps,model_mrid)
    Xfmr_query=Transformerquery(gapps,model_mrid)
    Switch_query=Switchquery(gapps,model_mrid)
    DG_query=DGQuery(gapps,model_mrid)
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
    return Xfmr_query


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
    return Switch_query

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

def NodeQuery(gapps,model_mrid):
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
    return Node_query
