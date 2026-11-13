"""Reference demo: an MCP style tool client with timeout, retry, and idempotency.

Plain Python, standard library only. No network calls. The server in this
file is a small fake, scripted to behave like a flaky tool server so the
client logic can be exercised end to end.
"""

import time


class TransientError(Exception):
    """A failure worth retrying, like a dropped connection or a busy server."""


class NotFoundError(Exception):
    """A failure not worth retrying, like calling a tool that does not exist."""


class FakeToolServer:
    """A scripted stand in for an MCP style tool server.

    Each tool has a scripted list of outcomes. An outcome of "slow" means the
    server never answered in time, so the client treats it as a timeout and
    the server counts no execution. An outcome of "flaky" means the server ran
    and failed with a transient error. An outcome of "ok" means the server ran
    and returned a result.
    """

    def __init__(self):
        self.scripts = {
            "get_weather": ["slow", "ok"],
            "summarize_text": ["flaky", "flaky", "ok"],
        }
        self.executions = {}

    def call(self, tool, arguments):
        if tool not in self.scripts:
            raise NotFoundError("tool not found: " + tool)
        script = self.scripts[tool]
        outcome = script.pop(0) if script else "ok"
        if outcome == "slow":
            return None
        self.executions[tool] = self.executions.get(tool, 0) + 1
        if outcome == "flaky":
            raise TransientError("transient failure from " + tool)
        if tool == "get_weather":
            return {"city": arguments["city"], "forecast": "clear, 21 degrees"}
        if tool == "summarize_text":
            return {"summary": "Three sentence summary of the sample text."}
        return {}


class ToolClient:
    """A small client with a deadline, retries with backoff, and idempotency keys."""

    def __init__(self, server, max_attempts=3, base_delay=0.05):
        self.server = server
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.cache = {}
        self.retries = 0
        self.cached_returns = 0

    def call_tool(self, tool, arguments, idempotency_key):
        if idempotency_key in self.cache:
            self.cached_returns += 1
            print("  cached result returned, server not called again")
            return self.cache[idempotency_key]
        last_error = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = self.server.call(tool, arguments)
            except TransientError as error:
                last_error = str(error)
                result = None
                timed_out = False
            except NotFoundError:
                raise
            else:
                timed_out = result is None
                if timed_out:
                    last_error = "timeout waiting for " + tool
            if result is not None:
                self.cache[idempotency_key] = result
                return result
            if attempt < self.max_attempts:
                self.retries += 1
                print("  attempt " + str(attempt) + " failed (" + last_error
                      + "), retrying after backoff")
                time.sleep(self.base_delay * (2 ** (attempt - 1)))
        raise RuntimeError("gave up on " + tool + " after "
                           + str(self.max_attempts) + " attempts: " + str(last_error))


def main():
    server = FakeToolServer()
    client = ToolClient(server)
    errors = 0

    print("Call 1: get_weather for New York, key weather-nyc-001")
    result = client.call_tool("get_weather", {"city": "New York"},
                              "weather-nyc-001")
    print("  result:", result)

    print("Call 2: summarize_text, key summary-001")
    result = client.call_tool("summarize_text",
                              {"text": "Sample text about a product launch."},
                              "summary-001")
    print("  result:", result)

    print("Call 3: get_weather again with the same key weather-nyc-001")
    result = client.call_tool("get_weather", {"city": "New York"},
                              "weather-nyc-001")
    print("  result:", result)

    print("Call 4: unknown_tool, key unknown-001")
    try:
        client.call_tool("unknown_tool", {}, "unknown-001")
    except NotFoundError as error:
        errors += 1
        print("  error, not retried:", error)

    print()
    print("Summary")
    print("  tool calls made: 4")
    print("  retries after a failure: " + str(client.retries))
    print("  cached results returned: " + str(client.cached_returns))
    print("  errors not retried: " + str(errors))
    print("  server executions by tool: " + str(server.executions))
    print("  total server executions: " + str(sum(server.executions.values())))


if __name__ == "__main__":
    main()
