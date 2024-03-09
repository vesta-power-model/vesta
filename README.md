# `VESTA`

VESTA is a power modeling system that uses *language runtime events* for prediction. Below is the abstract for the publication.

```
Power modeling is an essential building block for computer systems in support of energy optimization, energy profiling, and energy-aware application development. We introduce `VESTA`, a novel approach to modeling the power consumption of applications with one key insight: \emph{language runtime} events are often correlated with a sustained level of power consumption. When compared with the established approach of power modeling based on hardware performance counters (HPCs), `VESTA` has the benefit of not requiring root privileges and enabling higher-levels of explainability, while achieving comparable or even higher precision. Through experiments performed on 37 real-world applications on the Java Virtual Machine (JVM), `VESTA` is capable of predicting energy consumption with a mean absolute percentage error of 1.56\% while incurring a minimal performance and energy overhead.
```

## Setup

In order to run the experiments (in a Docker image or otherwise), the system must be Intel + Linux in order to be able to collect the data for the experiments.

`msr` is required to read the RAPL for energy sampling. For an Intel-Linux system, you will probably need to run `sudo modprobe msr` to enable it.

[`bpf`](https://docs.kernel.org/bpf) and [`bcc`](https://github.com/iovisor/bcc) are required for `UDST` instrumentation. Most of the time, you will only need to enable the kernel headers by adding [`CONFIG_IKHEADERS=y`](https://github.com/iovisor/bcc/blob/master/INSTALL.md#kernel-configuration) to your config. You can consult https://github.com/iovisor/bcc/blob/master/INSTALL.md if you are having trouble getting it to work.

Finally, you will need a version of `java` with [`DTrace Probes`](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/dtrace.html) enabled is needed to expose the `UDSTs`. Our official repository contains a pre-built version of `openjdk-19` that was used to run our experiments. If you would like to use a different version or you are running this from the github repository, you need to re-compile from [source](https://github.com/openjdk/jdk/blob/master/doc/building.md) with the `--enable-dtrace` flag set.

## Running with Docker

We provide a Dockerfile in this repository that should correctly set up the environment to have access to both `msr` and `bpf` so you can run the experiments. You will need to run it with the following flags for everything to work:

```
sudo docker build . -t vesta
sudo docker run -it --rm  --privileged \
    -v /lib/modules:/lib/modules:ro \
    -v /usr/src:/usr/src:ro \
    -v /etc/localtime:/etc/localtime:ro \
    vesta
```

## Running from Source

You can also reproduce our experiments directly from this repository. Our experiments were run on the following system:

```
dual socket Intel Xeon E5-3630 v4 2.20GHz
64GB DDR4 RAM
Debian 11
Linux kernel 5.17.0-3-amd64
```

### Setup

First you should install the following:

```
apt-get install -y git wget openjdk-11-jdk make \
    gcc maven bpftrace bpfcc-tools libbpfcc libbpfcc-dev \
    python3 python3-pip
pip3 install numpy pandas pytest numba
```

1. run `bash setup_benchmarks.sh` to get the dependency benchmarks.

2. run `mvn clean install` to build a fat vesta `jar`.

3. run `make native` to build the native libraries used for runtime sampling.

## Experiments Reproduction

An experiment is defined using a `json` file. The file should contain a list of dicts that define the parameters for the experiments:

```json
{
    "suite": "dacapo",
    "benchmark": "avrora",
    "size": "default",
    "probes": "NewStringUTF__entry,NewStringUTF__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,thread__park__begin,thread__park__end",
    "callback": "VestaDacapoCallback",
},
```

We provide a `benchmarks.json` file that describes which experiments to run. You can generate new experiment scripts by running `scripts/generate_multi_probe_experiment.py` with a  `benchmarks.json`. This will create a directory containing the experiment driving code:

```bash
mkdir data && python3 scripts/generate_multi_probe_experiment.py \
    --java_path=dtrace-jdk/bin/java \
    --iters=256 \
    --exp_path=data \
    --benchmarks=benchmarks.json
```

Once your experiment directory is generated, you can run everything with `bash scripts/run_experiments.sh data`.

## Modeling

The data can be pre-processed into an aligned time-series with:

```bash
python3 scripts/alignment.py \
    --out_file_name=data/aligned.csv \
    --bucket=1000 \
    --warm_up=5 \
    data
```

Modeling and evaluation is done through the code provided in `notebooks`.
