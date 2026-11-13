# Pattern notes: MCP tool client with timeout, retry, and idempotency

## The problem

A client that calls tools on a remote server cannot assume the call will work. The network can drop the request, the server can be slow, the server can fail for a passing reason, or the client itself can be unsure whether its request arrived. Each of those failures wants a different answer, and a client that gives the wrong answer makes things worse: retrying a call that already ran can charge a card twice, and waiting forever on a call that will never answer can stall the whole workflow. The pattern in this demo is to sort failures into kinds first, then give each kind its own handling.

## Timeouts: stop waiting, then decide

The demo treats a call that returns no answer inside the deadline as a timeout. In this fake server the slow outcome returns nothing at all, which stands in for a server that never answered. The client does not wait longer. It records the timeout and moves to the retry decision. The point of a deadline is not to make the call faster. It is to bound the wait, so one slow tool cannot hold the workflow hostage. On a real client the deadline would come from the transport layer, and it would usually be different per tool, since a weather lookup and a long document summary do not deserve the same wait.

## Retry with backoff: only for failures that might pass

The demo retries two kinds of failure: a timeout, and a transient error from the server. Both might pass on a second try, which is the only good reason to retry. The wait between attempts grows with each attempt, which is backoff. Backoff matters because a server that is busy gets busier when every client retries at once, so spreading the retries out is part of being a good citizen. The demo uses a small base delay and doubles it per attempt, which keeps the demo fast while showing the shape. The retry budget is capped at three attempts in total, so a tool that keeps failing eventually reports an error instead of looping forever.

## Idempotency keys: never run the same request twice

The demo gives every call an idempotency key, which is a client chosen label for one logical request. The client stores the result under that key, and a repeat call with the same key returns the stored result without touching the server. The demo proves this with numbers: get_weather is called twice with the key weather-nyc-001, but the server runs it exactly once. This is the guard that makes retries safe. A timeout is ambiguous, since the request may have arrived and run even though the answer never came back. Retrying that request without a key can run the work twice. With a key, the server can recognize the repeat and return the first result instead. In this demo the cache lives in the client, which is enough to show the idea. On a real system the key would travel with the request and the server would hold the result, so a repeat after a client restart still returns the first result.

## What not to retry

The demo refuses to retry a call to a tool that does not exist. A missing tool is a permanent error: trying again cannot help, and the extra calls only add noise. The same rule applies to any permanent failure, like a bad argument or a request the server refuses on policy. The useful habit is to separate permanent errors from passing ones at the point where the error is raised, so the retry logic never has to guess. The demo does this with two exception types, one for transient failures and one for a missing tool, and the client only retries the transient kind.

## Limits

The server is a scripted fake, so no latency, reliability, or retry success rate is claimed, because none was measured. The backoff delays are tiny and chosen to keep the demo fast. The cache lives only in memory for one run, and it has no size limit and no expiry, so it would grow without bound on a long running client. The demo covers one client and one server in the same process, so it says nothing about real network behavior, connection pooling, or concurrent calls. On a real client the deadline, the retry budget, and the backoff would be tuned per tool, the keys would be durable, and the cache would be bounded.
