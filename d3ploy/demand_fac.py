"""
This is a mock facility used to demonstrate and test the capabilities 
of the deploy instutitions in d3ploy. It produces a fixed (or random) 
amount of psuedo material per time step (the production can also be
set to every nth time step by the user). 
"""

import random
import numpy as np
import scipy as sp

from cyclus.agents import Facility
from cyclus import lib
import cyclus.typesystem as ts


class DemandFac(Facility):
    """
    This institution deploys facilities based on demand curves using 
    Non Optimizing (NO) methods. 
    """

    demand_rate_min = ts.Double(
        doc="The minimum rate at which this facility produces it's commodity. ", 
        tooltip="The minimum rate at which this facility produces its product.",
        uilabel="Min Production"
    )

    demand_rate_max = ts.Double(
        doc="The maximum rate at which this facility produces it's commodity.", 
        tooltip="The maximum rate at which this facility produces its product.",
        uilabel="Max Production"
    )

    demand_ts = ts.Int(
        doc="The number of timesteps between demand calls by the agent", 
        tooltip="The number of timesteps between demand calls by the agent", 
        uilabel="Demand Timestep",
        default=1
    )

    supply_rate_max = ts.Double(
        doc="The maximum rate at which this facility produces it's commodity.", 
        tooltip="The maximum rate at which this facility produces its product.",
        uilabel="Max Production"
    )

    supply_rate_min = ts.Double(
        doc="The maximum rate at which this facility produces it's commodity.", 
        tooltip="The maximum rate at which this facility produces its product.",
        uilabel="Max Production"
    )

    supply_ts = ts.Int(
        doc="The number of timesteps between supply calls by the agent", 
        tooltip="The number of timesteps between supply calls by the agent", 
        uilabel="Supply Timestep",
        default=1
    )    

    supply_commod = ts.String(
        doc="The commodity supplied by this facility.",
        tooltip="Supplied Commodity",
        uilabel="Supplied Commodity"
    )

    demand_commod = ts.String(
        doc="The commodity demanded by this facility.",
        tooltip="Commodity demanded",
        uilabel="Commodity Demanded"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.demand_t = -2
        self.supply_t = -2

    def tick(self):
        """
        This method defines the tick behavior for this archetype. The demand and supply
        rates are calculated, and those are recorded in time series. 
        """
        self.demand_t += 1
        self.supply_t += 1
        supply_rate = random.uniform(self.supply_rate_min, self.supply_rate_max)
        demand_rate = random.uniform(self.demand_rate_min, self.demand_rate_max)
        if self.supply_t == -1 or self.supply_t == self.supply_ts:
            lib.record_time_series("supply"+self.supply_commod, self, supply_rate)
            self.supply_t = 0
        else:
            lib.record_time_series("supply"+self.supply_commod, self, 0.)
        if self.demand_t == -1 or self.demand_t == self.demand_ts:
            lib.record_time_series("demand"+self.demand_commod, self, demand_rate)
            self.demand_t = 0
        else:
            lib.record_time_series("demand"+self.demand_commod, self, 0.)


