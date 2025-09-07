"""Monitoring and metrics collection for the Financial Wisdom Platform."""

import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from prometheus_client import (
    Counter, Histogram, Gauge, Info, 
    generate_latest, CONTENT_TYPE_LATEST
)
import structlog

logger = structlog.get_logger()


# Prometheus metrics
API_REQUESTS = Counter(
    'api_requests_total', 
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

API_REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

CONTENT_GENERATION_TOTAL = Counter(
    'content_generation_total',
    'Total content generations',
    ['status', 'cache_hit']
)

CONTENT_GENERATION_DURATION = Histogram(
    'content_generation_duration_seconds',
    'Content generation duration in seconds'
)

CONTENT_QUALITY_SCORE = Histogram(
    'content_quality_score',
    'Content quality scores',
    buckets=[0, 5, 6, 7, 8, 9, 10]
)

AI_SERVICE_CALLS = Counter(
    'ai_service_calls_total',
    'Total AI service calls',
    ['service', 'model', 'status']
)

AI_SERVICE_COST = Counter(
    'ai_service_cost_total',
    'Total AI service costs in USD',
    ['service', 'model']
)

AI_SERVICE_TOKENS = Counter(
    'ai_service_tokens_total',
    'Total AI service tokens used',
    ['service', 'model']
)

DATA_COLLECTION_ITEMS = Counter(
    'data_collection_items_total',
    'Total items collected',
    ['source_type', 'source_name']
)

CACHE_OPERATIONS = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_type', 'result']
)

WORKFLOW_EXECUTIONS = Counter(
    'workflow_executions_total',
    'Total workflow executions',
    ['workflow_type', 'status']
)

WORKFLOW_DURATION = Histogram(
    'workflow_duration_seconds',
    'Workflow execution duration in seconds',
    ['workflow_type']
)

# System metrics
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'System memory usage percentage')
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'System disk usage percentage')

# Application metrics
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')
KNOWLEDGE_BASE_SIZE = Gauge('knowledge_base_documents_total', 'Total documents in knowledge base')
CACHE_HIT_RATE = Gauge('cache_hit_rate_percent', 'Cache hit rate percentage')

# Cost tracking
DAILY_COST = Gauge('daily_cost_usd', 'Daily cost in USD', ['service'])
MONTHLY_COST = Gauge('monthly_cost_usd', 'Monthly cost in USD', ['service'])

# Application info
APP_INFO = Info('financial_wisdom_app', 'Application information')


