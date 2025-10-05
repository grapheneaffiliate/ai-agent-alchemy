"""Metrics collection and monitoring for the MCP AI Agent."""

from __future__ import annotations

import asyncio
import time
import threading
from collections import defaultdict, deque
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Deque
from datetime import datetime, timedelta

from .logging_utils import get_logger, LogComponent

logger = get_logger("metrics", LogComponent.AGENT)


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"           # Monotonically increasing value
    GAUGE = "gauge"              # Current value that can go up or down
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Duration measurements


class MetricUnit(str, Enum):
    """Units for metric values."""
    COUNT = "count"
    BYTES = "bytes"
    SECONDS = "seconds"
    MILLISECONDS = "milliseconds"
    PERCENTAGE = "percentage"
    RATIO = "ratio"


@dataclass
class MetricValue:
    """A single metric measurement."""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HistogramBucket:
    """A bucket for histogram measurements."""
    le: float  # Less than or equal
    count: int = 0


class Histogram:
    """Thread-safe histogram for measuring distributions."""

    def __init__(self, buckets: Optional[List[float]] = None):
        self.buckets = buckets or [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')]
        self._buckets: List[HistogramBucket] = [
            HistogramBucket(le=b) for b in self.buckets
        ]
        self._total_count = 0
        self._sum = 0.0
        self._lock = threading.Lock()

    def observe(self, value: float) -> None:
        """Record a value in the histogram."""
        with self._lock:
            self._total_count += 1
            self._sum += value

            for bucket in self._buckets:
                if value <= bucket.le:
                    bucket.count += 1

    def get_count(self) -> int:
        """Get total count of observations."""
        with self._lock:
            return self._total_count

    def get_sum(self) -> float:
        """Get sum of all observations."""
        with self._lock:
            return self._sum

    def get_buckets(self) -> List[HistogramBucket]:
        """Get current bucket counts."""
        with self._lock:
            return [HistogramBucket(le=b.le, count=b.count) for b in self._buckets]


class MetricsCollector:
    """Thread-safe metrics collection system."""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._timers: Dict[str, List[MetricValue]] = defaultdict(list)
        self._lock = threading.RLock()

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram."""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = Histogram()
            self._histograms[key].observe(value)

    def record_timer(
        self,
        name: str,
        duration: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a timer measurement."""
        with self._lock:
            key = self._make_key(name, labels)
            value = MetricValue(
                value=duration,
                timestamp=time.time(),
                labels=labels or {},
                metadata=metadata or {}
            )

            self._timers[key].append(value)

            # Keep only recent measurements
            if len(self._timers[key]) > self.max_history:
                self._timers[key] = self._timers[key][-self.max_history:]

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current counter value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key, 0.0)

    def get_histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[Histogram]:
        """Get histogram for the given name and labels."""
        with self._lock:
            key = self._make_key(name, labels)
            return self._histograms.get(key)

    def get_timer_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
        duration: Optional[timedelta] = None
    ) -> Dict[str, float]:
        """Get timer statistics for recent measurements."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._timers.get(key, [])

            if duration:
                cutoff = time.time() - duration.total_seconds()
                values = [v for v in values if v.timestamp >= cutoff]

            if not values:
                return {}

            durations = [v.value for v in values]

            return {
                "count": len(durations),
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "p50": self._percentile(durations, 0.5),
                "p95": self._percentile(durations, 0.95),
                "p99": self._percentile(durations, 0.99),
            }

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name

        # Sort labels for consistent key generation
        sorted_labels = sorted(labels.items())
        label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
        return f"{name}{{{label_str}}}"

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile from list of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * percentile
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_values) - 1)

        if lower_index == upper_index:
            return sorted_values[lower_index]

        # Linear interpolation between values
        weight = index - lower_index
        return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        with self._lock:
            # Export counters
            for key, value in self._counters.items():
                metric_name = key.split('{')[0]
                lines.append(f"# HELP {metric_name} Counter metric")
                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{metric_name} {value}")

            # Export gauges
            for key, value in self._gauges.items():
                metric_name = key.split('{')[0]
                lines.append(f"# HELP {metric_name} Gauge metric")
                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name} {value}")

            # Export histograms
            for key, histogram in self._histograms.items():
                metric_name = key.split('{')[0]
                buckets = histogram.get_buckets()

                lines.append(f"# HELP {metric_name} Histogram metric")
                lines.append(f"# TYPE {metric_name} histogram")

                for bucket in buckets:
                    bucket_key = f"{metric_name}_bucket{{le=\"{bucket.le}\"}}"
                    lines.append(f"{bucket_key} {bucket.count}")

                lines.append(f"{metric_name}_count {histogram.get_count()}")
                lines.append(f"{metric_name}_sum {histogram.get_sum()}")

        return "\n".join(lines) + "\n"


# Global metrics collector instance
_metrics_collector = MetricsCollector()


class MetricsTracker:
    """High-level interface for tracking metrics."""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or _metrics_collector

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        """Increment a counter."""
        self.collector.increment_counter(name, value, labels)

    def gauge(self, name: str, value: float, **labels: str) -> None:
        """Set a gauge value."""
        self.collector.set_gauge(name, value, labels)

    def histogram(self, name: str, value: float, **labels: str) -> None:
        """Record a histogram value."""
        self.collector.observe_histogram(name, value, labels)

    def timer(
        self,
        name: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None,
        **labels: str
    ) -> None:
        """Record a timer measurement."""
        self.collector.record_timer(name, duration, labels, metadata)

    def get_timer_stats(
        self,
        name: str,
        duration: Optional[timedelta] = None,
        **labels: str
    ) -> Dict[str, float]:
        """Get timer statistics."""
        return self.collector.get_timer_stats(name, labels, duration)


# Global metrics tracker instance
metrics = MetricsTracker()


@contextmanager
def timer_context(name: str, **labels: str):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        metrics.timer(name, duration, **labels)


@asynccontextmanager
async def async_timer_context(name: str, **labels: str):
    """Async context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        metrics.timer(name, duration, **labels)


