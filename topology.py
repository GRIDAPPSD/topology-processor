class topology(object):
    
    def __init__(self, model_mrid, gapps):
        self.model_mrid = model_mrid
        self.gapps = gapps
        self.EquipDict = {}
        self.ConnNodeDict = {}
        self.TerminalsDict = {}
        self.NodeList = []
        self.TermList = []
    @property    
    def switch_areas(self, model_mrid, gapps):
        message = switch_areas.create_switch_areas(gapps, model_mrid)