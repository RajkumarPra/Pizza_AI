import { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Declare Speech Recognition types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface VoiceButtonProps {
  onVoiceInput: (text: string) => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  className?: string;
}

export const VoiceButton = ({ 
  onVoiceInput, 
  onSpeechStart, 
  onSpeechEnd, 
  className 
}: VoiceButtonProps) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check if Speech Recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
        onSpeechStart?.();
      };

      recognition.onresult = (event) => {
        console.log('Speech recognition result event:', event);
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          }
        }
        
        if (finalTranscript.trim()) {
          console.log('Final transcript:', finalTranscript);
          onVoiceInput(finalTranscript);
          recognition.stop();
        }
      };

      recognition.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
        onSpeechEnd?.();
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
          console.log('No speech detected, please speak louder or closer to microphone');
        } else if (event.error === 'audio-capture') {
          console.error('Audio capture error - check microphone');
        } else if (event.error === 'not-allowed') {
          console.error('Speech recognition not allowed');
        }
        setIsListening(false);
        onSpeechEnd?.();
      };

      recognition.onspeechstart = () => {
        console.log('Speech detected');
      };

      recognition.onspeechend = () => {
        console.log('Speech ended');
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [onVoiceInput, onSpeechStart, onSpeechEnd]);

  const toggleListening = async () => {
    if (!recognitionRef.current || !isSupported) return;

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      try {
        // Request microphone permission first
        await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('Microphone permission granted, starting speech recognition');
        recognitionRef.current.start();
      } catch (error) {
        console.error('Microphone permission denied or not available:', error);
        alert('Microphone access is required for voice input. Please allow microphone access and try again.');
      }
    }
  };

  if (!isSupported) {
    return (
      <Button variant="outline" disabled className={cn("opacity-50", className)}>
        <Volume2 className="h-4 w-4" />
        <span className="sr-only">Voice not supported</span>
      </Button>
    );
  }

  return (
    <Button
      variant={isListening ? "default" : "outline"}
      onClick={toggleListening}
      className={cn(
        "relative transition-all duration-300",
        isListening && "animate-pulse-voice shadow-voice bg-gradient-primary",
        className
      )}
    >
      {isListening ? (
        <Mic className="h-4 w-4 text-primary-foreground" />
      ) : (
        <MicOff className="h-4 w-4" />
      )}
      <span className="sr-only">
        {isListening ? 'Stop listening' : 'Start voice input'}
      </span>
      
      {isListening && (
        <div className="absolute inset-0 rounded-md bg-gradient-primary opacity-20 animate-ping" />
      )}
    </Button>
  );
};