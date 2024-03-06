FROM debian:bullseye

RUN apt update && apt install -y wget git openjdk-11-jdk make maven python3 python3-pip bpftrace bpfcc-tools libbpfcc libbpfcc-dev && apt upgrade

RUN git clone https://github.com/vesta-power-model/vesta.git

RUN cd vesta && bash setup_benchmarks.sh
RUN cd vesta && mvn package
RUN cd vesta && make native

RUN cd vesta && pip3 install -r requirements.txt bcc

COPY dtrace-jdk.tar.gz vesta/.

RUN cd vesta && tar -xzvf dtrace-jdk.tar.gz

RUN cd vesta && mkdir data && python3 scripts/generate_multi_probe_experiment.py --java_path="/vesta/dtrace-jdk/bin/java" --iters=256 --exp_path=data --benchmarks=benchmarks.json

ENTRYPOINT [ "bash", "/vesta/scripts/run_experiments.sh", "/vesta/data"]