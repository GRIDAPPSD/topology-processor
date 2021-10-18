import time,json



def build_linked_list(Line_query,Xfmr_query,DG_query,Node_query):

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


    # ### Build list of Transformers


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


        


    # ## Add DG source nodes to list



    StartTime = time.process_time()
    #print(len(DG_query))
    for i4 in range(len(DG_query)):
        node=DG_query[i4]['node']['value']
        term=DG_query[i4]['term']['value']
        
        TerminalsDict[term] = {}
        TerminalsDict[term]['term'] = i4+2*(i3+i1+1)+1 #updated index, need to add to end of dict
        TerminalsDict[term]['next'] = 0
        TerminalsDict[term]['far'] = 0
        TerminalsDict[term]['name'] = DG_query[i4]['bus']['value']
        TermList.append(term)

        if node not in ConnNodeDict.keys():
            
            
            TerminalsDict[term]['far'] = index+1
            ConnNodeDict[node] = {}
            ConnNodeDict[node]['name'] = DG_query[i4]['bus']['value']
            ConnNodeDict[node]['node'] = index+1
            ConnNodeDict[node]['list'] = TerminalsDict[term]['term']
            ConnNodeDict[node]['tpid'] = DG_query[i4]['tpid']['value']
            index = index+1
            NodeList.append(node)
    if (len(DG_query)>0):        
        print("Processed ", i4, "generator objects in ", time.process_time() - StartTime, "seconds")


    # ## Add missing nodes to dictionary



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

    return ConnNodeDict,TerminalsDict,Xfmr_dict,XfmrKeys,TermList,NodeList