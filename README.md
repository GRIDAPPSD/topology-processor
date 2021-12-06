# GridAPPS-D Toolbox Topology Processor

The Topology Processor is a lightweight service based on the LinkNet data structure for mapping CIM ConnectivityNodes and Terminals.

The Topology Processor generates a series of linked lists that are used to create a spanning tree of nodes. The spanning tree is used to identify islands and substation connectivity.

The Topology Processor returns python dictionary of connectivity nodes and islands in the format

```
Message = {
	'timestamp': 1234567890
	'ConnNodeDict': {
		'_NODE1234-MRID-456ABC': {
			'lines': ['line234', 'line235', 'line236'],
			'line_ids': ['_234LINE-456-MRID', '_235LINE-576-MRID', '_236LINE-789-MRID'],
			'name': 'node1234',
			'node': 1,
			'list': 3587,
			'tpid': '_TOP5478-874-MRID',
			'xfmr': ['t087523a_T1']
			'nomv': '12470',
			'fdr_xfmr': 'sub2_x2_t2',
			'fdr_xfmr': '_928XFMR-29347-MRID'},
		'_NODE2356-MRID-789ABC': {
			'lines': ['line567', 'line568'],
			'line_ids': ['_568LINE-789-MRID', '_456LINE-789-MRID', '_236LINE-789-MRID'],
			'name': 'node1234',
			'node': 1,
			'list': 3587,
			'tpid': '_TOP5478-874-MRID',
			'der': ['diesel_1']
			'nomv': '12470',
			'island': 'microturbine-1'},
		...
			},
	'TopologyTree': {
		'_928XFMR-29347-MRID': ['_NODE1234-MRID-456ABC', '_NODE1547-MRID-479HKE', ... ],
		'_341XFMR-59480-MRID': ['_NODE7890-MRID-674CDF', '_NODE8623-MRID-034YIH', ... ],
		'_8949DER-28379-MRID': ['_NODE2000-MRID-100HJQ', '_NODE2001-MRID-101QUW', ... ]
		}
}
```

The Topology Processor Service publishes on the topic `'/topic/goss.gridappsd.simulation.topologyprocessor.simulation_id.output'`

To subscribe to the service create a class or function definition that is then passed to the `gapps.subscribe()` method:

```
output_topic = '/topic/goss.gridappsd.simulation.topologyprocessor.'+str(viz_simulation_id)+'.output'

def DemoTPsubscriber(header, message):

    # Extract time and measurement values from message
    timestamp = message["timestamp"]
    Tree = message["TopologyTree"]
    ConnNodeDict = message['ConnNodeDict']
    
conn_id = gapps.subscribe(output_topic, DemoTPsubscriber)
```