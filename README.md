# GridAPPS-D Toolbox Topology Processor

The Topology Processor is a lightweight service based on the LinkNet(TM) open-source data structure for mapping CIM ConnectivityNodes and Terminals developed by IncSys Corp. LinkNet(TM) is a trademark of Incremental Systems Corporation and is used with permission.

## Real-time Topology Processor Service

The Topology Processor service generates a series of linked lists that are used to create a spanning tree of nodes. The spanning tree is used to identify islands and substation connectivity.

The service is used in conjunction with a GridAPPS-D simulation and publishes the topology of simulated feeder in response to switching actions and other topology changes.

### Service Output Topic

To subscribe to the Topology Processor Service, use the `service_output_topic()` method from the GridAPPS-D Python library:

```
from gridappsd.topics import service_output_topic

topic = service_output_topic("gridappsd-topology-processor", simulation_id)
```

### Service Output Message

The Topology Processor publishes a Python dictionary of feeders and islands in the format

```
Message = {"feeder_id": "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62",
           "timestamp": 1645840953,
           "feeders": {"feeder_0": {"PowerTransformer": "_1XFMR-SUB1-MRID",
                                    "ConnectivityNode": ["_ABCD-NODE01-MRID", "_BCDE-NODE02-MRID"]},
                      {"feeder_1": {"PowerTransformer": "_2XFMR-SUB2-MRID",
                                    "ConnectivityNode": ["_CDEF-NODE35-MRID", "_DEFG-NODE36-MRID"]}, 
                      {"feeder_n": {"PowerTransformer": "_3XFMR-SUB3-MRID",
                                    "ConnectivityNode": ["_UWXY-NODE88-MRID", "_WXYZ-Node89-MRID"]}},
           "islands": {"island_0": {"SynchronousMachine": ["_1DER-DIES-MRID", "_2DER-WIND-MRID"],
                                    "ConnectivityNode": ["_1234-NODE44-MRID", "_2345-NODE45-MRID"]}}
```

### Sample Subscription Function

To subscribe to the service create a class or function definition that is then passed to the `gapps.subscribe()` method.

A working example is available in the `topo_service_tester.py` script, which subscribes to the topology service of a running simulation and then prints feeder and island info to the terminal window as switching actions are made.

```python
output_topic = "/topic/goss.gridappsd.simulation.topologyprocessor."+str(viz_simulation_id)+".output"

def DemoTPsubscriber(headers, message):

    # Extract time and measurement values from message
    feeder_id = message["feeder_id"]
    timestamp = message["timestamp"]
    feeders = message["feeders"]
    islands = message["islands"]
    # Parse topology as needed 
    
conn_id = gapps.subscribe(topic, DemoTPsubscriber)
```

## Topology Processor Background Service

The Topology Processor also includes a background service daemon, which is included in the GridAPPS-D platform as of [INSERT RELEASE INFO]

There are three API calls that can be made.

### GET_BASE_TOPOLOGY

This API call generates the full topology dictionary for the feeder using the normally-open / normally-closed switch positions in the CIM XML feeder model.

```python
topic = "goss.gridappsd.request.data.topology"

message = {
   "requestType": "GET_BASE_TOPOLOGY",
   "modelID":  "_FEEDER-1234-ABCD-MRID",
   "resultFormat": "JSON"
}

message = gapps.get_response(topic, message, timeout=30)
```

It returns a Python dictionary / JSON string message in the following format:

