FROM hdfgroup/hdf5lib:1.10.6
MAINTAINER Ben Galewsky <bengal1@illinois.edu>
RUN mkdir /opt/nasa
COPY scripts/requirements.txt /opt/nasa
RUN pip install -r /opt/nasa/requirements.txt
COPY scripts/*.py /opt/nasa/
CMD python /opt/nasa/index_file.py -q hsload_work.fifo

