# 🌌 LYNX Complete Setup Guide - Step by Step

**Detailed instructions for Windows users** - Every command explained!

## 📋 Prerequisites Check

First, verify you have the required software:

```powershell
# Check Node.js (need 20+)
node --version

# Check Python (need 3.11+)
python --version

# Check Docker
docker --version

# Check Git
git --version
```

If any are missing, install them first:
- **Node.js 20+**: https://nodejs.org/
- **Python 3.11+**: https://www.python.org/downloads/
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/

## 🚀 Complete Setup Process

### Step 1: Project Setup (2 minutes)

```powershell
# Navigate to your projects folder
cd C:\Users\%USERNAME%\repos

# Clone the repository (if not already done)
# git clone <your-repo-url>
cd lynx

# Install Node.js dependencies
npm install
```

**What this does**: Downloads all JavaScript/TypeScript packages needed for the frontend and API.

### Step 2: Environment Configuration (1 minute)

```powershell
# Copy the environment template
copy .env.example .env

# View the .env file (optional)
type .env
```

**What this does**: Creates your local environment configuration. With SBERT, you don't need to edit anything - the defaults work!

**Your .env should look like this:**
```
# Database Configuration
DATABASE_URL="postgresql://lynx_user:lynx_password@localhost:5432/lynx_dev"
SUPABASE_URL="your-supabase-url"
SUPABASE_ANON_KEY="your-supabase-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-role-key"

# OpenAI Configuration (NOT NEEDED for SBERT!)
OPENAI_API_KEY="your-openai-api-key"

# ... other settings
```

### Step 3: Database Setup (3 minutes)

This is the most important part! We'll use Docker to run PostgreSQL with the pgvector extension.

```powershell
# Start the database container
npm run docker:up
```

**What this does**: 
- Downloads PostgreSQL with pgvector extension
- Creates a database named `lynx_dev`
- Sets up user `lynx_user` with password `lynx_password`
- Exposes database on port 5432

**Wait for database to initialize** (about 30 seconds). You should see:
```
✅ lynx-postgres container started
✅ lynx-redis container started
```

Now run the database migrations:

```powershell
# Navigate to the web app folder
cd apps\web

# Run database migrations to create tables
npm run db:migrate
```

**What this does**: Creates all the tables (concepts, embeddings, edges, node_positions) in your database.

**Expected output:**
```
✅ Applying migrations...
✅ Database schema updated
```

```powershell
# Go back to project root
cd ..\..
```

### Step 4: Python Environment Setup (5 minutes)

Now let's set up Python properly with a virtual environment:

```powershell
# Navigate to the ingestion scripts
cd scripts\ingestion

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate
```

**What this does**: Creates an isolated Python environment so packages don't conflict with your system Python.

**You should see `(venv)` at the start of your command prompt now.**

### Step 5: Install Python Dependencies (10 minutes)

This step takes the longest because we're downloading PyTorch and SBERT:

```powershell
# Install PyTorch first (CPU version for compatibility)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install sentence-transformers (SBERT)
pip install sentence-transformers

# Install other dependencies
pip install -r requirements.txt
```

**What this does**:
- **PyTorch**: Machine learning framework (needed for SBERT)
- **sentence-transformers**: SBERT library for embeddings
- **Other packages**: Database drivers, data processing tools

**Expected downloads**:
- PyTorch: ~200MB
- SBERT models: ~90MB (downloaded on first use)
- Other packages: ~50MB

### Step 6: Test Database Connection (1 minute)

Let's verify the database is working:

```powershell
# Test database connection
python -c "import psycopg2; conn = psycopg2.connect('postgresql://lynx_user:lynx_password@localhost:5432/lynx_dev'); print('✅ Database connection successful'); conn.close()"
```

**Expected output**: `✅ Database connection successful`

If this fails, check:
- Docker Desktop is running
- Database container is up: `docker ps`
- No other PostgreSQL running on port 5432

### Step 7: Test Python Dependencies (1 minute)

```powershell
# Test all Python imports
python -c "
import requests
import pandas
import numpy
import sentence_transformers
import psycopg2
print('✅ All Python dependencies working')
"
```

**Expected output**: `✅ All Python dependencies working`

### Step 8: Run Test Pipeline (3 minutes)

Now let's test the complete pipeline with sample data:

```powershell
# Go back to project root (important!)
cd ..\..

# Run the test ingestion
python scripts\test-ingestion.py
```

