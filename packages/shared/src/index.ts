// Export all types and schemas
export * from './types';

// Utility functions
export const formatDistance = (distance: number): string => {
  if (distance < 0.001) return '< 0.001';
  return distance.toFixed(3);
};

export const formatSimilarity = (similarity: number): string => {
  return `${(similarity * 100).toFixed(1)}%`;
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
};

export const generateId = (): string => {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

// Constants
export const EMBEDDING_DIMENSIONS = 3072;
export const DEFAULT_KNN_K = 12;
export const DEFAULT_SIMILARITY_THRESHOLD = 0.6;
export const MAX_NEIGHBORS_PER_NODE = 20;
export const SEARCH_RESULTS_LIMIT = 100;
