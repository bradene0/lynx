# 🌌 LYNX Setup & Testing Guide

Complete instructions for setting up and testing LYNX - Linked Knowledge Network Explorer

## 📋 Prerequisites

### Required Software
- **Node.js 20+** - [Download here](https://nodejs.org/)
- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Docker Desktop** - [Download here](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download here](https://git-scm.com/)

### Hardware Requirements
- **RAM**: 8GB minimum (16GB recommended for full dataset)
- **Storage**: 5GB free space
- **CPU**: Multi-core recommended for SBERT processing

## 🚀 Quick Setup (15 minutes)

### Step 1: Clone and Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd lynx

# Install Node.js dependencies
npm install
```

### Step 2: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file - you can leave OPENAI_API_KEY empty for SBERT!
# Only DATABASE_URL is required for local development
```

**Important**: With SBERT, you **don't need** an OpenAI API key! 🎉

### Step 3: Start Database

```bash
# Start PostgreSQL with pgvector
npm run docker:up

# Wait 30 seconds for database to initialize
# Then run migrations
npm run db:migrate
```

### Step 4: Install Python Dependencies

```bash
cd scripts/ingestion

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (this may take 5-10 minutes)
pip install -r requirements.txt
```

**Note**: PyTorch installation may take time. If it fails, try:
```bash
# Install PyTorch separately first
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Then install the rest
pip install -r requirements.txt
```

### Step 5: Test the Setup

```bash
# Go back to project root
cd ../..

# Start the development server
npm run dev
```

Visit `http://localhost:3000` - you should see the beautiful galaxy interface! ✨

## 🧪 Testing Guide

### Test 1: Basic Functionality (2 minutes)

1. **Frontend Test**:
   - Open `http://localhost:3000`
   - ✅ Galaxy interface loads
   - ✅ Search bar is visible
   - ✅ Status bar shows "0 concepts • 0 embeddings • 0 edges"

2. **API Test**:
   - Visit `http://localhost:3000/api/status`
   - ✅ Returns JSON with status information

### Test 2: Database Connection (1 minute)

```bash
# Open database studio
cd apps/web
npm run db:studio
```

- ✅ Studio opens at `http://localhost:4983`
- ✅ You can see empty tables: `concepts`, `embeddings`, `edges`

### Test 3: Mini Data Pipeline (5 minutes)

```bash
# Run the test ingestion (fetches 5 Wikipedia articles)
python scripts/test-ingestion.py
```

**Expected Output**:
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
✅ SBERT model loaded successfully
✅ Generated 5 embeddings
🎉 Pipeline test completed successfully!
```

### Test 4: Search Functionality (2 minutes)

1. **Refresh the web interface** at `http://localhost:3000`
2. **Check status bar** - should show "5 concepts • 5 embeddings • 0 edges"
3. **Search test**:
   - Type "artificial intelligence" in search bar
   - ✅ Should return search results
   - ✅ Click on a result to see concept details

## 🔧 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `npm install` fails | Check Node.js version: `node --version` (need 20+) |
| Docker won't start | Ensure Docker Desktop is running |
| Database connection fails | Check `DATABASE_URL` in `.env` file |
| PyTorch install fails | Install PyTorch separately first (see Step 4) |
| SBERT model download fails | Check internet connection, model downloads ~90MB |
| Port 3000 in use | Kill process: `npx kill-port 3000` |
| Port 5432 in use | Stop other PostgreSQL instances |

### Reset Everything

If something goes wrong, reset with:

```bash
# Stop all services
npm run docker:down

# Clean install
rm -rf node_modules
npm install

# Restart database
npm run docker:up
npm run db:migrate
```

### Performance Issues

If SBERT is slow:
- **CPU**: SBERT uses CPU by default (normal for first run)
- **Memory**: Close other applications if running low on RAM
- **First run**: Model download + compilation takes extra time

## 📊 Full Dataset Testing (Optional)

Once basic testing works, try larger datasets:

### Small Dataset (100 concepts, ~2 minutes)
```bash
python scripts/ingestion/main.py --concepts 100
```

### Medium Dataset (1000 concepts, ~10 minutes)
```bash
python scripts/ingestion/main.py --concepts 1000
```

### Full MVP Dataset (10000 concepts, ~45 minutes)
```bash
python scripts/ingestion/main.py --concepts 10000
```

## 🎯 Success Criteria

Your setup is working if:

- ✅ **Frontend loads** with galaxy interface
- ✅ **Database connected** and migrations run
- ✅ **SBERT model loads** without errors
- ✅ **Test pipeline** completes successfully
- ✅ **Search returns results** for ingested concepts
- ✅ **No API costs** (SBERT runs locally!)

## 🚀 Next Steps

Once testing passes:

1. **Explore the interface** - search for different concepts
2. **Run larger ingestion** - try 1000 concepts
3. **Check the galaxy visualization** - basic Three.js rendering
4. **Review the code** - understand the architecture

## 💡 Development Tips

### Useful Commands

```bash
# Development
npm run dev              # Start dev server
npm run build           # Build for production

# Database
npm run docker:up       # Start database
npm run docker:down     # Stop database
npm run db:migrate      # Run migrations
npm run db:studio       # Open database studio

# Data Pipeline
python scripts/test-ingestion.py           # Quick test
python scripts/ingestion/main.py           # Full pipeline
```

### File Structure
```
lynx/
├── apps/web/           # Next.js frontend + API
├── packages/shared/    # Shared TypeScript types
├── scripts/ingestion/  # Python data pipeline
├── scripts/sql/        # Database schema
└── docs/              # Documentation
```

## 🎉 You're Ready!

If all tests pass, you have a working LYNX foundation with:
- 🌌 Beautiful galaxy-themed interface
- 🔍 Semantic search with SBERT embeddings
- 📊 Real-time status monitoring
- 💾 PostgreSQL + pgvector database
- 🐍 Python ingestion pipeline
- 💰 **$0 API costs** for MVP!

Happy exploring the knowledge galaxy! 🌟
