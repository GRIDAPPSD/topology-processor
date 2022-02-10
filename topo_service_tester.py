import time, os, json, argparse
from gridappsd import GridAPPSD
from gridappsd.topics import service_output_topic
os.environ['GRIDAPPSD_USER'] = 'tutorial_user'
os.environ['GRIDAPPSD_PASSWORD'] = '12345!'

def TopologySubscriber(header, message):
    global timestamp, feeders, islands   
    feeder_id = message['feeder_id']
    timestamp = message['timestamp']
    feeders = json.loads(message['feeders'])
    islands = json.loads(message['islands'])

    print('received message at time ', timestamp, 'for model ', feeder_id)
    
    for island_names in list(islands.keys()):
        print('Topology Island ', island_names, 'with DERs:')
        print(islands[island_names]['SynchronousMachine'])

    for feeder_names in list(feeders.keys()):
        print('Topology Feeder', feeder_names, 'from substation')
        print(feeders[feeder_names]['PowerTransformer'])

def _main():

    parser = argparse.ArgumentParser()
    parser.add_argument("simulation_id",
                        help="Simulation id to use for responses on the message bus.")
    opts = parser.parse_args()
    simulation_id = opts.simulation_id

    topic = service_output_topic('gridappsd-topology-processor', simulation_id)
    gapps = GridAPPSD(simulation_id)
    assert gapps.connected
    gapps.subscribe(topic, TopologySubscriber)
    
    while True:
        time.sleep(0.1)
        
if __name__ == "__main__":
    _main()