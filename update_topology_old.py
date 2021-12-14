import time,json

def topology_update(BaseConnDict,BaseTermDict,SwitchDict,SwitchKeys,TermList):

    # ## Merge Topology Nodes

    # Pull base topology Dictionary
    ConnNodeDict = json.loads(BaseConnDict)
    TerminalsDict = json.loads(BaseTermDict)

    StartTime = time.process_time()

    for i5 in range(len(SwitchKeys)):

        node1=SwitchDict[SwitchKeys[i5]]['node1']
        node2=SwitchDict[SwitchKeys[i5]]['node2']


        # If switch closed, merge nodes
        if SwitchDict[SwitchKeys[i5]]['open'] == 1:
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

    print("Processed ", i5+1, "switch objects in ", time.process_time() - StartTime, "seconds")
    return TerminalsDict,ConnNodeDict
