# d3ploy
A collection of Cyclus manager archetypes for demand driven deployment. It operates using
global calls within a Cyclus simulation so that all agents within the simulation
can communicate. The goal of this package is to provide three types of mathematical
basis for determining supply and demand of commodities within Cyclus; Non-optimizing (NO)
deterministing optimization (DO), and Stochastic optimization (SO). 

Non-Optimizing
==============
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
and ARCH methods. The user chooses the method as part of the institution
input. 

The institution works by using the chosen method to predict supply and 
demand for given commodities. It operates using a demand commodity and
a supply commidity. 

Demand Fac
==========

