# `Vesta`

## Setup

First install the following:

```bash
sudo apt-get install openjdk19 maven make python
```

Any version of `java` should be sufficient to build the source.

Then set up these:

[`msr`] is required to read the RAPL for energy sampling. For an Intel-Linux system, you will probably need to run `sudo modprobe msr` to enable it.

[`bpf`](https://docs.kernel.org/bpf) and [`bcc`](https://github.com/iovisor/bcc) to do `UDST` instrumentation. You can consult https://github.com/iovisor/bcc/blob/master/INSTALL.md if you are having trouble getting it to work.

A version of `java` with the [`DTrace Probes`](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/dtrace.html) enabled is needed to expose the `UDSTs`. You will likely have to re-compile from [source](https://github.com/openjdk/jdk/blob/master/doc/building.md) with the `--enable-dtrace` flag set. Ideally you will only need to run `bash configure --enable-dtrace`. You should be able to do this with any version; our experiments use `Java 19`.

## Building

1. run `bash setup_benchmarks.sh` to get the dependency benchmarks.

2. run `mvn clean install` to build a fat vesta `jar`.

3. run `make native` to build the native libraries used for runtime sampling.

4. run `pip install -r requirements.txt` to setup libraries for `BPF` sampling and modeling.

## Experiment Reproduction

An experiment is defined using a `json` file. The file should contain a list of dicts that define the parameters for the experiments:

```json
{
    "suite": "dacapo",
    "benchmark": "avrora",
    "size": "default",
    "probes": "CallObjectMethod__entry,CallObjectMethod__return,CallVoidMethod__entry,CallVoidMethod__return,DestroyJavaVM__entry,DestroyJavaVM__return,GetByteArrayElements__entry,GetByteArrayElements__return,GetEnv__entry,GetEnv__return,GetFloatField__entry,GetFloatField__return,GetLongField__entry,GetLongField__return,GetMethodID__entry,GetMethodID__return,GetObjectArrayElement__entry,GetObjectArrayElement__return,GetObjectClass__entry,GetObjectClass__return,GetStringLength__entry,GetStringLength__return,IsInstanceOf__entry,IsInstanceOf__return,NewDirectByteBuffer__entry,NewDirectByteBuffer__return,NewLongArray__entry,NewLongArray__return,NewString__entry,NewString__return,NewStringUTF__entry,NewStringUTF__return,ReleaseIntArrayElements__entry,ReleaseIntArrayElements__return,ReleaseShortArrayElements__entry,ReleaseShortArrayElements__return,SetByteArrayRegion__entry,SetByteArrayRegion__return,SetIntField__entry,SetIntField__return,Throw__entry,Throw__return,class__initialization__concurrent,class__initialization__error,class__unloaded,compiled__method__load,compiled__method__unload,gc__begin,gc__end,method__compile__begin,method__compile__end,safepoint__begin,safepoint__end,thread__park__begin,thread__park__end,thread__sleep__begin,thread__sleep__end,vmops__begin,vmops__end",
    "callback": "VpcDacapoCallback",
    "filter": "no",
    "window": "4",
    "variance": "125",
    "baseline_path": "/path/to/data/0_0_avrora"
},
```

We provide a `benchmarks.json` file that contains the experiments used to produce our data.

Then you can generate experiment scripts by running `scripts/generate_multi_probe_experiment.py` with your `benchmarks.json`. This will create a directory containing the experiment driving code:

```bash
python scripts/generate_multi_probe_experiment.py \
    --java_path=/path/to/dtrace_enabled/java \
    --iters=256 \
    --exp_path=/path/to/data \
    --benchmarks=benchmarks.json
```

The data can be processed into an aligned time-series with:

```bash
python scripts/alignment.py \
    --out_file_name=/path/to/data/aligned.csv \
    --bucket=1000 \
    --warm_up=5 \
    /path/to/data
```

Modeling and evaluation is done through the code provided in `notebooks`.
