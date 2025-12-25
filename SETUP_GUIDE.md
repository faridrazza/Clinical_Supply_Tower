# Quick Setup Guide - Using OpenAI GPT-4 and Embeddings

## ✅ Your Setup Plan is Perfect!

You want to use:
- **GPT-4** (or GPT-4-turbo) for the AI agents
- **OpenAI embeddings** for vector embeddings in ChromaDB

This is the **recommended setup** and will work great!

---

## Step-by-Step Setup

### 1. Install Dependencies

```bash
# Install all required packages (ChromaDB included!)
pip install -r requirements.txt
```

**What this installs**:
- ✅ `chromadb==0.4.22` - Vector database (runs locally, no separate download!)
- ✅ `langchain-openai` - OpenAI integration
- ✅ `streamlit` - Web interface
- ✅ All other dependencies

**Note**: ChromaDB will create a local folder (`./chroma_db`) to store embeddings. No separate server needed!

---

### 2. Get Your OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it (starts with `sk-...`)

---

### 3. Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env

# Edit .env file with your details
```

**Edit `.env` file**:
```bash
# Database (you'll set this up next)
DATABASE_URL=postgresql://username:password@localhost:5432/clinical_supply_chain

# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-your-actual-api-key-here

# LLM Model
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview  # or gpt-4, gpt-4-1106-preview

# Vector Database (ChromaDB will create this folder automatically)
VECTOR_DB_PATH=./chroma_db
EMBEDDING_MODEL=text-embedding-3-small  # OpenAI embedding model

# Application Settings
LOG_LEVEL=INFO
MAX_SQL_RETRIES=3
QUERY_TIMEOUT=30
```

---

### 4. Set Up PostgreSQL Database

#### Option A: Local PostgreSQL (Recommended for Development)

**Install PostgreSQL**:
- Windows: Download from https://www.postgresql.org/download/windows/
- During installation, remember your password!

**Create Database**:
```bash
# Open psql or pgAdmin
CREATE DATABASE clinical_supply_chain;
```

**Update .env**:
```bash
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/clinical_supply_chain
```

#### Option B: Cloud PostgreSQL (Recommended for Deployment)

**Free Options**:
- **Supabase**: https://supabase.com (Free tier: 500MB)
- **ElephantSQL**: https://www.elephantsql.com (Free tier: 20MB)
- **Render**: https://render.com (Free PostgreSQL)

**Get connection string** and add to `.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

### 5. Load Data into PostgreSQL

```bash
# Load all CSV files into database
python scripts/load_data.py
```

**What this does**:
- Reads all 40 CSV files from `synthetic_clinical_data/`
- Creates tables in PostgreSQL
- Loads data
- Shows progress

**Expected output**:
```
Loading affiliate_warehouse_inventory.csv into table affiliate_warehouse_inventory...
  Rows: 212, Columns: 15
✓ Successfully loaded affiliate_warehouse_inventory
...
Loading complete!
  Success: 40
  Failed: 0
```

---

### 6. Initialize Vector Database (ChromaDB)

```bash
# Create embeddings using OpenAI and store in ChromaDB
python scripts/init_vector_db.py
```

**What this does**:
- Reads table schemas from PostgreSQL
- Creates embeddings using **OpenAI's text-embedding-3-small**
- Stores in ChromaDB (local folder: `./chroma_db`)
- No separate ChromaDB installation needed!

**Expected output**:
```
Initializing vector database with schema metadata...
✓ Added schema for available_inventory_report
✓ Added schema for enrollment_rate_report
...
Vector DB initialization complete!
  Tables added: 40
```

**Note**: This will use your OpenAI API key to create embeddings. Cost is minimal (~$0.01 for 40 tables).

---

### 7. Run the Application

```bash
streamlit run app.py
```

**Opens in browser**: http://localhost:8501

---

## OpenAI Models Explained

### GPT-4 Models (for AI Agents)

**Recommended**: `gpt-4-turbo-preview`
- Faster than GPT-4
- 128K context window
- More cost-effective
- Latest features

**Alternatives**:
- `gpt-4` - Original GPT-4 (8K context)
- `gpt-4-1106-preview` - GPT-4 Turbo (128K context)
- `gpt-3.5-turbo` - Cheaper, faster, less capable

**Set in `.env`**:
```bash
LLM_MODEL=gpt-4-turbo-preview
```

### OpenAI Embedding Models (for Vector DB)

**Recommended**: `text-embedding-3-small`
- Latest model (released 2024)
- 1536 dimensions
- Cost: $0.02 / 1M tokens
- Great performance

**Alternatives**:
- `text-embedding-3-large` - Higher quality, more expensive
- `text-embedding-ada-002` - Previous generation, still good

**Set in `.env`**:
```bash
EMBEDDING_MODEL=text-embedding-3-small
```

---

## Cost Estimate (OpenAI)

### One-Time Setup Costs:
- **Vector DB initialization**: ~$0.01 (40 table schemas)

### Per-Query Costs:
- **Workflow A (Supply Watchdog)**: ~$0.05-0.10 per run
- **Workflow B (Chat query)**: ~$0.02-0.05 per query

### Monthly Estimate (Light Usage):
- 10 Workflow A runs: ~$1
- 100 chat queries: ~$3
- **Total**: ~$4/month

**Note**: Costs are approximate and depend on usage.

---

## Troubleshooting

### Issue: "No module named 'chromadb'"
**Solution**: 
```bash
pip install chromadb==0.4.22
```

### Issue: "OpenAI API key not found"
**Solution**: Check your `.env` file has:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Issue: "Cannot connect to database"
**Solution**: 
1. Check PostgreSQL is running
2. Verify DATABASE_URL in `.env`
3. Test connection:
```bash
python -c "import psycopg2; conn = psycopg2.connect('your_database_url'); print('Connected!')"
```

### Issue: ChromaDB folder not created
**Solution**: ChromaDB creates the folder automatically on first use. If you want to create it manually:
```bash
mkdir chroma_db
```

---

## Verification Checklist

Before running the app, verify:

- [ ] `pip install -r requirements.txt` completed successfully
- [ ] `.env` file created with your OPENAI_API_KEY
- [ ] PostgreSQL database created
- [ ] `python scripts/load_data.py` completed (40 tables loaded)
- [ ] `python scripts/init_vector_db.py` completed (embeddings created)
- [ ] `chroma_db/` folder exists (created automatically)

---

## Summary

### What You Need:
1. ✅ **OpenAI API Key** - Get from https://platform.openai.com
2. ✅ **PostgreSQL Database** - Local or cloud
3. ✅ **Python 3.11+** - Already have it
4. ✅ **ChromaDB** - Installed via pip (no separate download!)

### What Happens:
1. **pip install** → Installs ChromaDB and all dependencies
2. **load_data.py** → Loads CSV data into PostgreSQL
3. **init_vector_db.py** → Creates embeddings using OpenAI, stores in ChromaDB locally
4. **streamlit run app.py** → Runs the application

### Your Setup is Perfect! ✅
- Using GPT-4 for agents: ✅ Excellent choice
- Using OpenAI embeddings: ✅ Best quality
- ChromaDB local storage: ✅ No separate server needed

---

**Ready to start?** Run:
```bash
pip install -r requirements.txt
```

Then follow steps 2-7 above!
