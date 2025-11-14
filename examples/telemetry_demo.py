from __future__ import annotations

import logging
import os
from time import sleep

from wanaspects import AspectManager, default_bundle, init_telemetry
from wanaspects.core.context import AdviceContext


def main() -> None:
    # Initialize telemetry based on environment variables.
    # Requires: WANCHAIN_ASPECTS_ENABLED=true
    init_telemetry()

    # Configure stdlib logging to see output without extra setup
    logging.basicConfig(level=logging.DEBUG)

    manager = AspectManager(default_bundle())

    def step() -> str:
        # Simulate a bit of work
        sleep(0.05)
        return "ok"

    ctx = AdviceContext(step_name="demo_step", container_shape="single", boundary="none")
    result = manager.run(ctx, step)
    print("result:", result)


if __name__ == "__main__":
    # Helpful defaults for local demo when not set externally
    os.environ.setdefault("WANCHAIN_ASPECTS_ENABLED", "true")
    os.environ.setdefault("WANCHAIN_TRACE_SAMPLING", "0.1")
    os.environ.setdefault("WANCHAIN_OTEL_CONSOLE", "true")
    main()
