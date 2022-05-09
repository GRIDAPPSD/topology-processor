import time, json

class TopologyDictionary():
    
    def __init__(self, gapps, model_mrid):
        self.model_mrid = model_mrid
        self.gapps = gapps
        self.EquipDict = {}
        self.ConnNodeDict = {}
        self.TerminalsDict = {}
        self.NodeList = []
        self.TermList = []
        self.Feeders = {}
        self.Islands = {}
        self.log = self.gapps.get_logger()
        Tree = {}
        
    # Builds LinkNet linked lists for all CIM classes specified by EqTypes
    def build_linknet(self, EqTypes):
        # Intialize counter objects
        index = 0
        counter = 0
        # Build LinkNetList for all specified CIM classes:
        for i0 in range(len(EqTypes)): 
            [index, counter] = self.build_class_lists(EqTypes[i0], index, counter)
        # Add floating nodes not connected to a branch:
        StartTime = time.process_time()
        AllNodes = list(self.ConnNodeDict.keys())
        MissingNodes = list(set(AllNodes).difference(self.NodeList))
        for i1 in range(len(MissingNodes)):
            node = MissingNodes[i1]
            if 'list' not in self.ConnNodeDict[node]:
                self.ConnNodeDict[node]['node'] = index+1
                self.ConnNodeDict[node]['list'] = 0
                index = index+1
                self.NodeList.append(node)
        self.log.info("Processed " + str(len(MissingNodes)) + " missing nodes in " + str(round(1000*(time.process_time() - StartTime))) + " ms")
        # Dump JSON copies of base LinkNet structure. These are used to rebuild topo after each switch change
        self.BaseConnDict = json.dumps(self.ConnNodeDict)
        self.BaseTermDict = json.dumps(self.TerminalsDict)


    # Build LinkNet structure for single CIM equipment type, called by build_linknet()
    # Three-winding transformers not yet supported
    def build_class_lists(self, eqtype, index, old_counter):
        i2 = -1
        StartTime = time.process_time()
        EquipKeys = list(self.EquipDict[eqtype])

        for i2 in range(len(EquipKeys)):
            # Identify nodes and terminals for readability
            term1=self.EquipDict[eqtype][EquipKeys[i2]]['term1']
            node1=self.EquipDict[eqtype][EquipKeys[i2]]['node1']
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
            if 'node2' in self.EquipDict[eqtype][EquipKeys[i2]]:
                # Identify nodes and terminals for readability
                term2=self.EquipDict[eqtype][EquipKeys[i2]]['term2']
                node2=self.EquipDict[eqtype][EquipKeys[i2]]['node2']
                # Create keys for new terminals
                self.TerminalsDict[term2] = {}
                self.TerminalsDict[term2]['ConnectivityNode'] = node2
                self.TerminalsDict[term1]['term'] = 2*(i2+old_counter)+1
                self.TerminalsDict[term2]['term'] = 2*(i2+old_counter)+2
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
                self.TerminalsDict[term1]['term'] = i2+2*(old_counter)+1
                self.TerminalsDict[term1]['next'] = 0
                if self.ConnNodeDict[node1]['node'] == index:
                    self.TerminalsDict[term1]['far'] = index
                    self.ConnNodeDict[node1]['list'] = self.TerminalsDict[term1]['term']
                else:
                    self.TerminalsDict[term1]['far'] = 0
                    self.ConnNodeDict[node1]['list'] = 0

        self.log.info("Processed " + str(i2+1) + ' ' + str(eqtype) + " objects in " + str(round(1000*(time.process_time() - StartTime))) + " ms")

        counter = old_counter+i2+1
        return index, counter
    

    # Method to update Linknet Lists with current switch positions
    def update_switches(self):

        SwitchKeys = list(self.EquipDict['Breaker'].keys()) + list(self.EquipDict['Fuse'].keys()) + list(self.EquipDict['LoadBreakSwitch'].keys()) + list(self.EquipDict['Recloser'].keys())
        SwitchDict = {}
        SwitchDict.update(self.EquipDict['Breaker'])
        SwitchDict.update(self.EquipDict['Fuse'])
        SwitchDict.update(self.EquipDict['LoadBreakSwitch'])
        SwitchDict.update(self.EquipDict['Recloser'])

        self.ConnNodeDict = json.loads(self.BaseConnDict)
        self.TerminalsDict = json.loads(self.BaseTermDict)

        StartTime = time.process_time()
        i3 = -1
        for i3 in range(len(SwitchKeys)):

            node1=SwitchDict[SwitchKeys[i3]]['node1']
            node2=SwitchDict[SwitchKeys[i3]]['node2']


            # If switch closed, merge nodes
            if SwitchDict[SwitchKeys[i3]]['open'] == 1:
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

        self.log.info("Processed " + str(i3+1) + "switch objects in " + str(round(1000*(time.process_time() - StartTime))) + " ms")

    def build_feeder_islands(self):
        self.Feeders = {}
        self.Islands = {}
        FeederTree = {}
        fdr = -1
        isl = -1
        
        # Iterate through all PowerTransfomer objects
        XfmrKeys = list(self.EquipDict['PowerTransformer'].keys())
        StartTime = time.process_time()
        for i4 in range(len(XfmrKeys)):
            SubXfmr = XfmrKeys[i4]
            # Identify substation transfomers with high-side >34kV and low-side >1kV
            volt1 = self.EquipDict['PowerTransformer'][SubXfmr]['volt1']
            volt2 = self.EquipDict['PowerTransformer'][SubXfmr]['volt2']
            if volt1 >= 34000 and 34000 >= volt2 >= 1000:
                fdr = fdr + 1
                self.spanning_tree('PowerTransformer', [SubXfmr], FeederTree, 'single') 
                 # Add nodes to Feeder dictionary
                self.Feeders['feeder_' + str(fdr)] = {}
                self.Feeders['feeder_' + str(fdr)]['root_node'] = self.EquipDict['PowerTransformer'][SubXfmr]['node2']
                self.Feeders['feeder_' + str(fdr)]['PowerTransformer'] = SubXfmr
                self.Feeders['feeder_' + str(fdr)]['ConnectivityNode'] = FeederTree[SubXfmr] 
                # Add feeder to Node dictionary
                for i5 in range(len(FeederTree[SubXfmr])): 
                    self.ConnNodeDict[FeederTree[SubXfmr][i5]]['Feeder'].append(('feeder_' + str(fdr)))
        self.log.info('Processed ' + str(fdr + 1) + ' feeders in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
        
        # If no suitable PowerTransformer found, build from EnergySource
        if not self.Feeders:
            Sources = list(self.EquipDict['EnergySource'].keys())
            StartTime = time.process_time()
            for i4 in range(len(Sources)):
                Sub = Sources[i4]
                fdr = fdr + 1
                self.spanning_tree('EnergySource', [Sub], FeederTree, 'single') 
                 # Add nodes to Feeder dictionary
                self.Feeders['feeder_' + str(fdr)] = {}
                self.Feeders['feeder_' + str(fdr)]['root_node'] = self.EquipDict['EnergySource'][Sub]['node1']
                self.Feeders['feeder_' + str(fdr)]['EnergySource'] = Sub
                
                self.Feeders['feeder_' + str(fdr)]['ConnectivityNode'] = FeederTree[Sub] 
                # Add feeder to Node dictionary
                for i5 in range(len(FeederTree[Sub])): 
                    self.ConnNodeDict[FeederTree[Sub][i5]]['Feeder'].append(('feeder_' + str(fdr)))
            self.log.info('Processed ' + str(fdr + 1) + ' feeders in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")
        
        # Iterate through all SynchronousMachine objects
        StartTime = time.process_time()
        IslandTree = {}
        DGKeys = list(self.EquipDict['SynchronousMachine'].keys())
        for i6 in range(len(DGKeys)):
            DG = DGKeys[i6]
            DGNode = self.EquipDict['SynchronousMachine'][DG]['node1']
            [not_in_feeder, found] = self.check_tree(DGNode, FeederTree, 'all', DG)
            if not_in_feeder:
                #IslandTree[DG] = {}
                [not_in_island, found] = self.check_tree(DGNode, IslandTree, 'all', DG)
                if not_in_island:
                    isl = isl + 1
                    self.spanning_tree('SynchronousMachine', [DG], IslandTree, 'single')
                    self.Islands['island_' + str(isl)] = {}
                    self.Islands['island_' + str(isl)]['SynchronousMachine'] = [DG]
                    self.Islands['island_' + str(isl)]['ConnectivityNode'] = IslandTree[DG] 
                    
                    # Add island to Node dictionary
                    for i7 in range(len(IslandTree[DG])): 
                        self.ConnNodeDict[IslandTree[DG][i7]]['Island'].append(('island_' + str(isl)))
                else:
                    self.Islands['island_' + str(isl)]['SynchronousMachine'].append(DGKeys[i6])
        self.log.info('Processed ' + str(isl + 1) + ' islands in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")


        # Iterate through all PowerElectronicsConnection objects
        StartTime = time.process_time()
        DERKeys = list(self.EquipDict['PowerElectronicsConnection'].keys())
        for i6 in range(len(DERKeys)):
            DER = DERKeys[i6]
            DERNode = self.EquipDict['PowerElectronicsConnection'][DER]['node1']
            [not_in_feeder, found] = self.check_tree(DERNode, FeederTree, 'all', DER)
            if not_in_feeder:
                #IslandTree[DG] = {}
                [not_in_island, found] = self.check_tree(DERNode, IslandTree, 'all', DER)
                if not_in_island:
                    isl = isl + 1
                    self.spanning_tree('PowerElectronicsConnection', [DER], IslandTree, 'single')
                    self.Islands['island_' + str(isl)] = {}
                    self.Islands['island_' + str(isl)]['PowerElectronicsConnection'] = [DER]
                    self.Islands['island_' + str(isl)]['ConnectivityNode'] = IslandTree[DER] 
                    
                    # Add island to Node dictionary
                    for i7 in range(len(IslandTree[DER])): 
                        self.ConnNodeDict[IslandTree[DER][i7]]['Island'].append(('island_' + str(isl)))
                else:
                    self.Islands['island_' + str(isl)]['SynchronousMachine'].append(DGKeys[i6])
        self.log.info('Processed ' + str(isl + 1) + ' islands in ' + str(round(1000*(time.process_time() - StartTime))) + " ms")        
    
    def spanning_tree(self, eqtype, RootKeys, Tree, Scope):
        root = ''
        TotalNodes=0
        old_len = len(Tree.keys())
        StartTime = time.process_time()

        
        for i6 in range(len(RootKeys)):
            root = RootKeys[i6]
            Tree[root] = []

            # If switch object, only use second node
            if eqtype in ['Breaker', 'Fuse', 'LoadBreakSwitch', 'Recloser']:
                Tree[root].append(self.EquipDict[eqtype][root]['node2'])
                FirstNode = 0
                LastNode = 1 # only 1 node used, so initialize list at 0,1
            # If DER object, only has one node
            elif eqtype in ['SynchronousMachine', 'PowerElectronicsConnection', 'EnergySource']:
                #[not_in_tree, found] = self.check_tree(self.EquipDict[eqtype][root]['node1'], Tree, Scope, root)
               # if not_in_tree:
                Tree[root].append(self.EquipDict[eqtype][root]['node1'])
                FirstNode = 0 
                LastNode = 1 # only 1 node exists, so initialize list at 0,1
                #else:
                    
            # Otherwise, use both nodes    
            else: # Then 2-terminal object

                [not_in_tree, found] = self.check_tree(self.EquipDict[eqtype][root]['node2'], Tree, Scope, root)
                if not_in_tree:
                    Tree[root].append(self.EquipDict[eqtype][root]['node1'])
                    Tree[root].append(self.EquipDict[eqtype][root]['node2'])
                    FirstNode = 1 
                    LastNode = 2 # 2 nodes in starting list, so initialize at 1,2
                else:
                    break
            while LastNode != FirstNode:
                NextTerm = self.ConnNodeDict[Tree[root][FirstNode]]['list']
                FirstNode = FirstNode + 1
                while NextTerm != 0:
                    # Get next node and terminal for current node
                    NextNode = self.TerminalsDict[self.TermList[NextTerm-1]]['far']
                    NextTerm = self.TerminalsDict[self.TermList[NextTerm-1]]['next']
                    node = self.NodeList[NextNode-1]
                    [not_in_tree, found] = self.check_tree(node, Tree, Scope, root)
                    # Add node if not in another tree        
                    if not_in_tree:       
                        if self.ConnNodeDict[node]['nominalVoltage']:
                            # Stop building tree into sub-transmission network
                            if int(self.ConnNodeDict[node]['nominalVoltage']) < 34000: 
                                Tree[root].append(self.NodeList[NextNode-1])
                                LastNode = LastNode + 1                       
                        else: # Add node to tree if no nominal voltage defined
                            Tree[root].append(self.NodeList[NextNode-1])
                            LastNode = LastNode + 1


            self.log.info("Processed topology from  " + str(root) + ' with ' + str(len(Tree[root])) + " buses")

        if root: self.log.info("Processed " + str(len(Tree.keys()) - old_len) + " topology trees containing " + str(TotalNodes+len(Tree[root])) + " buses in " + str(round(1000*(time.process_time() - StartTime))) + " ms")

        return Tree
    
    # function to check if a node is the spanning tree
    # use argument "all" to check all trees from all root nodes
    # use argument "single" to only check the single tree from current root node
    # node is ConnectivityNode mRID to be checked
    # root is used to specify "single" tree root key 
    def check_tree(self, node, Tree, Scope, root):
        not_in_tree = True
        found = 'False'
        if Scope == 'all': 
            TreeKeys = list(Tree.keys())
            for i7 in range(len(TreeKeys)):
                if node in Tree[TreeKeys[i7]]:
                    not_in_tree = False
                    found = TreeKeys[i7]
                    break
        else: 
            if node in Tree[root]: 
                not_in_tree = False
                found = root
        return not_in_tree, found