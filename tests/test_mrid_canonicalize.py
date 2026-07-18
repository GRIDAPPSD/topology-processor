"""Unit tests for the TO-005 caller-side mRID fix in topo_background_service.

topo_background_service imports gridappsd and cimgraph at module scope; those are
container-only dependencies. We stub them in sys.modules before import so the
pure-Python canonicalization and the None-vs-empty distinction can be exercised
without the broker or Blazegraph.
"""
import importlib
import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _install_stubs():
    """Register lightweight stand-ins for the container-only dependencies."""

    class _Feeder:
        pass

    class _FeederArea:
        pass

    class _DistributionArea:
        pass

    class _GridAPPSD:
        def __init__(self, *a, **k):
            self.connected = True

        def get_logger(self):
            return mock.MagicMock()

    gridappsd_mod = types.ModuleType('gridappsd')
    gridappsd_mod.GridAPPSD = _GridAPPSD
    sys.modules['gridappsd'] = gridappsd_mod

    cimgraph = types.ModuleType('cimgraph')
    databases = types.ModuleType('cimgraph.databases')
    blazegraph = types.ModuleType('cimgraph.databases.blazegraph')
    blazegraph.BlazegraphConnection = mock.MagicMock
    databases.blazegraph = blazegraph
    cimgraph.databases = databases
    sys.modules['cimgraph'] = cimgraph
    sys.modules['cimgraph.databases'] = databases
    sys.modules['cimgraph.databases.blazegraph'] = blazegraph

    cim = types.ModuleType('cimgraph.data_profile.cimhub_2023')
    cim.Feeder = _Feeder
    cim.FeederArea = _FeederArea
    cim.DistributionArea = _DistributionArea
    data_profile = types.ModuleType('cimgraph.data_profile')
    data_profile.cimhub_2023 = cim
    cimgraph.data_profile = data_profile
    sys.modules['cimgraph.data_profile'] = data_profile
    sys.modules['cimgraph.data_profile.cimhub_2023'] = cim

    class _DistributedTopologyMessage:
        def __init__(self):
            self.message = {'DistributionArea': {}}

        def get_context_from_feeder(self, *a, **k):
            # Simulate a populated topology for the resolved-Feeder success case.
            self.message['DistributionArea'] = {'@id': 'stub', 'Substations': []}

        def get_context_from_feeder_area(self, *a, **k):
            pass

        def get_context_from_distribution_area(self, *a, **k):
            pass

    utils = types.ModuleType('topology_processor.utils')
    utils.DistributedTopologyMessage = _DistributedTopologyMessage
    tp = types.ModuleType('topology_processor')
    tp.utils = utils
    sys.modules.setdefault('topology_processor', tp)
    sys.modules['topology_processor.utils'] = utils

    dotenv = types.ModuleType('dotenv')
    dotenv.load_dotenv = lambda *a, **k: None
    sys.modules['dotenv'] = dotenv

    return cim


@pytest.fixture(scope='module')
def svc_module():
    _install_stubs()
    mod = importlib.import_module('topo_background_service')
    return importlib.reload(mod)


# --- canonicalization ---------------------------------------------------------

# ieee123 Feeder mRID stored by Blazegraph as bare lowercase urn:uuid.
CANONICAL = 'c1c3e687-6ffd-c753-582b-632a27e28507'


@pytest.mark.parametrize('raw', [
    'C1C3E687-6FFD-C753-582B-632A27E28507',      # plain uppercase (FieldBusManager form)
    'c1c3e687-6ffd-c753-582b-632a27e28507',      # already canonical
    '_C1C3E687-6FFD-C753-582B-632A27E28507',     # underscore-prefixed RDF ID, uppercase
    '_c1c3e687-6ffd-c753-582b-632a27e28507',     # underscore-prefixed, lowercase
    'C1c3E687-6ffd-C753-582b-632A27e28507',      # mixed case
])
def test_canonicalize_maps_any_form_to_bare_lowercase(svc_module, raw):
    assert svc_module.canonicalize_mrid(raw) == CANONICAL


@pytest.mark.parametrize('bad', ['not-a-uuid', '', 'urn:uuid:xyz', None, 12345])
def test_canonicalize_returns_none_for_malformed(svc_module, bad):
    assert svc_module.canonicalize_mrid(bad) is None


# --- None-vs-empty distinction ------------------------------------------------

def _build_service(svc_module, get_object_return):
    """Construct a TopologyProcessor with __init__ bypassed and a stubbed conn."""
    svc = svc_module.TopologyProcessor.__new__(svc_module.TopologyProcessor)
    svc.gapps = mock.MagicMock()
    svc.log = mock.MagicMock()
    svc.blazegraph = mock.MagicMock()
    svc.blazegraph.get_object.return_value = get_object_return
    svc.return_message = {}
    return svc


def _sent_payload(svc):
    assert svc.gapps.send.called, 'service never sent a reply'
    return svc.gapps.send.call_args.args[1]


def test_unresolved_mrid_signals_not_found_not_empty_success(svc_module):
    """get_object -> None must produce a distinguishable not-found error, not {}."""
    svc = _build_service(svc_module, get_object_return=None)
    headers = {'reply-to': 'reply.topic'}
    message = {'requestType': 'GET_DISTRIBUTED_AREAS',
               'mRID': 'C1C3E687-6FFD-C753-582B-632A27E28507'}

    svc.on_message(headers, message)

    payload = json.loads(_sent_payload(svc))
    assert 'error' in payload, 'None path must emit an explicit error field'
    assert 'DistributionArea' not in payload, 'must not masquerade as empty-but-valid topology'
    assert svc.log.error.called, 'None path must log an actionable error'


def test_malformed_mrid_signals_error_before_query(svc_module):
    svc = _build_service(svc_module, get_object_return=None)
    headers = {'reply-to': 'reply.topic'}
    message = {'requestType': 'GET_DISTRIBUTED_AREAS', 'mRID': 'not-a-uuid'}

    svc.on_message(headers, message)

    payload = json.loads(_sent_payload(svc))
    assert 'error' in payload
    svc.blazegraph.get_object.assert_not_called()
    assert svc.log.error.called


def test_resolved_feeder_keeps_success_shape(svc_module):
    """A genuine Feeder still yields the DistributionArea success message."""
    feeder = svc_module.cim.Feeder()
    svc = _build_service(svc_module, get_object_return=feeder)
    headers = {'reply-to': 'reply.topic'}
    message = {'requestType': 'GET_DISTRIBUTED_AREAS',
               'mRID': 'C1C3E687-6FFD-C753-582B-632A27E28507'}

    svc.on_message(headers, message)

    # get_object was called with the canonicalized mRID, not the raw uppercase form.
    svc.blazegraph.get_object.assert_called_once_with(mRID=CANONICAL)
    payload = json.loads(_sent_payload(svc))
    assert 'error' not in payload
    assert 'DistributionArea' in payload
