class TopologyDictionary():
    
    def __init__(self, gapps, model_mrid):
        self.model_mrid = model_mrid
        self.gapps = gapps
        self.EquipDict = {}
        self.ConnNodeDict = {}
        self.TerminalsDict = {}
        self.NodeList = []
        self.TermList = []
        Tree = {}
    
    def build_linknet(self, EqTypes):
        # Builds LinkNet linked lists for all CIM classes specified by EqTypes
        index = 0
        counter = 0
        TerminalsDict = {}
        NodeList = []
        TermList = []

        # Build LinkNetList for all specified CIM classes:
        for i0 in range(len(EqTypes)):
            [index, counter] = self.build_class_lists(EqTypes[i0], index, counter)
        # Add floating nodes not connected to a branch:
        StartTime = time.process_time()
        AllNodes = list(self.ConnNodeDict.keys())
        MissingNodes = list(set(AllNodes).difference(self.NodeList))
        for i2 in range(len(MissingNodes)):
            node = MissingNodes[i2]
            if 'list' not in self.ConnNodeDict[node]:
                self.ConnNodeDict[node]['node'] = index+1
                self.ConnNodeDict[node]['list'] = 0
                index = index+1
                self.NodeList.append(node)
        print("Processed ", len(MissingNodes), "missing nodes in "+ str(round(1000*(time.process_time() - StartTime))) + " ms")

        self.BaseConnDict = json.dumps(self.ConnNodeDict)
        self.BaseTermDict = json.dumps(self.TerminalsDict)


    
    def build_class_lists(self, eqtype, index, old_counter):
        i1 = -1
        StartTime = time.process_time()
        EquipKeys = list(self.EquipDict[eqtype])

        for i1 in range(len(EquipKeys)):
            # Identify nodes and terminals for readability
            term1=self.EquipDict[eqtype][EquipKeys[i1]]['term1']
            node1=self.EquipDict[eqtype][EquipKeys[i1]]['node1']
            # Create keys for new terminals
            self.TerminalsDict[term1] = {}
            self.TerminalsDict[term1]['ConnectivityNode'] = node1

            self.TermList.append(term1)
            # If node1 not in LinkNet , create new keys
            if 'node' not in self.ConnNodeDict[node1]:
                self.ConnNodeDict[node1]['node'] = index+1
                self.ConnNodeDict[node1]['list'] = 0
                index = index+1
                self.NodeList.append(node1)

            # If two-terminal device, process both terminals
            if 'node2' in self.EquipDict[eqtype][EquipKeys[i1]]:
                # Identify nodes and terminals for readability
                term2=self.EquipDict[eqtype][EquipKeys[i1]]['term2']
                node2=self.EquipDict[eqtype][EquipKeys[i1]]['node2']
                # Create keys for new terminals
                self.TerminalsDict[term2] = {}
                self.TerminalsDict[term2]['ConnectivityNode'] = node2
                self.TerminalsDict[term1]['term'] = 2*(i1+old_counter)+1
                self.TerminalsDict[term2]['term'] = 2*(i1+old_counter)+2
                self.TermList.append(term2)
                # If node2 not in LinkNet , create new keys
                if 'node' not in self.ConnNodeDict[node2]: 
                    self.ConnNodeDict[node2]['node'] = index+1
                    self.ConnNodeDict[node2]['list'] = 0
                    index = index+1
                    self.NodeList.append(node2)
                # 1. Move node list variables to terinal next    
                self.TerminalsDict[term1]['next'] = self.ConnNodeDict[node1]['list']
                self.TerminalsDict[term2]['next'] = self.ConnNodeDict[node2]['list']
                # 2. Populate Terminal list far field with nodes
                self.TerminalsDict[term1]['far'] = self.ConnNodeDict[node2]['node']
                self.TerminalsDict[term2]['far'] = self.ConnNodeDict[node1]['node']
                # 3. Populate Connectivity nodes list with terminals
                self.ConnNodeDict[node1]['list'] = self.TerminalsDict[term1]['term']
                self.ConnNodeDict[node2]['list'] = self.TerminalsDict[term2]['term']

            # If one-terminal device, process only single terminal
            else:
                self.TerminalsDict[term1]['term'] = i1+2*(old_counter)+1
                self.TerminalsDict[term1]['next'] = 0
                self.TerminalsDict[term1]['far'] = 0
                self.ConnNodeDict[node1]['list'] = self.TerminalsDict[term1]['term']

        print("Processed " + str(i1+1) + str(eqtype) + "objects in " + str(round(1000*(time.process_time() - StartTime))) + " ms")

        counter = old_counter+i1+1
        return index, counter
    


    def update_switches(self):

        SwitchKeys = list(EquipDict['Breaker'].keys()) + list(EquipDict['Fuse'].keys()) + list(EquipDict['LoadBreakSwitch'].keys()) + list(EquipDict['Recloser'].keys())
        SwitchDict = {}
        SwitchDict.update(EquipDict['Breaker'])
        SwitchDict.update(EquipDict['Fuse'])
        SwitchDict.update(EquipDict['LoadBreakSwitch'])
        SwitchDict.update(EquipDict['Recloser'])

        self.ConnNodeDict = json.loads(self.BaseConnDict)
        self.TerminalsDict = json.loads(self.BaseTermDict)

        StartTime = time.process_time()

        for i5 in range(len(SwitchKeys)):

            node1=SwitchDict[SwitchKeys[i5]]['node1']
            node2=SwitchDict[SwitchKeys[i5]]['node2']


            # If switch closed, merge nodes
            if SwitchDict[SwitchKeys[i5]]['open'] == 1:
                # Merge topology Nodes
                #ConnNodeDict[node1]['TopologicalNode'] = tpnode1
                self.ConnNodeDict[node2]['TopologicalNode'] = self.ConnNodeDict[node1]['TopologicalNode'] #tpnode1
                #TopoNodeDict[tpnode1] = [node1, node2] # not implemented
                #TopoNodeDict[tpnode2] = [node2, node1]

                # Update Linked Lists
                if self.ConnNodeDict[node2]['list'] > self.ConnNodeDict[node1]['list']:
                    term2 = self.TermList[self.ConnNodeDict[node2]['list']-1]
                    next2 = self.TerminalsDict[term2]['next']
                    while next2 != 0:
                        term2 = self.TermList[next2-1]
                        next2 = self.TerminalsDict[term2]['next']
                    self.TerminalsDict[term2]['next'] = self.ConnNodeDict[node1]['list']
                    self.ConnNodeDict[node1]['list'] = self.ConnNodeDict[node2]['list']
                else:
                    term1 = self.TermList[self.ConnNodeDict[node1]['list']-1]
                    next1 = self.TerminalsDict[term1]['next']
                    while next1 != 0:
                        term1 = self.TermList[next1-1]
                        next1 = self.TerminalsDict[term1]['next']
                    self.TerminalsDict[term1]['next'] = self.ConnNodeDict[node2]['list']
                    self.ConnNodeDict[node2]['list'] = self.ConnNodeDict[node1]['list']

        print("Processed " + str(i5+1) + "switch objects in " + str(round(1000*(time.process_time() - StartTime))) + " ms")



    
    def spanning_tree(self, eqtype, RootKeys, Tree, Scope):

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
                    Tree[key].append(self.EquipDict[eqtype][key]['node2'])
                    FirstNode = 0
                    LastNode = 1 # only 1 node, so initialize list at 0,1
            # Otherwise, use both nodes    
            else: # Then 2-terminal object
                not_in_tree = self.check_tree(self.EquipDict[eqtype][key]['node2'], Tree, Scope, key)
                if not_in_tree:
                    Tree[key].append(self.EquipDict[eqtype][key]['node1'])
                    Tree[key].append(self.EquipDict[eqtype][key]['node2'])
                    FirstNode = 1 
                    LastNode = 2 # 2 nodes in starting list, so initialize at 1,2
                else:
                    break
            while LastNode != FirstNode:
                NextTerm = self.ConnNodeDict[Tree[key][FirstNode]]['list']
                FirstNode = FirstNode + 1
                while NextTerm != 0:
                    # Get next node and terminal for current node
                    NextNode = self.TerminalsDict[self.TermList[NextTerm-1]]['far']
                    NextTerm = self.TerminalsDict[self.TermList[NextTerm-1]]['next']
                    node = self.NodeList[NextNode-1]
                    not_in_tree = self.check_tree(node, Tree, Scope, key)
                    # Add node if not in another tree        
                    if not_in_tree:       
                        if self.ConnNodeDict[node]['nominalVoltage']:
                            # Stop building tree into sub-transmission network
                            if int(self.ConnNodeDict[node]['nominalVoltage']) < 34000: 
                                Tree[key].append(self.NodeList[NextNode-1])
                                LastNode = LastNode + 1                       
                        else: # Add node to tree if no nominal voltage defined
                            Tree[key].append(self.NodeList[NextNode-1])
                            LastNode = LastNode + 1


            print("Processed topology from  " + str(key) + ' with ' + str(len(Tree[key])) + " buses")

        print("Processed " + str(len(Tree.keys()) - old_len) + "topology trees containing " + str(TotalNodes+len(Tree[key])) + " buses in " + str(round(1000*(time.process_time() - StartTime))) + " ms")

        return Tree
    
    # function to check if a node is the spanning tree
    # use argument "all" to check all trees from all root nodes
    # use argument "single" to only check the single tree from current root node
    def check_tree(self, node, Tree, Scope, key):
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