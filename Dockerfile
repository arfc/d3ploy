FROM cyclus/cycamore:latest

COPY . /d3ploy
WORKDIR /d3ploy
RUN conda install pyqt -y && \
    conda install -c bashtage arch -y && \
    conda install statsmodels matplotlib scipy numpy -y && \
    conda update --all -y && \
    pip install pmdarima && \
    pip install -U pytest && \
    pip uninstall h5py && \
    pip install --no-cache-dir h5py && \
    python setup.py install && \
    sudo apt-get update && \
    sudo apt-get install libhdf5-dev && \
    sudo apt-get update && \
    sudo apt-get install libhdf5-serial-dev && \

