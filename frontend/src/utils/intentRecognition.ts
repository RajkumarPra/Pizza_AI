import { ChatMessage } from '@/components/ChatInterface';
import { MenuItem } from '@/components/MenuComponent';

export type Intent = 'order' | 'menu' | 'track' | 'schedule' | 'general' | 'greeting' | 'direct_order';

export interface IntentResult {
  intent: Intent;
  confidence: number;
  entities?: Record<string, string>;
  menuCategory?: 'all' | 'veg' | 'non-veg';
  directOrderItem?: MenuItem;
}

// Note: Intent recognition is now handled by the MCP backend server
// This file is kept for type definitions and legacy compatibility
export function recognizeIntent(message: string): IntentResult {
  // Simple fallback - the MCP backend handles all actual intent recognition
  return {
    intent: 'general',
    confidence: 0.5,
    menuCategory: 'all'
  };
}

function extractMenuCategory(text: string): 'all' | 'veg' | 'non-veg' {
  if (/\b(veg|vegetarian)\b/i.test(text) && !/\bnon[- ]?veg/i.test(text)) {
    return 'veg';
  }
  if (/\b(non[- ]?veg|meat|chicken|pepperoni)\b/i.test(text)) {
    return 'non-veg';
  }
  return 'all';
}

// Legacy export for compatibility
export { extractMenuCategory };