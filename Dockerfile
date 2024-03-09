FROM debian:bullseye-slim

# setup
RUN apt-get update && apt-get install -y git wget openjdk-11-jdk make gcc maven
RUN git clone https://github.com/vesta-power-model/vesta.git

# setup java code
COPY lib vesta/lib
RUN cd vesta && bash setup_benchmarks.sh
RUN cd vesta && mvn package
RUN cd vesta && make native

# setup bpf probing
COPY dtrace-jdk.tar.gz vesta/.
RUN cd vesta && tar -xzvf dtrace-jdk.tar.gz
RUN apt-get install -y bpftrace bpfcc-tools libbpfcc libbpfcc-dev
RUN apt-get install -y python3 python3-pip
RUN cd vesta && pip3 install numpy pandas pytest numba xgboost sklearn

