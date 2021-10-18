import time,json

def topology_update(BaseConnDict,BaseTermDict,Switch_query,TermList):

    # ## Merge Topology Nodes

    # Pull base topology Dictionary
    ConnNodeDict = json.loads(BaseConnDict)
    TerminalsDict = json.loads(BaseTermDict)

    StartTime = time.process_time()

    

    for i5 in range(len(Switch_query)):
        #bus1=Switch_query[i5]['bus1']['value']
        #bus2=Switch_query[i5]['bus2']['value']
        #term1=Switch_query[i5]['term1']['value']
        #term2=Switch_query[i5]['term2']['value']
        node1=Switch_query[i5]['node1']['value']
        node2=Switch_query[i5]['node2']['value']
        #tpnode1=Switch_query[i5]['tpnode1']['value']
        #tpnode2=Switch_query[i5]['tpnode2']['value']
        
        # If switch closed, merge nodes
        if Switch_query[i5]['open']['value'] == 'false':
            
            # Merge topology Nodes
            #ConnNodeDict[node1]['tpid'] = tpnode1
            ConnNodeDict[node2]['tpid'] = ConnNodeDict[node1]['tpid'] #tpnode1
            #TopoNodeDict[tpnode1] = [node1, node2] # not implemented
            #TopoNodeDict[tpnode2] = [node2, node1]
            
            # Update Linked Lists
            if ConnNodeDict[node2]['list'] > ConnNodeDict[node1]['list']:
                term2 = TermList[ConnNodeDict[node2]['list']-1]
                next2 = TerminalsDict[term2]['next']
                while next2 != 0:
                    term2 = TermList[next2-1]
                    next2 = TerminalsDict[term2]['next']
                TerminalsDict[term2]['next'] = ConnNodeDict[node1]['list']
                ConnNodeDict[node1]['list'] = ConnNodeDict[node2]['list']
            else:
                term1 = TermList[ConnNodeDict[node1]['list']-1]
                next1 = TerminalsDict[term1]['next']
                while next1 != 0:
                    term1 = TermList[next1-1]
                    next1 = TerminalsDict[term1]['next']
                TerminalsDict[term1]['next'] = ConnNodeDict[node2]['list']
                ConnNodeDict[node2]['list'] = ConnNodeDict[node1]['list']
                
    print("Processed ", i5, "switch objects in ", time.process_time() - StartTime, "seconds")
    return TerminalsDict,ConnNodeDict
