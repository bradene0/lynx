# LYNX - Linked Knowledge Network Explorer 🌌

A semantic mapping and visualization platform that explores knowledge as a zoomable galaxy. LYNX demonstrates the intersection of semantic search, graph theory, and immersive visualization.

## ✨ Features

- **Interactive Galaxy Visualization**: Explore 10k-250k knowledge concepts in a beautiful 3D space
- **Semantic Search**: Find concepts using natural language with vector similarity
- **Pathfinding**: Discover connections between seemingly unrelated concepts
- **Wormhole Discovery**: Find cross-domain links that bridge different fields of knowledge
- **Real-time Exploration**: Smooth pan, zoom, and fly-to interactions

## 🚀 Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Three.js, D3.js, TailwindCSS
- **Backend**: Next.js API routes, Supabase Postgres + pgvector
- **Data Pipeline**: Python 3.11, OpenAI embeddings, NetworkX
- **Deployment**: Vercel + Supabase (~$20/month)

## 🏗️ Architecture

```
lynx/
├── apps/
│   └── web/                 # Next.js frontend + API routes
├── packages/
│   └── shared/              # Shared types and utilities
├── scripts/
│   └── ingestion/           # Python data pipeline
└── docs/                    # Documentation
```

## 🛠️ Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- Docker & Docker Compose

### Quick Start

1. **Clone and install dependencies**:
   ```bash
   git clone <repo-url>
   cd lynx
   npm install
   ```

2. **Set up environment** (No OpenAI API key needed!):
   ```bash
   cp .env.example .env
   # DATABASE_URL is auto-configured for local development
   ```

3. **Start local database**:
   ```bash
   npm run docker:up
   npm run db:migrate
   ```

4. **Install Python dependencies**:
   ```bash
   cd scripts/ingestion
   pip install -r requirements.txt
   cd ../..
   ```

5. **Quick test everything**:
   ```bash
   # Windows:
   scripts\quick-test.bat
   
   # Or manually:
   npm run dev
   ```

6. **Test with sample data**:
   ```bash
   python scripts/test-ingestion.py
   ```

📖 **Detailed setup instructions**: See [SETUP.md](SETUP.md)

## 📊 Data Sources

- **Wikipedia**: English summaries of notable concepts
- **arXiv**: Scientific paper abstracts from key domains
- **News**: Optional headlines for current events (future)

## 🎯 Roadmap

### Phase 1: MVP (Current)
- [x] Project structure and database schema
- [x] Data ingestion pipeline (Wikipedia + arXiv)
- [x] SBERT embedding generation (local, $0 cost!)
- [x] Basic galaxy visualization foundation
- [x] Semantic search functionality
- [ ] Enhanced Three.js galaxy rendering
- [ ] Graph construction and layout

### Phase 2: Advanced Features
- [ ] Pathfinding algorithms
- [ ] Wormhole discovery
- [ ] Clustering and community detection
- [ ] Performance optimizations

### Phase 3: User Features
- [ ] User authentication
- [ ] Saved maps and collections
- [ ] Export functionality
- [ ] Admin dashboard

### Phase 4: Polish
- [ ] Advanced visualizations
- [ ] Documentation site
- [ ] Public demo deployment

## 🔧 Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run docker:up` - Start local database
- `npm run db:migrate` - Run database migrations
- `npm run ingest` - Run data ingestion pipeline

## 📈 Performance Targets

- Search latency: <300ms P95
- Pathfinding: <1s for 50k-250k nodes
- Initial load: <2s
- Progressive rendering for smooth interaction

## 🤝 Contributing

This is currently a private development project. Once the MVP is complete, we'll open it up for contributions.

## 📄 License

MIT License - see LICENSE file for details.

---

**Built with ❤️ for the exploration of human knowledge**
