import { GalaxyVisualization } from '@/components/galaxy/galaxy-visualization';
import { SearchInterface } from '@/components/search/search-interface';
import { ConceptPanel } from '@/components/concept/concept-panel';
import { StatusBar } from '@/components/ui/status-bar';

export default function HomePage() {
  return (
    <main className="relative w-full h-screen overflow-hidden bg-galaxy-black">
      {/* Galaxy Visualization - Full Screen Background */}
      <div className="galaxy-container">
        <GalaxyVisualization />
      </div>

      {/* UI Overlay */}
      <div className="ui-overlay">
        {/* Top Navigation */}
        <header className="absolute top-0 left-0 right-0 z-20 p-6">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-galaxy-pink to-galaxy-gold rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">L</span>
              </div>
              <h1 className="text-2xl font-bold text-galaxy-white glow-text">
                LYNX
              </h1>
            </div>

            {/* Status Indicator */}
            <StatusBar />
          </div>
        </header>

        {/* Search Interface */}
        <div className="absolute top-24 left-6 right-[650px] z-20">
          <SearchInterface />
        </div>

        {/* Concept Detail Panel - Fixed positioning for proper height */}
        <div className="absolute top-32 right-6 w-[600px] h-[calc(100vh-200px)] z-20">
          <ConceptPanel />
        </div>

        {/* Bottom Controls */}
        <footer className="absolute bottom-0 left-0 right-0 z-20 p-6">
          <div className="flex items-center justify-between">
            {/* Navigation Hints */}
            <div className="flex items-center space-x-6 text-sm text-galaxy-white/60">
              <div className="flex items-center space-x-2">
                <kbd className="px-2 py-1 bg-galaxy-dark/50 rounded text-xs">
                  /
                </kbd>
                <span>Search</span>
              </div>
              <div className="flex items-center space-x-2">
                <kbd className="px-2 py-1 bg-galaxy-dark/50 rounded text-xs">
                  Click
                </kbd>
                <span>Select</span>
              </div>
              <div className="flex items-center space-x-2">
                <kbd className="px-2 py-1 bg-galaxy-dark/50 rounded text-xs">
                  Drag
                </kbd>
                <span>Navigate</span>
              </div>
            </div>

            {/* Version Info */}
            <div className="text-xs text-galaxy-white/40">
              LYNX v0.1.0 - MVP
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
