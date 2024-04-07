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

[`bpf`](https://docs.kernel.org/bpf) and [`bcc`](https://github.com/iovisor/bcc) must be enabled on the host machine for `UDST` instrumentation. You will need to ensure that your kernel has been compiled with the Linux kernel headers. Most modern distributions of Linux have already been compiled with the headers, so you may not need to do any additional work.

Next you need to enable `bpf` by updating your configuration, which can be found at either `/proc/config.gz` or `/boot/config-<kernel-version>`. You will need to add the following flags (if they are not already present) and set all of them to `y`:

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
    "suite": "dacapo", // options: ["dacapo", "renaissance", "custom"]
    "benchmark": "avrora",
    "size": "default", // only necessary for "dacapo"
    "probes": "NewStringUTF__entry,NewStringUTF__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,thread__park__begin,thread__park__end",
},
```

We provide some `json` files that contain the experiments used to produce our data. You can generate new experiment scripts by running `scripts/generate_experiments.py` with a `benchmarks.json`. This will create a directory containing the experiment driving code. The probes listed in `benchmark-confgs/benchmarks.json` were selected during `VESTA`'s screening. You may add or remove probes from this list by consulting the full list of Java's [DTrace Probes](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/dtrace.html); make sure that any instance of a hyphen (`-`) is replaced by two underscores (`__`) if you do add probes. There are two additional caveats regarding modifying the sampled probes:

1. As mentioned in the publication, unselected probes incurred significant overhead 
2. Language runtime events (LREs) are represented through a pair of probes with the same prefix but ending with `__entry`/`__return` and `__begin`/`__end`. If a given probe does not have its pair, then it will be modeled individually as a counter.

To do a full reproduction, first you'll need to build and run the baseline, i.e. benchmarks with no probing:

```bash
python3 scripts/generate_experiments.py \
    --java_path=dtrace-jdk/bin/java \
    --iters=256 \
    --exp_path="${PWD}/baseline" \
    --benchmarks="${PWD}/benchmark-configs/baseline.json"
bash scripts/run_experiments.sh "${PWD}/baseline"
```

Then do the same with the probing enabled:

```bash
python3 scripts/generate_experiments.py \
    --java_path=dtrace-jdk/bin/java \
    --iters=256 \
    --exp_path="${PWD}/data" \
    --benchmarks="${PWD}/benchmark-configs/benchmarks.json"
bash scripts/run_experiments.sh "${PWD}/data"
```

After the benchmarks complete, you can check the summary of the experiment by using the `scripts/overhead.py` `scripts/metrics.py` scripts:

```bash
python3 scripts/overhead.py 
    --ref=baseline \
    --data=data \
    --bucket=1000 \
    --warm_up=5 \
    --output_directory=data
python3 scripts/metrics.py 
    --output_directory=data \
    --bucket=1000 \
    --warm_up=5 \
    data
```

## Modeling

The data can be pre-processed into an aligned time-series with `scripts/alignment.py`:

```bash
python3 scripts/alignment.py \
    --out_file_name=data/aligned.csv \
    --bucket=1000 \
    --warm_up=5 \
    data
```

Modeling is done with the `scripts/model_builder.py`:

```bash
python3 scripts/model_builder.py \
    --out_path=data \
    --name=vesta-artifact \
    data/aligned.csv
```

Then you can produce plots using ``:

```bash
python3 scripts/inference.py \
    --out_path=data/vesta-artifact_inference.pdf \
    data/vesta-artifact.json \
    data/vesta-artifact_test.csv
```


## Running a custom benchmark

VESTA supports the addition of new Java benchmarks that can be run either standalone or as part of an experiment.

### Creating a Java Benchmark

You can add your Java program to this repository (preferably at `src/main/java/vesta`) and use the `vesta.SampleCollector` in your program to add energy data collection:

```java
package vesta;

final class MyFibonacci {
    int fib(int n) { ...}

    public static void main(String[] args) {
        int iterations = Integer.parseInt(args[0]);
        SampleCollector collector = new SampleCollector();
        for (int i = 0; i < iterations; i++) {
            collector.start();
            fib(42);
            collector.stop();
        }
        collector.dump();
    }
}
```

Next, recompile the tool with `mvn package`; if you have third-party dependencies, you should add them to the `pom.xml`. You should be able to directly run your benchmark from the newly built jar:

```bash
OUT_DIR=data/my-fibonacci
dtrace-jdk/bin/java -cp "${PWD}/target/vesta-0.1.0-jar-with-dependencies.jar" \
    -Dvesta.output.directory="${OUT_DIR}" \
    -Dvesta.library.path="${PWD}/bin" \
    vesta.MyFibonacci 50
```

The above command will produce `summary.csv`, which contains end-to-end measurements of energy and runtime, and `energy.csv`, which contains timestamped measurements` of energy, at `data/my-fibonacci`.

### BPF Probing

Next, you can do bpf probing by calling the `scripts/java_multi_probe.py` script on your executing Java program:

```bash
PROBES=NewStringUTF__entry,NewStringUTF__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,thread__park__begin,thread__park__end
python3 /mnt/c/Users/atpov/Documents/projects/vesta/scripts/java_multi_probe.py --pid "${pid}" \
    --output_directory="${OUT_DIR}" \
    --probes="${PROBES}"
```

This will produce a `probes.csv` file containing the probing information.

### Collecting data for `VESTA`

You can manually execute the benchmark as a sanity test with a small script:

```bash
OUT_DIR="${PWD}/data/my-fibonacci"
PROBES=NewStringUTF__entry,NewStringUTF__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,thread__park__begin,thread__park__end
dtrace-jdk/bin/java -cp "${PWD}/target/vesta-0.1.0-jar-with-dependencies.jar" \
    -Dvesta.output.directory="${OUT_DIR}" \
    -Dvesta.library.path="${PWD}/bin" \
    vesta.MyFibonacci 50 &
pid=$! # retrieve last process pid
python3 "${PWD}/scripts/java_multi_probe.py" --pid "${pid}" \
    --output_directory="${OUT_DIR}" \
    --probes="${PROBES}"
```

We provide an example script at `scripts/my_fibonacci.sh` that you can copy and modify to achieve this behavior quickly.

You can then add your benchmark to a `benchmarks.json` file as a `"custom"` suite:

```json
{
    "suite": "custom",  
    "benchmark": "my-fibonacci",
    "main_class": "vesta.MyFibonacci",
    "args": "42 {iters}",
    "probes": "NewStringUTF__entry,NewStringUTF__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,thread__park__begin,thread__park__end",
}
````

Now you can follow the steps in the [experiment reproduction](#experiments-reproduction) and [modeling guide](#modeling) to evaluate and model with your new benchmark.
