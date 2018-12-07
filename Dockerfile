FROM cyclus/cycamore:latest

COPY . /d3ploy
WORKDIR /d3ploy
RUN apt-get update
RUN conda install pyqt -y && \
    conda install -c bashtage arch -y && \
    conda install statsmodels matplotlib scipy numpy -y && \
    conda update --all -y && \
    pip install pyramid-arima && \
    pip install -U pytest && \
    python setup.py install