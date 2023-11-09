import gc
import logging
import os
import time
from pathlib import Path

import psutil
import pytest
from _pytest.python import Function

LOGGER = logging.getLogger(__name__)


@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    start = time.time()
    process = psutil.Process(os.getpid())

    base_memory_usage = process.memory_info().rss

    yield
    memory_usage = process.memory_info().rss
    fixture_memory_usage = memory_usage - base_memory_usage  # in bytes
    fixture_memory_usage = fixture_memory_usage / (1024 * 1024)  # in mo

    end = time.time()

    if fixture_memory_usage > 1:
        file = Path("memory_fixtures.csv")
        with file.open("a", encoding="utf-8") as writer:
            # Add overall test results
            writer.write(f"{request.fixturename},{end - start:.3f},{fixture_memory_usage:.3f}\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: Function, nextitem: Function):
    process = psutil.Process(os.getpid())
    file = Path("memory_tests.csv")
    activate_gc = False
    if activate_gc:
        gc.collect()
        gc.collect()
    base_memory_usage = process.memory_info().rss

    yield
    if activate_gc:
        gc.collect()
        gc.collect()
    memory_usage = process.memory_info().rss
    test_memory_usage = memory_usage - base_memory_usage  # in bytes
    test_memory_usage = test_memory_usage / (1024 * 1024)  # in mo
    full_memory_usage = memory_usage / (1024 * 1024)
    with file.open("a", encoding="utf-8") as writer:
        # Add overall test results
        writer.write(f"{item.name},{test_memory_usage:.3f},{full_memory_usage:.3f}\n")
