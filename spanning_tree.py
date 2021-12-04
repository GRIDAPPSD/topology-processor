import time,json

def generate_spanning_tree(XfmrKeys,Xfmr_dict,ConnNodeDict,TerminalsDict,TermList,NodeList,DG_query):

    # ## Build Spanning Tree from Xfmrs
    
    Tree={}
    #ProcessedNodes=[]
    TotalNodes=0
    StartTime = time.process_time()

    # Iterate through all substation transformers
    for i6 in range(len(XfmrKeys)):

        # Identify if distribution substation transformer
        if (int(Xfmr_dict[XfmrKeys[i6]]['volt1']) >= 34000 and 34000 >= int(Xfmr_dict[XfmrKeys[i6]]['volt2']) > 1000) or (int(Xfmr_dict[XfmrKeys[i6]]['volt2']) >= 34000 and 34000 >= int(Xfmr_dict[XfmrKeys[i6]]['volt1']) > 1000):
            # Create Tree starting from this transformer
            FirstNode = 1 
            LastNode = 2
            # Set as rootnode 
            # assuming node1 is high and node2 is low - need to verify will work otherwise
            Tree[XfmrKeys[i6]]=[Xfmr_dict[XfmrKeys[i6]]['node1'], Xfmr_dict[XfmrKeys[i6]]['node2']]

            while LastNode != FirstNode:
                NextTerm = ConnNodeDict[Tree[XfmrKeys[i6]][FirstNode]]['list']
                FirstNode = FirstNode + 1
                while NextTerm != 0:
                    # Get next node and terminal for current node
                    NextNode = TerminalsDict[TermList[NextTerm-1]]['far']
                    NextTerm = TerminalsDict[TermList[NextTerm-1]]['next']
                    # Add to tree if not there already
                    not_in_tree = False

                    if NodeList[NextNode-1] not in Tree[XfmrKeys[i6]]:
                        if 'nomv' in ConnNodeDict[NodeList[NextNode-1]]:
                            if int(ConnNodeDict[NodeList[NextNode-1]]['nomv']) < 34000:
                                Tree[XfmrKeys[i6]].append(NodeList[NextNode-1])
                                ConnNodeDict[NodeList[NextNode-1]]['fdr_xfmr'] = Xfmr_dict[XfmrKeys[i6]]['tname2']
                                ConnNodeDict[NodeList[NextNode-1]]['fdr_xfmr_id'] = XfmrKeys[i6]
                                LastNode = LastNode + 1
                        else:
                            Tree[XfmrKeys[i6]].append(NodeList[NextNode-1])
                            ConnNodeDict[NodeList[NextNode-1]]['fdr_xfmr'] = Xfmr_dict[XfmrKeys[i6]]['tname2']
                            ConnNodeDict[NodeList[NextNode-1]]['fdr_xfmr_id'] = XfmrKeys[i6]
                            LastNode = LastNode + 1
                        
            NodesInTree=len(Tree[XfmrKeys[i6]])
            print("Processed topology from substation transformer ", Xfmr_dict[XfmrKeys[i6]]['tname1'], " with ", NodesInTree, " buses")
            TotalNodes=TotalNodes+NodesInTree
                
    print("Processed ", len(Tree.keys()), "topology trees containing ", TotalNodes, " buses in ", time.process_time() - StartTime, "seconds")


    # ## Build Spanning Tree from DGs



    Subs_old=list(Tree.keys())
    TotalNodes = 0
    StartTime = time.process_time()


    # Iterate through all SynchronousMachine
    for i7 in range(len(DG_query)):
        node=DG_query[i7]['node']['value']
        term=DG_query[i7]['term']['value']
        name=DG_query[i7]['name']['value']
        islanded = True
        Subs=list(Tree.keys())
        
        # Identify if DER is really islanded
        for i8 in range(len(Subs)):
            if node in Tree[Subs[i8]]:
                islanded = False
            
        if islanded == True:
            # Create Tree starting from this transformer
            FirstNode = 0 
            LastNode = 1
            # Set as rootnode 
            # assuming node1 is high and node2 is low - need to verify will work otherwise
            Tree[node]=[node]
            ConnNodeDict[node]['island'] = name

            while LastNode != FirstNode:
                NextTerm = ConnNodeDict[Tree[node][FirstNode]]['list']
                FirstNode = FirstNode + 1
                while NextTerm != 0:
                    # Get next node and terminal for current node
                    NextNode = TerminalsDict[TermList[NextTerm-1]]['far']
                    NextTerm = TerminalsDict[TermList[NextTerm-1]]['next']
                    # Add to tree if not there already
                    if NodeList[NextNode-1] not in Tree[node]:
                        Tree[node].append(NodeList[NextNode-1])
                        ConnNodeDict[NodeList[NextNode-1]]['island'] = name
                        LastNode = LastNode + 1
                        
            NodesInTree=len(Tree[node])
            TotalNodes=TotalNodes+NodesInTree
                
    print("Processed ", len(Tree.keys())-len(Subs_old), " more islands containing ", TotalNodes, " buses in ", time.process_time() - StartTime, "seconds")
    print(' ')
    print(' ')
    return Tree,TotalNodes
