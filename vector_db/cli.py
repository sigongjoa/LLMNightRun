"""
Command line tool for VectorDB.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from .vector_store import VectorDB, Document
from .encoders import DefaultEncoder

try:
    from .encoders import SentenceTransformerEncoder
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False

# 디버그용 로그 출력 설정
DEBUG = True


def create_vector_db(args) -> VectorDB:
    """
    Create a VectorDB instance based on command line arguments.
    
    Args:
        args: The parsed command line arguments
        
    Returns:
        A VectorDB instance
    """
    # Determine encoder
    encoder = None
    if args.encoder == "default":
        encoder = DefaultEncoder(dimension=args.dimension)
    elif args.encoder == "sentence_transformer":
        if not SENTENCE_TRANSFORMER_AVAILABLE:
            print("Error: SentenceTransformer not available. Please install it with:")
            print("  pip install sentence-transformers")
            sys.exit(1)
        encoder = SentenceTransformerEncoder(model_name=args.model)
    
    # Create storage directory if needed
    if args.storage_dir:
        os.makedirs(args.storage_dir, exist_ok=True)
    
    # Create the database
    db = VectorDB(
        encoder=encoder,
        storage_dir=args.storage_dir
    )
    
    if DEBUG:
        print(f"Created VectorDB with encoder: {args.encoder}")
        print(f"Storage directory: {args.storage_dir or 'In-memory only'}")
    
    return db


def add_document(args) -> None:
    """Add a document to the database."""
    db = create_vector_db(args)
    
    # Parse metadata
    metadata = {}
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for metadata")
            sys.exit(1)
    
    # Add document
    if args.file:
        # Read from file
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        # Read from argument
        text = args.text
    
    doc_id = db.add(text, metadata=metadata)
    
    print(f"Document added with ID: {doc_id}")
    print(f"Total documents in database: {db.count()}")


def search_documents(args) -> None:
    """Search for documents in the database."""
    db = create_vector_db(args)
    
    # Parse metadata filter
    filter_metadata = None
    if args.filter:
        try:
            filter_metadata = json.loads(args.filter)
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for filter")
            sys.exit(1)
    
    # Search
    results = db.search(
        query=args.query,
        k=args.limit,
        threshold=args.threshold,
        filter_metadata=filter_metadata
    )
    
    # Display results
    print(f"Found {len(results)} document(s) for query: '{args.query}'")
    print("-" * 80)
    
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1} - Score: {score:.4f}")
        print(f"Document ID: {doc.id}")
        print(f"Metadata: {json.dumps(doc.metadata)}")
        
        # Limit text display length
        text_preview = doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
        print(f"Text: {text_preview}")
        print("-" * 80)


def list_documents(args) -> None:
    """List documents in the database."""
    db = create_vector_db(args)
    
    # Get documents
    documents = db.list_documents(limit=args.limit, offset=args.offset)
    
    print(f"Total documents in database: {db.count()}")
    print(f"Showing {len(documents)} document(s) (offset: {args.offset}, limit: {args.limit})")
    print("-" * 80)
    
    for i, doc in enumerate(documents):
        print(f"Document {i+1 + args.offset}:")
        print(f"ID: {doc.id}")
        print(f"Metadata: {json.dumps(doc.metadata)}")
        
        # Limit text display length
        text_preview = doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
        print(f"Text: {text_preview}")
        print("-" * 80)


def delete_document(args) -> None:
    """Delete a document from the database."""
    db = create_vector_db(args)
    
    # Delete document
    success = db.delete(args.id)
    
    if success:
        print(f"Document {args.id} deleted successfully")
        print(f"Remaining documents: {db.count()}")
    else:
        print(f"Document {args.id} not found")


def clear_database(args) -> None:
    """Clear the entire database."""
    db = create_vector_db(args)
    
    # Ask for confirmation
    if not args.force:
        confirm = input("Are you sure you want to clear the entire database? [y/N] ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Clear database
    initial_count = db.count()
    db.clear()
    
    print(f"Database cleared. Removed {initial_count} document(s)")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="VectorDB Command Line Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Common arguments
    parser.add_argument(
        "--storage-dir", 
        help="Directory for database storage (if omitted, in-memory only)"
    )
    parser.add_argument(
        "--encoder", 
        choices=["default", "sentence_transformer"],
        default="default",
        help="Encoder type to use"
    )
    parser.add_argument(
        "--dimension", 
        type=int, 
        default=768,
        help="Embedding dimension (only for default encoder)"
    )
    parser.add_argument(
        "--model", 
        default="all-MiniLM-L6-v2",
        help="Model name (only for sentence_transformer encoder)"
    )
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        help="Command to execute"
    )
    subparsers.required = True
    
    # Add command
    add_parser = subparsers.add_parser(
        "add", 
        help="Add a document to the database"
    )
    add_source = add_parser.add_mutually_exclusive_group(required=True)
    add_source.add_argument(
        "--text", 
        help="Text content to add"
    )
    add_source.add_argument(
        "--file", 
        help="File containing text to add"
    )
    add_parser.add_argument(
        "--metadata", 
        help="JSON metadata to associate with the document"
    )
    add_parser.set_defaults(func=add_document)
    
    # Search command
    search_parser = subparsers.add_parser(
        "search", 
        help="Search for similar documents"
    )
    search_parser.add_argument(
        "query", 
        help="Search query"
    )
    search_parser.add_argument(
        "--limit", 
        type=int, 
        default=5,
        help="Maximum number of results"
    )
    search_parser.add_argument(
        "--threshold", 
        type=float,
        help="Minimum similarity threshold (0-1)"
    )
    search_parser.add_argument(
        "--filter", 
        help="JSON metadata filter"
    )
    search_parser.set_defaults(func=search_documents)
    
    # List command
    list_parser = subparsers.add_parser(
        "list", 
        help="List documents in the database"
    )
    list_parser.add_argument(
        "--limit", 
        type=int, 
        default=10,
        help="Maximum number of documents to list"
    )
    list_parser.add_argument(
        "--offset", 
        type=int, 
        default=0,
        help="Offset for pagination"
    )
    list_parser.set_defaults(func=list_documents)
    
    # Delete command
    delete_parser = subparsers.add_parser(
        "delete", 
        help="Delete a document by ID"
    )
    delete_parser.add_argument(
        "id", 
        help="Document ID to delete"
    )
    delete_parser.set_defaults(func=delete_document)
    
    # Clear command
    clear_parser = subparsers.add_parser(
        "clear", 
        help="Clear the entire database"
    )
    clear_parser.add_argument(
        "--force", 
        action="store_true",
        help="Skip confirmation prompt"
    )
    clear_parser.set_defaults(func=clear_database)
    
    # Parse arguments and execute command
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
