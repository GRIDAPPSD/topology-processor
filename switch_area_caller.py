import os, json
from gridappsd import GridAPPSD
import switch_areas

os.environ['GRIDAPPSD_USER'] = 'app_user'
os.environ['GRIDAPPSD_PASSWORD'] = '1234App'

gapps = GridAPPSD()
assert gapps.connected

model_mrid = "_49AD8E07-3BF9-A4E2-CB8F-C3722F837B62"  # 13 bus


message = switch_areas.create_switch_areas(gapps, model_mrid)
print(json.loads(message))
