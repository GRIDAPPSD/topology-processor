import json
from cimgraph.models import DistributedArea
from uuid import UUID
# import cimgraph.data_profile.cimhub_2023 as cim

jsonld = dict["@id":str(UUID),"@type":str(type)]

def identify_addressable(network: DistributedArea, 
                         equipment_list: list[jsonld] = None) -> list[jsonld]:
    
    if equipment_list is None:
        equipment_list = []

    cim = network.cim
    addressable_classes = [cim.Switch, cim.Breaker, cim.Disconnector,
        cim.Recloser, cim.LoadBreakSwitch, cim.Sectionaliser,
        cim.PowerElectronicsConnection, cim.PowerElectronicsUnit,
        cim.PhotovoltaicUnit, cim.BatteryUnit, cim.PowerElectronicsWindUnit,
        cim.RatioTapChanger, # Not technically equipment, but included for GridAPPSD
        cim.ShuntCompensator, cim.LinearShuntCompensator,
        cim.AsynchronousMachine, cim.SynchronousMachine]
    
    for class_type in addressable_classes:
        for equipment in network.graph.get(class_type, {}).values():
            # obj_json = {"@id":equipment.uri(), "@type":equipment.__class__.__name__}
            equipment_list.append(json.loads(equipment.__repr__()))
    return equipment_list

def identify_unaddressable(network: DistributedArea, 
                         equipment_list: list[jsonld] = None) -> list[jsonld]:

    if equipment_list is None:
        equipment_list = []

    cim = network.cim
    unaddressable_classes = [cim.ACLineSegment, cim.Fuse,
        cim.PowerTransformer, cim.TransformerTank,
        cim.EnergySource, cim.EnergyConsumer]
    
    for class_type in unaddressable_classes:
        for equipment in network.graph.get(class_type, {}).values():
            # obj_json = {"@id":equipment.uri(), "@type":equipment.__class__.__name__}
            equipment_list.append(json.loads(equipment.__repr__()))
    return equipment_list

def identify_measurements(network: DistributedArea, 
                         meas_list: list[jsonld] = None) -> list[jsonld]:
    
    if meas_list is None:
        meas_list = []

    cim = network.cim    
    meas_classes = [cim.Measurement, cim.Analog, cim.Discrete]
    
    for class_type in meas_classes:
        for measurement in network.graph.get(class_type, {}).values():
            meas_list.append(json.loads(measurement.__repr__()))
    return meas_list

def identify_boundaries(network: DistributedArea) -> list[jsonld]:
    
    terminals = []
    for terminal in network.container.BoundaryTerminals:
        terminals.append(json.loads(terminal.__repr__()))

    return terminals

