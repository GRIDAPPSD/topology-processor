import time
import topo_meas_queries as topology

# Create dictionary of all equipment and measurements sorted by ConnectivityNode
def build_equip_dicts(gapps, model_mrid):
    gapps_log = gapps.get_logger()
    ConnNodeDict = {}
    EquipDict = {}
    EquipDict['ACLineSegment'] = {}
    EquipDict['Breaker'] = {}
    EquipDict['EnergyConsumer'] = {}
    EquipDict['House'] = {}
    EquipDict['Fuse'] = {}
    EquipDict['LinearShuntCompensator'] = {}
    EquipDict['LoadBreakSwitch'] = {}
    EquipDict['PowerTransformer'] = {}
    EquipDict['RatioTapChanger'] = {}
    EquipDict['Recloser'] = {}
    EquipDict['TransformerTank'] = {}    
    EquipDict['SynchronousMachine'] = {}
    EquipDict['PowerElectronicsConnection'] = {}
    
    # Initialize dictionary keys for all ConnectivityNode objects in model:
    StartTime = time.process_time()
    i0=-1
    NodeQuery=topology.get_all_nodes(gapps,model_mrid)
    for i0 in range(len(NodeQuery)):
        node=NodeQuery[i0]['cnid']['value']
        ConnNodeDict[node] = {}
        ConnNodeDict[node]['name'] = NodeQuery[i0]['busname']['value']
        ConnNodeDict[node]['TopologicalNode'] = NodeQuery[i0]['tpnid']['value']
        if 'nomv' in NodeQuery[i0]:
            ConnNodeDict[node]['nominalVoltage'] = NodeQuery[i0]['nomv']['value']
        else:
            ConnNodeDict[node]['nominalVoltage'] = []
        ConnNodeDict[node]['ACLineSegment'] = []
        ConnNodeDict[node]['Breaker'] = []
        ConnNodeDict[node]['EnergyConsumer'] = []
        ConnNodeDict[node]['Fuse'] = []
        ConnNodeDict[node]['House'] = []
        ConnNodeDict[node]['LinearShuntCompensator'] = []
        ConnNodeDict[node]['LoadBreakSwitch'] = []
        ConnNodeDict[node]['PowerTransformer'] = []
        ConnNodeDict[node]['RatioTapChanger'] = []
        ConnNodeDict[node]['Recloser'] = []
        ConnNodeDict[node]['TransformerTank'] = []    
        ConnNodeDict[node]['SynchronousMachine'] = []
        ConnNodeDict[node]['PowerElectronicsConnection'] = []
        ConnNodeDict[node]['Measurement'] = []
    gapps_log.debug('Processed ' + str(i0+1) + ' ConnectivyNode objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
    
    # Import all measurements and associated objects:
    StartTime = time.process_time()
    MeasurementQuery=topology.get_all_measurements(gapps,model_mrid)
    i1 = -1
    # Parse all entries in query response
    for i1 in range(len(MeasurementQuery)):    
        node = MeasurementQuery[i1]['cnid']['value']
        eqtype = MeasurementQuery[i1]['meastype']['value']
        eqid = MeasurementQuery[i1]['eqid']['value']
        # Associate measurement mRID with ConnectivityNode
        ConnNodeDict[node]['Measurement'].append(MeasurementQuery[i1]['measid']['value'])
        # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
        if eqid not in ConnNodeDict[node][eqtype]: ConnNodeDict[node][eqtype].append(eqid)
        # Create equipment dictionary entry if not already defined by prior measurement
        if eqid not in EquipDict[eqtype]: 
            EquipDict[eqtype][eqid] = {}
        # Associate ConnectivityNode with equipment mRID - FIRST PASS
        if 'node1' in EquipDict[eqtype][eqid]: # If one node already defined, then assume two-terminal branch
            if EquipDict[eqtype][eqid]['node1'] != node:
                EquipDict[eqtype][eqid]['node2'] = node
                EquipDict[eqtype][eqid]['term2'] = MeasurementQuery[i1]['trmid']['value']
        else: # If first node, assume that it is first node
            EquipDict[eqtype][eqid]['name'] = MeasurementQuery[i1]['eqname']['value']
            EquipDict[eqtype][eqid]['node1'] = node
            EquipDict[eqtype][eqid]['term1'] = MeasurementQuery[i1]['trmid']['value']
        # NEED TO ADD LOGIC FOR 3-WINDING TRANSFORMERS LATER
    gapps_log.debug('Processed ' + str(i1+1) + ' Measurement objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
    
    # Import all ACLineSegment objects - SECOND PASS
    StartTime = time.process_time()
    LineQuery = topology.get_all_lines(gapps, model_mrid)
    i2 = -1
    eqtype = 'ACLineSegment'
    for i2 in range(len(LineQuery)):
        eqid = LineQuery[i2]['id']['value']
        
        # Associate equipment mRID with ConnectivityNode if not already defined by prior measurement
        if eqid not in ConnNodeDict[LineQuery[i2]['node1']['value']][eqtype]: 
            ConnNodeDict[LineQuery[i2]['node1']['value']][eqtype].append(eqid)
        if eqid not in ConnNodeDict[LineQuery[i2]['node2']['value']][eqtype]: 
            ConnNodeDict[LineQuery[i2]['node2']['value']][eqtype].append(eqid)
        EquipDict[eqtype][eqid]['term1'] = LineQuery[i2]['term1']['value']
        EquipDict[eqtype][eqid]['term2'] = LineQuery[i2]['term2']['value']
        EquipDict[eqtype][eqid]['node1'] = LineQuery[i2]['node1']['value']
        EquipDict[eqtype][eqid]['node2'] = LineQuery[i2]['node2']['value']
    gapps_log.debug('Processed ' + str(i2+1) + ' ACLineSegment objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
    
    # Import all PowerTransformer and TransformerTank objects - SECOND PASS
    StartTime = time.process_time()
    XfmrQuery = topology.get_all_transformers(gapps, model_mrid)
    i2 = -1
    for i2 in range(len(XfmrQuery)):
        eqtype = XfmrQuery[i2]['class']['value']
        eqid = XfmrQuery[i2]['eqid']['value']
        seq = str(XfmrQuery[i2]['seq']['value'])
        # Check if transformer not defined when parsing measurements
        if eqid not in EquipDict[eqtype]: EquipDict[eqtype][eqid] = {}
        # Identify terminal sequence and create keys for new terminals
        EquipDict[eqtype][eqid]['bus' + seq] = XfmrQuery[i2]['bus']['value']
        EquipDict[eqtype][eqid]['term' + seq] = XfmrQuery[i2]['tid']['value']
        EquipDict[eqtype][eqid]['node' + seq] = XfmrQuery[i2]['cnid']['value']
        EquipDict[eqtype][eqid]['tname' + seq] = XfmrQuery[i2]['tname']['value']
        if eqid not in ConnNodeDict[XfmrQuery[i2]['cnid']['value']][eqtype]:
            ConnNodeDict[XfmrQuery[i2]['cnid']['value']][eqtype].append(eqid)
        if 'ratedu' in XfmrQuery[i2]: # Add rated voltage if defined
            EquipDict[eqtype][eqid]['volt' + seq] = int(float(XfmrQuery[i2]['ratedu']['value']))
        else: EquipDict[eqtype][eqid]['volt' + seq] = 0 
        if 'phs' in XfmrQuery[i2]:  # Add phase if defined
            EquipDict[eqtype][eqid]['phase' + seq] = XfmrQuery[i2]['phs']['value'] 
        else: EquipDict[eqtype][eqid]['phase' + seq] = {}
    gapps_log.debug('Processed ' + str(i2+1) + ' Transformer objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
    
    # Import all Breaker, Fuse, LoadBreakSwitch, and Recloser objects -  SECOND PASS
    StartTime = time.process_time()
    SwitchQuery = topology.get_all_switches(gapps, model_mrid)
    i3 = -1
    for i3 in range(len(SwitchQuery)):
        eqid = SwitchQuery[i3]['id']['value']
        eqtype = SwitchQuery[i3]['cimtype']['value']
        # Check if switch not defined when parsing measurements
        if eqid not in EquipDict[eqtype]: EquipDict[eqtype][eqid] = {}
        EquipDict[eqtype][eqid]['term1']=SwitchQuery[i3]['term1']['value']
        EquipDict[eqtype][eqid]['term2']=SwitchQuery[i3]['term2']['value']
        EquipDict[eqtype][eqid]['node1']=SwitchQuery[i3]['node1']['value']
        EquipDict[eqtype][eqid]['node2']=SwitchQuery[i3]['node2']['value']
        # Check if switch is open or closed in base model
        if SwitchQuery[i3]['open']['value'] == 'false': 
            EquipDict[eqtype][eqid]['open'] = 1
        else: 
            EquipDict[eqtype][eqid]['open'] = 0
    gapps_log.debug('Processed ' + str(i3+1) + ' Switch objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")


    # Import all House objects
    StartTime = time.process_time()
    HouseQuery = topology.get_all_houses(gapps, model_mrid)
    i4 = -1
    for i4 in range(len(HouseQuery)):
        eqid = HouseQuery[i3]['id']['value']
        eqtype = 'House'
        # Check if house not defined when parsing measurements
        if eqid not in EquipDict[eqtype]: EquipDict[eqtype][eqid] = {}
        EquipDict[eqtype][eqid]['term1']=HouseQuery[i3]['tid']['value']
        EquipDict[eqtype][eqid]['node1']=HouseQuery[i3]['cnid']['value']

    gapps_log.debug('Processed ' + str(i4+1) + ' House objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
    
    # Import all RatioTapChanger objects
    StartTime = time.process_time()
    TapChangerQuery = topology.get_all_tapchangers(gapps, model_mrid)
    eqtype = 'RatioTapChanger'
    i5 = -1
    for i5 in range(len(TapChangerQuery)):
        eqid = TapChangerQuery[i5]['pxfid']['value']
        tankid = TapChangerQuery[i5]['tankid']['value']
        pxfid = TapChangerQuery[i5]['pxfid']['value']
        if tankid in EquipDict['TransformerTank']:
            EquipDict[eqtype][eqid] = dict(EquipDict['TransformerTank'][tankid])
        elif pxfid in EquipDict['PowerTransformer']:
            EquipDict[eqtype][eqid] = dict(EquipDict['PowerTransformer'][pxfid])
        EquipDict[eqtype][eqid]['name'] = TapChangerQuery[i5]['rname']['value']
        EquipDict[eqtype][eqid]['TransformerTank'] = tankid
        EquipDict[eqtype][eqid]['PowerTransformer'] = pxfid
        EquipDict[eqtype][eqid]['node'] = TapChangerQuery[i5]['cnid']['value']
        EquipDict[eqtype][eqid]['term'] = TapChangerQuery[i5]['tid']['value']
    gapps_log.debug('Processed ' + str(i5+1) + ' RatioTapChanger objects in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
        
    return ConnNodeDict, EquipDict