package vesta;

import javax.security.auth.callback.Callback;
import org.renaissance.Plugin;

/** {@link Callback} for renaissance that wraps usage of the {@link SampleCollector}. */
public class VestaRenaissancePlugin
    implements Plugin.BeforeBenchmarkTearDownListener,
        Plugin.AfterOperationSetUpListener,
        Plugin.BeforeOperationTearDownListener {
  private final PowercapCollector collector = new PowercapCollector();

  @Override
  public void afterOperationSetUp(String benchmark, int opIndex, boolean isLastOp) {
    collector.start();
  }

  @Override
  public void beforeOperationTearDown(String benchmark, int opIndex, long durationNanos) {
    collector.stop();
  }

  @Override
  public void beforeBenchmarkTearDown(String benchmark) {
    System.out.println("dumping data");
    collector.dump();
  }
}
