'use client';

import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { type SearchResponse } from '@lynx/shared';

export function SearchInterface() {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const { highlightSearchResults, clearSearchHighlight, flyToNode } = useGalaxyStore();

  const { data: searchResults, isLoading, error } = useQuery({
    queryKey: ['search', query],
    queryFn: async (): Promise<SearchResponse> => {
      const response = await fetch(`/api/search?query=${encodeURIComponent(query)}&limit=10`);
      if (!response.ok) {
        throw new Error('Search failed');
      }
      return response.json();
    },
    enabled: query.length > 2,
    staleTime: 30000, // 30 seconds
  });

  const handleSearch = useCallback((searchQuery: string) => {
    setQuery(searchQuery);
    if (searchQuery.length > 2) {
      setIsOpen(true);
    } else {
      setIsOpen(false);
      clearSearchHighlight();
    }
  }, [clearSearchHighlight]);

  const handleSelectResult = useCallback((conceptId: string) => {
    flyToNode(conceptId);
    setIsOpen(false);
    setQuery('');
    // Delay clearing highlight so user can see the golden effect
    setTimeout(() => {
      clearSearchHighlight();
    }, 2000); // Keep highlight for 2 seconds
  }, [flyToNode, clearSearchHighlight]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setQuery('');
      clearSearchHighlight();
    }
  }, [clearSearchHighlight]);

  // Highlight search results in the galaxy when they arrive
  useEffect(() => {
    if (searchResults && searchResults.results.length > 0) {
      const resultIds = searchResults.results.map(result => result.concept.id);
      highlightSearchResults(resultIds);
    } else if (query.length <= 2) {
      clearSearchHighlight();
    }
  }, [searchResults, query, highlightSearchResults, clearSearchHighlight]);

  return (
    <div className="relative w-full">
      {/* Search Input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-galaxy-white/60" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length > 2 && setIsOpen(true)}
          placeholder="Search the knowledge galaxy... (Press / to focus)"
          className="search-input w-full pl-10 pr-4 py-3 rounded-xl text-galaxy-white placeholder-galaxy-white/60 focus:outline-none focus:ring-2 focus:ring-galaxy-pink/50"
        />
        {isLoading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <div className="spinner w-5 h-5"></div>
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {isOpen && searchResults && searchResults.results.length > 0 && (
        <div className="absolute top-full mt-2 w-full glass rounded-xl shadow-2xl border border-galaxy-purple/30 max-h-96 overflow-y-auto z-50">
          <div className="p-2">
            <div className="text-xs text-galaxy-white/60 px-3 py-2">
              Found {searchResults.total} results in {searchResults.took_ms}ms
            </div>
            {searchResults.results.map((result) => (
              <button
                key={result.concept.id}
                onClick={() => handleSelectResult(result.concept.id)}
                className="w-full text-left p-3 rounded-lg hover:bg-galaxy-purple/20 transition-colors group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-galaxy-white font-medium group-hover:text-galaxy-pink transition-colors">
                      {result.concept.title}
                    </h3>
                    <p className="text-galaxy-white/70 text-sm mt-1 line-clamp-2">
                      {result.concept.summary}
                    </p>
                    <div className="flex items-center mt-2 space-x-3 text-xs">
                      <span className="text-galaxy-cyan">
                        {result.concept.source}
                      </span>
                      {result.concept.category && (
                        <span className="text-galaxy-gold">
                          {result.concept.category}
                        </span>
                      )}
                      <span className="text-galaxy-white/50">
                        {(result.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {isOpen && searchResults && searchResults.results.length === 0 && query.length > 2 && (
        <div className="absolute top-full mt-2 w-full glass rounded-xl shadow-2xl border border-galaxy-purple/30 p-6 text-center">
          <p className="text-galaxy-white/70">
            No concepts found for "{query}"
          </p>
          <p className="text-galaxy-white/50 text-sm mt-1">
            Try a different search term or check the spelling
          </p>
        </div>
      )}
    </div>
  );
}
