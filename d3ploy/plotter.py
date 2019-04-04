import matplotlib.pyplot as plt
import numpy as np


def plot_demand_supply(all_dict, commod, test, demand_driven, log_scale):
    """ Plots demand, supply, calculated demand and calculated supply
    on a curve for a non-driving commodity
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
        if log_scale:
            ax.semilogy(*zip(*sorted(dict_demand.items())), '+', color='red',
                    label='Demand')
            ax.semilogy(*zip(*sorted(dict_calc_demand.items())),
                    'o', color='red', label='Calculated Demand')
        else:
            ax.plot(*zip(*sorted(dict_demand.items())), '+', color='red',
                    label='Demand')
            ax.plot(*zip(*sorted(dict_calc_demand.items())),
                    'o', color='red', label='Calculated Demand')
        ax.set_title('%s Demand Supply plot' % test)
    else:
        if log_scale:
            ax.semilogy(*zip(*sorted(dict_demand.items())),
                    '+', color='red', label='Capacity')
            ax.semilogy(*zip(*sorted(dict_calc_demand.items())),
                    'o', color='red', label='Calculated Capacity')
        else:
            ax.plot(*zip(*sorted(dict_demand.items())),
                    '+', color='red', label='Capacity')
            ax.plot(*zip(*sorted(dict_calc_demand.items())),
                    'o', color='red', label='Calculated Capacity')
        ax.set_title('%s Capacity Supply plot' % test)
    if log_scale:
        ax.semilogy(*zip(*sorted(dict_supply.items())), 'x', color='c',
                    label='Supply')
        ax.semilogy(*zip(*sorted(dict_calc_supply.items())),
                    'o', alpha=0.5, color='c', label='Calculated Supply')
    else:
        ax.plot(*zip(*sorted(dict_supply.items())), 'x', color='c',
                label='Supply')
        ax.plot(*zip(*sorted(dict_calc_supply.items())),
                'o', alpha=0.5, color='c', label='Calculated Supply')
    ax.grid()
    ax.set_xlabel('Time (month timestep)', fontsize=14)
    if commod.lower() == 'power':
        ax.set_ylabel('Power (MW)', fontsize=14)
    else:
        ax.set_ylabel('Mass (Kg)', fontsize=14)
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


def plot_demand_supply_agent(all_dict, agent_dict, commod, test,
                             demand_driven, log_scale):
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
    
    top_indx = True
    for key, val in agent_dict.items():
        x, y = get_xy_from_dict(val)
        if top_indx:
            ax1.bar(x, y, label=key,
                    edgecolor='none')
            prev = y
            top_indx = False
        else:
            ax1.bar(x, y, label=key,
                    bottom=prev, edgecolor='none')
            prev = np.add(prev, y)
    ax1.grid()
    ax1.legend()
    ax1.set_xlabel('Time (month timestep)')
    ax1.set_ylabel('agents')
    
    marksize = 6

    if demand_driven:
        if log_scale:
            ax2.semilogy(*zip(*sorted(dict_demand.items())),
                         label='Demand')
            ax2.semilogy(*zip(*sorted(dict_calc_demand.items())),
                         label='Calculated Demand')
        else:
            ax2.plot(*zip(*sorted(dict_demand.items())),
                         label='Demand')
            ax2.plot(*zip(*sorted(dict_calc_demand.items())),
                         label='Calculated Demand')
    else:
        if log_scale:
            ax2.semilogy(*zip(*sorted(dict_demand.items())),
                         label='Capacity')
            ax2.semilogy(*zip(*sorted(dict_calc_demand.items())),
                         label='Calculated Capacity')
        else:
            ax2.plot(*zip(*sorted(dict_demand.items())),
                         label='Capacity')
            ax2.plot(*zip(*sorted(dict_calc_demand.items())),
                         label='Calculated Capacity')
    if log_scale:
        ax2.semilogy(*zip(*sorted(dict_supply.items())),
                     label='Supply')
        ax2.semilogy(*zip(*sorted(dict_calc_supply.items())),
                     alpha=0.5,  label='Calculated Supply')
    else:
        ax2.plot(*zip(*sorted(dict_supply.items())),
                 label='Supply')
        ax2.plot(*zip(*sorted(dict_calc_supply.items())),
                 alpha=0.5,  label='Calculated Supply')
    ax2.grid()
    if commod.lower() == 'power':
        ax.set_ylabel('Power (MW)', fontsize=14)
    else:
        ax.set_ylabel('Mass (Kg)', fontsize=14)
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, labels, fontsize=11, loc='upper left',
               fancybox=True)
    
    ax1.set_title('Supply, Demand and prototypes for %s' %test)
    plt.savefig(test, dpi=300, bbox_inches='tight')
    plt.close()

def get_xy_from_dict(dictionary):
    maxindx = max(dictionary.keys()) + 1
    y = np.zeros(maxindx)
    x = np.arange(maxindx)
    for key, val in dictionary.items():
        y[key] = val
    return x, y
