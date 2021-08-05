# GridAPPS-D Toolbox Topology Processor

The Topology Processor is a lightweight service based on the LinkNet data structure for mapping CIM ConnectivityNodes and Terminals.

The Topology Processor generates a series of linked lists that are used to create a spanning tree of nodes. The spanning tree is used to identify islands and substation connectivity.

The Topology Processor returns python dictionary of connectivity nodes and islands in the format

```
{
  "ConnectivityNodes": {
           "cn1mrid": {"name" : "cn1",
                       "NODE" : value,
                       "LIST" : value,
                       "TopologicalNode" : "tp1mrid",
                       "terminals" : [t1, t2, t3],
                       "lines" : [line4, line5, line6],
                       "transformer" : {},
                       "island" : "island1",
                       "substation" : "sub3"},
           "cn2mrid": {"name" : "cn2",
                       "NODE" : value,
                       "LIST" : value,
                       "TopologicalNode" : "tp2mrid",
                       "terminals" : [t4, t5, t6],
                       "lines" : [line8, line9, line10],
                       "transformer" : [xfmr5],
                       "island" : "island1",
                       "substation" : "sub3"},
             ...
}
```
