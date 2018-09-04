# d3ploy
A collection of Cyclus manager archetypes for demand driven deployment. It operates using
global calls within a Cyclus simulation so that all agents within the simulation
can communicate. The goal of this package is to provide three types of mathematical
basis for determining supply and demand of commodities within Cyclus; Non-optimizing (NO)
deterministing optimization (DO), and Stochastic optimization (SO).

The user needs to specify the supply chain by setting the appropriate `initialfacilitylist`. With the
`driving commodity` and initial facilities, the Institution will figure out the supply
chain and will deploy prototypes to meet the demand of the driving commodity.

Dependencies
============
**statsmodels**: Python package for statistical analysis

**arch**: Python package for conditional heteroskidasticity models.

Non-Optimizing Methods
======================
There are two methods currently being considered for the NO models. Autoregressive
moving average (ARMA), and autoregressive conditional heteroskedasticity (ARCH).

ARMA
----
The autoregressive moving average method takes a time series and uses an
auto regressive term and a moving average term.

ARCH
----
Currently a work in progress

Deterministic Optimization
==========================
Currently a work in progress

Stochastic Optimization
=======================
Currently a work in progress


NO Instutition
==============
This represents the Non-Optimizing instition, included in this are the ARMA
and ARCH methods. Additionally a simple moving average calculation is included
with this archetype. The user chooses the method as part of the institution
input. 

The institution works by using the chosen method to predict supply and 
demand for given commodities. Each timestep the institution calculates a prediction
on the supply and demand for the next time step. If the demand exceeds the
supply it deploys facilities to ensure supply exceeds demand. Predictions are not
performed if the method chosen by the institution is 'moving average'. In this instance
the institution will schedule facilities for deployment only if there is a 
deficit in the current time step. 

Required Inputs
---------------
- **driving_commod**: This is the commodity that drives the deployment. The
demand of this commodity is calculated by the `demand_eq` (default = `POWER`).
- **demand_eq**: This is the string for the demand equation of the driving
commodity. The equation should use `t` as the dependent variable.
- **calc_method**: This is the method used to calculate the supply and demand.
Current available options are 'ARMA' and 'MA' for autoregressive moving average
and moving average.


Optional Inputs
---------------
- **record**: This boolean indicates whether or not the institution should record its
output to text file outputs. The output files match the name of the demand commodity
of the institution. Default: False.
- **supply_std_dev**: The number of standard deviations off of the predicted supply
value to use as the predicted value. For example if the predicted value is 10
with a standard deviation of 2, +1 will result in a predicted value of 12 and 
-1 will result in a predicted value of 8. Default: 0
- **demand_std_dev**: The number of standard deviations off of the predicted demand
value to use as the predicted value. For example if the predicted value is 10
with a standard deviation of 2, +1 will result in a predicted value of 12 and 
-1 will result in a predicted value of 8. Default: 0
- **steps**: This is the number of time steps forward the supply and demand will
be predicted. Default: 1. 
- **back_steps**: This input is for the ARCH methods. It provides the user with
the ability to set the number of timesteps back from the current time step
to use for prediction. If this is set to '0', all values in the time series
are used. Default: 5. 

Demand Fac
==========
This facility is a test facility for D3ploy. It generates a random amount of
supply and demand for commodities, and then reports these using the 
**RecordTimeSeries** functions inside of Cyclus.Thus providing a supply and
demand to the institutions.

Amount of commodity demanded and supplied can be determined randomly through
their minimum and maximum values. If for instance you'd like variability in
the production rate of your supply you can set these minimum and maximum 
values to reflect that. 

Required Inputs
--------------- 
- **demand_commod**: This is the commodity that the facility demands in order to
operate. 
- **demand_rate_min**: Minimum amount of the demanded commodity needed. 
- **demand_rate_max**: Maximum amount of the demanded commodity needed.
- **supply_commod**: The commodity that the facility supplies. 
- **supply_rate_min**: Minimum rate of production of the supplied commodity.
- **supply_rate_max**: Maximum rate of production of the supplied commodity.

Optional Inputs
---------------
- **demand_ts**: The amount of time steps between demanding material. For
example a reactor may only demand material every 18 months.
- **supply_ts**: The amount of time steps between supplying material.

