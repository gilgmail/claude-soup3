"""Structured logging configuration for the Financial Wisdom Platform."""

import sys
import logging
from typing import Dict, Any
from datetime import datetime

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging():
    """Configure structured logging with JSON format."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level, logging.INFO)
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="ISO"),
            # Add caller information
            structlog.processors.add_caller_info,
            # Stack info processor
            structlog.processors.StackInfoRenderer(),
            # Exception processor
            structlog.dev.set_exc_info,
            # JSON renderer
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class FinancialWisdomLogger:
    """Custom logger for Financial Wisdom Platform with specialized methods."""
    
    def __init__(self, name: str = "financial_wisdom"):
        self.logger = structlog.get_logger(name)
    
    def log_api_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        **kwargs
    ):
        """Log API request with standardized fields."""
        self.logger.info(
            "API request completed",
            event_type="api_request",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
            **kwargs
        )
    
    def log_content_generation(
        self,
        article_id: str,
        topic_keywords: list,
        quality_score: float,
        cost_estimate: float,
        duration_seconds: float,
        cache_hit: bool = False,
        **kwargs
    ):
        """Log content generation events."""
        self.logger.info(
            "Content generation completed",
            event_type="content_generation",
            article_id=article_id,
            topic_keywords=topic_keywords,
            quality_score=quality_score,
            cost_estimate=cost_estimate,
            duration_seconds=round(duration_seconds, 2),
            cache_hit=cache_hit,
            **kwargs
        )
    
    def log_data_collection(
        self,
        source_name: str,
        source_type: str,
        items_collected: int,
        success_rate: float,
        duration_seconds: float,
        **kwargs
    ):
        """Log data collection events."""
        self.logger.info(
            "Data collection completed",
            event_type="data_collection",
            source_name=source_name,
            source_type=source_type,
            items_collected=items_collected,
            success_rate=round(success_rate, 3),
            duration_seconds=round(duration_seconds, 2),
            **kwargs
        )
    
    def log_cache_operation(
        self,
        operation: str,  # get, set, delete, clear
        cache_type: str,
        key: str,
        hit: bool = None,
        ttl: int = None,
        **kwargs
    ):
        """Log cache operations."""
        self.logger.debug(
            f"Cache {operation}",
            event_type="cache_operation",
            operation=operation,
            cache_type=cache_type,
            key=key[:50] + "..." if len(key) > 50 else key,  # Truncate long keys
            hit=hit,
            ttl=ttl,
            **kwargs
        )
    
    def log_ai_service_call(
        self,
        service: str,  # anthropic, openai
        model: str,
        tokens_used: int,
        cost: float,
        duration_seconds: float,
        success: bool = True,
        **kwargs
    ):
        """Log AI service API calls."""
        level = "info" if success else "error"
        getattr(self.logger, level)(
            "AI service call completed",
            event_type="ai_service_call",
            service=service,
            model=model,
            tokens_used=tokens_used,
            cost=round(cost, 4),
            duration_seconds=round(duration_seconds, 2),
            success=success,
            **kwargs
        )
    
    def log_workflow_execution(
        self,
        workflow_type: str,
        status: str,  # started, completed, failed
        duration_seconds: float = None,
        metrics: Dict[str, Any] = None,
        **kwargs
    ):
        """Log workflow execution."""
        level = "info" if status != "failed" else "error"
        getattr(self.logger, level)(
            f"Workflow {status}",
            event_type="workflow_execution",
            workflow_type=workflow_type,
            status=status,
            duration_seconds=round(duration_seconds, 2) if duration_seconds else None,
            metrics=metrics or {},
            **kwargs
        )
    
    def log_quality_assessment(
        self,
        article_id: str,
        overall_score: float,
        readability: float,
        engagement: float,
        educational_value: float,
        actionability: float,
        originality: float,
        **kwargs
    ):
        """Log content quality assessments."""
        self.logger.info(
            "Quality assessment completed",
            event_type="quality_assessment",
            article_id=article_id,
            scores={
                "overall": round(overall_score, 2),
                "readability": round(readability, 2),
                "engagement": round(engagement, 2),
                "educational_value": round(educational_value, 2),
                "actionability": round(actionability, 2),
                "originality": round(originality, 2)
            },
            **kwargs
        )
    
    def log_cost_tracking(
        self,
        service: str,
        operation: str,
        cost: float,
        daily_total: float,
        monthly_total: float,
        **kwargs
    ):
        """Log cost tracking information."""
        self.logger.info(
            "Cost tracking update",
            event_type="cost_tracking",
            service=service,
            operation=operation,
            cost=round(cost, 4),
            daily_total=round(daily_total, 2),
            monthly_total=round(monthly_total, 2),
            **kwargs
        )
    
    def log_error_with_context(
        self,
        error: Exception,
        operation: str,
        context: Dict[str, Any] = None,
        **kwargs
    ):
        """Log errors with rich context."""
        self.logger.error(
            f"Error in {operation}",
            event_type="error",
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            context=context or {},
            **kwargs,
            exc_info=True
        )
    
    def log_performance_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        tags: Dict[str, str] = None,
        **kwargs
    ):
        """Log performance metrics."""
        self.logger.info(
            f"Performance metric: {metric_name}",
            event_type="performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {},
            **kwargs
        )


# Global logger instance
app_logger = FinancialWisdomLogger()


def get_logger(name: str = None) -> FinancialWisdomLogger:
    """Get logger instance."""
    if name:
        return FinancialWisdomLogger(name)
    return app_logger