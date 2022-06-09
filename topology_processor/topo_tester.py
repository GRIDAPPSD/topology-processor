@profile
def _main():
    import os, json, time
    from gridappsd import GridAPPSD, topics as t
    from gridappsd.topics import service_input_topic, service_output_topic
    from distributedtopology import DistributedTopology
    from topologydictionary import TopologyDictionary
    from networkmodel import NetworkModel

    os.environ['GRIDAPPSD_APPLICATION_ID'] = 'gridappsd-topology-processor'
    os.environ['GRIDAPPSD_APPLICATION_STATUS'] = 'STARTED'
    os.environ['GRIDAPPSD_USER'] = 'app_user'
    os.environ['GRIDAPPSD_PASSWORD'] = '1234App'

    # Connect to GridAPPS-D Platform
    gapps = GridAPPSD()
    assert gapps.connected


    model_mrid = "_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"

    Topology = TopologyDictionary(gapps, model_mrid)

    network = NetworkModel(gapps)

    network.build_equip_dicts(model_mrid, Topology)

    EqTypes = ['ACLineSegment', 'PowerTransformer', 'TransformerTank', 'SynchronousMachine', 'PowerElectronicsConnection']
    Topology.build_linknet(EqTypes)

    Topology.update_switches()

    Topology.build_feeder_islands()
    
            
if __name__ == "__main__":
    _main()