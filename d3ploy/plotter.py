import matplotlib.pyplot as plt


def plot_demand_supply(dict_demand, dict_supply, dict_calc_demand, dict_calc_supply, commod, test, demand_driven):
    """ Plots demand, supply, calculated demand and calculated supply on a curve 
    for a non-driving commodity 
    Parameters
    ----------
    4 dicts: dictionaries of supply, demand, calculated
    demand and calculated supply
    demand_driven: Boolean. If true, the commodity is demand driven, 
    if false, the commodity is supply driven 
    Returns
    -------
    plot of all four dicts 
    """
    fig, ax = plt.subplots(figsize=(15, 7))
    if demand_driven:
        ax.plot(*zip(*sorted(dict_demand.items())), '*', label='Demand')
        ax.plot(*zip(*sorted(dict_calc_demand.items())),
                'o', alpha=0.5, label='Calculated Demand')
        ax.set_title('%s Demand Supply plot' % commod)
    else:
        ax.plot(*zip(*sorted(dict_demand.items())), '*', label='Capacity')
        ax.plot(*zip(*sorted(dict_calc_demand.items())),
                'o', alpha=0.5, label='Calculated Capacity')
        ax.set_title('%s Capacity Supply plot' % commod)
    ax.plot(*zip(*sorted(dict_supply.items())), '*', label='Supply')
    ax.plot(*zip(*sorted(dict_calc_supply.items())),
            'o', alpha=0.5, label='Calculated Supply')
    ax.grid()
    ax.set_xlabel('Time (month timestep)', fontsize=14)
    ax.set_ylabel('Mass (kg)', fontsize=14)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(
        handles,
        labels,
        fontsize=11,
        loc='upper center',
        bbox_to_anchor=(
            1.1,
            1.0),
        fancybox=True)
    plt.savefig(test, dpi=300, bbox_inches='tight')
