"""
Setup script for ChromaDB with OpenAI embeddings.

This script:
1. Verifies OpenAI API key
2. Initializes ChromaDB with OpenAI embeddings
3. Generates embeddings for all 40 table schemas
4. Verifies the setup
"""
import sys
import os
import logging
import subprocess
from dotenv import load_dotenv

# Load .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_openai_api_key():
    """Check if OpenAI API key is set."""
    logger.info("Checking OpenAI API key...")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("✗ OPENAI_API_KEY environment variable not set")
        logger.info("\nTo set it:")
        logger.info("  Windows: set OPENAI_API_KEY=your_key_here")
        logger.info("  Linux/Mac: export OPENAI_API_KEY=your_key_here")
        return False
    
    # Mask the key for display
    masked_key = api_key[:10] + "..." + api_key[-4:]
    logger.info(f"✓ OpenAI API key found: {masked_key}")
    return True


def install_dependencies():
    """Install required dependencies."""
    logger.info("\nInstalling dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "chromadb>=0.4.24",
            "sentence-transformers>=3.0.0",
            "openai>=1.3.0"
        ])
        logger.info("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install dependencies: {e}")
        return False


def initialize_chromadb_openai():
    """Initialize ChromaDB with OpenAI embeddings."""
    logger.info("\nInitializing ChromaDB with OpenAI embeddings...")
    
    try:
        from src.utils.chroma_schema_manager_openai import get_chroma_manager_openai
        
        logger.info("Creating ChromaDB collection with OpenAI embeddings...")
        logger.info("This may take 1-2 minutes (generating embeddings for 40 tables)...")
        
        chroma_manager = get_chroma_manager_openai()
        
        stats = chroma_manager.get_collection_stats()
        logger.info(f"✓ ChromaDB initialized successfully")
        logger.info(f"  Collection: {stats.get('collection_name')}")
        logger.info(f"  Total tables: {stats.get('total_tables')}")
        logger.info(f"  Embedding model: {stats.get('embedding_model')}")
        logger.info(f"  Embedding dimension: {stats.get('embedding_dimension')}")
        logger.info(f"  Persist directory: {stats.get('persist_directory')}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize ChromaDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_setup():
    """Verify ChromaDB setup with OpenAI embeddings."""
    logger.info("\nVerifying ChromaDB setup...")
    
    try:
        from src.agents.schema_retrieval_agent_v2_openai import SchemaRetrievalAgentV2OpenAI
        
        agent = SchemaRetrievalAgentV2OpenAI()
        
        logger.info("Testing semantic search with OpenAI embeddings...")
        result = agent.execute({
            "query": "material requirements",
            "workflow": "B",
            "n_results": 3
        })
        
        if result.get("success"):
            tables = result.get("table_names", [])
            scores = result.get("similarity_scores", {})
            
            logger.info(f"✓ Semantic search working")
            logger.info(f"  Found tables: {tables}")
            for table in tables:
                logger.info(f"    - {table}: {scores.get(table, 0):.2%} relevance")
            
            return True
        else:
            logger.error(f"✗ Semantic search failed: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow():
    """Test Workflow B V2 with OpenAI embeddings."""
    logger.info("\nTesting Workflow B V2 with OpenAI embeddings...")
    
    try:
        from src.workflows.workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI
        
        workflow = ScenarioStrategistWorkflowV2OpenAI()
        
        logger.info("Executing test query...")
        result = workflow.execute("Show material requirements")
        
        if result.get("success"):
            logger.info(f"✓ Workflow B V2 (OpenAI) working")
            logger.info(f"  Intent: {result.get('intent')}")
            logger.info(f"  Tables searched: {result.get('tables_searched')}")
            logger.info(f"  Table used: {result.get('table_used')}")
            logger.info(f"  Rows returned: {result.get('row_count')}")
            logger.info(f"  Embedding model: {result.get('embedding_model')}")
            return True
        else:
            logger.error(f"✗ Workflow B V2 failed: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"✗ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_usage_examples():
    """Show usage examples."""
    logger.info("\n" + "=" * 80)
    logger.info("USAGE EXAMPLES - Workflow B V2 with OpenAI Embeddings")
    logger.info("=" * 80)
    
    examples = """
1. Basic Query:
   from src.workflows.workflow_b_v2_openai import ScenarioStrategistWorkflowV2OpenAI
   
   workflow = ScenarioStrategistWorkflowV2OpenAI()
   result = workflow.execute("Show material requirements")
   print(result['response'])

2. Query with Filters:
   result = workflow.execute("Show purchase requirements for material Drug A")

3. Complex Query:
   result = workflow.execute("What's the status of outstanding shipments?")

4. Check ChromaDB Stats:
   stats = workflow.get_chroma_stats()
   print(f"Embedding model: {stats['embedding_model']}")
   print(f"Embedding dimension: {stats['embedding_dimension']}")

5. Refresh ChromaDB:
   workflow.refresh_chroma()

Key Features:
- Uses OpenAI's text-embedding-3-small model
- 1536-dimensional embeddings
- Semantic search across all 40 tables
- Stores only schema embeddings (not data)
- Fast query execution (~1-3 seconds)

For more examples, see CHROMADB_IMPLEMENTATION_GUIDE.md
"""
    logger.info(examples)


def main():
    """Run setup."""
    logger.info("=" * 80)
    logger.info("CHROMADB SETUP WITH OPENAI EMBEDDINGS")
    logger.info("=" * 80)
    
    steps = [
        ("Check OpenAI API Key", check_openai_api_key),
        ("Install Dependencies", install_dependencies),
        ("Initialize ChromaDB (OpenAI)", initialize_chromadb_openai),
        ("Verify Setup", verify_setup),
        ("Test Workflow", test_workflow),
    ]
    
    results = {}
    for step_name, step_func in steps:
        logger.info(f"\n[{len(results) + 1}/{len(steps)}] {step_name}")
        logger.info("-" * 80)
        
        try:
            results[step_name] = step_func()
        except Exception as e:
            logger.error(f"✗ {step_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[step_name] = False
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SETUP SUMMARY")
    logger.info("=" * 80)
    
    for step_name, passed in results.items():
        status = "✓" if passed else "✗"
        logger.info(f"{status} {step_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ Setup completed successfully!")
        show_usage_examples()
        return 0
    else:
        logger.error("\n✗ Setup failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
