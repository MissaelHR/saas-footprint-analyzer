class DatadogError(Exception):
    """Base Datadog client error."""


class DatadogAuthError(DatadogError):
    """Raised when authentication or authorization fails."""


class DatadogRateLimitError(DatadogError):
    """Raised when the Datadog API rate limits a request."""


class DatadogRequestError(DatadogError):
    """Raised when an unexpected Datadog API response is returned."""