# Pre-defined metrics for common agent operations
def track_tool_execution(tool_name: str, success: bool, duration_ms: float, **labels: str) -> None:
    """Track tool execution metrics."""
    # Counter for total executions
    metrics.increment("agent_tool_executions_total", labels={"tool": tool_name, **labels})

    # Counter for success/failure
    if success:
        metrics.increment("agent_tool_success_total", labels={"tool": tool_name, **labels})
    else:
        metrics.increment("agent_tool_failures_total", labels={"tool": tool_name, **labels})

    # Histogram for duration
    metrics.histogram("agent_tool_duration_ms", duration_ms, tool=tool_name, **labels)


def track_plugin_operation(
    plugin_name: str,
    operation: str,
    success: bool,
    duration_ms: float,
    **labels: str
) -> None:
    """Track plugin operation metrics."""
    # Counter for total operations
    metrics.increment(
        "agent_plugin_operations_total",
        labels={"plugin": plugin_name, "operation": operation, **labels}
    )

    # Counter for success/failure
    if success:
        metrics.increment(
            "agent_plugin_success_total",
            labels={"plugin": plugin_name, "operation": operation, **labels}
        )
    else:
        metrics.increment(
            "agent_plugin_failures_total",
            labels={"plugin": plugin_name, "operation": operation, **labels}
        )

    # Histogram for duration
    metrics.histogram(
        "agent_plugin_duration_ms",
        duration_ms,
        plugin=plugin_name,
        operation=operation,
        **labels
    )


def track_memory_usage(operation: str, memory_mb: float, **labels: str) -> None:
    """Track memory usage metrics."""
    metrics.gauge("agent_memory_usage_mb", memory_mb, operation=operation, **labels)


def track_api_requests(endpoint: str, method: str, status_code: int, duration_ms: float) -> None:
    """Track API request metrics."""
    # Counter for total requests
    metrics.increment(
        "agent_api_requests_total",
        labels={"endpoint": endpoint, "method": method, "status_code": str(status_code)}
    )

    # Histogram for duration
    metrics.histogram(
        "agent_api_request_duration_ms",
        duration_ms,
        endpoint=endpoint,
        method=method,
        status_code=str(status_code)
    )


