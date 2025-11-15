import asyncio
import logging
import aiohttp
import random
import string
from pathlib import Path
from time import perf_counter
from dataclasses import dataclass
from typing import List
import statistics


@dataclass
class TestResult:
    concurrency: int
    total_requests: int
    duration: float
    requests_per_second: float
    avg_response_time: float
    median_response_time: float


def generate_xml_content(size_kb: int = 15) -> str:
    target_size = size_kb * 1024
    current_size = 0
    elements = []

    while current_size < target_size:
        text_length = min(200, target_size - current_size)
        text = "".join(
            random.choices(string.ascii_letters + string.digits, k=text_length)
        )
        element = f'  <item id="{random.randint(1000, 9999)}">{text}</item>\n'
        elements.append(element)
        current_size += len(element.encode("utf-8"))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
    xml += "".join(elements)
    xml += "</root>"

    return xml


def prepare_test_files(num_files: int = 100, output_dir: str = "test_xmls"):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    for i in range(num_files):
        xml_content = generate_xml_content()
        file_path = output_path / f"test_{i:04d}.xml"
        file_path.write_text(xml_content)
    return output_path


async def send_request(
    session: aiohttp.ClientSession, url: str, xml_path: Path
) -> float:
    start = perf_counter()
    xml_content = xml_path.read_text()
    async with session.post(
        url,
        data=xml_content.encode("utf-8"),
        headers={"Content-Type": "application/xml"},
    ) as resp:
        await resp.read()
    return perf_counter() - start


async def run_test(
    url: str, xml_files: List[Path], concurrency: int, total_requests: int
) -> TestResult:
    print("test", concurrency)
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=300)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        response_times = []
        start_time = perf_counter()

        for i in range(total_requests):
            xml_file = xml_files[i % len(xml_files)]
            task = asyncio.create_task(send_request(session, url, xml_file))
            tasks.append(task)

        response_times = await asyncio.gather(*tasks)
        duration = perf_counter() - start_time

    return TestResult(
        concurrency=concurrency,
        total_requests=total_requests,
        duration=duration,
        requests_per_second=total_requests / duration,
        avg_response_time=statistics.mean(response_times),
        median_response_time=statistics.median(response_times),
    )


def benchmark(
    url: str = "http://localhost:8080/process",
    xml_dir: str = "test_xmls",
    total_requests: int = 200,
):
    xml_path = Path(xml_dir)
    xml_files = sorted(xml_path.glob("*.xml"))
    concurrency_levels = [20, 50, 100, 200, 500, 1000, 2000]
    results: List[TestResult] = []

    # print(
    #     f"{'Conc':>6} | {'Duration':>10} | {'Req/s':>10} | "
    #     f"{'Avg RT':>10} | {'Med RT':>10}"
    # )
    # print("-" * 65)

    for concurrency in concurrency_levels:
        result = asyncio.run(run_test(url, xml_files, concurrency, total_requests))
        results.append(result)

        # print(
        #     f"{result.concurrency:>6} | {result.duration:>9.2f}s | "
        #     f"{result.requests_per_second:>9.2f}/s | "
        #     f"{result.avg_response_time:>9.3f}s | "
        #     f"{result.median_response_time:>9.3f}s"
        # )

    # print("\n" + "=" * 65)
    # print("ANALYSIS")
    # print("=" * 65)

    max_rps = max(results, key=lambda r: r.requests_per_second)
    print(
        f"\nBest throughput: {max_rps.requests_per_second:.2f} req/s "
        f"at concurrency {max_rps.concurrency}"
    )

    for i in range(1, len(results)):
        prev_rps = results[i - 1].requests_per_second
        each = results[i]
        curr_rps = each.requests_per_second
        improvement = ((curr_rps - prev_rps) / prev_rps) * 100
        # print("perf", each.concurrency, each.requests_per_second, improvement)
        print(
            "perf {:4d} {:6.1f} {:6.1f}".format(
                each.concurrency, each.requests_per_second, improvement
            )
        )

        # if improvement < 5:
        #     print(
        #         f"\nDiminishing returns start at concurrency "
        #         f"{results[i].concurrency}"
        #     )
        #     print(
        #         f"Improvement from {results[i-1].concurrency} to "
        #         f"{results[i].concurrency}: {improvement:.1f}%"
        #     )
        #     break


def setup_logging():
    logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    setup_logging()
    prepare_test_files(num_files=5000)
    benchmark()
