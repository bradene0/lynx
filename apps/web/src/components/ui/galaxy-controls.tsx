'use client';

import { useState } from 'react';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { 
  AdjustmentsHorizontalIcon, 
  SparklesIcon 
} from '@heroicons/react/24/outline';

export function GalaxyControls() {
  const { edgeThreshold, setEdgeThreshold } = useGalaxyStore();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="absolute bottom-6 left-6 z-30">
      {/* Control Panel */}
      <div className={`glass rounded-xl p-4 transition-all duration-300 ${
        isOpen ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'
      }`}>
        <div className="space-y-4 w-64">
          {/* Edge Visibility Control */}
          <div>
            <label className="block text-sm font-medium text-galaxy-white mb-3">
              Connection Visibility
            </label>
            <div className="flex space-x-1 bg-galaxy-dark/50 rounded-lg p-1">
              {(['high', 'medium', 'low'] as const).map((level) => (
                <button
                  key={level}
                  onClick={() => setEdgeThreshold(level)}
                  className={`flex-1 px-3 py-2 text-xs font-medium rounded-md transition-all ${
                    edgeThreshold === level
                      ? 'bg-galaxy-purple text-white shadow-lg'
                      : 'text-galaxy-white/60 hover:text-galaxy-white hover:bg-galaxy-purple/20'
                  }`}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
            <div className="mt-2 text-xs text-galaxy-white/50">
              {edgeThreshold === 'high' && 'Only strongest connections'}
              {edgeThreshold === 'medium' && 'Moderate connections'}
              {edgeThreshold === 'low' && 'All discovered connections'}
            </div>
          </div>

          {/* Dataset Info */}
          <div className="text-xs text-galaxy-white/50 bg-galaxy-dark/30 rounded-lg p-3">
            <div className="flex items-center space-x-2 mb-2">
              <SparklesIcon className="h-3 w-3" />
              <span className="font-medium">Knowledge Galaxy</span>
            </div>
            <div className="space-y-1">
              <div>📚 9,422 Concepts</div>
              <div>🔬 34 Knowledge Domains</div>
              <div>🧠 SBERT Embeddings (384D)</div>
              <div>⚡ LOD System (5 Levels)</div>
              <div>🔗 Semantic Connections</div>
            </div>
            <div className="mt-2 pt-2 border-t border-galaxy-white/10">
              <div className="text-xs text-galaxy-white/40">
                {edgeThreshold === 'high' && 'Showing strongest connections (>0.7 similarity)'}
                {edgeThreshold === 'medium' && 'Showing moderate connections (>0.5 similarity)'}
                {edgeThreshold === 'low' && 'Showing all connections (>0.3 similarity)'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Toggle Button - Made more visible */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`mt-3 bg-galaxy-purple/30 border border-galaxy-purple/50 rounded-full p-3 hover:bg-galaxy-purple/40 transition-all shadow-lg ${
          isOpen ? 'bg-galaxy-purple/40' : ''
        }`}
        style={{ backdropFilter: 'blur(10px)' }}
      >
        <AdjustmentsHorizontalIcon className="h-5 w-5 text-galaxy-white" />
      </button>
    </div>
  );
}
