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

2. **Start local database**:
   ```bash
   npm run docker:up
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key and other configs
   ```

4. **Run database migrations**:
   ```bash
   npm run db:migrate
   ```

5. **Start development server**:
   ```bash
   npm run dev
   ```

6. **Ingest initial data** (optional):
   ```bash
   npm run ingest
   ```

## 📊 Data Sources

- **Wikipedia**: English summaries of notable concepts
- **arXiv**: Scientific paper abstracts from key domains
- **News**: Optional headlines for current events (future)

## 🎯 Roadmap

### Phase 1: MVP (Current)
- [x] Project structure and database schema
- [ ] Data ingestion pipeline (Wikipedia + arXiv)
- [ ] OpenAI embedding generation
- [ ] Basic galaxy visualization
- [ ] Semantic search functionality

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
