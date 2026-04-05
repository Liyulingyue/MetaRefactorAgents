import { useCallback } from 'react';
import type { Message } from '../types';

const STORAGE_KEY = 'chat_histories';

export const loadHistories = (): Record<string, Message[]> => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : {};
  } catch {
    return {};
  }
};

const saveHistories = (histories: Record<string, Message[]>) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(histories));
  } catch (e) {
    console.error('Failed to save chat history', e);
  }
};

export function useChatHistory() {
  const load = useCallback(() => loadHistories(), []);

  const save = useCallback((histories: Record<string, Message[]>) => {
    saveHistories(histories);
  }, []);

  const clear = useCallback((histories: Record<string, Message[]>, agentId: string) => {
    const newHistories = { ...histories, [agentId]: [] };
    saveHistories(newHistories);
    return newHistories;
  }, []);

  return { load, save, clear };
}
