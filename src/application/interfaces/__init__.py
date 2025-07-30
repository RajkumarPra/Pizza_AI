"""
Application Interfaces
Interfaces for external services following dependency inversion principle.
"""

from .llm_service import ILLMService

__all__ = [
    'ILLMService',
] 