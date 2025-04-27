"""
LocalDocsView is the view for managing document collections.
It allows creating, importing, and searching documents.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QListWidget, QListWidgetItem, QSplitter,
    QTextEdit, QFileDialog, QInputDialog, QMessageBox,
    QLineEdit, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QIcon, QFont, QAction

class DocumentSearchThread(QThread):
    """Thread for searching documents in the background."""
    
    results_ready = pyqtSignal(list)  # Signal for search results
    
    def __init__(self, document_store, vector_store, collection_id, query):
        super().__init__()
        
        self.document_store = document_store
        self.vector_store = vector_store
        self.collection_id = collection_id
        self.query = query
    
    def run(self):
        """Run the search thread."""
        try:
            # Search documents
            results = self.document_store.search_documents(
                self.collection_id,
                self.query
            )
            
            # Emit results
            self.results_ready.emit(results)
        except Exception as e:
            # Emit empty results on error
            self.results_ready.emit([])

class DocumentIndexingThread(QThread):
    """Thread for indexing documents in the background."""
    
    completed = pyqtSignal(bool, str)  # Signal for indexing completion (success, message)
    
    def __init__(self, document_store, collection_id):
        super().__init__()
        
        self.document_store = document_store
        self.collection_id = collection_id
    
    def run(self):
        """Run the indexing thread."""
        try:
            # Index collection
            success = self.document_store.index_collection(self.collection_id)
            
            # Emit completion signal
            if success:
                self.completed.emit(True, f"Collection indexed successfully")
            else:
                self.completed.emit(False, f"Failed to index collection")
        except Exception as e:
            self.completed.emit(False, f"Error indexing collection: {str(e)}")

class LocalDocsView(QWidget):
    """View for managing document collections."""
    
    def __init__(self, document_store, vector_store, chat_engine, parent=None):
        super().__init__(parent)
        
        self.document_store = document_store
        self.vector_store = vector_store
        self.chat_engine = chat_engine
        
        self.current_collection_id = None
        self.current_document_id = None
        
        self.indexing_thread = None
        self.search_thread = None
        
        self._init_ui()
        self._load_collections()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Header
        self.header_label = QLabel("Local Documents")
        self.header_label.setObjectName("viewHeader")
        self.header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Collection controls
        self.collection_frame = QFrame()
        self.collection_frame.setObjectName("collectionFrame")
        
        self.collection_layout = QHBoxLayout(self.collection_frame)
        self.collection_layout.setContentsMargins(0, 0, 0, 0)
        
        self.collection_label = QLabel("Collections:")
        self.collection_label.setObjectName("collectionLabel")
        
        self.new_collection_button = QPushButton("New Collection")
        self.new_collection_button.setObjectName("newCollectionButton")
        self.new_collection_button.clicked.connect(self._on_new_collection)
        
        self.collection_layout.addWidget(self.collection_label)
        self.collection_layout.addStretch()
        self.collection_layout.addWidget(self.new_collection_button)
        
        # Collections list
        self.collections_list = QListWidget()
        self.collections_list.setObjectName("collectionsList")
        self.collections_list.setMinimumWidth(200)
        self.collections_list.setMaximumWidth(300)
        self.collections_list.currentItemChanged.connect(self._on_collection_changed)
        
        # Main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Document view
        self.document_widget = QWidget()
        self.document_layout = QVBoxLayout(self.document_widget)
        self.document_layout.setContentsMargins(0, 0, 0, 0)
        self.document_layout.setSpacing(10)
        
        # Document controls
        self.document_controls = QFrame()
        self.document_controls.setObjectName("documentControls")
        
        self.document_controls_layout = QHBoxLayout(self.document_controls)
        self.document_controls_layout.setContentsMargins(0, 0, 0, 0)
        
        self.import_button = QPushButton("Import Documents")
        self.import_button.setObjectName("importButton")
        self.import_button.clicked.connect(self._on_import_documents)
        self.import_button.setEnabled(False)
        
        self.index_button = QPushButton("Index Collection")
        self.index_button.setObjectName("indexButton")
        self.index_button.clicked.connect(self._on_index_collection)
        self.index_button.setEnabled(False)
        
        self.search_label = QLabel("Search:")
        self.search_label.setObjectName("searchLabel")
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.returnPressed.connect(self._on_search)
        self.search_input.setEnabled(False)
        
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("searchButton")
        self.search_button.clicked.connect(self._on_search)
        self.search_button.setEnabled(False)
        
        self.document_controls_layout.addWidget(self.import_button)
        self.document_controls_layout.addWidget(self.index_button)
        self.document_controls_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.document_controls_layout.addWidget(self.search_label)
        self.document_controls_layout.addWidget(self.search_input)
        self.document_controls_layout.addWidget(self.search_button)
        
        # Documents list
        self.documents_list = QListWidget()
        self.documents_list.setObjectName("documentsList")
        self.documents_list.currentItemChanged.connect(self._on_document_changed)
        
        # Document content
        self.document_content = QTextEdit()
        self.document_content.setObjectName("documentContent")
        self.document_content.setReadOnly(True)
        
        # Add widgets to document layout
        self.document_layout.addWidget(self.document_controls)
        self.document_layout.addWidget(self.documents_list)
        self.document_layout.addWidget(self.document_content)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.collections_list)
        self.main_splitter.addWidget(self.document_widget)
        
        # Set splitter proportions
        self.main_splitter.setSizes([200, 800])
        
        # Add widgets to main layout
        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.collection_frame)
        self.layout.addWidget(self.main_splitter)
    
    def _load_collections(self):
        """Load collections from document store."""
        # Save current selection
        current_id = self.current_collection_id
        
        # Clear list
        self.collections_list.clear()
        
        # Get collections
        collections = self.document_store.list_collections()
        
        # Add items for each collection
        for collection in collections:
            item = QListWidgetItem(collection.get("name", "Unnamed Collection"))
            item.setData(Qt.ItemDataRole.UserRole, collection.get("id"))
            self.collections_list.addItem(item)
            
            # Select if this is the current collection
            if collection.get("id") == current_id:
                self.collections_list.setCurrentItem(item)
        
        # If no selection but we have collections, select the first one
        if self.collections_list.count() > 0 and not self.collections_list.currentItem():
            self.collections_list.setCurrentRow(0)
    
    def _load_documents(self, collection_id):
        """Load documents for a collection."""
        # Clear list
        self.documents_list.clear()
        
        # Clear content
        self.document_content.clear()
        
        if not collection_id:
            return
        
        # Get documents
        documents = self.document_store.list_documents(collection_id)
        
        # Add items for each document
        for document in documents:
            # Get title
            title = document.get("title", "Untitled Document")
            
            # Create item
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, document.get("id"))
            self.documents_list.addItem(item)
    
    def _on_collection_changed(self, current, previous):
        """Handle collection selection change."""
        if not current:
            self.current_collection_id = None
            self.import_button.setEnabled(False)
            self.index_button.setEnabled(False)
            self.search_input.setEnabled(False)
            self.search_button.setEnabled(False)
            self.documents_list.clear()
            self.document_content.clear()
            return
        
        # Get collection ID
        collection_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_collection_id = collection_id
        
        # Enable buttons
        self.import_button.setEnabled(True)
        self.index_button.setEnabled(True)
        self.search_input.setEnabled(True)
        self.search_button.setEnabled(True)
        
        # Load documents
        self._load_documents(collection_id)
    
    def _on_document_changed(self, current, previous):
        """Handle document selection change."""
        if not current or not self.current_collection_id:
            self.current_document_id = None
            self.document_content.clear()
            return
        
        # Get document ID
        document_id = current.data(Qt.ItemDataRole.UserRole)
        self.current_document_id = document_id
        
        # Load document content
        document = self.document_store.get_document(self.current_collection_id, document_id)
        if document:
            content = document.get("content", "")
            self.document_content.setText(content)
    
    def _on_new_collection(self):
        """Handle new collection button click."""
        # Get name
        name, ok = QInputDialog.getText(
            self,
            "New Collection",
            "Collection Name:",
            QLineEdit.EchoMode.Normal,
            "My Collection"
        )
        
        if not ok or not name:
            return
        
        # Get description
        description, ok = QInputDialog.getText(
            self,
            "New Collection",
            "Description (optional):",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if not ok:
            return
        
        # Create collection
        collection = self.document_store.create_collection(name, description)
        
        # Reload collections
        self._load_collections()
        
        # Select new collection
        for i in range(self.collections_list.count()):
            item = self.collections_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == collection.get("id"):
                self.collections_list.setCurrentItem(item)
                break
    
    def _on_import_documents(self):
        """Handle import documents button click."""
        if not self.current_collection_id:
            return
        
        # Ask for directory
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory with Documents",
            os.path.expanduser("~/Documents")
        )
        
        if not directory:
            return
        
        # Import documents
        imported_count = self.document_store.import_documents_from_directory(
            self.current_collection_id,
            directory
        )
        
        # Show result
        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {imported_count} documents"
        )
        
        # Reload documents
        self._load_documents(self.current_collection_id)
    
    def _on_index_collection(self):
        """Handle index collection button click."""
        if not self.current_collection_id:
            return
        
        # Check if already indexing
        if self.indexing_thread and self.indexing_thread.isRunning():
            return
        
        # Disable buttons
        self.index_button.setEnabled(False)
        self.index_button.setText("Indexing...")
        
        # Create and start indexing thread
        self.indexing_thread = DocumentIndexingThread(
            self.document_store,
            self.current_collection_id
        )
        self.indexing_thread.completed.connect(self._on_indexing_completed)
        self.indexing_thread.start()
    
    def _on_indexing_completed(self, success, message):
        """Handle indexing completion."""
        # Re-enable button
        self.index_button.setEnabled(True)
        self.index_button.setText("Index Collection")
        
        # Show result
        if success:
            QMessageBox.information(
                self,
                "Indexing Complete",
                message
            )
        else:
            QMessageBox.warning(
                self,
                "Indexing Failed",
                message
            )
    
    def _on_search(self):
        """Handle search button click."""
        if not self.current_collection_id:
            return
        
        # Get query
        query = self.search_input.text().strip()
        if not query:
            return
        
        # Check if already searching
        if self.search_thread and self.search_thread.isRunning():
            return
        
        # Clear documents list
        self.documents_list.clear()
        
        # Add searching indicator
        searching_item = QListWidgetItem("Searching...")
        self.documents_list.addItem(searching_item)
        
        # Create and start search thread
        self.search_thread = DocumentSearchThread(
            self.document_store,
            self.vector_store,
            self.current_collection_id,
            query
        )
        self.search_thread.results_ready.connect(self._on_search_results)
        self.search_thread.start()
    
    def _on_search_results(self, results):
        """Handle search results."""
        # Clear documents list
        self.documents_list.clear()
        
        if not results:
            # Add no results indicator
            no_results_item = QListWidgetItem("No results found")
            self.documents_list.addItem(no_results_item)
            return
        
        # Add items for each result
        for document in results:
            # Get title
            title = document.get("title", "Untitled Document")
            
            # Create item
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, document.get("id"))
            self.documents_list.addItem(item)
        
        # Select first result
        if self.documents_list.count() > 0:
            self.documents_list.setCurrentRow(0)
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        
        # Reload collections when view is shown
        self._load_collections()
