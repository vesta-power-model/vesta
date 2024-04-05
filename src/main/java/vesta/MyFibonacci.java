package vesta;

final class MyFibonacci {
  private static int fib(int n) {
    if (n == 0 || n == 1) {
      return n;
    } else {
      return fibonacci(n - 1) + fibonacci(n - 2);
    }
  }

  public static void main(String[] args) {
    int iterations = Integer.parseInt(args[0]);
    PowercapCollector collector = new PowercapCollector();
    for (int i = 0; i < iterations; i++) {
      collector.start();
      fib(42);
      collector.stop();
    }
    collector.dump();
  }
}
