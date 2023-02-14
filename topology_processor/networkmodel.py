# from gridappsd import GridAPPSD
import time, json
import topology_processor.topo_meas_queries as queries
from topology_processor.blazegraph_connection import BlazegraphConnection
import sys
class NetworkModel():

    def __init__(self, gapps):
        self.gapps = gapps
        self.log = self.gapps.get_logger()
        self.blazegraph = BlazegraphConnection()
        self.log.info(sys.argv[0])
    # This method builds equipment dictionaries for given model and Topology object
    def build_equip_dicts(self, model_mrid, Topology):
        # Initialize all equipment dictionary keys
        Topology.EquipDict['ACLineSegment'] = {}
        Topology.EquipDict['BatteryUnit'] = {}
        Topology.EquipDict['Breaker'] = {}
        Topology.EquipDict['EnergyConsumer'] = {}
        Topology.EquipDict['House'] = {}
        Topology.EquipDict['Fuse'] = {}
        Topology.EquipDict['LinearShuntCompensator'] = {}
        Topology.EquipDict['LoadBreakSwitch'] = {}
        Topology.EquipDict['PhotovoltaicUnit'] = {}
        Topology.EquipDict['PowerTransformer'] = {}
        Topology.EquipDict['RatioTapChanger'] = {}
        Topology.EquipDict['Recloser'] = {}
        Topology.EquipDict['TransformerTank'] = {}    
        Topology.EquipDict['SynchronousMachine'] = {}
        Topology.EquipDict['PowerElectronicsConnection'] = {}
        Topology.EquipDict['EnergySource'] = {}

        # Initialize dictionary keys for all ConnectivityNode objects in model:
        StartTime = time.process_time()
        i0=-1
        NodeQuery=queries.get_all_nodes(self.blazegraph,model_mrid)
        for i0 in range(len(NodeQuery)):
            node=NodeQuery[i0]['cnid']['value']
            Topology.ConnNodeDict[node] = {}
            Topology.ConnNodeDict[node]['name'] = NodeQuery[i0]['busname']['value']
            Topology.ConnNodeDict[node]['TopologicalNode'] = NodeQuery[i0]['tpnid']['value']
            if 'nomv' in NodeQuery[i0]:
                Topology.ConnNodeDict[node]['nominalVoltage'] = NodeQuery[i0]['nomv']['value']
            else:
                Topology.ConnNodeDict[node]['nominalVoltage'] = []
            Topology.ConnNodeDict[node]['ACLineSegment'] = []
            Topology.ConnNodeDict[node]['BatteryUnit'] = []
            Topology.ConnNodeDict[node]['Breaker'] = []
            Topology.ConnNodeDict[node]['EnergyConsumer'] = []
            Topology.ConnNodeDict[node]['Fuse'] = []
            Topology.ConnNodeDict[node]['House'] = []
            Topology.ConnNodeDict[node]['LinearShuntCompensator'] = []
            Topology.ConnNodeDict[node]['LoadBreakSwitch'] = []
            Topology.ConnNodeDict[node]['PhotovoltaicUnit'] = []
            Topology.ConnNodeDict[node]['PowerTransformer'] = []
            Topology.ConnNodeDict[node]['RatioTapChanger'] = []
            Topology.ConnNodeDict[node]['Recloser'] = []
            Topology.ConnNodeDict[node]['TransformerTank'] = []    
            Topology.ConnNodeDict[node]['SynchronousMachine'] = []
            Topology.ConnNodeDict[node]['PowerElectronicsConnection'] = []
            Topology.ConnNodeDict[node]['Measurement'] = []
            Topology.ConnNodeDict[node]['Feeder'] = []
            Topology.ConnNodeDict[node]['Island'] = []
        self.log.info('Processed ' + str(i0+1) + ' ConnectivyNode objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")

        # Import all measurements and associated objects:
        StartTime = time.process_time()
        MeasurementQuery=queries.get_all_measurements(self.blazegraph,model_mrid)
        i1 = -1
        # Parse all entries in query response
        for i1 in range(len(MeasurementQuery)):    
            node = MeasurementQuery[i1]['cnid']['value']
            eqtype = MeasurementQuery[i1]['meastype']['value']
            eqid = MeasurementQuery[i1]['eqid']['value']
            meastype = MeasurementQuery[i1]['type']['value']
            measid = MeasurementQuery[i1]['measid']['value']
            # Associate measurement mRID with ConnectivityNode
            Topology.ConnNodeDict[node]['Measurement'].append(MeasurementQuery[i1]['measid']['value'])
            # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
            if eqid not in Topology.ConnNodeDict[node][eqtype]: 
                Topology.ConnNodeDict[node][eqtype].append(eqid)
            # Create equipment dictionary entry if not already defined by prior measurement
            if eqid not in Topology.EquipDict[eqtype]: 
                Topology.EquipDict[eqtype][eqid] = {}
                #Topology.EquipDict[eqtype][eqid]['meas'] = {}
                #Topology.EquipDict[eqtype][eqid]['meas']['PNV'] = []
                #Topology.EquipDict[eqtype][eqid]['meas']['VA'] = []
                #Topology.EquipDict[eqtype][eqid]['meas']['Pos'] = []
                #Topology.EquipDict[eqtype][eqid]['meas']['A'] = []
                #Topology.EquipDict[eqtype][eqid]['meas']['SoC'] = []
                
            # Associate measurement value with equipment
            #Topology.EquipDict[eqtype][eqid]['meas'][meastype].append(measid)
            
            # Associate ConnectivityNode with equipment mRID - FIRST PASS
            if 'node1' in Topology.EquipDict[eqtype][eqid]: # If one node already defined, then assume two-terminal branch
                if Topology.EquipDict[eqtype][eqid]['node1'] != node:
                    Topology.EquipDict[eqtype][eqid]['node2'] = node
                    Topology.EquipDict[eqtype][eqid]['term2'] = MeasurementQuery[i1]['trmid']['value']
            else: # If first node, assume that it is first node
                Topology.EquipDict[eqtype][eqid]['name'] = MeasurementQuery[i1]['eqname']['value']
                Topology.EquipDict[eqtype][eqid]['node1'] = node
                Topology.EquipDict[eqtype][eqid]['term1'] = MeasurementQuery[i1]['trmid']['value']
            # NEED TO ADD LOGIC FOR 3-WINDING TRANSFORMERS LATER
        self.log.info('Processed ' + str(i1+1) + ' Measurement objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")

        # Import all ACLineSegment objects - SECOND PASS
        StartTime = time.process_time()
        LineQuery = queries.get_all_lines(self.blazegraph, model_mrid)
        i2 = -1
        eqtype = 'ACLineSegment'
        for i2 in range(len(LineQuery)):
            eqid = LineQuery[i2]['id']['value']

            # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
            if eqid not in Topology.ConnNodeDict[LineQuery[i2]['node1']['value']][eqtype]: 
                Topology.ConnNodeDict[LineQuery[i2]['node1']['value']][eqtype].append(eqid)
            if eqid not in Topology.ConnNodeDict[LineQuery[i2]['node2']['value']][eqtype]: 
                Topology.ConnNodeDict[LineQuery[i2]['node2']['value']][eqtype].append(eqid)
            Topology.EquipDict[eqtype][eqid]['term1'] = LineQuery[i2]['term1']['value']
            Topology.EquipDict[eqtype][eqid]['term2'] = LineQuery[i2]['term2']['value']
            Topology.EquipDict[eqtype][eqid]['node1'] = LineQuery[i2]['node1']['value']
            Topology.EquipDict[eqtype][eqid]['node2'] = LineQuery[i2]['node2']['value']
        self.log.info('Processed ' + str(i2+1) + ' ACLineSegment objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")

        # Import all PowerTransformer and TransformerTank objects - SECOND PASS
        StartTime = time.process_time()
        XfmrQuery = queries.get_all_transformers(self.blazegraph, model_mrid)
        i2 = -1
        for i2 in range(len(XfmrQuery)):
            eqtype = XfmrQuery[i2]['class']['value']
            eqid = XfmrQuery[i2]['eqid']['value']
            seq = str(XfmrQuery[i2]['seq']['value'])
            # Check if transformer not defined when parsing measurements
            if eqid not in Topology.EquipDict[eqtype]: Topology.EquipDict[eqtype][eqid] = {}
            # Identify terminal sequence and create keys for new terminals
            Topology.EquipDict[eqtype][eqid]['bus' + seq] = XfmrQuery[i2]['bus']['value']
            Topology.EquipDict[eqtype][eqid]['term' + seq] = XfmrQuery[i2]['tid']['value']
            Topology.EquipDict[eqtype][eqid]['node' + seq] = XfmrQuery[i2]['cnid']['value']
            Topology.EquipDict[eqtype][eqid]['tname' + seq] = XfmrQuery[i2]['tname']['value']
            if eqid not in Topology.ConnNodeDict[XfmrQuery[i2]['cnid']['value']][eqtype]:
                Topology.ConnNodeDict[XfmrQuery[i2]['cnid']['value']][eqtype].append(eqid)
            if 'ratedu' in XfmrQuery[i2]: # Add rated voltage if defined
                Topology.EquipDict[eqtype][eqid]['volt' + seq] = int(float(XfmrQuery[i2]['ratedu']['value']))
            else: Topology.EquipDict[eqtype][eqid]['volt' + seq] = 0 
            if 'phs' in XfmrQuery[i2]:  # Add phase if defined
                Topology.EquipDict[eqtype][eqid]['phase' + seq] = XfmrQuery[i2]['phs']['value'] 
            else: Topology.EquipDict[eqtype][eqid]['phase' + seq] = {}
        self.log.info('Processed ' + str(i2+1) + ' Transformer objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")

        # Import all Breaker, Fuse, LoadBreakSwitch, and Recloser objects -  SECOND PASS
        StartTime = time.process_time()
        SwitchQuery = queries.get_all_switches(self.blazegraph, model_mrid)
        i3 = -1
        for i3 in range(len(SwitchQuery)):
            eqid = SwitchQuery[i3]['id']['value']
            eqtype = SwitchQuery[i3]['cimtype']['value']
            # Check if switch not defined when parsing measurements
            if eqid not in Topology.EquipDict[eqtype]: Topology.EquipDict[eqtype][eqid] = {}
            Topology.EquipDict[eqtype][eqid]['term1']=SwitchQuery[i3]['term1']['value']
            Topology.EquipDict[eqtype][eqid]['term2']=SwitchQuery[i3]['term2']['value']
            Topology.EquipDict[eqtype][eqid]['node1']=SwitchQuery[i3]['node1']['value']
            Topology.EquipDict[eqtype][eqid]['node2']=SwitchQuery[i3]['node2']['value']
            if eqid not in Topology.ConnNodeDict[SwitchQuery[i3]['node1']['value']][eqtype]:
                Topology.ConnNodeDict[SwitchQuery[i3]['node1']['value']][eqtype].append(eqid)
            if eqid not in Topology.ConnNodeDict[SwitchQuery[i3]['node2']['value']][eqtype]:
                Topology.ConnNodeDict[SwitchQuery[i3]['node2']['value']][eqtype].append(eqid)
            # Check if switch is open or closed in base model
            if SwitchQuery[i3]['open']['value'] == 'false': 
                Topology.EquipDict[eqtype][eqid]['open'] = 1
            else: 
                Topology.EquipDict[eqtype][eqid]['open'] = 0
        self.log.info('Processed ' + str(i3+1) + ' Switch objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")


        # Import all House objects
        StartTime = time.process_time()
        HouseQuery = queries.get_all_houses(self.blazegraph, model_mrid)
        i4 = -1
        for i4 in range(len(HouseQuery)):
            eqid = HouseQuery[i3]['id']['value']
            eqtype = 'House'
            # Check if house not defined when parsing measurements
            if eqid not in Topology.EquipDict[eqtype]: Topology.EquipDict[eqtype][eqid] = {}
            Topology.EquipDict[eqtype][eqid]['term1']=HouseQuery[i3]['tid']['value']
            Topology.EquipDict[eqtype][eqid]['node1']=HouseQuery[i3]['cnid']['value']

        self.log.info('Processed ' + str(i4+1) + ' House objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")

        # Import all RatioTapChanger objects
        StartTime = time.process_time()
        TapChangerQuery = queries.get_all_tapchangers(self.blazegraph, model_mrid)
        eqtype = 'RatioTapChanger'
        i5 = -1
        for i5 in range(len(TapChangerQuery)):
            eqid = TapChangerQuery[i5]['pxfid']['value']

            if 'tankid' in TapChangerQuery[i5]:
                tankid = TapChangerQuery[i5]['tankid']['value']
                if tankid in Topology.EquipDict['TransformerTank']:                     
                    Topology.EquipDict[eqtype][eqid] = dict(Topology.EquipDict['TransformerTank'][tankid])
                    Topology.EquipDict[eqtype][eqid]['TransformerTank'] = tankid
                    
            if 'pxfid' in TapChangerQuery[i5]:
                pxfid = TapChangerQuery[i5]['pxfid']['value']
                if pxfid in Topology.EquipDict['PowerTransformer']:
                    Topology.EquipDict[eqtype][eqid] = dict(Topology.EquipDict['PowerTransformer'][pxfid])
                    Topology.EquipDict[eqtype][eqid]['PowerTransformer'] = pxfid
                    
            Topology.EquipDict[eqtype][eqid]['name'] = TapChangerQuery[i5]['rname']['value']
            
        self.log.info('Processed ' + str(i5+1) + ' RatioTapChanger objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
        
        # Import all EnergySource objects
        startTime = time.process_time()
        SourceQuery = queries.get_all_energy_sources(self.blazegraph, model_mrid)
        eqtype = 'EnergySource'
        for i6 in range(len(SourceQuery)):
            eqid = SourceQuery[i6]['source']['value']
            if eqid not in Topology.EquipDict[eqtype]:
                Topology.EquipDict[eqtype][eqid] = {}
            Topology.EquipDict[eqtype][eqid]['name'] = SourceQuery[i6]['name']['value']
            Topology.EquipDict[eqtype][eqid]['node1'] = SourceQuery[i6]['node']['value']
            Topology.EquipDict[eqtype][eqid]['term1'] = SourceQuery[i6]['term']['value']
            
        # Import all BatteryUnit objects
        startTime = time.process_time()
        BattQuery = queries.get_all_batteries(self.blazegraph, model_mrid)
        eqtype = 'BatteryUnit'
        for i7 in range(len(BattQuery)):
            eqid = BattQuery[i7]['eqid']['value']
            node = BattQuery[i7]['cnid']['value']
            if eqid not in Topology.EquipDict[eqtype]:
                Topology.EquipDict[eqtype][eqid] = {}
            Topology.EquipDict[eqtype][eqid]['name'] = BattQuery[i7]['name']['value']
            Topology.EquipDict[eqtype][eqid]['node1'] = BattQuery[i7]['cnid']['value']
            Topology.EquipDict[eqtype][eqid]['term1'] = BattQuery[i7]['termid']['value']
            # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
            if eqid not in Topology.ConnNodeDict[node][eqtype]: 
                Topology.ConnNodeDict[node][eqtype].append(eqid)
            
        # Import all PhotovoltaicUnit objects
        startTime = time.process_time()
        PVQuery = queries.get_all_photovoltaics(self.blazegraph, model_mrid)
        eqtype = 'PhotovoltaicUnit'
        for i7 in range(len(PVQuery)):
            eqid = PVQuery[i7]['eqid']['value']
            node = PVQuery[i7]['cnid']['value']
            if eqid not in Topology.EquipDict[eqtype]:
                Topology.EquipDict[eqtype][eqid] = {}
            Topology.EquipDict[eqtype][eqid]['name'] = PVQuery[i7]['name']['value']
            Topology.EquipDict[eqtype][eqid]['node1'] = PVQuery[i7]['cnid']['value']
            Topology.EquipDict[eqtype][eqid]['term1'] = PVQuery[i7]['termid']['value']
            # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
            if eqid not in Topology.ConnNodeDict[node][eqtype]: 
                Topology.ConnNodeDict[node][eqtype].append(eqid)
            
