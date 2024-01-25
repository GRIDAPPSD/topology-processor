# Custom SPARQL queries to obtain all equipment needed to build feeder topology

    
    # Get all measurements points for all equipment from Blazegraph Database
def get_all_measurements(blazegraph, model_mrid):
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

    results = blazegraph.execute(QueryMeasurementMessage)
#     results = gapps.query_data(query = QueryMeasurementMessage, timeout = 60)
#     MeasurementQuery = results['data']['results']['bindings']
    return results



# Get all ConnectivityNode and TopologicalNode objects
def get_all_nodes(blazegraph, model_mrid):
    QueryNodeMessage="""
        PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX c:  <http://iec.ch/TC57/CIM100#>
        SELECT DISTINCT ?busname ?cnid ?tpnid (group_concat(distinct ?nomu;separator="") as ?nomv ) WHERE {
        SELECT ?busname ?cnid ?tpnid ?nomu WHERE {
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
        ?bv  c:BaseVoltage.nominalVoltage ?nomu.
          }
        bind(strafter(str(?tp), str("http://localhost:8889/bigdata/namespace/kb/sparql#")) as ?tpnid)
        } ORDER by ?busname
        } 
        GROUP by ?busname ?cnid ?tpnid 
        ORDER by ?busname
        """%model_mrid

#     results = gapps.query_data(query = QueryNodeMessage, timeout = 60)
    results = blazegraph.execute(QueryNodeMessage)
#     NodeQuery = results['data']['results']['bindings']
    return results

# Get all switches with nodes, terminals, and default positions
def get_all_switches(blazegraph, model_mrid):
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
#     results = gapps.query_data(query = QuerySwitchMessage, timeout = 60)
    results = blazegraph.execute(QuerySwitchMessage)
#     SwitchQuery = results['data']['results']['bindings']
    return results

def get_all_transformers(blazegraph,model_mrid):
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
#     results = gapps.query_data(query = QueryXfmrMessage, timeout = 60)
    results = blazegraph.execute(QueryXfmrMessage)
#     XfmrQuery = results['data']['results']['bindings']
    return results

def get_all_lines(blazegraph, model_mrid):
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
#     results = gapps.query_data(query = QueryLineMessage, timeout = 60)
    results = blazegraph.execute(QueryLineMessage)
#     LineQuery = results['data']['results']['bindings']
    return results

def get_all_houses(blazegraph, model_mrid):
    QueryHouseMessage = """
    # list houses - DistHouse
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT  ?name ?parent ?id ?cnid ?tid
    WHERE { 
    VALUES ?fdrid {"%s"} 
       ?h r:type c:House.
       ?h c:IdentifiedObject.name ?name.
       ?h c:IdentifiedObject.mRID ?id.
       ?h c:House.EnergyConsumer ?econ.
       ?econ c:IdentifiedObject.name ?parent.
       ?t c:Terminal.ConductingEquipment ?econ.
       ?t c:Terminal.ConnectivityNode ?cn.
       ?fdr c:IdentifiedObject.mRID ?fdrid.
       ?fdr c:IdentifiedObject.name ?fdrname.
       ?econ c:Equipment.EquipmentContainer ?fdr.
       bind(strafter(str(?t),"#") as ?tid).
       bind(strafter(str(?cn),"#") as ?cnid).
    } ORDER BY ?name
    """%model_mrid
#     results = gapps.query_data(query = QueryHouseMessage, timeout = 60)
    results = blazegraph.execute(QueryHouseMessage)
#     HouseQuery = results['data']['results']['bindings']
    return results

def get_all_tapchangers(blazegraph, model_mrid):
    QueryTapMessage = """
    # voltage regulators - DistRegulator
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?rname ?eqid ?wnum ?cnid ?tid ?seq ?pxfid ?tankid
    WHERE {
    VALUES ?fdrid {"%s"}  # 123 PV
     ?pxf c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
     ?rtc r:type c:RatioTapChanger.
     ?rtc c:IdentifiedObject.name ?rname.
     ?rtc c:RatioTapChanger.TransformerEnd ?end.
     ?end c:TransformerEnd.endNumber ?wnum.
     ?end c:TransformerEnd.Terminal ?t.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?t c:ACDCTerminal.sequenceNumber ?seq.
     {?end c:PowerTransformerEnd.PowerTransformer ?pxf.
      ?pxf c:IdentifiedObject.mRID ?eqid.}
     UNION
     {?end c:TransformerTankEnd.TransformerTank ?tank.
     ?tank c:IdentifiedObject.mRID ?eqid.
     ?tank c:TransformerTank.PowerTransformer ?pxf.}
     bind(strafter(str(?t),"#") as ?tid).
     bind(strafter(str(?cn),"#") as ?cnid).
     bind(strafter(str(?pxf),"#") as ?pxfid).
     bind(strafter(str(?tank),"#") as ?tankid).
    }
    ORDER BY ?rname ?wnum
    """%model_mrid
