import logging
import time
import json
from typing import Optional
from datetime import datetime
from functools import wraps

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("voice_agent")

class Metrics:
    """In-memory metrics (replace with Prometheus/CloudWatch in prod)"""
    
    def __init__(self):
        self.counters = {}
        self.histograms = {}
        self.gauges = {}
    
    def increment(self, metric: str, value: int = 1, tags: dict = None):
        key = f"{metric}:{json.dumps(tags or {}, sort_keys=True)}"
        self.counters[key] = self.counters.get(key, 0) + value
        logger.info(f"METRIC counter {metric}={self.counters[key]} tags={tags}")
    
    def record(self, metric: str, value: float, tags: dict = None):
        key = f"{metric}:{json.dumps(tags or {}, sort_keys=True)}"
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        logger.info(f"METRIC histogram {metric}={value} tags={tags}")
    
    def set_gauge(self, metric: str, value: float, tags: dict = None):
        key = f"{metric}:{json.dumps(tags or {}, sort_keys=True)}"
        self.gauges[key] = value
        logger.info(f"METRIC gauge {metric}={value} tags={tags}")

metrics = Metrics()

class Monitor:
    """Monitoring and alerting"""
    
    @staticmethod
    def log_interaction(session_id: str, turn: int, transcript: str, response: str, 
                       intent: str, confidence: float, language: str, latency_ms: float):
        """Structured logging for every interaction"""
        log_data = {
            "event": "interaction",
            "session_id": session_id,
            "turn": turn,
            "transcript": transcript[:100],
            "response": response[:100],
            "intent": intent,
            "confidence": confidence,
            "language": language,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(json.dumps(log_data))
        
        # Metrics
        metrics.increment("interactions.total", tags={"language": language, "intent": intent})
        metrics.record("interactions.latency_ms", latency_ms, tags={"language": language})
        metrics.record("interactions.confidence", confidence, tags={"intent": intent})
    
    @staticmethod
    def log_extraction(session_id: str, field: str, value: str, confidence: float, validated: bool):
        """Log data extraction attempts"""
        log_data = {
            "event": "extraction",
            "session_id": session_id,
            "field": field,
            "value": value[:50] if value else None,
            "confidence": confidence,
            "validated": validated,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(json.dumps(log_data))
        
        metrics.increment("extractions.total", tags={"field": field, "validated": str(validated)})
        metrics.record("extractions.confidence", confidence, tags={"field": field})
    
    @staticmethod
    def log_llm_call(model: str, prompt_tokens: int, completion_tokens: int, latency_ms: float, cost_usd: float):
        """Track LLM usage and costs"""
        log_data = {
            "event": "llm_call",
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(json.dumps(log_data))
        
        metrics.increment("llm.calls", tags={"model": model})
        metrics.increment("llm.tokens", value=prompt_tokens + completion_tokens, tags={"model": model})
        metrics.record("llm.cost_usd", cost_usd, tags={"model": model})
        metrics.record("llm.latency_ms", latency_ms, tags={"model": model})
    
    @staticmethod
    def log_lead_completion(session_id: str, turns: int, language: str):
        """Track successful lead captures"""
        log_data = {
            "event": "lead_completed",
            "session_id": session_id,
            "turns": turns,
            "language": language,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(json.dumps(log_data))
        
        metrics.increment("leads.completed", tags={"language": language})
        metrics.record("leads.turns_to_complete", turns, tags={"language": language})
    
    @staticmethod
    def log_rag_retrieval(session_id: str, query: str, context_length: int):
        """Track RAG retrieval performance"""
        log_data = {
            "event": "rag_retrieval",
            "session_id": session_id,
            "query": query[:100],
            "context_length": context_length,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(json.dumps(log_data))
        
        metrics.increment("rag.retrievals")
        metrics.record("rag.context_length", context_length)
    
    @staticmethod
    def alert(severity: str, message: str, context: dict = None):
        """Alert on critical issues"""
        alert_data = {
            "event": "alert",
            "severity": severity,
            "message": message,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.error(json.dumps(alert_data))
        
        metrics.increment("alerts.total", tags={"severity": severity})
        
        # In production: send to PagerDuty/Slack/SNS
        if severity == "CRITICAL":
            # send_to_pagerduty(alert_data)
            pass

def trace_function(func):
    """Decorator for tracing function execution"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start) * 1000
            metrics.record(f"function.latency_ms", latency_ms, tags={"function": func_name})
            return result
        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            logger.error(f"Function {func_name} failed after {latency_ms:.2f}ms: {str(e)}")
            metrics.increment("function.errors", tags={"function": func_name})
            raise
    
    return wrapper
