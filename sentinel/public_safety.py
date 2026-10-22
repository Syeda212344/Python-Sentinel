"""Basic public demo write throttling to reduce accidental shared-demo abuse.

This is a presentation/demo safeguard, not a comprehensive abuse prevention
system. For a large public audience add real user accounts and centralized rate
limiting, and isolate visitors' records.
"""
from collections import deque
from threading import Lock
from time import monotonic
from django.http import JsonResponse

class PublicDemoRateLimitMiddleware:
    # Single Gunicorn worker; all HTTP POST endpoints modify one shared demo.
    _lock = Lock()
    _requests = deque()
    _per_client = {}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and request.path.startswith("/api/"):
            now = monotonic()
            # REMOTE_ADDR is only a best-effort demo grouping mechanism.
            client = request.META.get("REMOTE_ADDR", "unknown")
            with self._lock:
                while self._requests and self._requests[0] < now - 60:
                    self._requests.popleft()
                current = self._per_client.get(client)
                if current is None:
                    current = deque()
                    self._per_client[client] = current
                while current and current[0] < now - 60:
                    current.popleft()
                if len(self._requests) >= 120 or len(current) >= 60:
                    response = JsonResponse(
                        {"error":"The shared demo has reached its temporary activity limit. Please retry in one minute."},
                        status=429
                    )
                    response["Retry-After"] = "60"
                    return response
                self._requests.append(now)
                current.append(now)
                if len(self._per_client) > 300:
                    self._per_client = {k:v for k,v in self._per_client.items() if v}
        return self.get_response(request)
