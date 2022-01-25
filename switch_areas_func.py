import time, sys, json
import topo_meas_queries
import process_network
import linknet
import update_topology
import spanning_tree




def create_switch_areas(gapps, model_mrid):
    gapps_log = gapps.get_logger()
    gapps_log.debug('Querying for power system model')
    [ConnNodeDict, EquipDict] = process_network.build_equip_dicts(gapps, model_mrid)
    BaseConnDict = json.dumps(ConnNodeDict)
    MVConnNodeDict = json.loads(BaseConnDict)
    gapps_log.debug('Building linked lists of all equipment')
    EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine']
    [ConnNodeDict, TerminalsDict, NodeList, TermList] = linknet.build_linknet_lists(ConnNodeDict, EquipDict, EqTypes)
    gapps_log.debug('Building linked lists of medium-voltage equipment')
    EqTypes = ['ACLineSegment', 'RatioTapChanger', 'SynchronousMachine']
    [MVConnNodeDict, MVTerminalsDict, MVNodeList, MVTermList] = linknet.build_linknet_lists(MVConnNodeDict, EquipDict, EqTypes)
    gapps_log.debug('Processing switch-delimited areas')
    MVTrees = {}
    [MVTrees, MVConnNodeDict] = spanning_tree.local_spanning_tree(MVConnNodeDict, MVTerminalsDict, MVNodeList, MVTermList, EquipDict, 'Breaker', list(EquipDict['Breaker'].keys()), MVTrees, 'all')
    [MVTrees, MVConnNodeDict] = spanning_tree.local_spanning_tree(MVConnNodeDict, MVTerminalsDict, MVNodeList, MVTermList, EquipDict, 'Fuse', list(EquipDict['Fuse'].keys()), MVTrees, 'all')
    [MVTrees, MVConnNodeDict] = spanning_tree.local_spanning_tree(MVConnNodeDict, MVTerminalsDict, MVNodeList, MVTermList, EquipDict, 'LoadBreakSwitch', list(EquipDict['LoadBreakSwitch'].keys()), MVTrees, 'all')
    [MVTrees, MVConnNodeDict] = spanning_tree.local_spanning_tree(MVConnNodeDict, MVTerminalsDict, MVNodeList, MVTermList, EquipDict, 'Recloser', list(EquipDict['Recloser'].keys()), MVTrees, 'all')

    output_message = create_output_message(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, MVTrees, model_mrid)
    message = json.dumps(output_message)
    return message
    
