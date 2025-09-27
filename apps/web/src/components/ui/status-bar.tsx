'use client';

import { useQuery } from '@tanstack/react-query';
import { type IngestionStatus } from '@lynx/shared';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  ArrowPathIcon 
} from '@heroicons/react/24/outline';

export function StatusBar() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['ingestion-status'],
    queryFn: async (): Promise<IngestionStatus> => {
      const response = await fetch('/api/ingestion/status');
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      return response.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading || !status) {
    return (
      <div className="flex items-center space-x-2 text-galaxy-white/60">
        <div className="spinner w-4 h-4"></div>
        <span className="text-sm">Loading...</span>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'complete':
        return <CheckCircleIcon className="h-4 w-4 text-green-400" />;
      case 'error':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-400" />;
      case 'idle':
        return <CheckCircleIcon className="h-4 w-4 text-galaxy-cyan" />;
      default:
        return <ArrowPathIcon className="h-4 w-4 text-galaxy-gold animate-spin" />;
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'ingesting':
        return 'Ingesting data...';
      case 'embedding':
        return 'Generating embeddings...';
      case 'building_graph':
        return 'Building graph...';
      case 'complete':
        return 'Ready';
      case 'error':
        return 'Error';
      default:
        return 'Idle';
    }
  };

  const getProgressPercentage = () => {
    if (status.total_concepts === 0) return 0;
    return Math.round((status.processed_concepts / status.total_concepts) * 100);
  };

  return (
    <div className="glass rounded-lg px-4 py-2">
      <div className="flex items-center space-x-3">
        {getStatusIcon()}
        <div className="text-sm">
          <div className="flex items-center space-x-2">
            <span className="text-galaxy-white font-medium">
              {getStatusText()}
            </span>
            {status.status !== 'idle' && status.status !== 'complete' && status.status !== 'error' && (
              <span className="text-galaxy-white/60">
                {getProgressPercentage()}%
              </span>
            )}
          </div>
          <div className="text-galaxy-white/60 text-xs">
            {status.total_concepts.toLocaleString()} concepts • {' '}
            {status.total_embeddings.toLocaleString()} embeddings • {' '}
            {status.total_edges.toLocaleString()} edges
          </div>
        </div>
      </div>
      
      {/* Progress Bar */}
      {status.status !== 'idle' && status.status !== 'complete' && status.status !== 'error' && (
        <div className="mt-2 w-full bg-galaxy-dark/50 rounded-full h-1">
          <div 
            className="bg-gradient-to-r from-galaxy-cyan to-galaxy-pink h-1 rounded-full transition-all duration-300"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>
      )}
    </div>
  );
}
