import { GalaxyVisualization } from '@/components/galaxy/galaxy-visualization';
import { SearchInterface } from '@/components/search/search-interface';
import { ConceptPanel } from '@/components/concept/concept-panel';
import { StatusBar } from '@/components/ui/status-bar';

export default function HomePage() {
  return (
    <main className="relative w-full h-screen overflow-hidden bg-galaxy-black">
      {/* Apple-style Gradient Border - Below Top Bar */}
      <div className="absolute top-20 left-2 right-2 bottom-2 z-10">
        <div className="w-full h-full rounded-xl border-2 border-transparent bg-gradient-to-r from-blue-500 via-purple-500 via-pink-400 via-blue-400 to-blue-600 p-[2px] animate-gradient-x">
          <div className="w-full h-full rounded-xl bg-galaxy-black">
            {/* Galaxy Visualization - Inside Gradient Border */}
            <div className="galaxy-container w-full h-full rounded-xl overflow-hidden">
              <GalaxyVisualization />
            </div>
          </div>
        </div>
      </div>

      {/* UI Overlay */}
      <div className="ui-overlay">
        {/* Top Navigation - Centered Layout */}
        <header className="absolute top-0 left-0 right-0 z-20 p-6">
          <div className="flex items-center justify-center space-x-8">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-galaxy-pink to-galaxy-gold rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-sm">L</span>
              </div>
              <h1 className="text-2xl font-bold text-galaxy-white glow-text">
                LYNX
              </h1>
            </div>

            {/* Centered Search Interface */}
            <div className="flex-1 max-w-2xl">
              <SearchInterface />
            </div>

            {/* Status Indicator */}
            <StatusBar />
          </div>
        </header>

        {/* Concept Detail Panel - Adjusted for new layout */}
        <div className="absolute top-28 right-8 w-[600px] h-[calc(100vh-200px)] z-20">
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
