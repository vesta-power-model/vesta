# `VESTA`

VESTA is a power modeling system that uses *language runtime events* for prediction. Below is the abstract for the publication.

```
Power modeling is an essential building block for computer systems in support of energy optimization,
energy profiling, and energy-aware application development. We introduce `VESTA`, a novel approach
to modeling the power consumption of applications with one key insight: *language runtime* events
are often correlated with a sustained level of power consumption. When compared with the established
approach of power modeling based on hardware performance counters (HPCs), `VESTA` has the benefit of not
requiring root privileges and enabling higher-levels of explainability, while achieving comparable or
even higher precision. Through experiments performed on 37 real-world applications on the
Java Virtual Machine (JVM), `VESTA` is capable of predicting energy consumption with a mean absolute
percentage error of 1.56\% while incurring a minimal performance and energy overhead.
```

## Setup

In order to run the experiments (in a Docker image or otherwise), the system must be Intel + Linux and you must have `sudo` access in order to collect the data for the experiments. These following steps must be done on your system even if you are running through the Docker image.

### RAPL

`msr` is required to read the RAPL for energy sampling. For an Intel-Linux system, you will probably need to run `sudo modprobe msr` to enable it.

### bcc

[`bpf`](https://docs.kernel.org/bpf) and [`bcc`](https://github.com/iovisor/bcc) are required for `UDST` instrumentation. First you need to enable the kernel headers by updating your configuration, which can be found at either `/proc/config.gz` or `/boot/config-<kernel-version>`. You should ensure the following flags in the configuration are set to `y`:

```
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_HAVE_EBPF_JIT=y
CONFIG_BPF_EVENTS=y
CONFIG_IKHEADERS=y
```

Next, you will need to setup `bpf` and `bcc` for your distribution, which is listed in `bcc`'s [installation guide](https://github.com/iovisor/bcc/blob/master/INSTALL.md). For this process, you will need to install the kernel headers, `bpf`, and `bcc` which is frequently available through your package manager. The specific packages will differ and can be found in the installation guide, but we provide the instructions here for ease:

```
# debian
echo deb http://cloudfront.debian.net/debian sid main >> /etc/apt/sources.list
sudo apt-get install -y bpfcc-tools libbpfcc libbpfcc-dev linux-headers-$(uname -r)

# ubuntu
sudo apt-get install bpfcc-tools linux-headers-$(uname -r)

# fedora 30 and higher
sudo dnf install bcc

# fedora 29 and lower
sudo dnf config-manager --add-repo=http://alt.fedoraproject.org/pub/alt/rawhide-kernel-nodebug/fedora-rawhide-kernel-nodebug.repo
sudo dnf update

# arch linux
pacman -S bcc bcc-tools python-bcc

# gentoo
emerge sys-kernel/gentoo-sources
emerge dev-util/bcc

# openSUSE
sudo zypper ref
sudo zypper in bcc-tools bcc-examples

# RHEL
yum install bcc-tools

# amazon linux 1
sudo yum update kernel
sudo yum install bcc
sudo reboot

# amazon linux 2
sudo amazon-linux-extras install BCC

# alpine
sudo apk add bcc-tools bcc-doc
```

### Java with Dtrace

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

If you are trying to reproduce the experiments from the github repo, you will need to get the benchmark jars before building the Docker image, which can be done with `bash setup_benchmarks.sh`.

## Running from Source

You can also reproduce our experiments directly from this repository. Our experiments were run on the following system:

```
Dual socket Intel Xeon E5-3630 v4 2.20GHz
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
pip3 install numpy pandas pytest numba xgboost scikit-learn
```
If you are not on Debian. your system's package manager likely has similar targets.

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

Modeling and evaluation can done through the two provided scripts:

```bash
python3 scripts/model_builder.py \
    --out_path=data \
    --name=vesta-artifact \
    data/aligned.csv
```

```bash
python3 scripts/inference.py \
    --out_path=data/vesta-artifact_inference.pdf \
    data/vesta-artifact.json \
    data/vesta-artifact_test.csv
```
