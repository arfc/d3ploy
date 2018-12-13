import matplotlib.pyplot as plt


def plot_demand_supply(all_dict, commod, test, demand_driven):
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
    
    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']
    dict_calc_demand = all_dict['dict_calc_demand']
    dict_calc_supply = all_dict['dict_calc_supply']

    fig, ax = plt.subplots(figsize=(15, 7))
    if demand_driven:
        ax.plot(*zip(*sorted(dict_demand.items())), '*', color='red', label='Demand')
        ax.plot(*zip(*sorted(dict_calc_demand.items())),
                'o', alpha=0.5, color='red', label='Calculated Demand')
        ax.set_title('%s Demand Supply plot' % commod)
    else:
        ax.plot(*zip(*sorted(dict_demand.items())),
                '*', color='red', label='Capacity')
        ax.plot(*zip(*sorted(dict_calc_demand.items())),
                'o', alpha=0.5, color='red', label='Calculated Capacity')
        ax.set_title('%s Capacity Supply plot' % commod)
    ax.plot(*zip(*sorted(dict_supply.items())), '*', color='blue', label='Supply')
    ax.plot(*zip(*sorted(dict_calc_supply.items())),
            'o', alpha=0.5, color='blue', label='Calculated Supply')
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
    plt.close()


def plot_demand_supply_agent(all_dict, agent_dict, commod, test, demand_driven):
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
    
    dict_demand = all_dict['dict_demand']
    dict_supply = all_dict['dict_supply']
    dict_calc_demand = all_dict['dict_calc_demand']
    dict_calc_supply = all_dict['dict_calc_supply']
    f, (ax1, ax2) = plt.subplots(2,1, sharex='all',
                                 gridspec_kw = {'height_ratios': [1,3]})
    
    for key, val in agent_dict.items():
        ax1.scatter(*zip(*sorted(val.items())), label=key)
    ax1.grid()
    ax1.legend()
    ax1.set_xlabel('Time (month timestep)')
    ax1.set_ylabel('agents')
    
    if demand_driven:
        ax2.plot(*zip(*sorted(dict_demand.items())), '*', color='red', label='Demand')
        ax2.plot(*zip(*sorted(dict_calc_demand.items())),
                    'o', alpha=0.5, color='red', label='Calculated Demand')
    else:
        ax2.plot(*zip(*sorted(dict_demand.items())), '*', color='red', label='Capacity')
        ax2.plot(*zip(*sorted(dict_calc_demand.items())),
                'o', alpha=0.5, color='red', label='Calculated Capacity')
    ax2.plot(*zip(*sorted(dict_supply.items())), '*', color='blue', label='Supply')
    ax2.plot(*zip(*sorted(dict_calc_supply.items())),
             'o', alpha=0.5, color='blue', label='Calculated Supply')
    ax2.grid()
    ax2.set_ylabel('Mass (kg)')
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, labels, fontsize=11, loc='upper left',
               fancybox=True)
    
    ax1.set_title('Supply, Demand and prototypes for %s' %commod)
    plt.savefig(test, dpi=300, bbox_inches='tight')
    plt.close()
