import time

def local_spanning_tree(ConnNodeDict, TerminalsDict, NodeList, TermList, EquipDict, eqtype, RootKeys, Tree, Scope):

    TotalNodes=0
    old_len = len(Tree.keys())
    StartTime = time.process_time()

    # Iterate through all substation transformers
    for i6 in range(len(RootKeys)):
        key = RootKeys[i6]
        Tree[key] = []

        # If switch object, only use second node
        if eqtype in ['Breaker', 'Fuse', 'LoadBreakSwitch', 'Recloser']:
        #, 'SynchronousMachine', 'PowerElectronicsConnection']:
                Tree[key].append(EquipDict[eqtype][key]['node2'])
                FirstNode = 0
                LastNode = 1 # only 1 node, so initialize list at 0,1
        # Otherwise, use both nodes    
        else: # Then 2-terminal object
            not_in_tree = check_tree(EquipDict[eqtype][key]['node2'], Tree, Scope, key)
            if not_in_tree:
                Tree[key].append(EquipDict[eqtype][key]['node1'])
                Tree[key].append(EquipDict[eqtype][key]['node2'])
                FirstNode = 1 
                LastNode = 2 # 2 nodes in starting list, so initialize at 1,2
            else:
                break
        while LastNode != FirstNode:
            NextTerm = ConnNodeDict[Tree[key][FirstNode]]['list']
            FirstNode = FirstNode + 1
            while NextTerm != 0:
                # Get next node and terminal for current node
                NextNode = TerminalsDict[TermList[NextTerm-1]]['far']
                NextTerm = TerminalsDict[TermList[NextTerm-1]]['next']
                node = NodeList[NextNode-1]
                not_in_tree = check_tree(node, Tree, Scope, key)
                # Add node if not in another tree        
                if not_in_tree:       
                    if ConnNodeDict[node]['nominalVoltage']:
                        # Stop building tree into sub-transmission network
                        if int(ConnNodeDict[node]['nominalVoltage']) < 34000: 
                            Tree[key].append(NodeList[NextNode-1])
                            LastNode = LastNode + 1                       
                    else: # Add node to tree if no nominal voltage defined
                        Tree[key].append(NodeList[NextNode-1])
                        LastNode = LastNode + 1

        NodesInTree=len(Tree[key])
        
        
        print("Processed topology from  ",  key, ' with ', NodesInTree, " buses")

        #print("Processed topology from  ", EquipDict[key]['name'], " with id ", key, ' with ', NodesInTree, " buses")
        TotalNodes=TotalNodes+NodesInTree

    print("Processed ", len(Tree.keys()) - old_len, "topology trees containing ", TotalNodes, " buses in ", time.process_time() - StartTime, "seconds")

    return Tree, ConnNodeDict
# function to check if a node is the spanning tree
# use argument "all" to check all trees from all root nodes
# use argument "single" to only check the single tree from current root node
def check_tree(node, Tree, Scope, key):
    not_in_tree = True
    if Scope == 'all': 
        TreeKeys = list(Tree.keys())
        for i7 in range(len(TreeKeys)):
            if node in Tree[TreeKeys[i7]]:
                not_in_tree = False
                break
    else: 
        if node in Tree[key]: 
            not_in_tree = False# Check if node already in all other tree
    return not_in_tree