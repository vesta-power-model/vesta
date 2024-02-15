package vesta;

import org.dacapo.harness.Callback;
import org.dacapo.harness.CommandLineArgs;

/** {@link Callback} for dacapo that wraps usage of the {@link SampleCollector}. */
public class VestaDacapoCallback extends Callback {
  // private final SampleCollector collector = new SampleCollector();
  // private final SampleCollectorPapi papiCollector = new SampleCollectorPapi();
  private final PowercapCollector powercapCollector = new PowercapCollector();
    
  public VestaDacapoCallback(CommandLineArgs args) {
    super(args);
  }

  @Override
  public void start(String benchmark) {
    super.start(benchmark);
    // collector.start();
    // papiCollector.start();
    powercapCollector.start();
  }

  @Override
  public void stop(long w) {
    super.stop(w);
    // collector.stop();
    // papiCollector.stop();
    powercapCollector.stop();
  }

  @Override
  public boolean runAgain() {
    // if we have run every iteration, dump the data and terminate
    if (!super.runAgain()) {
      System.out.println("dumping data");
      // collector.dump();
      // papiCollector.dump();
      powercapCollector.dump();
      return false;
    } else {
      return true;
    }
  }
}
