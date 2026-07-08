import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

def setup_tracing(app=None, engine=None):
    try:
        resource = Resource.create(attributes={
            "service.name": "python-app"
        })
        provider = TracerProvider(resource=resource)
        
        # Try to use OTLP if configured, fallback to console
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        processor = None
        
        if otlp_endpoint:
            try:
                # NextGen OTLP Http exporter preferred
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPExporter
                processor = BatchSpanProcessor(HTTPExporter(endpoint=otlp_endpoint))
                logger.info(f"OTEL tracing configured with HTTP exporter to endpoint {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to initialize OTLP HTTP exporter: {e}. Trying gRPC exporter.")
                try:
                    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GRPCExporter
                    processor = BatchSpanProcessor(GRPCExporter(endpoint=otlp_endpoint))
                    logger.info(f"OTEL tracing configured with gRPC exporter to endpoint {otlp_endpoint}")
                except Exception as ex:
                    logger.error(f"Failed to initialize OTLP gRPC exporter: {ex}. Falling back to Console exporter.")
        
        if not processor:
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            logger.info("OTEL tracing configured with Console exporter.")
            
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI app
        if app:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI successfully instrumented with OTEL.")
            except Exception as e:
                logger.error(f"Failed to instrument FastAPI: {e}")
                
        # Instrument SQLAlchemy engine
        if engine:
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                SQLAlchemyInstrumentor().instrument(engine=engine)
                logger.info("SQLAlchemy successfully instrumented with OTEL.")
            except Exception as e:
                logger.error(f"Failed to instrument SQLAlchemy: {e}")
                
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
