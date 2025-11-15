# Purpose

It seemed that using Python's async and aiohttp library ran into its limits when adding more concurrency didn't anymore improve
performance in a specific case. That's what this quick test tests: when doesn't it anymore make sense to add more async concurrency
when uploading files. There's lots of caveats with the test. Client and server ran on the same laptop, there's just one server to
pretend being ten separate servers (each with default 200 Tomcat threads), and the test is very short so any issues with memory leaks
or such are bypassed. Claude 4.5 Sonnet wrote most of the Python code.

# How?

Start server:

    cd server &&
        ./mvnw package &&
        java -jar target/*.jar

Start client / test:

    cd client &&
        python3 -m venv venv &&
        . venv/bin/activate &&
        pip install -r requirements.txt &&
        python aio.py

# Results

On my laptop:

    $ python aio.py
    test 20
    test 50
    test 100
    test 200
    test 500
    test 1000
    test 2000

    Best throughput: 462.05 req/s at concurrency 2000
    perf   50  122.5  153.8
    perf  100  238.1   94.4
    perf  200  449.3   88.7
    perf  500  459.4    2.3
    perf 1000  455.1   -0.9
    perf 2000  462.0    1.5

Laptop specs:

1. OS: Ubuntu 24.04.3 LTS x86_64 
1. Host: ASUS Zenbook 14 UX3405MA_UX3405MA 1.0 
1. Kernel: 6.14.0-35-generic 
1. Shell: bash 5.2.21 
1. CPU: Intel Ultra 7 155H (22) @ 4.500GHz 
1. GPU: Intel Arc Graphics
1. Memory: 28574MiB / 31451MiB 