@dataclass
class MetricsCollector:
    """Centralized metrics collection and reporting."""
    
    start_time: datetime = field(default_factory=datetime.now)
    daily_costs: Dict[str, float] = field(default_factory=dict)
    monthly_costs: Dict[str, float] = field(default_factory=dict)
    
    def record_api_request(
        self, 
        method: str, 
        endpoint: str, 
        status_code: int,
        duration: float
    ):
        """Record API request metrics."""
        API_REQUESTS.labels(
            method=method,
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        API_REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_content_generation(
        self,
        duration: float,
        quality_score: float,
        cache_hit: bool = False,
        success: bool = True
    ):
        """Record content generation metrics."""
        status = 'success' if success else 'failed'
        cache_status = 'hit' if cache_hit else 'miss'
        
        CONTENT_GENERATION_TOTAL.labels(
            status=status,
            cache_hit=cache_status
        ).inc()
        
        CONTENT_GENERATION_DURATION.observe(duration)
        
        if quality_score is not None:
            CONTENT_QUALITY_SCORE.observe(quality_score)
    
    def record_ai_service_call(
        self,
        service: str,
        model: str,
        tokens: int,
        cost: float,
        success: bool = True
    ):
        """Record AI service call metrics."""
        status = 'success' if success else 'failed'
        
        AI_SERVICE_CALLS.labels(
            service=service,
            model=model,
            status=status
        ).inc()
        
        if success:
            AI_SERVICE_COST.labels(
                service=service,
                model=model
            ).inc(cost)
            
            AI_SERVICE_TOKENS.labels(
                service=service,
                model=model
            ).inc(tokens)
            
            # Track daily/monthly costs
            self._update_cost_tracking(service, cost)
    
    def record_data_collection(
        self,
        source_type: str,
        source_name: str,
        items_collected: int
    ):
        """Record data collection metrics."""
        DATA_COLLECTION_ITEMS.labels(
            source_type=source_type,
            source_name=source_name
        ).inc(items_collected)
    
    def record_cache_operation(
        self,
        operation: str,
        cache_type: str,
        hit: bool = None
    ):
        """Record cache operation metrics."""
        if hit is not None:
            result = 'hit' if hit else 'miss'
        else:
            result = 'unknown'
            
        CACHE_OPERATIONS.labels(
            operation=operation,
            cache_type=cache_type,
            result=result
        ).inc()
    
    def record_workflow_execution(
        self,
        workflow_type: str,
        duration: float,
        success: bool = True
    ):
        """Record workflow execution metrics."""
        status = 'success' if success else 'failed'
        
        WORKFLOW_EXECUTIONS.labels(
            workflow_type=workflow_type,
            status=status
        ).inc()
        
        WORKFLOW_DURATION.labels(
            workflow_type=workflow_type
        ).observe(duration)
    
    def update_system_metrics(self):
        """Update system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            SYSTEM_DISK_USAGE.set(disk_percent)
            
        except Exception as e:
            logger.error("Failed to update system metrics", error=str(e))
    
    def update_application_metrics(
        self,
        db_connections: int = 0,
        kb_documents: int = 0,
        cache_hit_rate: float = 0.0
    ):
        """Update application-specific metrics."""
        ACTIVE_CONNECTIONS.set(db_connections)
        KNOWLEDGE_BASE_SIZE.set(kb_documents)
        CACHE_HIT_RATE.set(cache_hit_rate)
    
    def _update_cost_tracking(self, service: str, cost: float):
        """Update daily and monthly cost tracking."""
        today = datetime.now().date()
        current_month = datetime.now().strftime("%Y-%m")
        
        # Update daily costs
        daily_key = f"{service}_{today}"
        self.daily_costs[daily_key] = self.daily_costs.get(daily_key, 0) + cost
        DAILY_COST.labels(service=service).set(self.daily_costs[daily_key])
        
        # Update monthly costs
        monthly_key = f"{service}_{current_month}"
        self.monthly_costs[monthly_key] = self.monthly_costs.get(monthly_key, 0) + cost
        MONTHLY_COST.labels(service=service).set(self.monthly_costs[monthly_key])
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for monitoring."""
        today = datetime.now().date()
        current_month = datetime.now().strftime("%Y-%m")
        
        daily_total = sum(
            cost for key, cost in self.daily_costs.items()
            if key.endswith(str(today))
        )
        
        monthly_total = sum(
            cost for key, cost in self.monthly_costs.items()
            if key.endswith(current_month)
        )
        
        return {
            "daily_total": round(daily_total, 2),
            "monthly_total": round(monthly_total, 2),
            "services": {
                "anthropic": {
                    "daily": round(self.daily_costs.get(f"anthropic_{today}", 0), 2),
                    "monthly": round(self.monthly_costs.get(f"anthropic_{current_month}", 0), 2)
                },
                "openai": {
                    "daily": round(self.daily_costs.get(f"openai_{today}", 0), 2),
                    "monthly": round(self.monthly_costs.get(f"openai_{current_month}", 0), 2)
                }
            }
        }
    
    def set_app_info(self, version: str, environment: str):
        """Set application information."""
        APP_INFO.info({
            'version': version,
            'environment': environment,
            'start_time': self.start_time.isoformat()
        })


class PerformanceTimer:
    """Context manager for performance timing."""
    
    def __init__(self, operation: str, logger_instance = None):
        self.operation = operation
        self.logger = logger_instance or logger
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        self.logger.debug(
            f"Performance: {self.operation}",
            operation=self.operation,
            duration_seconds=round(self.duration, 3)
        )


class HealthChecker:
    """System health monitoring."""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
    
    async def check_database_health(self, db_session) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            # Simple query to test connectivity
            await db_session.execute("SELECT 1")
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_redis_health(self, redis_client) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            start_time = time.time()
            await redis_client.ping()
            duration = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time_ms": round(duration * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_elasticsearch_health(self, es_client) -> Dict[str, Any]:
        """Check Elasticsearch connectivity and cluster health."""
        try:
            start_time = time.time()
            health = await es_client.cluster.health()
            duration = time.time() - start_time
            
            return {
                "status": health.get("status", "unknown"),
                "cluster_name": health.get("cluster_name"),
                "number_of_nodes": health.get("number_of_nodes"),
                "response_time_ms": round(duration * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine overall health based on thresholds
            health_status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or (disk.used / disk.total) > 0.9:
                health_status = "warning"
            if cpu_percent > 95 or memory.percent > 95 or (disk.used / disk.total) > 0.95:
                health_status = "critical"
            
            return {
                "status": health_status,
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_comprehensive_health(
        self,
        db_session=None,
        redis_client=None,
        es_client=None
    ) -> Dict[str, Any]:
        """Get comprehensive system health check."""
        checks = {
            "timestamp": datetime.now().isoformat(),
            "system": self.check_system_resources()
        }
        
        if db_session:
            checks["database"] = await self.check_database_health(db_session)
        
        if redis_client:
            checks["redis"] = await self.check_redis_health(redis_client)
        
        if es_client:
            checks["elasticsearch"] = await self.check_elasticsearch_health(es_client)
        
        # Determine overall health
        statuses = [check.get("status") for check in checks.values() if isinstance(check, dict) and "status" in check]
        
        if "unhealthy" in statuses or "critical" in statuses:
            overall_status = "unhealthy"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        checks["overall_status"] = overall_status
        self.last_check_time = datetime.now()
        
        return checks


# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    return metrics_collector


def get_health_checker() -> HealthChecker:
    """Get global health checker instance."""
    return health_checker


def get_prometheus_metrics():
    """Get Prometheus metrics for /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST