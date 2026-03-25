from typing import Callable
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, multiprocess
from fastapi import Request, Response
from starlette.responses import PlainTextResponse
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
import time


# Prometheus metrics
REQUEST_COUNT = Counter("autodops_requests_total", "Total API requests", ["path", "method", "status"])
STEP_DURATION = Histogram("autodops_step_duration_seconds", "Duration of pipeline step execution", ["agent", "action"])


def init_tracing(service_name: str = "autodops"):
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def trace_span(name: str):
    tracer = trace.get_tracer(__name__)
    return tracer.start_as_current_span(name)


def init_metrics(app):
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next: Callable):
        start = time.time()
        resp = await call_next(request)
        elapsed = time.time() - start
        path = request.url.path
        REQUEST_COUNT.labels(path=path, method=request.method, status=str(resp.status_code)).inc()
        return resp

    @app.get("/metrics")
    def metrics():
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)


def init_observability(app, service_name: str = "autodops"):
    init_tracing(service_name)
    init_metrics(app)
