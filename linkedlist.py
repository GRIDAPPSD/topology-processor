import time,json



def build_linked_list(Line_query,XfmrDict,XfmrKeys,DG_query,Node_query):

    index=0
    ConnNodeDict = {}
    TerminalsDict = {}
    NodeList = []
    TermList = []
    
    StartTime = time.process_time()

    for i0 in range(len(Node_query)):
        node=Node_query[i0]['cnid']['value']
        
        ConnNodeDict[node] = {}
        ConnNodeDict[node]['name'] = Node_query[i0]['busname']['value']
        ConnNodeDict[node]['tpid'] = Node_query[i0]['tpnid']['value']
        if 'nomv' in Node_query[i0]: 
            ConnNodeDict[node]['nomv'] = Node_query[i0]['nomv']['value']
        else:
            ConnNodeDict[node]['nomv'] = []
        ConnNodeDict[node]['ACLineSegment.name'] = []
        ConnNodeDict[node]['ACLineSegment.mRID'] = []
        ConnNodeDict[node]['TransformerEnd.name'] = []
        ConnNodeDict[node]['TransformerEnd.mRID'] = []
        ConnNodeDict[node]['switch.name'] = []
        ConnNodeDict[node]['switch.mRID'] = []
        ConnNodeDict[node]['SynchronousMachine.name'] = []
        ConnNodeDict[node]['SynchronousMachine.mRID'] = []

    print("Processed ", i0+1, "buses in ", time.process_time() - StartTime, "seconds")

    StartTime = time.process_time()

    for i1 in range(len(Line_query)):
        lname=Line_query[i1]['name']['value']
        bus1=Line_query[i1]['bus1']['value']
        bus2=Line_query[i1]['bus2']['value']
        line_mrid=Line_query[i1]['id']['value']
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
        if 'node' not in ConnNodeDict[node1]:

            ConnNodeDict[node1]['node'] = index+1
            ConnNodeDict[node1]['list'] = 0
            index = index+1
            NodeList.append(node1)

        if 'node' not in ConnNodeDict[node2]: 
            ConnNodeDict[node2]['node'] = index+1
            ConnNodeDict[node2]['list'] = 0
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
        
        # 4. Update other node properties
        ConnNodeDict[node1]['ACLineSegment.name'].append(lname)
        ConnNodeDict[node2]['ACLineSegment.name'].append(lname)
        ConnNodeDict[node1]['ACLineSegment.mRID'].append(line_mrid)
        ConnNodeDict[node2]['ACLineSegment.mRID'].append(line_mrid)
        
    print("Processed ", i1+1, "line objects in ", time.process_time() - StartTime, "seconds")


    # Build list of Transformers
    i3=-1
    i1=i1+1
    StartTime = time.process_time()

    for i3 in range(len(XfmrKeys)):
        
        bus1=XfmrDict[XfmrKeys[i3]]['bus1']
        bus2=XfmrDict[XfmrKeys[i3]]['bus2']
        term1=XfmrDict[XfmrKeys[i3]]['term1']
        term2=XfmrDict[XfmrKeys[i3]]['term2']
        tname1=XfmrDict[XfmrKeys[i3]]['tname1']
        tname2=XfmrDict[XfmrKeys[i3]]['tname2']
        node1=XfmrDict[XfmrKeys[i3]]['node1']
        node2=XfmrDict[XfmrKeys[i3]]['node2']
        
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
        if 'node' not in ConnNodeDict[node1]:
            ConnNodeDict[node1]['node'] = index+1
            ConnNodeDict[node1]['list'] = 0
            index = index+1
            NodeList.append(node1)

        if 'node' not in ConnNodeDict[node2]: 
            ConnNodeDict[node2]['node'] = index+1
            ConnNodeDict[node2]['list'] = 0
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
        
        # 4. Update other node properties

        ConnNodeDict[node1]['TransformerEnd.name'].append(tname1)
        ConnNodeDict[node1]['TransformerEnd.mRID'].append(XfmrKeys[i3])

        ConnNodeDict[node2]['TransformerEnd.name'].append(tname2)
        ConnNodeDict[node2]['TransformerEnd.mRID'].append(XfmrKeys[i3])

        
        #NEED TO INSERT LOGIC TO HANDLE THREE-WINDING SUBSTATION XFMR
        
    print("Processed ", i3+1, "transformer objects in ", time.process_time() - StartTime, "seconds")


    # Add DG source nodes to list
    i4=-1
    StartTime = time.process_time()
    #print(len(DG_query))
    for i4 in range(len(DG_query)):
        node=DG_query[i4]['node']['value']
        term=DG_query[i4]['term']['value']
        name=DG_query[i4]['name']['value']
        TerminalsDict[term] = {}
        TerminalsDict[term]['term'] = i4+2*(i3+i1+1)+1 #updated index, need to add to end of dict
        TerminalsDict[term]['next'] = 0
        TerminalsDict[term]['far'] = 0
        TerminalsDict[term]['name'] = DG_query[i4]['bus']['value']
        TermList.append(term)

        if 'list' not in ConnNodeDict[node]:            
            TerminalsDict[term]['far'] = index+1
            ConnNodeDict[node]['node'] = index+1
            ConnNodeDict[node]['list'] = TerminalsDict[term]['term']
            index = index+1
            NodeList.append(node)
            #ConnNodeDict[node]['SynchronousMachine.name'].append(name)
            #ConnNodeDict[node]['SynchronousMachine.mRID'].append(DG_query[i4]['eqid']['value'])
            
    if (len(DG_query)>0):        
        print("Processed ", i4+1, "generator objects in ", time.process_time() - StartTime, "seconds")


    # Add missing nodes to dictionary

    StartTime = time.process_time()
    old_index = index
    for i5 in range(len(Node_query)):
        node=Node_query[i5]['cnid']['value']
        if 'list' not in ConnNodeDict[node]:
            ConnNodeDict[node]['node'] = index+1
            ConnNodeDict[node]['list'] = 0
            index = index+1
            NodeList.append(node)
            
    print("Processed ", index-old_index, "missing nodes in ", time.process_time() - StartTime, "seconds")

    return ConnNodeDict,TerminalsDict,TermList,NodeList