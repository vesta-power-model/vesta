package vesta;

import java.time.Duration;
import java.time.Instant;

final class MyFibonacci {
  private static int fib(int n) {
    if (n == 0 || n == 1) {
      return n;
    } else {
      return fib(n - 1) + fib(n - 2);
    }
  }

  public static void main(String[] args) {
    int iterations = Integer.parseInt(args[0]);
    PowercapCollector collector = new PowercapCollector();
    for (int i = 0; i < iterations; i++) {
      Instant start = Instant.now();
      collector.start();
      fib(42);
      collector.stop();
      System.out.println(
          String.format(
              "computed fib(42) in %s millis", Duration.between(start, Instant.now()).toMillis()));
    }
    collector.dump();
  }
}
