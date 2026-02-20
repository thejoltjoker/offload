"""
Benchmark all copy functions for comparison.
Run with: pytest tests/benchmark_copy.py --benchmark-only
Or with options: pytest tests/benchmark_copy.py --benchmark-only --benchmark-sort=mean
"""

import pytest
from pathlib import Path

from offload import utils

# Size of temp file used for benchmarking (MiB)
BENCHMARK_FILE_SIZE_MB = 50


@pytest.fixture(scope="module")
def benchmark_source_file(tmp_path_factory):
    """Create a single source file of fixed size for all copy benchmarks."""
    tmp = tmp_path_factory.mktemp("bench_copy")
    source = tmp / "source.bin"
    size_bytes = BENCHMARK_FILE_SIZE_MB * 1024 * 1024
    source.write_bytes(bytes(size_bytes))
    return source


@pytest.fixture
def benchmark_dest_path(benchmark_source_file):
    """Fresh destination path for each benchmark (same dir as source)."""
    return benchmark_source_file.parent / "dest.bin"


def _prepare_dest(dest: Path):
    dest.unlink(missing_ok=True)


def test_benchmark_copy_file(benchmark, benchmark_source_file, benchmark_dest_path):
    """copy_file (shutil.copy2) – copy only, preserves metadata."""

    def run():
        _prepare_dest(benchmark_dest_path)
        utils.copy_file(benchmark_source_file, benchmark_dest_path)

    benchmark(run)


def test_benchmark_pathlib_copy(benchmark, benchmark_source_file, benchmark_dest_path):
    """pathlib_copy – chunked copy, no metadata."""

    def run():
        _prepare_dest(benchmark_dest_path)
        utils.pathlib_copy(benchmark_source_file, benchmark_dest_path)

    benchmark(run)


def test_benchmark_pathlib_copy_with_checksum(
    benchmark, benchmark_source_file, benchmark_dest_path
):
    """pathlib_copy_with_checksum – copy + in-stream xxhash (no extra read)."""

    def run():
        _prepare_dest(benchmark_dest_path)
        utils.pathlib_copy_with_checksum(benchmark_source_file, benchmark_dest_path)

    benchmark(run)


def test_benchmark_pathlib_copy_then_verify(benchmark, benchmark_source_file, benchmark_dest_path):
    """pathlib_copy + hash source + hash dest – old copy-then-verify path."""

    def run():
        _prepare_dest(benchmark_dest_path)
        utils.pathlib_copy(benchmark_source_file, benchmark_dest_path)
        utils.checksum_xxhash(benchmark_source_file)
        utils.checksum_xxhash(benchmark_dest_path)

    benchmark(run)