```python
{
    "feeder_id": "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62",
    "feeders": {
        "feeder_0": {
            "PowerTransformer":"_1XFMR-SUB1-MRID",
            "ConnectivityNode": ["_ABCD-NODE01-MRID", "_BCDE-NODE02-MRID"]
        },
        "feeder_1": {
            "PowerTransformer": "_2XFMR-SUB2-MRID",
            "ConnectivityNode": ["_CDEF-NODE35-MRID", "_DEFG-NODE36-MRID"]
        }, 
        "feeder_n": {
            "PowerTransformer": "_3XFMR-SUB3-MRID",
            "ConnectivityNode": ["_UWXY-NODE88-MRID", "_WXYZ-Node89-MRID"]}
    },

    "islands": {
        "island_0": {
            "SynchronousMachine": ["_1DER-DIES-MRID", "_2DER-WIND-MRID"],
            "ConnectivityNode": ["_1234-NODE44-MRID", "_2345-NODE45-MRID"]
         }
    },
    "connectivity": {
        "_ABCD-NODE01-MRID": {
            "name": "node01",
            "TopologicalNode": "_TOPONODE-001D-MRID",
            "nominalVoltage": "4160",
            "ACLineSegment": ["_ACLINE-LINE-4136-MRID"],
            "Breaker": [],
            "EnergyConsumer": ["_LOAD-DD71-9858-MRID"],
            "Fuse": [],
            "House": [],
            "LinearShuntCompensator": ["_LINEAR-CAP1-MRID"],
            "LoadBreakSwitch": [],
            "PowerTransformer": [],
            "RatioTapChanger": [],
            "Recloser": [],
            "TransformerTank": [],
            "SynchronousMachine": [],
            "PowerElectronicsConnection": [],
            "Measurement": [ "_778MEAS1-D427-MRID", "275MEAS2-F344-MRID"],
            "Feeder": ["feeder_0", "feeder_2"],
            "Island": [],
            "node": 7,
            "list": 8 
        },
        "_1234-NODE44-MRID": {
            "name": "node44",
            "TopologicalNode": "_TOPONODE-044D-MRID",
            "nominalVoltage": "208",
            "ACLineSegment": ["_ACLINE-LINE-4378-MRID"],
            "Breaker": [],
            "EnergyConsumer": ["_LOAD-AA45-6980-MRID"],
            "Fuse": [],
            "House": ["_HOUSE-FF45-5948-MRID"],
            "LinearShuntCompensator": [],
            "LoadBreakSwitch": [],
            "PowerTransformer": [],
            "RatioTapChanger": [],
            "Recloser": [],
            "TransformerTank": [],
            "SynchronousMachine": [],
            "PowerElectronicsConnection": ["_SOLAR-JJ78-4598-MRID"],
            "Measurement": [ "_576MEAS81-D985-MRID", "985MEAS92-F968-MRID"],
            "Feeder": [],
            "Island": ["island_0"],
            "node": 98,
            "list": 230 
         }
    },
    "equipment": {
        "ACLineSegment": {
            "_ACLINE-LINE-4136-MRID": {
                "name": "632645",
                "node1": "_ABCD-NODE01-MRID",
                "term1": "_43A5-TERM23-MRID",
                "node2": "_BCDE-NODE02-MRID",
                "term2": "_537F-TERM24-MRID"
             }
        },
         "Breaker": {
            "_52DE9189-20DC-4C73-BDEE-E960FE1F9493": {
                "name": "brkr1",
                "node1": "_7BEDDADD-0A14-429F-8601-9EA8B892CA6E",
                "term1": "_1D81C7FE-E88F-41E3-A900-476CA6476CCD",
                "node2": "_94F822E0-7130-4205-8597-B47110BBEF4B",
                "term2": "_2847E06B-C8ED-41E6-B515-C61C9E8EB4B4",
                "open": 1
            }
        },
        "EnergyConsumer": {
            "_32F02D2B-EE6E-4D3F-8486-1B5CAEF70204": {
                "name": "house",
                "node1": "_0A98A62D-7642-4F03-8317-A8605CBDBA37",
                "term1": "_2128BB42-3E2D-490A-A29D-05549E81F25D"
            }
        },
        "House": {},
        "Fuse": {
            "_43EF8365-F932-409B-A51E-FBED3F6DFFAA": {
                "term1": "_3621713B-852E-4F95-8586-2D55313ED673",
                "term2": "_D1CF8D27-7793-45FD-BA55-ADDB77AFED1E",
                "node1": "_C6256170-E6ED-4F91-8EBD-748090C3FDD5",
                "node2": "_ADDB7A30-5A3C-4179-AF5D-5C9A7213B0E7",
                "open": 1
            }
        },
        "LinearShuntCompensator": {
            "_A9DE8829-58CB-4750-B2A2-672846A89753": {
                "name": "cap1",
                "node1": "_63DFBEA0-CD06-4D2E-B956-DF9517BE057B",
                "term1": "_5B38070B-E918-4EAA-8BDB-8B3CE4F8A917"
            },
        },
        "LoadBreakSwitch": {
            "_2858B6C2-0886-4269-884C-06FA8B887319": {
                "name": "sect1",
                "node1": "_8E99F99D-FE8F-420B-AC49-0B52DF5362AB",
                "term1": "_8F517DFE-D985-4D24-8339-96FA2A789E88",
                "node2": "_2A6DC4DD-D3DC-434D-A187-D2C58A0A72C8",
                "term2": "_02AE202B-D91B-4EAD-8EC9-3B87BDD67C8B",
                "open": 1
            },
        },
        "PowerTransformer": {
            "_259E820F-B4AF-4E1A-8271-687534EDAECC": {
                "name": "sub3",
                "node1": "_A8A25B50-3AE3-4A31-A18B-B3FA13397ED3",
                "term1": "_717DFB1A-A300-444D-8D3B-0A093EAAD47B",
                "node2": "_7BEDDADD-0A14-429F-8601-9EA8B892CA6E",
                "term2": "_BB0411D7-5261-433D-B327-549DA536EEEC",
                "bus1": "sourcebus",
                "tname1": "sub3_T1",
                "volt1": 115000,
                "phase1": {},
                "bus2": "650",
                "tname2": "sub3_T2",
                "volt2": 4160,
                "phase2": {},
                "bus3": "650z",
                "term3": "_F6CE3095-9089-4B61-9C13-C7647ADBA888",
                "node3": "_04984C4D-CC29-477A-9AF4-61AC7D74F16F",
                "tname3": "sub3_T3",
                "volt3": 13200,
                "phase3": {}
            },
        },
        "RatioTapChanger": {
            "_67B57539-590B-4158-9CBB-9DBA2FE6C1F0": {
                "bus1": "brkr",
                "term1": "_F8856652-20FB-4760-874D-3D785E91A83E",
                "node1": "_94F822E0-7130-4205-8597-B47110BBEF4B",
                "tname1": "reg3_T1",
                "volt1": 0,
                "phase1": "C",
                "bus2": "rg60",
                "term2": "_F5258B9A-B51E-40DD-9A06-5918E41F3C35",
                "node2": "_673E896A-DCBF-4E43-9924-BEB31C5B6005",
                "tname2": "reg3_T2",
                "volt2": 0,
                "phase2": "C",
                "TransformerTank": "_E2E0FC64-8D45-4C55-BDB9-EAB827A46FBC",
                "name": "reg3",
                "node": "_673E896A-DCBF-4E43-9924-BEB31C5B6005",
                "term": "_F5258B9A-B51E-40DD-9A06-5918E41F3C35"
            }
        },
        "Recloser": {
            "_CE5D0651-676B-4AF3-8D67-41BF1B33E30C": {
                "name": "rec1",
                "node1": "_6CB5E5CE-2CD0-40CC-A979-B4F9ED05E49B",
                "term1": "_EBAEF4A4-5D80-4FAD-A133-AA18607F3C31",
                "node2": "_421E99BE-A834-4809-B924-84D88F634A45",
                "term2": "_DD4717B2-5FCD-4E67-9BC8-DD307B80AFEA",
                "open": 1
            }
        },
        "TransformerTank": {
            "_17A934C7-1510-481F-BAD7-189058957FF1": {
                "bus1": "670",
                "term1": "_8C674F14-D9FF-4B1C-B246-1235022CD4C2",
                "node1": "_DC889FA5-7B28-4273-A1D7-205BE3E0BFED",
                "tname1": "tpoletop_T1",
                "volt1": 0,
                "phase1": "B",
                "bus2": "house",
                "term2": "_8E29BA3D-9523-446F-BD9F-989D8182A723",
                "node2": "_0A98A62D-7642-4F03-8317-A8605CBDBA37",
                "tname2": "tpoletop_T2",
                "volt2": 0,
                "phase2": "s1",
                "bus3": "house",
                "term3": "_9D06670E-F8AD-46A1-9854-BBA7ADAF1CF0",
                "node3": "_0A98A62D-7642-4F03-8317-A8605CBDBA37",
                "tname3": "tpoletop_T3",
                "volt3": 0,
                "phase3": "s2"
            },
            "_B6363F07-B1BC-420B-AA4C-A34BB8F05827": {
                "bus1": "brkr",
                "term1": "_9AC596A8-D859-48F3-A286-D2533F9B9733",
                "node1": "_94F822E0-7130-4205-8597-B47110BBEF4B",
                "tname1": "reg1_T1",
                "volt1": 0,
                "phase1": "A",
                "bus2": "rg60",
                "term2": "_5A1120EE-0F2A-4698-9FF5-0F0F4F507BAF",
                "node2": "_673E896A-DCBF-4E43-9924-BEB31C5B6005",
                "tname2": "reg1_T2",
                "volt2": 0,
                "phase2": "A"
            },

        },
        "SynchronousMachine": {},
        "PowerElectronicsConnection": {
            "_682AB7A9-4FBF-4204-BDE1-27EAB3425DA0": {
                "name": "house",
                "node1": "_0A98A62D-7642-4F03-8317-A8605CBDBA37",
                "term1": "_A4B4C25C-8744-4B8B-A612-19B80AFA110D"
            }
        }
    }
}
```

### GET_SNAPSHOT_TOPOLOGY

```python
topic = "goss.gridappsd.request.data.topology"

message = {
   "requestType": "GET_SNAPSHOT_TOPOLOGY",
   "modelID": "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62",
   "simulationID": "12345678",
   "timestamp": "1645917817",
   "resultFormat": "JSON"
}

message = gapps.get_response(topic, message, timeout=90)

```

### GET_SWITCH_AREAS

This call returns the dictionary of feeder equipment used by the GridAPPS-D Distributed API.

```python
topic = "goss.gridappsd.request.data.topology"

message = {
   "requestType": "GET_SWITCH_AREAS",
   "modelID":  "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62",
   "resultFormat": "JSON"
}

dist_api_message = gapps.get_response(topic, message, timeout=30)
```
