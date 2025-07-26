import { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent } from '@/components/ui/card';
import { VoiceButton } from './VoiceButton';
import { Badge } from '@/components/ui/badge';

export interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  intent?: string;
  suggestedItems?: any[];
}

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  onVoiceInput: (text: string) => void;
  isProcessing: boolean;
  className?: string;
}

const API_BASE = 'http://localhost:8001/api'; // MCP Server

export const ChatInterface = ({ 
  messages, 
  onSendMessage, 
  onVoiceInput,
  isProcessing,
  className 
}: ChatInterfaceProps) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isProcessing) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    
    // Send message to backend instead of local processing
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          user_id: 'frontend_user'
        })
      });

      if (response.ok) {
        const data = await response.json();
        // The parent component will handle the response through onSendMessage
        onSendMessage(userMessage);
      } else {
        console.error('Failed to send message to backend');
        onSendMessage(userMessage); // Fallback to local processing
      }
    } catch (error) {
      console.error('Error sending message:', error);
      onSendMessage(userMessage); // Fallback to local processing
    }
  };

  const handleVoiceResult = (text: string) => {
    onVoiceInput(text);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card className={`flex flex-col h-full ${className}`}>
      <CardContent className="flex flex-col h-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-border/50">
          <div>
            <h2 className="text-xl font-semibold">Pizza AI Assistant</h2>
            <p className="text-sm text-muted-foreground">Ask me anything about our menu or place an order!</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="bg-green-100 text-green-700">
              Online
            </Badge>
        </div>
      </div>

        {/* Messages */}
        <ScrollArea className="flex-1 pr-4 chat-scrollbar">
          <div className="space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-gradient-primary text-primary-foreground ml-4'
                      : 'bg-muted mr-4'
                  }`}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  
                  {/* Show suggested items if available */}
                  {message.suggestedItems && message.suggestedItems.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <p className="text-xs opacity-75">Suggested items:</p>
                      {message.suggestedItems.map((item, index) => (
                        <div key={index} className="text-xs bg-white/10 rounded p-2">
                          <div className="font-medium">{item.name} ({item.size})</div>
                          <div className="opacity-75">${item.price}</div>
                          {item.description && (
                            <div className="opacity-60 mt-1">{item.description}</div>
                          )}
            </div>
                      ))}
          </div>
        )}

                  <div className={`text-xs mt-2 opacity-60 ${
                    message.type === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    {formatTime(message.timestamp)}
              </div>
            </div>
          </div>
        ))}
        
        {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-3 mr-4">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
                    <span className="text-sm text-muted-foreground">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
        </ScrollArea>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-2 pt-4 border-t border-border/50">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message or use voice..."
            disabled={isProcessing}
            className="flex-1"
          />
          <VoiceButton onVoiceInput={handleVoiceResult} />
          <Button 
            type="submit" 
            disabled={!inputValue.trim() || isProcessing}
            className="bg-gradient-primary hover:opacity-90"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};