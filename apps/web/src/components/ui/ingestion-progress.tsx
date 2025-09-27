'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

interface IngestionStatus {
  totalConcepts: number;
  processedConcepts: number;
  totalEmbeddings: number;
  totalEdges: number;
  status: 'idle' | 'ingesting' | 'embedding' | 'building_graph' | 'complete' | 'error';
  lastUpdated: string;
  errorMessage?: string;
}

export function IngestionProgress() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['ingestion-status'],
    queryFn: async (): Promise<IngestionStatus> => {
      const response = await fetch('/api/ingestion/status');
      if (!response.ok) throw new Error('Failed to fetch status');
      return response.json();
    },
    refetchInterval: 2000, // Poll every 2 seconds during ingestion
    enabled: true,
  });

  if (isLoading || !status) {
    return null;
  }

  if (status.status === 'idle' || status.status === 'complete') {
    return null;
  }

  const progress = status.totalConcepts > 0 
    ? (status.processedConcepts / status.totalConcepts) * 100 
    : 0;

  const getStatusMessage = () => {
    switch (status.status) {
      case 'ingesting':
        return `Ingesting concepts: ${status.processedConcepts}/${status.totalConcepts}`;
      case 'embedding':
        return `Generating embeddings: ${status.totalEmbeddings} complete`;
      case 'building_graph':
        return `Building knowledge graph: ${status.totalEdges} connections`;
      case 'error':
        return `Error: ${status.errorMessage}`;
      default:
        return 'Processing...';
    }
  };

  return (
    <div className="fixed top-24 left-1/2 transform -translate-x-1/2 z-50">
      <div className="glass rounded-lg p-4 min-w-96 border border-galaxy-purple/30">
        <div className="flex items-center space-x-3 mb-3">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-galaxy-purple border-t-transparent" />
          <span className="text-galaxy-white font-medium">
            Building Knowledge Universe
          </span>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-galaxy-white/70">
            <span>{getStatusMessage()}</span>
            <span>{Math.round(progress)}%</span>
          </div>
          
          <div className="w-full bg-galaxy-dark/50 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-galaxy-purple to-galaxy-cyan h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          
          {status.status === 'complete' && (
            <div className="text-xs text-galaxy-green mt-2">
              🎉 Knowledge universe ready! {status.totalConcepts} concepts, {status.totalEdges} connections
            </div>
          )}
          
          {status.status === 'error' && (
            <div className="text-xs text-galaxy-red mt-2">
              ❌ {status.errorMessage}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
