import numpy as np
import scipy as sp
import random

from cyclus.agents import Facility
from cyclus import lib
import cyclus.typesystem as ts


class DemandFac(Facility):
    """
    This institution deploys facilities based on demand curves using 
    Non Optimizing (NO) methods. 
    """

    demand_rate_min = ts.Double(
        doc = "The minimum rate at which this facility produces it's commodity. ", 
        tooltip = "The minimum rate at which this facility produces its product.",
        uilabel = "Min Production"
    )


    demand_rate_max = ts.Double(
        doc = "The maximum rate at which this facility produces it's commodity.", 
        tooltip = "The maximum rate at which this facility produces its product.",
        uilabel = "Max Production"
    )

    supply_rate_max = ts.Double(
        doc = "The maximum rate at which this facility produces it's commodity.", 
        tooltip = "The maximum rate at which this facility produces its product.",
        uilabel = "Max Production"
    )

    supply_rate_min = ts.Double(
        doc = "The maximum rate at which this facility produces it's commodity.", 
        tooltip = "The maximum rate at which this facility produces its product.",
        uilabel = "Max Production"
    )    

    supply_commod = ts.String(
        doc = "",
        tooltip = "",
        uilabel = ""
    )

    demand_commod = ts.String(
        doc = "",
        tooltip = "",
        uilabel = ""
    )

    proto = ts.String(
        doc = "",
        tooltip = "",
        uilabel = ""
    )

    def tick(self):
        supply_rate = random.uniform(self.supply_rate_min, self.supply_rate_max)
        demand_rate = random.uniform(self.demand_rate_min, self.demand_rate_max)
        lib.record_time_series(self.supply_commod, self, supply_rate)
        lib.record_time_series(self.demand_commod, self, demand_rate)

