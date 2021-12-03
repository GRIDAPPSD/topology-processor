import json, os
from gridappsd import GridAPPSD
from gridappsd.simulation import Simulation


run_config_9500 = {
    "power_system_config": {
        "GeographicalRegion_name":"_73C512BD-7249-4F50-50DA-D93849B89C43",
        "SubGeographicalRegion_name":"_A1170111-942A-6ABD-D325-C64886DC4D7D",
        "Line_name":"_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"
    },
    "application_config": {
        "applications": []
    },
    "simulation_config": {
        "start_time": "1570041113",
        "duration": "120",
        "simulator": "GridLAB-D",
        "timestep_frequency": "1000",
        "timestep_increment": "1000",
        "run_realtime": True,
        "simulation_name": "final9500",
        "power_flow_solver_method": "NR",
        "model_creation_config": {
            "load_scaling_factor": "1",
            "schedule_name": "ieeezipload",
            "z_fraction": "0",
            "i_fraction": "1",
            "p_fraction": "0",
            "randomize_zipload_fractions": False,
            "use_houses": False
        }
    },
    "test_config": {
        "events": [{
            "message": {
                "forward_differences": [
                    {
                        "object": "_494810CC-1A00-4EE8-8360-484FA7C19D01",
                        "attribute": "Switch.open",
                        "value": 1
                    }
                ],
                "reverse_differences": [
                    {
                        "object": "_494810CC-1A00-4EE8-8360-484FA7C19D01",
                        "attribute": "Switch.open",
                        "value": 0
                    }
                ]
            },
            "event_type": "ScheduledCommandEvent",
            "occuredDateTime": 1570041120,
            "stopDateTime": 1570041200
        }]
    }

}

# Set username and password
os.environ['GRIDAPPSD_USER'] = 'tutorial_user'
os.environ['GRIDAPPSD_PASSWORD'] = '12345!'

# Connect to GridAPPS-D Platform
gapps = GridAPPSD()
assert gapps.connected

request = {"configurationType":"CIM Dictionary","parameters":{"model_id":"_EE71F6C9-56F0-4167-A14E-7F4C71F10EAA"}}
simulation = Simulation(gapps, run_config_9500)
simulation.start_simulation()
