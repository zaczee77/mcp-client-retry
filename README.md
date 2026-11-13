# MCP tool client: timeout, retry, and idempotency

A small reference demo for a client that calls tools on an MCP style server, built by Nirmeet Rao. It shows the three habits that keep tool calls safe when the server is slow, flaky, or called twice by accident: wait only as long as a deadline allows, retry a failure that might pass, and never run the same request twice.

The demo uses a small scripted fake server in the same file, so it runs with plain Python and no network calls. The fake server is slow on the first weather call, fails twice on the first summary call, and has no tool called unknown_tool. The client answers each of those cases in turn: it retries the timeout, retries the transient failures with backoff, returns the cached result when the weather call is repeated with the same key, and refuses to retry the unknown tool. The weather, the forecast, the sample text, and the summary are invented sample values written only to exercise the client. They are not real data, and no latency, reliability, or performance number is claimed anywhere here.

## The idea in one paragraph

A tool call over a network can fail in three different ways, and each way wants a different answer. A call that never answers wants a deadline, so the client stops waiting and tries again. A call that fails for a passing reason, like a busy server, wants a retry after a short wait, so the client tries again with backoff. A call that already ran wants an idempotency key, so a repeat returns the first result instead of running the work twice. A call that names a tool that does not exist wants no retry at all, because trying again cannot help. This demo gives each case its own code path, so the client never confuses one failure for another.

## The four calls

1. get_weather for New York, key weather-nyc-001. The first attempt times out, the client retries once, and the second attempt returns clear, 21 degrees.
2. summarize_text, key summary-001. The first two attempts fail with a transient error, the client retries twice with backoff, and the third attempt returns the sample summary.
3. get_weather again with the same key weather-nyc-001. The client returns the cached result and the server is not called again, so the server runs get_weather exactly once in total.
4. unknown_tool, key unknown-001. The server reports that the tool does not exist, and the client raises the error at once with no retry.

## The demo in this repository

The demo folder contains a small reference demo in plain Python with no external packages. It runs the four calls above and prints a per call trace plus a summary: 4 tool calls made, 3 retries after a failure, 1 cached result returned, 1 error not retried, and 4 total server executions, 1 for get_weather and 3 for summarize_text. The docs folder describes the pattern in general terms and its limits.

## Where this pattern already runs

The same shape appears in the products Nirmeet has built. ephe, his MCP platform in this same GitHub account, is the server side of this story: it exposes tools over the MCP protocol, and a client like this one is what calls them. PharmFlows, the LLM workflows he shipped at Concordia Pharma, reported serving time errors down 86 percent and cycle time down 30 percent on his resume, and those gains came from structure, validation, and review around the model rather than from more model calls. Paxei, his prior authorization preparation product, designs LLM document parsing and clinical drafts around payer criteria guardrails and human review. In each case the system earns trust by checking its own work in the open, with a human deciding what a flag means.

## What this is not

This repository is not a production MCP client, and it is not a claim about any real server. It contains no real tool server, no network calls, and no measured latency or reliability number. The fake server is scripted to fail on purpose, the backoff delays are tiny, and the cache lives only in memory for one run. On a real client the deadline would come from the transport, the retry budget would be tuned to the tool, and the idempotency keys would be stored somewhere durable so a repeat after a restart still returns the first result. A cached result here is a demonstration of the idea, not a guarantee.

## Links

1. Portfolio: https://nirmeetrao.com
2. GitHub: https://github.com/Zaczee77
3. LinkedIn: https://www.linkedin.com/in/nirmeet-rao
