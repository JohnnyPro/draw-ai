"""
LangFuse Observability Integration

Provides tracing and observability for the DrawAI graph.
Gracefully handles missing configuration.
"""

import os
import functools
from typing import Optional, Callable, Any
from datetime import datetime

# Try to import langfuse, handle if not available
try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    observe = None
    langfuse_context = None


_langfuse_client: Optional[Any] = None
_langfuse_initialized: bool = False
_langfuse_warning_shown: bool = False


def _get_env_vars() -> dict:
    """Get LangFuse environment variables."""
    return {
        "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
        "host": os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    }


def _show_setup_warning():
    """Show helpful warning about LangFuse setup."""
    global _langfuse_warning_shown
    if _langfuse_warning_shown:
        return
    
    _langfuse_warning_shown = True
    print("\n" + "=" * 60)
    print("⚠️  LangFuse observability is not configured")
    print("=" * 60)
    print("To enable tracing and observability, set these environment variables:")
    print("")
    print("  LANGFUSE_PUBLIC_KEY=your_public_key")
    print("  LANGFUSE_SECRET_KEY=your_secret_key")
    print("  LANGFUSE_HOST=http://localhost:3000  # for self-hosted")
    print("")
    print("Add them to your .env file or export them in your shell.")
    print("The application will continue without observability.")
    print("=" * 60 + "\n")


def init_langfuse() -> bool:
    """
    Initialize LangFuse client.
    
    Returns:
        True if initialization successful, False otherwise.
    """
    global _langfuse_client, _langfuse_initialized
    
    if _langfuse_initialized:
        return _langfuse_client is not None
    
    _langfuse_initialized = True
    
    # Check if langfuse package is available
    if not LANGFUSE_AVAILABLE:
        print("Warning: langfuse package not installed. Run: pip install langfuse")
        return False
    
    # Check environment variables
    env_vars = _get_env_vars()
    
    if not env_vars["public_key"] or not env_vars["secret_key"]:
        _show_setup_warning()
        return False
    
    try:
        _langfuse_client = Langfuse(
            public_key=env_vars["public_key"],
            secret_key=env_vars["secret_key"],
            host=env_vars["host"],
        )
        print(f"✅ LangFuse initialized (host: {env_vars['host']})")
        return True
    except Exception as e:
        print(f"Warning: Failed to initialize LangFuse: {e}")
        return False


def get_langfuse() -> Optional[Any]:
    """Get the LangFuse client, initializing if needed."""
    if not _langfuse_initialized:
        init_langfuse()
    return _langfuse_client


def trace_drawing(func: Callable) -> Callable:
    """
    Decorator to trace a drawing operation.
    
    If LangFuse is not configured, the function runs normally without tracing.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        client = get_langfuse()
        
        if client is None:
            # No tracing, just run the function
            return func(*args, **kwargs)
        
        # Create trace
        trace = client.trace(
            name=func.__name__,
            metadata={
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        try:
            result = func(*args, **kwargs)
            
            # Log success
            trace.update(
                output={"status": "success"},
            )
            
            return result
            
        except Exception as e:
            # Log failure
            trace.update(
                output={"status": "error", "error": str(e)},
            )
            raise
        
        finally:
            # Ensure trace is flushed
            client.flush()
    
    return wrapper


def log_node_execution(node_name: str, state: dict, result: dict):
    """
    Log a graph node execution to LangFuse.
    
    Args:
        node_name: Name of the node being executed
        state: Input state
        result: Output state
    """
    client = get_langfuse()
    if client is None:
        return
    
    try:
        client.span(
            name=f"node:{node_name}",
            input=state,
            output=result,
        )
        client.flush()
    except Exception as e:
        # Don't let logging failures break the app
        print(f"Warning: Failed to log to LangFuse: {e}")


def log_score(name: str, value: float, comment: Optional[str] = None):
    """
    Log a score to LangFuse (e.g., confidence score).
    
    Args:
        name: Score name
        value: Score value (0-1)
        comment: Optional comment
    """
    client = get_langfuse()
    if client is None:
        return
    
    try:
        client.score(
            name=name,
            value=value,
            comment=comment,
        )
        client.flush()
    except Exception as e:
        print(f"Warning: Failed to log score to LangFuse: {e}")


def shutdown():
    """Shutdown LangFuse client gracefully."""
    global _langfuse_client
    
    if _langfuse_client is not None:
        try:
            _langfuse_client.flush()
            _langfuse_client.shutdown()
        except Exception:
            pass
        _langfuse_client = None
