'use client';

import { useQuery } from '@tanstack/react-query';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { type ConceptDetail } from '@lynx/shared';
import { ArrowTopRightOnSquareIcon, SparklesIcon } from '@heroicons/react/24/outline';

export function ConceptPanel() {
  const { selectedNode, flyToNode } = useGalaxyStore();

  const { data: conceptDetail, isLoading } = useQuery({
    queryKey: ['concept', selectedNode],
    queryFn: async (): Promise<ConceptDetail> => {
      const response = await fetch(`/api/concept/${selectedNode}`);
      if (!response.ok) {
        throw new Error('Failed to fetch concept details');
      }
      return response.json();
    },
    enabled: !!selectedNode,
  });

  if (!selectedNode) {
    return (
      <div className="glass rounded-xl p-6 h-full flex items-center justify-center">
        <div className="text-center">
          <SparklesIcon className="h-12 w-12 text-galaxy-white/30 mx-auto mb-4" />
          <p className="text-galaxy-white/60">
            Select a concept to explore its connections
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="glass rounded-xl p-6 h-full flex items-center justify-center">
        <div className="spinner w-8 h-8"></div>
      </div>
    );
  }

  if (!conceptDetail) {
    return (
      <div className="glass rounded-xl p-6 h-full flex items-center justify-center">
      </div>
    );
  }

  return (
    <div className="glass rounded-xl h-full overflow-hidden">
      <div className="p-8 h-full flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 mb-6">
        <div className="flex items-start justify-between mb-3">
          <h2 className="text-xl font-bold text-galaxy-white glow-text">
            {conceptDetail.concept.title}
          </h2>
          <a
            href={conceptDetail.concept.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-galaxy-cyan hover:text-galaxy-pink transition-colors"
          >
            <ArrowTopRightOnSquareIcon className="h-5 w-5" />
          </a>
        </div>
        
        <div className="flex items-center space-x-3 text-sm mb-4">
          <span className="px-2 py-1 bg-galaxy-cyan/20 text-galaxy-cyan rounded-full">
            {conceptDetail.concept.source}
          </span>
          {conceptDetail.concept.category && (
            <span className="px-2 py-1 bg-galaxy-gold/20 text-galaxy-gold rounded-full">
              {conceptDetail.concept.category}
            </span>
          )}
        </div>

        </div>

        {/* Single Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto pr-2">
          {/* Article Summary */}
          <div className="mb-8">
            <p className="text-galaxy-white/90 text-base leading-relaxed">
              {conceptDetail.concept.summary}
            </p>
          </div>

          {/* Wormholes Section */}
          {conceptDetail.wormholes.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-galaxy-pink mb-4 flex items-center">
                <SparklesIcon className="h-5 w-5 mr-2" />
                Wormholes
              </h3>
              <p className="text-galaxy-white/60 text-sm mb-4">
                Cross-domain connections that bridge different fields of knowledge
              </p>
              <div className="space-y-3">
                {conceptDetail.wormholes.map((wormhole, index) => (
                  <div
                    key={index}
                    className="concept-card p-4 rounded-lg cursor-pointer hover:bg-galaxy-purple/10 transition-colors"
                    onClick={() => {
                      // TODO: Navigate to wormhole target
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-galaxy-white">
                        {wormhole.target.title}
                      </h4>
                      <span className="text-sm text-galaxy-pink font-medium">
                        {(wormhole.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-galaxy-white/70 text-sm line-clamp-2 mb-3">
                      {wormhole.target.summary}
                    </p>
                    <div className="flex items-center space-x-2 text-xs">
                      <span className="text-galaxy-cyan">{wormhole.source_category}</span>
                      <span className="text-galaxy-white/40">→</span>
                      <span className="text-galaxy-gold">{wormhole.target_category}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Connected Concepts Section - At Bottom */}
          <div className="border-t border-galaxy-purple/20 pt-6">
            <h3 className="text-lg font-semibold text-galaxy-white mb-4">
              Connected Concepts ({conceptDetail.neighbors.length})
            </h3>
            <p className="text-galaxy-white/60 text-sm mb-4">
              Explore related concepts discovered through semantic similarity
            </p>
            <div className="space-y-3">
              {conceptDetail.neighbors.slice(0, 10).map((neighbor) => (
                <div
                  key={neighbor.concept.id}
                  className="concept-card p-4 rounded-lg cursor-pointer hover:bg-galaxy-cyan/10 transition-colors border border-galaxy-cyan/20"
                  onClick={() => {
                    // Navigate to connected concept with smooth animation
                    flyToNode(neighbor.concept.id);
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-galaxy-white">
                      {neighbor.concept.title}
                    </h4>
                    <div className="flex items-center space-x-3">
                      <span className="text-xs text-galaxy-white/50 bg-galaxy-dark/50 px-2 py-1 rounded">
                        {neighbor.edge_type}
                      </span>
                      <span className="text-sm text-galaxy-cyan font-medium">
                        {(neighbor.similarity * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-galaxy-white/70 text-sm line-clamp-2 mb-3">
                    {neighbor.concept.summary}
                  </p>
                  {neighbor.concept.category && (
                    <span className="inline-block px-3 py-1 bg-galaxy-purple/20 text-galaxy-purple text-xs rounded-full">
                      {neighbor.concept.category}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
