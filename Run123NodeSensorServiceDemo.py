import json
from gridappsd import GridAPPSD
from gridappsd.simulation import Simulation


run_config_123 = {
    "power_system_config": {
        "GeographicalRegion_name": "_73C512BD-7249-4F50-50DA-D93849B89C43",
        "SubGeographicalRegion_name": "_1CD7D2EE-3C91-3248-5662-A43EFEFAC224",
        "Line_name": "_C1C3E687-6FFD-C753-582B-632A27E28507"
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
        "simulation_name": "ieee123",
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
                        "object": "_6C1FDA90-1F4E-4716-BC90-1CCB59A6D5A9",
                        "attribute": "Switch.open",
                        "value": 1
                    }
                ],
                "reverse_differences": [
                    {
                        "object": "_6C1FDA90-1F4E-4716-BC90-1CCB59A6D5A9",
                        "attribute": "Switch.open",
                        "value": 0
                    }
                ]
            },
            "event_type": "ScheduledCommandEvent",
            "occuredDateTime": 1570041140,
            "stopDateTime": 1570041200
        }]
    }
}

import os # Set username and password
os.environ['GRIDAPPSD_USER'] = 'tutorial_user'
os.environ['GRIDAPPSD_PASSWORD'] = '12345!'

# Connect to GridAPPS-D Platform
gapps = GridAPPSD()
assert gapps.connected

request = {"configurationType":"CIM Dictionary","parameters":{"model_id":"_C1C3E687-6FFD-C753-582B-632A27E28507"}}
simulation = Simulation(gapps, run_config_123)
simulation.start_simulation()
