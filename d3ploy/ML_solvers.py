import numpy
from pyramid.arima import auto_arima
import d3ploy.NO_solvers as no


def stepwise_seasonal(ts, period=5):
    data = list(ts.values())
    if len(data) == 1:
        return no.predict_ma(ts)
    try:
        stepwise_model = auto_arima(data, start_p=1, start_q=1,
                                    max_p=5, max_q=5, m=period,
                                    start_P=0, seasonal=True,
                                    d=1, D=1, trace=True,
                                    error_action='ignore',
                                    suppress_warnings=True,
                                    stepwise=True)
        stepwise_model.fit(data)
        future_forecast = stepwise_model.predict(n_periods=1)[-1]
    except:
        return no.predict_ma(ts)
    return future_forecast
