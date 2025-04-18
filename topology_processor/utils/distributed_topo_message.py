import json
import logging

from cimgraph.databases import ConnectionInterface
from cimgraph.models import FeederModel, DistributedArea
import cimgraph.data_profile.cimhub_2023 as cim
import topology_processor.utils as utils

_log = logging.getLogger(__name__)

class DistributedTopologyMessage():

    def __init__(self) -> None:
        self.message = {}
        self.message['DistributionArea'] = {}

    def get_context_from_feeder(self, feeder: cim.Feeder, connection: ConnectionInterface) -> None:

        cim = connection.cim
        if not isinstance(feeder, cim.Feeder):
            raise TypeError('feeder argument should be a cim.Feeder object')
        
        feeder_model = FeederModel(container=feeder, connection=connection, distributed=True)
        feeder_area_model = feeder_model.distributed_areas[0]

        try:
            distribution_area = feeder_model.get_from_triple(feeder, 'Feeder.DistributionArea')[0]
            self.message['DistributionArea'] = json.loads(distribution_area.__repr__())
        except:
            _log.warning(f'Feeder does not have an associated DistributionArea')

        try:
            substation = feeder_model.get_from_triple(feeder, 'Feeder.NormalEnergizingSubstation')[0]
            sub_msg = json.loads(substation.__repr__())
            sub_msg['NormalEnergizedFeeder'] = []
            
            
            fdr_msg = json.loads(feeder.__repr__())
            fdr_msg['FeederArea'] = self.add_feeder_area(feeder_area_model)

            sub_msg['NormalEnergizedFeeder'].append(fdr_msg)
            self.message['DistributionArea']['Substations'] = []
            self.message['DistributionArea']['Substations'].append(sub_msg)

        except:
            _log.warning(f'Feeder does not have an associated Normal Energizing Substation')

    def get_context_from_feeder_area(self, feeder_area: cim.FeederArea,
                                     connection: ConnectionInterface) -> None:
        
        cim = connection.cim
        if not isinstance(feeder_area, cim.FeederArea):
            raise TypeError('feeder argument should be a cim.FeederArea object')
        
        feeder_area_model = DistributedArea(container=feeder_area,
                                            connection=connection, distributed=True)
        substation = feeder_area_model.get_from_triple(feeder_area, 'FeederArea.Substation')[0]
        feeders = feeder_area_model.get_from_triple(feeder_area )

        #TODO: Finish this method


    def get_context_from_distribution_area(self, distribution_area: cim.DistributionArea,
                                           connection:ConnectionInterface) -> None:
        
        cim = connection.cim
        if not isinstance(distribution_area, cim.DistributionArea):
            raise TypeError('feeder argument should be a cim.DistributionArea object')
        
        distribution_area_model = DistributedArea(container=distribution_area,
                                            connection=connection, distributed=True)
        distribution_area_model.get_all_edges(cim.DistributionArea)
        distribution_area_model.get_all_edges(cim.Substation)

        self.message['DistributionArea'] = json.loads(distribution_area.__repr__())
        self.message['DistributionArea']['Substations'] = []

        
        for substation in distribution_area.Substation:
            sub_msg = json.loads(substation.__repr__())
            sub_msg['NormalEnergizedFeeder'] = []

            for feeder in substation.NormalEnergizedFeeder:
                feeder_model = FeederModel(container=feeder, connection=connection, distributed=True)
                
                fdr_msg = json.loads(feeder.__repr__())
                # try:
                feeder_area_model = feeder_model.distributed_areas[0]
                feeder_area_model.get_all_edges(cim.FeederArea)
                fdr_msg['FeederArea'] = self.add_feeder_area(feeder_area_model)
                # except:
                #     _log.warning(f'Feeder {feeder.uri()} does not have distributed areas')

                sub_msg['NormalEnergizedFeeder'].append(fdr_msg)
                del feeder_model

            new_sub = cim.Substation()
            new_sub.uuid(uri = substation.uri())
            sub_model = DistributedArea(container=new_sub,
                                            connection=connection, distributed=False)
            sub_model.get_all_edges(cim.Substation)
            sub_model.get_all_edges(cim.ConnectivityNode)
            sub_model.get_all_edges(cim.Terminal)
            sub_msg['AddressableEquipment'] = utils.identify_addressable(sub_model)
            sub_msg['UnaddressableEquipment'] = utils.identify_unaddressable(sub_model)
            sub_msg['Measurements'] = utils.identify_measurements(sub_model)
            self.message['DistributionArea']['Substations'].append(sub_msg)
            del sub_msg
            del sub_model








    def add_feeder_area(self, feeder_area_model: DistributedArea) -> dict:
        feeder_area_model.get_all_edges(cim.FeederArea)
        feeder_area = feeder_area_model.container

        msg = json.loads(feeder_area.__repr__())
        msg['BoundaryTerminals'] = utils.identify_boundaries(feeder_area_model)
        msg['AddressableEquipment'] = utils.identify_addressable(feeder_area_model)
        msg['UnaddressableEquipment'] = utils.identify_unaddressable(feeder_area_model)
        msg['Measurements'] = utils.identify_measurements(feeder_area_model)
        msg['SwitchAreas'] = []

        for switch_area_model in feeder_area_model.distributed_areas:
            sw_msg = self.add_switch_area(switch_area_model)
            msg['SwitchAreas'].append(sw_msg)

        return msg

        

    def add_switch_area(self, switch_area_model:DistributedArea) -> dict:

        switch_area_model.get_all_edges(cim.SwitchArea)
        switch_area = switch_area_model.container
        feeder_area = switch_area_model.get_from_triple(switch_area, 'SwitchArea.FeederArea')[0]

        sw_msg = json.loads(switch_area.__repr__())
        sw_msg['FeederArea'] = json.loads(feeder_area.__repr__())
        sw_msg['BoundaryTerminals'] = utils.identify_boundaries(switch_area_model)
        sw_msg['AddressableEquipment'] = utils.identify_addressable(switch_area_model)
        sw_msg['UnaddressableEquipment'] = utils.identify_unaddressable(switch_area_model)
        sw_msg['Measurements'] = utils.identify_measurements(switch_area_model)
        sw_msg['SecondaryAreas'] = []

        for secondary_area_model in switch_area_model.distributed_areas:
            sec_msg = self.add_secondary_area(secondary_area_model)
            sw_msg['SecondaryAreas'].append(sec_msg)

        return sw_msg

    def add_secondary_area(self, secondary_area_model: DistributedArea) -> dict:

        secondary_area_model.get_all_edges(cim.SecondaryArea)
        secondary_area = secondary_area_model.container
        switch_area = secondary_area_model.get_from_triple(secondary_area, 'SecondaryArea.SwitchArea')[0]

        sa_msg = json.loads(secondary_area.__repr__())
        sa_msg['SwitchArea'] = json.loads(switch_area.__repr__())
        sa_msg['BoundaryTerminals'] = utils.identify_boundaries(secondary_area_model)
        sa_msg['AddressableEquipment'] = utils.identify_addressable(secondary_area_model)
        sa_msg['UnaddressableEquipment'] = utils.identify_unaddressable(secondary_area_model)
        sa_msg['Measurements'] = utils.identify_measurements(secondary_area_model)
        
        return sa_msg
