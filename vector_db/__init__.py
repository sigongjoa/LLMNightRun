"""
Vector Database Module for LLMNightRun feature.
This module provides vector embedding storage and retrieval capabilities.
"""

from .vector_store import VectorDB, Document
from .encoders import Encoder, DefaultEncoder

__all__ = ['VectorDB', 'Document', 'Encoder', 'DefaultEncoder']
