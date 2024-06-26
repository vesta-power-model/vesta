package vesta;

import org.renaissance.Plugin;

public class FilteringVestaRenaissancePlugin
    implements Plugin.ExecutionPolicy,
        Plugin.AfterOperationSetUpListener,
        Plugin.BeforeOperationTearDownListener {
  private final SampleCollector collector = new SampleCollector();
  private final int maxIters =
      Integer.parseInt(System.getProperty("vesta.renaissance.args").split(",")[0]);
  private final int batchSize =
      Integer.parseInt(System.getProperty("vesta.renaissance.args").split(",")[1]);
  private final double threshold =
      Double.parseDouble(System.getProperty("vesta.renaissance.args").split(",")[2]) / 100.0;
  private final double baselineRuntime = SampleCollector.getBaselineRuntime(batchSize);

  @Override
  public void afterOperationSetUp(String benchmark, int opIndex, boolean isLastOp) {
    collector.start();
  }

  @Override
  public void beforeOperationTearDown(String benchmark, int opIndex, long durationNanos) {
    collector.stop();
  }

  @Override
  public boolean canExecute(String benchmark, int opIndex) {
    if (opIndex >= maxIters) {
      collector.dumpWithStatus(true);
      return false;
    } else if (opIndex % batchSize == 0 && opIndex >= batchSize) {
      // filter by metric
      double runtime =
          collector.getSummary().stream()
              .skip(batchSize)
              .mapToDouble(s -> s.duration)
              .average()
              .orElse(0);
      if (runtime / baselineRuntime > nextThreshold(opIndex)) {
        System.out.println(
            String.format(
                "last %d runs exceeded threshold (%f / %f = %f > %f)",
                opIndex, runtime, baselineRuntime, runtime / baselineRuntime, threshold));
        collector.dumpWithStatus(false);
        return false;
      } else {
        System.out.println(
            String.format(
                "last %d runs met threshold (%f / %f = %f < %f)",
                opIndex, runtime, baselineRuntime, runtime / baselineRuntime, threshold));
      }
    }

    return true;
  }

  @Override
  public boolean isLast(String benchmark, int opIndex) {
    return true;
  }

  private double nextThreshold(int opIndex) {
    return 1 + (threshold - 1) / (opIndex / batchSize - 1);
  }
}
