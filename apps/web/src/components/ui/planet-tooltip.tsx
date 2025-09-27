'use client';

import { useGalaxyStore } from '@/stores/galaxy-store';

export function PlanetTooltip() {
  const { nodes, hoveredNode } = useGalaxyStore();
  
  if (!hoveredNode) return null;
  
  const node = nodes.find(n => n.id === hoveredNode);
  if (!node) return null;

  return (
    <div className="fixed pointer-events-none z-50 transform -translate-x-1/2 -translate-y-full">
      <div className="glass rounded-lg p-3 max-w-xs shadow-xl border border-galaxy-purple/30">
        <h3 className="font-semibold text-galaxy-white text-sm mb-1">
          {node.title}
        </h3>
        {node.category && (
          <div className="flex items-center space-x-2 mb-2">
            <div 
              className="w-2 h-2 rounded-full" 
              style={{ backgroundColor: node.color }}
            />
            <span className="text-xs text-galaxy-white/70">
              {node.category}
            </span>
          </div>
        )}
        <p className="text-xs text-galaxy-white/80 line-clamp-3">
          {node.summary}
        </p>
      </div>
      {/* Arrow */}
      <div className="absolute top-full left-1/2 transform -translate-x-1/2">
        <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-galaxy-dark/80" />
      </div>
    </div>
  );
}
