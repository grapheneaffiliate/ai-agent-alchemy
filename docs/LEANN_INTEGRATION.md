# LEANN Vector Database Integration

## Overview
LEANN (Lightweight Efficient Archive for Neural Networks) is now integrated into the MCP AI Agent system as a fully available tool for semantic search and RAG operations across documents.

## Key Features
- **97% Storage Reduction**: Uses graph-based selective recomputation instead of storing all embeddings
- **Zero Privacy Loss**: All data stays on your local machine
- **MCP Integration**: Directly available to the agent for intelligent document retrieval
- **Multi-format Support**: PDFs, text files, code, emails, browser history, chat logs, and more

## Available Tools

### 1. Build Index (`leann-build-index`)
Create vector indexes from document collections.

```json
{
  "index_name": "my-docs",
  "docs": ["./docs/paper.pdf", "./docs/notes.txt", "./src/"]
}
```

### 2. Search Documents (`leann-search-documents`)
Perform semantic search through indexed documents.

```json
{
  "index_name": "my-docs",
  "query": "machine learning algorithms",
  "top_k": 5
}
```

### 3. Ask Questions (`leann-ask-question`)
Get AI-generated answers based on document content.

```json
{
  "index_name": "my-docs",
  "question": "What are the main techniques LEANN uses?",
  "top_k": 3
}
```

### 4. List Indexes (`leann-list-indexes`)
View all available vector indexes.

## Usage Examples

### Document RAG
```python
# Agent can now index your entire document collection
agent.call("build-index", {
  "index_name": "my-papers",
  "docs": ["./research/", "./notes/"]
})

# Then search semantically
results = agent.call("search-documents", {
  "index_name": "my-papers",
  "query": "neural network optimization"
})

# Or ask questions
answer = agent.call("ask-question", {
  "index_name": "my-papers",
  "question": "How do you implement selective recomputation?"
})
```

## Platform Features

### Windows + WSL Support
- ✅ **CLI Interface**: Fully functional on Windows
- ✅ **Text Search Fallback**: Robust fallback when vector backends fail
- ✅ **WSL2 Integration**: Full vector search and advanced features via WSL2
- ✅ **Smart Runtime Selection**: Automatically uses WSL when available for optimal performance

### Linux/macOS
- ✅ **Complete Support**: All features available including vector operations

### New Advanced Features
- 🎯 **Semantic Codebase Analysis**: Intelligent architecture, function, and class analysis
- 🔍 **Code Intelligence**: Automatic extraction of patterns and documentation quality
- 📊 **Fallback Analytics**: Basic analysis even without vector search

## MCP Integration Status

LEANN is now fully integrated as an MCP server:
- Added to `config/mcp_tools.json`
- Plugin executor handles LEANN commands
- Available alongside existing tools (search, browser, news, etc.)

The agent can now use LEANN whenever document search or RAG capabilities are needed to provide more accurate and contextually relevant responses.

## Architecture Benefits
- **Selective Recomputation**: Only computes embeddings during search, not storage
- **Graph-based Pruning**: High-degree preserving graph structure minimizes memory usage
- **Dynamic Batching**: Efficient GPU utilization for embedding computations
- **AST-aware Chunking**: Code-aware document splitting for better code understanding
