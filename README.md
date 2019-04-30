# d3ploy
A collection of Cyclus manager archetypes for demand driven deployment. It operates using
global calls within a Cyclus simulation so that all agents within the simulation
can communicate. The goal of this package is to provide three types of mathematical
basis for predicting supply and demand of commodities within Cyclus; Non-optimizing (NO)
deterministing optimization (DO), and Stochastic optimization (SO). 

## Dependencies
**Cyclus**: Fuel cycle simulation tool. [Documentation](fuelcycle.org)

**statsmodels**: Python package for statistical analysis.[Documentation](https://www.statsmodels.org/stable/index.html)

**arch**: Python package for conditional heteroskidasticity models.[Documentation](https://arch.readthedocs.io/en/latest/index.html)

**Pmdarima**: A python package for ARIMA/SARIMA methods. [Documentation](https://pypi.org/project/pmdarima/)


## demand_driven_deployment_inst and supply_driven_deployment_inst

### demand_driven_deployment_inst
`demand_driven_deployment_inst` is a  Cyclus `Institution` archetype that performs demand-driven
deployment of Cyclus agents.

The institution works by using the chosen method to predict supply and 
demand for given commodities. Each timestep the institution calculates a prediction
on the supply and demand for the next time step. If the demand exceeds the
supply it deploys facilities to ensure supply exceeds demand. Predictions are not
performed if the method chosen by the institution is 'moving average'. In this instance
the institution will schedule facilities for deployment only if there is a 
deficit in the current time step. 

This institution is used for facilities that exist in the front end of the fuel cycle. 

### supply_driven_deployment_inst 
`supply_driven_deployment_inst` is a  Cyclus `Institution` archetype that performs supply-driven
deployment of Cyclus agents.

The institution works by using the chosen method to predict supply and 
capacity for given commodities. Each timestep the institution calculates a prediction
on the supply and capacity for the next time step. If the supply exceeds the
capacity it deploys facilities to ensure capacity exceeds supply. Predictions are not
performed if the method chosen by the institution is 'moving average'. In this instance
the institution will schedule facilities for deployment only if there is a 
deficit in the current time step. 

This institution is used for facilities that exist in the back end of the fuel cycle. 

### Required Inputs for each institution  
In the first four inputs,  for `demand_driven_deployment_inst`, the facility included should be the facility that supplies the commodity
and for `supply_driven_deployment_inst`, the facility included should be the facility that supplies capacity for that commodity. 
- **facility_commod**: This is a mapstringstring defining each facility and the output commodity to track. 
 Every facility that the user wants to control using this institution must be included in this input. 
- **facility_capacity**: This is a mapstringdouble defining each facility and the (initial) capacity of the facility. 
 Every facility that the user wants to control using this institution must be included in this input. 
- **facility_pref**: This is a mapstringstring defining each facility and the preference for that facility. 
 The preference can be given as an equation, using `t` as the dependent variable (e.g. `(1.01)**t`). 
  Only the facilities that the user wants to give preference values to need to be included in this input. 
- **facility_constraintcommod**: This is a mapstringstring defining each facility and the second commodity that constraints its deployment. 
 Only the facilities that the user wants to constrain with a second commodity need to be included in this input. 
- **facility_constraintval**: This is a mapstringdouble defining each facility and the amount accumulated of the second commodity 
 before the facility can be deployed. 
 Only the facilities that the user wants to constrain by a second commodity need to be included in this input. 
- **driving_commod**: The driving commodity for the institution.
- **demand_eq**:  The demand equation for the driving commodity, using `t` as the dependent variable.
- **calc_method**: This is the method used to predict the supply and demand.
- **buffer_type**: This is a mapstringstring defining each commodity and the type of supply/capacity 
buffer for it. For percentage, the user should input `perc`, for a absolute value, the user should 
input `float`. The default is percentage. 
- **installed_cap**: This is a boolean to determine whether deployment is governed by supply of the commodity of installed capacity for that commodity. 



#### Differing Inputs 
DemandDrivenDeploymentInst:
- **supply_buffer**: This is the amount above demand that the user wants the supply to meet. 
The user can define the buffer type in the state variable `buffer_type`.
If the user wants a 20% value of supply higher than demand, they should input '0.2'
and if the user wants a 100[whatever unit] value of supply higher than demand, they should input '100'. 

SupplyDrivenDeploymentInst:
- **capacity_buffer**: This is the amount above supply that the user wants the capacity to meet. 
The user can define the buffer type in the state variable `buffer_type`.
If the user wants a 20% value of capacity higher than supply, they should input '0.2'
and if the user wants a 100[whatever unit] value of capacity higher than supply, they should input '100'. 


### Prediction Methods
Prediction methods are categorized in three - Non-optimizing, deterministic-optimizing,
and stochastic-optimizing.

#### Non-Optimizing Methods
There are three methods implemented for the NO models. Autoregressive
moving average (ARMA), and autoregressive conditional heteroskedasticity (ARCH).
There are four parameters users can define:
- **steps**: Number of timesteps forward to prdict supply and demand (default = 2)
- **back_steps**: Number of steps backwards from the current timestep to use for the prediction (default = 10)
- **supply_std_dev** = Standard deviation adjustment for supply (default = 0)
- **demand_std_dev** = Standard deviation adjustment for demand  (default = 0)

##### MA (`ma`)


##### ARMA (`arma`)
The autoregressive moving average method takes a time series and uses an 
auto regressive term and a moving average term. 


##### ARCH (`arch`)
The Autoregressive Conditional Heteroskedasticity (ARCH) method predicts the
future value by using the observed values of returns or residuals.

#### Deterministic Optimization
There are three methods implemented for the DO models. Polynomial fit regression,
simple exponential smoothing, and triple exponential smoothing (holt-winters).
There are two parameters users can define:
- **back_steps**: Number of steps backwards from the current timestep to use for the prediction (default = 10)
- **degree** : degree of polynomial fit (default = 1)

##### Polynomial fit regression (`poly`)
The polynomial fit regression method fits a polynomial equation of
degree k (`degree`) for the  n (`back_steps`) previous values to predict the next value.
A polynomial equation of degree 1 is a linear equation (`y = ax + b`)
This method is suitable for values with a clear trend. 

##### Exponential smoothing (`exp_smoothing`)
The exponential smoothing method takes the weighted average of past n (`back_steps`),
in which more weight is given to the last observation.
This method is suitable for values with no clear trend or pattern.

##### Triple exponential smoothing, Holt-Winters (`holt_winters`)
The triple smoothing method combines three smoothing equations -
one for the level, one for trend, and one for the seasonal component -
to predict the next value. This method is suitable for values with
seasonality.

#### Fast Fourier Transform (`fft`)
(EXPERIMENTAL)
The method builds a function that represents the data as a sumation of harmonics of different order. In the case of having a set of data that presents oscilations the user should set the degree to 2.

#### Stochastic Optimization
Currently a work in progress


## Demand Fac
This facility is a test facility for D3ploy. It generates a random amount of
supply and demand for commodities, and then reports these using the 
**RecordTimeSeries** functions inside of Cyclus.Thus providing a supply and
demand to the institutions.

Amount of commodity demanded and supplied can be determined randomly through
their minimum and maximum values. If for instance you'd like variability in
the production rate of your supply you can set these minimum and maximum 
values to reflect that. 

### Required Inputs 
- **demand_commod**: This is the commodity that the facility demands in order to
operate. 
- **demand_rate_min**: Minimum amount of the demanded commodity needed. 
- **demand_rate_max**: Maximum amount of the demanded commodity needed.
- **supply_commod**: The commodity that the facility supplies. 
- **supply_rate_min**: Minimum rate of production of the supplied commodity.
- **supply_rate_max**: Maximum rate of production of the supplied commodity.

### Optional Inputs
- **demand_ts**: The amount of time steps between demanding material. For
example a reactor may only demand material every 18 months.
- **supply_ts**: The amount of time steps between supplying material.