#     results = gapps.query_data(query = QueryTapMessage, timeout = 60)
    results = blazegraph.execute(QueryTapMessage)
#     TapChangerQuery = results['data']['results']['bindings']
    return results

def get_all_energy_sources(blazegraph, model_mrid):
    QuerySourceMessage = """
    # substation source - DistSubstation
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?bus ?basev ?nomv ?node ?term ?source WHERE {
     ?s r:type c:EnergySource.
    # feeder selection options - if all commented out, query matches all feeders
    VALUES ?fdrid {"%s"}
     ?s c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
     ?s c:IdentifiedObject.name ?name.
     ?s c:ConductingEquipment.BaseVoltage ?bv.
     ?bv c:BaseVoltage.nominalVoltage ?basev.
     ?s c:EnergySource.nominalVoltage ?nomv.  
     ?t c:Terminal.ConductingEquipment ?s.
     ?t c:Terminal.ConnectivityNode ?cn. 
     ?cn c:IdentifiedObject.name ?bus
     bind(strafter(str(?t), "#") as ?term)
     bind(strafter(str(?cn), "#") as ?node)
     bind(strafter(str(?s), "#") as ?source)
    }
    ORDER by ?name
    """%model_mrid
#     results = gapps.query_data(query = QuerySourceMessage, timeout = 60)
    results = blazegraph.execute(QuerySourceMessage)
#     SourceQuery = results['data']['results']['bindings']
    return results

def get_all_batteries(blazegraph, model_mrid):
    QueryBattMessage = """
    # Storage - DistStorage
    PREFIX r:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c:  <http://iec.ch/TC57/CIM100#>
    SELECT ?name ?eqid ?fdrid ?pecid ?termid ?cnid WHERE {
     ?s r:type c:BatteryUnit.
     ?s c:IdentifiedObject.name ?name.
     ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.

     VALUES ?fdrid {"%s"}  
     ?pec c:Equipment.EquipmentContainer ?fdr.
     ?fdr c:IdentifiedObject.mRID ?fdrid.
     ?pec c:IdentifiedObject.mRID ?pecid.
     bind(strafter(str(?s),"#") as ?eqid).
     ?t c:Terminal.ConductingEquipment ?pec.
     ?t c:Terminal.ConnectivityNode ?cn. 
     bind(strafter(str(?cn),"#") as ?cnid).
     ?t c:IdentifiedObject.mRID ?termid.

    }
    GROUP by ?name ?eqid ?fdrid ?pecid ?termid ?cnid
    ORDER by ?name
    """%model_mrid
#     results = gapps.query_data(query = QueryBattMessage, timeout = 60)
    results = blazegraph.execute(QueryBattMessage)
#     BattQuery = results['data']['results']['bindings']
    return results

def get_all_photovoltaics(blazegraph, model_mrid):
    QueryPVMessage = """
    PREFIX r: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX c: <http://iec.ch/TC57/CIM100#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?name ?eqid ?pecid ?cnid ?termid
    WHERE {
    VALUES ?feeder_mrid {"%s"}
    ?s r:type c:PhotovoltaicUnit.
    ?s c:IdentifiedObject.name ?name.
    ?s c:IdentifiedObject.mRID ?eqid.
    ?pec c:PowerElectronicsConnection.PowerElectronicsUnit ?s.
    ?pec c:IdentifiedObject.mRID ?pecid.
    ?pec c:Equipment.EquipmentContainer ?fdr.
    ?fdr c:IdentifiedObject.mRID ?feeder_mrid.
    ?t c:Terminal.ConductingEquipment ?pec.
    ?t c:Terminal.ConnectivityNode ?cn.
    bind(strafter(str(?cn),"#") as ?cnid).
    ?t c:IdentifiedObject.mRID ?termid.
    }
    GROUP by ?name ?eqid ?pecid ?cnid ?termid
    ORDER by ?name
    """%model_mrid
    results = blazegraph.execute(QueryPVMessage)
#     results = gapps.query_data(query = QueryPVMessage, timeout = 60)
#     PVQuery = results['data']['results']['bindings']
    return results