def create_output_message(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, MVTrees, model_mrid):
    # Initialize output message structure
    DistAppStruct = {}
    DistAppStruct['feeders'] = {}
    DistAppStruct['feeders'][model_mrid] = {}
    DistAppStruct['feeders'][model_mrid]['addressable_equipment'] = []
    DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'] = []
    DistAppStruct['feeders'][model_mrid]['connectivity_node'] = []
    DistAppStruct['feeders'][model_mrid]['switch_areas'] = []
    ProcessedNodes = [] # List to keep track of which nodes have been processed
    SwitchKeys = list(MVTrees.keys()) # Get list of all switching devices from all CIM classes
    # Iterate through all switches
    for i1 in range(len(SwitchKeys)):
        # Initialize switch area dictionary
        SwitchArea = {}
        SwitchArea['boundary_switches'] = []
        SwitchArea['addressable_equipment'] = []
        SwitchArea['unaddressable_equipment'] = []
        SwitchArea['connectivity_node'] = []
        SwitchArea['secondary_areas'] = []
        # Initialize secondary area dictionary
        DistArea = {}
        DistArea['distribution_transformer'] = []
        DistArea['addressable_equipment'] = []
        DistArea['unaddressable_equipment'] = []
        DistArea['connectivity_node'] = []
        DistAreaFlag1 = True
        for i2 in range(len(MVTrees[SwitchKeys[i1]])):
            # Select next medium-voltage node, append to processed list
            node = MVTrees[SwitchKeys[i1]][i2]
            ProcessedNodes.append(node)
            # Add all connected equipment
            SwitchArea['boundary_switches'].extend(ConnNodeDict[node]['Breaker'])
            SwitchArea['boundary_switches'].extend(ConnNodeDict[node]['Fuse'])
            SwitchArea['boundary_switches'].extend(ConnNodeDict[node]['LoadBreakSwitch'])
            SwitchArea['boundary_switches'].extend(ConnNodeDict[node]['Recloser'])
            SwitchArea['addressable_equipment'].extend(ConnNodeDict[node]['SynchronousMachine'])
            SwitchArea['addressable_equipment'].extend(ConnNodeDict[node]['PowerElectronicsConnection'])
            SwitchArea['addressable_equipment'].extend(ConnNodeDict[node]['LinearShuntCompensator'])
            SwitchArea['addressable_equipment'].extend(ConnNodeDict[node]['RatioTapChanger'])
            SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[node]['ACLineSegment'])
            SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[node]['PowerTransformer'])
            SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[node]['TransformerTank'])
            SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[node]['Measurement'])
            SwitchArea['connectivity_node'].append(ConnNodeDict[node]['name'])
            # Identify PowerTransformer and TransformerTanks for secondary areas
            DistXfmrTanks = ConnNodeDict[node]['TransformerTank'] 
            DistXfmrs = ConnNodeDict[node]['PowerTransformer']
            if DistXfmrs: # Check all PowerTransformers connected to this node
                DistAreaFlag1 = False
                SwitchArea['unaddressable_equipment'].extend(DistXfmrs)
                [SwitchArea, LVNodes] = create_dist_area(ConnNodeDict, TerminalsDict, NodeList, TermList, MVTrees, DistXfmrs, EquipDict, 'PowerTransformer', SwitchArea.copy())
                ProcessedNodes.extend(LVNodes)
            if DistXfmrTanks: # Check all TransformerTanks connected to this node
                DistAreaFlag1 = False
                SwitchArea['unaddressable_equipment'].extend(DistXfmrTanks)
                [SwitchArea, LVNodes] = create_dist_area(ConnNodeDict, TerminalsDict, NodeList, TermList, MVTrees, DistXfmrTanks, EquipDict, 'TransformerTank', SwitchArea.copy())
                ProcessedNodes.extend(LVNodes)

        if DistAreaFlag1: # Append empty dictionary if no secondary areas
            SwitchArea['secondary_areas'].append((DistArea.copy()))

        if SwitchArea['boundary_switches']: # Append switch area if not duplicate
            DistAppStruct['feeders'][model_mrid]['switch_areas'].append(dict(SwitchArea))
            DistAppStruct['feeders'][model_mrid]['addressable_equipment'].extend(SwitchArea['boundary_switches'])
            DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'].extend(SwitchArea['unaddressable_equipment'])
            
    # Add missing nodes to feeder level (not in switch area or secondary area)
    AllNodes = list(ConnNodeDict.keys())
    MissingNodes = list(set(AllNodes).difference(ProcessedNodes))
    for i5 in range(len(MissingNodes)):
        node = MissingNodes[i5]
        DistAppStruct['feeders'][model_mrid]['addressable_equipment'].extend(ConnNodeDict[node]['SynchronousMachine'])
        DistAppStruct['feeders'][model_mrid]['addressable_equipment'].extend(ConnNodeDict[node]['PowerElectronicsConnection'])
        DistAppStruct['feeders'][model_mrid]['addressable_equipment'].extend(ConnNodeDict[node]['LinearShuntCompensator'])
        DistAppStruct['feeders'][model_mrid]['addressable_equipment'].extend(ConnNodeDict[node]['RatioTapChanger'])
        DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'].extend(ConnNodeDict[node]['ACLineSegment'])
        DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'].extend(ConnNodeDict[node]['PowerTransformer'])
        DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'].extend(ConnNodeDict[node]['TransformerTank'])
        DistAppStruct['feeders'][model_mrid]['unaddressable_equipment'].extend(ConnNodeDict[node]['Measurement'])
        DistAppStruct['feeders'][model_mrid]['connectivity_node'].append(node)
        
    return DistAppStruct
    
def create_dist_area(ConnNodeDict, TerminalsDict, NodeList, TermList, MVTree, Xfmrs, EquipDict, eqtype, SwitchArea):
    # Initialize secondary area dictionary
    DistArea = {}
    DistArea['distribution_transformer'] = []
    DistArea['addressable_equipment'] = []
    DistArea['unaddressable_equipment'] = []
    DistArea['connectivity_node'] = []
    LVNodes = []
    DistAreaFlag2 = False
    # Iterate through all secondary transformers
    for i3 in range(len(Xfmrs)):
        xfmr = Xfmrs[i3]
        [LVTree, LVConnNodeDict] = spanning_tree.local_spanning_tree(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, eqtype, [xfmr],  MVTree, 'all')
        LVTreeKeys = LVTree[xfmr]
        if LVTreeKeys: 
            LVTreeKeys.pop(0) # dump first node (xfmr hi-side, duplicate)
            for i4 in range(len(LVTreeKeys)):
                lvnode = LVTreeKeys[i4]
                DistAreaFlag2 = True
                LVNodes.append(lvnode)
                DistArea['distribution_transformer'] = [xfmr]
                DistArea['addressable_equipment'].extend(ConnNodeDict[lvnode]['SynchronousMachine'])
                DistArea['addressable_equipment'].extend(ConnNodeDict[lvnode]['PowerElectronicsConnection'])
                DistArea['addressable_equipment'].extend(ConnNodeDict[lvnode]['EnergyConsumer'])
                DistArea['addressable_equipment'].extend(ConnNodeDict[lvnode]['House'])
                DistArea['unaddressable_equipment'].extend(ConnNodeDict[lvnode]['ACLineSegment'])
                DistArea['unaddressable_equipment'].extend(ConnNodeDict[lvnode]['Measurement'])
                DistArea['connectivity_node'].append(lvnode)
                SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[lvnode]['ACLineSegment'])
                SwitchArea['unaddressable_equipment'].extend(ConnNodeDict[lvnode]['Measurement'])
    if DistAreaFlag2: # append secondary area if not empty
        SwitchArea['secondary_areas'].append((DistArea.copy()))
    return SwitchArea, LVNodes