**Expected output** (this will take 2-3 minutes):
```
🧪 Testing database connection...
✅ Database connection working
🧪 Testing Wikipedia ingestion...
✅ Fetched: Artificial intelligence
✅ Fetched: Black hole
✅ Fetched: DNA
✅ Fetched: Quantum mechanics
✅ Fetched: Leonardo da Vinci
✅ Fetched 5 test concepts
🧪 Testing concept storage...
✅ Concepts stored in database
🧪 Testing SBERT embedding generation...
Loading SBERT model: all-MiniLM-L6-v2
Downloading (…)_Pooling/config.json: 100%|████| 190/190
Downloading (…)b85/.gitattributes: 100%|████| 1.18k/1.18k
Downloading (…)_modules.json: 100%|████| 349/349
Downloading (…)/config.json: 100%|████| 612/612
Downloading (…)ce_transformers.json: 100%|████| 116/116
Downloading (…)e1/.gitattributes: 100%|████| 1.18k/1.18k
Downloading (…)_config.json: 100%|████| 684/684
Downloading (…)pytorch_model.bin: 100%|████| 90.9M/90.9M
Downloading (…)okenizer_config.json: 100%|████| 350/350
Downloading (…)solve/main/vocab.txt: 100%|████| 232k/232k
Downloading (…)/special_tokens_map.json: 100%|████| 112/112
Downloading (…)a8e1d/.gitattributes: 100%|████| 1.18k/1.18k
Downloading (…)1_Pooling/config.json: 100%|████| 190/190
✅ SBERT model loaded successfully
Processing batches: 100%|████████████| 1/1 [00:00<00:00,  2.34it/s]
✅ Generated 5 embeddings
🎉 Pipeline test completed successfully!
📊 Results: 5 concepts, 5 embeddings

🎉 Test passed! Your LYNX pipeline is working with SBERT.

Next steps:
1. Check http://localhost:3000/api/status to see updated counts
2. Try searching for 'artificial intelligence' in the web interface
3. Run full ingestion with: python scripts/ingestion/main.py --concepts 1000
4. No OpenAI API costs - SBERT runs locally! 🎆
```

### Step 9: Start the Frontend (1 minute)

```powershell
# Start the development server
npm run dev
```

**Expected output**:
```
▲ Next.js 14.0.0
- Local:        http://localhost:3000
- Network:      http://192.168.1.xxx:3000

✓ Ready in 2.3s
```

### Step 10: Test the Web Interface (2 minutes)

1. **Open your browser** and go to: `http://localhost:3000`

2. **You should see**:
   - 🌌 Beautiful galaxy-themed interface
   - 🔍 Search bar at the top
   - 📊 Status bar showing "5 concepts • 5 embeddings • 0 edges"
   - 🎨 Dark space-like background

3. **Test search**:
   - Type "artificial intelligence" in the search bar
   - You should see search results appear
   - Click on a result to see concept details in the right panel

4. **Test API directly**:
   - Visit: `http://localhost:3000/api/status`
   - Should return JSON with concept counts

## 🎯 Verification Checklist

Check off each item as you complete it:

- ✅ Node.js dependencies installed (`npm install` succeeded)
- ✅ Environment file created (`.env` exists)
- ✅ Docker containers running (`docker ps` shows lynx-postgres)
- ✅ Database migrations applied (tables created)
- ✅ Python virtual environment activated (`(venv)` in prompt)
- ✅ Python dependencies installed (PyTorch, SBERT, etc.)
- ✅ Database connection test passed
- ✅ Test ingestion completed (5 concepts processed)
- ✅ Frontend loads at localhost:3000
- ✅ Search returns results for "artificial intelligence"

## 🔧 Troubleshooting Common Issues

### Issue: `npm install` fails
**Solution**: 
```powershell
# Check Node.js version
node --version
# Should be 20.x.x or higher

# Clear npm cache if needed
npm cache clean --force
npm install
```

### Issue: Docker containers won't start
**Solution**:
```powershell
# Make sure Docker Desktop is running
# Check if ports are free
netstat -an | findstr :5432
netstat -an | findstr :6379

# If ports are in use, stop other services or change ports
```

### Issue: Database migration fails
**Solution**:
```powershell
# Reset database
npm run docker:down
npm run docker:up

# Wait 30 seconds, then try again
cd apps\web
npm run db:migrate
```

### Issue: Python virtual environment not working
**Solution**:
```powershell
# Make sure you're using the right Python command
python --version
# or try:
py --version

# Create venv with full path
python -m venv venv

# Activate with full path
.\venv\Scripts\activate
```

### Issue: PyTorch installation fails
**Solution**:
```powershell
# Install PyTorch separately with CPU-only version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Then install other requirements
pip install sentence-transformers pandas numpy psycopg2-binary
```

### Issue: SBERT model download fails
**Solution**:
- Check internet connection
- The model is ~90MB, so it may take time
- If it fails, try running the test again - it will resume download

### Issue: Frontend shows errors
**Solution**:
```powershell
# Check browser console (F12)
# Common fixes:

# 1. Rebuild the frontend
npm run build

# 2. Clear browser cache (Ctrl+Shift+R)

# 3. Check if API is running
# Visit: http://localhost:3000/api/status
```

## 🎉 Success! What You've Built

If all tests pass, you now have:

- 🌌 **Beautiful galaxy interface** with semantic search
- 🗄️ **PostgreSQL database** with pgvector for embeddings
- 🤖 **SBERT embeddings** running locally (no API costs!)
- 🔍 **Semantic search** that finds related concepts
- 📊 **Real-time status** monitoring
- 🐍 **Python pipeline** for data ingestion
- 💰 **$0 API costs** for the MVP!

## 🚀 Next Steps

Now that everything works:

1. **Explore the interface** - try different searches
2. **Run larger ingestion**: `python scripts\ingestion\main.py --concepts 100`
3. **Check the database**: `cd apps\web && npm run db:studio`
4. **Review the code** - understand the architecture
5. **Start building features** - galaxy visualization, pathfinding, etc.

You're ready to build the knowledge galaxy! 🌟
