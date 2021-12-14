import time

def build_linknet_lists(ConnNodeDict, EquipDict, EqTypes):
    # Builds LinkNet linked lists for all CIM classes specified by EqTypes
    index = 0
    counter = 0
    TerminalsDict = {}
    NodeList = []
    TermList = []
    
    # Build LinkNetList for all specified CIM classes:
    for i0 in range(len(EqTypes)):
        [ConnNodeDict, TerminalsDict, NodeList, TermList, index, counter] = build_class_lists(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, EqTypes[i0], index, counter)
    # Add floating nodes not connected to a branch:
    StartTime = time.process_time()
    AllNodes = list(ConnNodeDict.keys())
    MissingNodes = list(set(AllNodes).difference(NodeList))
    for i2 in range(len(MissingNodes)):
        node = MissingNodes[i2]
        if 'list' not in ConnNodeDict[node]:
            ConnNodeDict[node]['node'] = index+1
            ConnNodeDict[node]['list'] = 0
            index = index+1
            NodeList.append(node)
    print("Processed ", len(MissingNodes), "missing nodes in ", time.process_time() - StartTime, "seconds")
    
    return ConnNodeDict, TerminalsDict, NodeList, TermList

def build_class_lists(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, eqtype, index, old_counter):
    i1 = -1
    StartTime = time.process_time()
    EquipKeys = list(EquipDict[eqtype])

    for i1 in range(len(EquipKeys)):
        # Identify nodes and terminals for readability
        term1=EquipDict[eqtype][EquipKeys[i1]]['term1']
        node1=EquipDict[eqtype][EquipKeys[i1]]['node1']
        # Create keys for new terminals
        TerminalsDict[term1] = {}
        TerminalsDict[term1]['ConnectivityNode'] = node1
        
        TermList.append(term1)
        # If node1 not in LinkNet , create new keys
        if 'node' not in ConnNodeDict[node1]:
            ConnNodeDict[node1]['node'] = index+1
            ConnNodeDict[node1]['list'] = 0
            index = index+1
            NodeList.append(node1)
            
        # If two-terminal device, process both terminals
        if 'node2' in EquipDict[eqtype][EquipKeys[i1]]:
            # Identify nodes and terminals for readability
            term2=EquipDict[eqtype][EquipKeys[i1]]['term2']
            node2=EquipDict[eqtype][EquipKeys[i1]]['node2']
            # Create keys for new terminals
            TerminalsDict[term2] = {}
            TerminalsDict[term2]['ConnectivityNode'] = node2
            TerminalsDict[term1]['term'] = 2*(i1+old_counter)+1
            TerminalsDict[term2]['term'] = 2*(i1+old_counter)+2
            TermList.append(term2)
            # If node2 not in LinkNet , create new keys
            if 'node' not in ConnNodeDict[node2]: 
                ConnNodeDict[node2]['node'] = index+1
                ConnNodeDict[node2]['list'] = 0
                index = index+1
                NodeList.append(node2)
            # 1. Move node list variables to terinal next    
            TerminalsDict[term1]['next'] = ConnNodeDict[node1]['list']
            TerminalsDict[term2]['next'] = ConnNodeDict[node2]['list']
            # 2. Populate Terminal list far field with nodes
            TerminalsDict[term1]['far'] = ConnNodeDict[node2]['node']
            TerminalsDict[term2]['far'] = ConnNodeDict[node1]['node']
            # 3. Populate Connectivity nodes list with terminals
            ConnNodeDict[node1]['list'] = TerminalsDict[term1]['term']
            ConnNodeDict[node2]['list'] = TerminalsDict[term2]['term']
            
        # If one-terminal device, process only single terminal
        else:
            TerminalsDict[term1]['term'] = i1+2*(old_counter)+1
            TerminalsDict[term1]['next'] = 0
            TerminalsDict[term1]['far'] = 0
            ConnNodeDict[node1]['list'] = TerminalsDict[term1]['term']
            
    print("Processed ", i1+1, eqtype, "objects in ", time.process_time() - StartTime, "seconds")
    counter = old_counter+i1+1
    return ConnNodeDict, TerminalsDict, NodeList, TermList, index, counter

 