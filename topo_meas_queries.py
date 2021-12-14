# Custom SPARQL queries to obtain all equipment needed to build feeder topology

# Get all measurements points for all equipment from Blazegraph Database
def get_all_measurements(gapps, model_mrid):
    QueryMeasurementMessage="""
        # list all measurements, with buses and equipments - DistMeasurement
        PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX c: <http://iec.ch/TC57/CIM100#>
        SELECT ?class ?cnid ?type ?name ?bus ?phases ?meastype ?eqname ?eqid ?trmid ?measid WHERE {
        VALUES ?fdrid {"%s"}
         ?eq c:Equipment.EquipmentContainer ?fdr.
         ?fdr c:IdentifiedObject.mRID ?fdrid. 
        { ?s r:type c:Discrete. bind ("Discrete" as ?class)}
          UNION
        { ?s r:type c:Analog. bind ("Analog" as ?class)}
         ?s c:IdentifiedObject.name ?name .
         ?s c:IdentifiedObject.mRID ?measid .
         ?s c:Measurement.PowerSystemResource ?eq .
         ?s c:Measurement.Terminal ?trm .
         ?s c:Measurement.measurementType ?type .
         ?trm c:IdentifiedObject.mRID ?trmid.
         ?eq c:IdentifiedObject.mRID ?eqid.
         ?eq c:IdentifiedObject.name ?eqname.
         #?eq r:type ?typeraw.
         # bind(strafter(str(?typeraw),"#") as ?eqtype)
         bind(strbefore(str(?name),"_") as ?meastype)
         ?trm c:Terminal.ConnectivityNode ?cn.
         ?cn c:IdentifiedObject.name ?bus.
         ?cn c:IdentifiedObject.mRID ?cnid.
         ?s c:Measurement.phases ?phsraw .
           {bind(strafter(str(?phsraw),"PhaseCode.") as ?phases)}

        } ORDER BY ?cnid ?type
        """%model_mrid
    
    results = gapps.query_data(query = QueryMeasurementMessage, timeout = 60)
    MeasurementQuery = results['data']['results']['bindings']
    return MeasurementQuery
    
    
    
# Get all ConnectivityNode and TopologicalNode objects
def get_all_nodes(gapps, model_mrid):
    QueryNodeMessage="""
        PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX c:  <http://iec.ch/TC57/CIM100#>
        SELECT DISTINCT ?busname ?cnid ?tpnid ?nomv  WHERE {
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
        GROUP by ?busname ?cnid ?tpnid ?nomv
        ORDER by ?busname
        """%model_mrid

    results = gapps.query_data(query = QueryNodeMessage, timeout = 60)
    NodeQuery = results['data']['results']['bindings']
    return NodeQuery

# Get all switches with nodes, terminals, and default positions
def get_all_switches(gapps, model_mrid):
    QuerySwitchMessage="""
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
    results = gapps.query_data(query = QuerySwitchMessage, timeout = 60)
    SwitchQuery = results['data']['results']['bindings']
    return SwitchQuery
    
def get_all_transformers(gapps,model_mrid):
    QueryXfmrMessage="""
        # list all the terminals connected to a TransformerEnd for CIMWriter
        PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX c:  <http://iec.ch/TC57/CIM100#>
        SELECT ?class ?eqid ?endid ?tname ?tid ?bus ?cnid ?tpid ?seq ?phs ?ratedu WHERE {
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
        bind(strbefore(str(?endclass), "E") as ?class)
        bind(strafter(str(?ph),"e.") as ?phs).
        ?end a ?classraw.
        bind(strafter(str(?classraw),"CIM100#") as ?endclass)
        }
        ORDER by ?class ?eqid ?tname ?endid ?bus ?cnid ?tpid ?seq ?phs ?ratedu
        """%model_mrid
    results = gapps.query_data(query = QueryXfmrMessage, timeout = 60)
    XfmrQuery = results['data']['results']['bindings']
    return XfmrQuery

def get_all_lines(gapps, model_mrid):
    QueryLineMessage="""
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
    results = gapps.query_data(query = QueryLineMessage, timeout = 60)
    LineQuery = results['data']['results']['bindings']
    return LineQuery