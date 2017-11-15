import numpy as np
import scipy as sp
import random

from cyclus.agents import Institution
from cyclus import lib
import cyclus.typesystem as ts


class DemandFac(Facility):
"""
This institution deploys facilities based on demand curves using 
Non Optimizing (NO) methods. 
"""

    production_rate_min = ts.Double(
        doc = "The minimum rate at which this facility produces it's commodity. " 
        tooltip = "The minimum rate at which this facility produces its product."
        uilabel = "Min Production"
    )


    production_rate_max = ts.Double(
        doc = "The maximum rate at which this facility produces it's commodity. " 
        tooltip = "The maximum rate at which this facility produces its product."
        uilabel = "Max Production"
    )

    commodity = ts.String(
        doc = "The rate at which this facility produces it's commodity. This commodity should "
              "be the same as the commodity that the D3ploy institution is attempting to meet." 
        tooltip = "The rate at which this facility produces its product."
        uilabel = "Rate of production"
    )

    def tick():
        rate = random.uniform(minimum, maximum):
        lib.record_time_series(commodity, self, rate)

