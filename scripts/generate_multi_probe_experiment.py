#!/usr/bin/python
# The idea here is to generate scripts that can be run later on in the pipeline
# Some things are still hard-coded for convenience, but should be changed later
#       i.e. library_path, script_path, dacapo_path, renaissance_path, renaissance_jar, when calling the renaissance jar, & the references to the vesta jar
import argparse
import os
import json

parser = argparse.ArgumentParser(
    description="Probes Parser", formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("-iters", "--iters", type=int, help="Number of iterations")
parser.add_argument("-exp_path", "--exp_path", type=str,
                    help="Path where benchmarks file is stored")
parser.add_argument("-java_path", "--java_path", type=str,
                    help="Path to specified java version", default="java")
parser.set_defaults(verbose=False)

args = parser.parse_args()
exp_path = args.exp_path
java_path = args.java_path
iters = args.iters
launch_path = exp_path + "/launch/"
library_extra_papi = f"LD_LIBRARY_PATH={os.getcwd()}/bin/.:/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
library_path = f"{os.getcwd()}/bin/"
vesta_jar = f"{os.getcwd()}/target/vesta-0.1.0-jar-with-dependencies.jar"
dacapo_path = f"{os.getcwd()}/lib/dacapo.jar:{vesta_jar}"
renaissance_path = f"{os.getcwd()}/lib/renaissance-gpl-0.14.1.jar:{vesta_jar}"
renaissance_jar = f"{os.getcwd()}/lib/renaissance-gpl-0.14.1.jar"
script_path = f"{os.getcwd()}/scripts/"
gc = ""


def create_dir(str_dir):
    try:
        os.mkdir(str_dir)
    except FileExistsError:
        print("Directory already exists...skipping creation")
    except:
        print("OS error! Could not create %s" % (str_dir))
        quit()


create_dir(launch_path)
with open(exp_path + "/benchmarks.json") as fp:
    # cluster_count and bench_count are used to enforce a naming convention for the experimental folders
    # <cluster #>_<bench #>_benchmark
    cluster_count = 0
    tests = json.load(fp)
    for test in tests:
        #    <benchmark suite letter> <benchmarks separated by commas> <probes>
        benchmark = test["benchmark"]
        probes = test["probes"]
        suite = test["suite"]
        # hpcs = test["hpcs"]
        hpcs = "none"
        # iters = test["iterations"]
        if (suite == "dacapo"):
            size = test["size"]
        callback = test["callback"]
        filter_status = test["filter"]
        if (filter_status == "yes"):
            window = test["window"]
            variance = test["variance"]
            baseline_path = test["baseline_path"]
        output_file = open(launch_path + "cluster_" +
                           str(cluster_count) + ".sh", "w")
        if (suite == "dacapo"):
            if (filter_status == "yes"):
                output_file.write(f'{library_extra_papi} {java_path} {gc} -XX:+ExtendedDTraceProbes -Dvesta.library.path={library_path} -Dvesta.output.directory={exp_path}/{cluster_count}_{benchmark} -Dvesta.baseline.path={baseline_path} -Dvesta.hpc.names={hpcs} -cp {dacapo_path} Harness {benchmark} -s {size} -no-validation --iterations {iters} --window {window} --variance {variance} -c vesta.{callback} &\n')
            else:
                output_file.write(f'{library_extra_papi} {java_path} {gc} -XX:+ExtendedDTraceProbes -Dvesta.library.path={library_path} -Dvesta.output.directory={exp_path}/{cluster_count}_{benchmark} -Dvesta.hpc.names={hpcs} -cp {dacapo_path} Harness {benchmark} -s {size} -no-validation --iterations {iters} -c vesta.{callback} &\n')
        else:
            if (filter_status == "yes"):
                output_file.write(f'{library_extra_papi} {java_path} {gc} -XX:+ExtendedDTraceProbes -Dvesta.library.path={library_path} -Dvesta.output.directory={exp_path}/{cluster_count}_{benchmark} -Dvesta.baseline.path={baseline_path} -Dvesta.renaissance.args={iters},{window},{variance} -Dvesta.hpc.names={hpcs} -cp {renaissance_path} -jar {renaissance_jar} --plugin {vesta_jar}!vesta.{callback} --policy {vesta_jar}!vesta.{callback} {benchmark} &\n')
            else:
                output_file.write(f'{library_extra_papi} {java_path} {gc} -XX:+ExtendedDTraceProbes -Dvesta.library.path={library_path} -Dvesta.output.directory={exp_path}/{cluster_count}_{benchmark} -Dvesta.hpc.names={hpcs} -cp {renaissance_path} -jar {renaissance_jar} -r {iters} --plugin {vesta_jar}!vesta.{callback} {benchmark} &\n')
        if probes != "none" and 0:
            output_file.write(
                f"python3 {script_path}java_multi_probe.py --pid $! --probes={probes} --output_directory={exp_path}/{cluster_count}_{benchmark} \n")
        else:
            output_file.write("pid=$! \n")
            output_file.write(
                f"python3 {script_path}java_multi_probe.py --pid $pid --probes={probes} --output_directory={exp_path}/{cluster_count}_{benchmark} & \n")
            # output_file.write(f"{library_path}perf stat -e {hpcs} -I 1 -a -x '@' -o {exp_path}/{cluster_count}_{benchmark}/hpc.csv -p $pid\n")
            # output_file.write(f"sed -i -e 1,3d {exp_path}/{cluster_count}_{benchmark}/hpc.csv\n")
            # output_file.write(f"sed -i '1s/^/ts@events@unit@hpc@event-runtime@pcnt-running@metric-value@metric-unit\\n/' {exp_path}/{cluster_count}_{benchmark}/hpc.csv \n")
            output_file.write("tail --pid=$pid -f /dev/null \n")
        create_dir("%s/%d_%s" % (exp_path, cluster_count, benchmark))
        cluster_count = cluster_count + 1
        output_file.close()
fp.close()