# Dashboard data structures
@dataclass
class DashboardMetric:
    """A metric for dashboard display."""
    name: str
    value: float
    unit: str
    labels: Dict[str, str]
    timestamp: float
    trend: Optional[float] = None  # Percentage change from previous period


@dataclass
class DashboardData:
    """Complete dashboard data."""
    timestamp: float
    metrics: List[DashboardMetric]
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class MetricsDashboard:
    """Dashboard for visualizing metrics."""

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or _metrics_collector
        self._history: Deque[DashboardData] = deque(maxlen=100)

    def generate_dashboard(self, time_window: Optional[timedelta] = None) -> DashboardData:
        """Generate current dashboard data."""
        timestamp = time.time()
        metrics_list = []

        # Get timer statistics for key operations
        operations = [
            ("agent_tool_duration_ms", "Tool Execution"),
            ("agent_plugin_duration_ms", "Plugin Operations"),
            ("agent_api_request_duration_ms", "API Requests"),
        ]

        for metric_name, display_name in operations:
            stats = self.collector.get_timer_stats(metric_name, time_window)

            if stats:
                metrics_list.append(DashboardMetric(
                    name=display_name,
                    value=stats.get("avg", 0),
                    unit="ms",
                    labels={"metric_type": "latency"},
                    timestamp=timestamp,
                ))

        # Get gauge values
        gauge_metrics = [
            ("agent_memory_usage_mb", "Memory Usage", "MB"),
        ]

        for metric_name, display_name, unit in gauge_metrics:
            value = self.collector.get_gauge(metric_name)
            if value > 0:
                metrics_list.append(DashboardMetric(
                    name=display_name,
                    value=value,
                    unit=unit,
                    labels={"metric_type": "resource"},
                    timestamp=timestamp,
                ))

        # Get counter values (rates)
        counter_metrics = [
            ("agent_tool_executions_total", "Tool Executions", "count"),
            ("agent_api_requests_total", "API Requests", "count"),
        ]

        for metric_name, display_name, unit in counter_metrics:
            value = self.collector.get_counter(metric_name)
            if value > 0:
                metrics_list.append(DashboardMetric(
                    name=display_name,
                    value=value,
                    unit=unit,
                    labels={"metric_type": "throughput"},
                    timestamp=timestamp,
                ))

        dashboard = DashboardData(
            timestamp=timestamp,
            metrics=metrics_list,
            summary=self._generate_summary(metrics_list)
        )

        self._history.append(dashboard)
        return dashboard

    def _generate_summary(self, metrics: List[DashboardMetric]) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not metrics:
            return {}

        # Calculate averages by metric type
        by_type = defaultdict(list)
        for metric in metrics:
            by_type[metric.labels.get("metric_type", "unknown")].append(metric.value)

        summary = {}
        for metric_type, values in by_type.items():
            if values:
                summary[f"{metric_type}_avg"] = sum(values) / len(values)

        return summary

    def get_historical_data(self, count: int = 10) -> List[DashboardData]:
        """Get recent dashboard data points."""
        return list(self._history)[-count:]


# Global dashboard instance
dashboard = MetricsDashboard()


# Integration with logging system
def log_metric_event(
    metric_name: str,
    value: float,
    level: str = "INFO",
    **labels: str
) -> None:
    """Log a metric event with structured logging."""
    logger.info(
        f"Metric recorded: {metric_name}={value}",
        operation="metric_collection",
        extra_fields={
            "metric_name": metric_name,
            "metric_value": value,
            **labels
        }
    )


# Performance monitoring decorators
def track_performance(metric_name: str, **labels: str):
    """Decorator to track function performance."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with timer_context(metric_name, **labels):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with timer_context(metric_name, **labels):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def track_plugin_performance(plugin_name: str, operation: str):
    """Decorator specifically for plugin operations."""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    track_plugin_operation(plugin_name, operation, True, duration)
                    return result
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    track_plugin_operation(plugin_name, operation, False, duration)
                    raise e
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    track_plugin_operation(plugin_name, operation, True, duration)
                    return result
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    track_plugin_operation(plugin_name, operation, False, duration)
                    raise e
            return sync_wrapper
    return decorator
