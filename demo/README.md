# Demo: MCP tool client with timeout, retry, and idempotency

This demo is a small reference implementation of the client pattern described in the pattern notes, in plain Python with no external packages. It uses a small scripted fake server in the same file. It holds no real data and it makes no network calls. It is an illustrative reference demo, not a production client.

## How to run it

1. Open a terminal in this folder.
2. Run the command: python3 mcp_client_demo.py

## What it does

1. It calls get_weather for New York with the key weather-nyc-001. The fake server stays silent on the first attempt, so the client treats it as a timeout, retries once, and the second attempt returns clear, 21 degrees.
2. It calls summarize_text with the key summary-001. The fake server fails with a transient error on the first two attempts, so the client retries twice with backoff, and the third attempt returns the sample summary.
3. It calls get_weather again with the same key weather-nyc-001. The client returns the cached result and the server is not called again.
4. It calls unknown_tool with the key unknown-001. The fake server reports that the tool does not exist, and the client raises the error at once with no retry.
5. It prints a summary of the run: tool calls made, retries after a failure, cached results returned, errors not retried, and server executions by tool.

## Expected output

1. Call 1: get_weather for New York. Attempt 1 fails with a timeout, then the retry returns clear, 21 degrees.
2. Call 2: summarize_text. Attempts 1 and 2 fail with a transient error, then the third attempt returns the sample summary.
3. Call 3: get_weather again with the same key. A cached result is returned and the server is not called again.
4. Call 4: unknown_tool. An error is raised at once, not retried, reporting that the tool does not exist.
5. Summary: 4 tool calls made, 3 retries after a failure, 1 cached result returned, 1 error not retried, and 4 total server executions, 1 for get_weather and 3 for summarize_text.

## Limits

The server is a scripted fake, so no latency, reliability, or retry success rate is claimed, because none was measured. The weather, the forecast, the sample text, and the summary are invented sample values written only to exercise the client. The backoff delays are tiny and chosen to keep the demo fast. The cache lives only in memory for one run, with no size limit and no expiry. The demo covers one client and one server in the same process, so it says nothing about real network behavior. A cached result here is a demonstration of the idea, not a guarantee.
