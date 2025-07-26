import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Volume2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

// Declare Speech Recognition types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
    speechTimeout: NodeJS.Timeout | null;
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
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const recognitionRef = useRef<any>(null);
  const { toast } = useToast();

  // Memoize callbacks to prevent unnecessary re-renders
  const handleVoiceInput = useCallback((text: string) => {
    onVoiceInput(text);
  }, [onVoiceInput]);

  const handleSpeechStart = useCallback(() => {
    onSpeechStart?.();
  }, [onSpeechStart]);

  const handleSpeechEnd = useCallback(() => {
    onSpeechEnd?.();
  }, [onSpeechEnd]);

  const testMicrophonePermission = useCallback(async () => {
    if (hasPermission !== null) return; // Already tested
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone permission granted');
      setHasPermission(true);
      // Stop the stream immediately
      stream.getTracks().forEach(track => track.stop());
    } catch (error) {
      console.log('❌ Microphone permission denied or not available');
      setHasPermission(false);
    }
  }, [hasPermission]);

  // Initialize speech recognition only once
  useEffect(() => {
    if (isInitialized) return; // Prevent multiple initializations
    
    console.log('🎤 Initializing voice recognition...');
    
    // Check if Speech Recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const supported = !!SpeechRecognition;
    setIsSupported(supported);
    
    if (supported) {
      console.log('✅ Speech Recognition is supported');

      // Check if running on HTTPS or localhost (required for speech recognition)
      const isSecure = location.protocol === 'https:' || location.hostname === 'localhost';
      if (!isSecure) {
        console.warn('⚠️ Speech Recognition requires HTTPS or localhost');
        toast({
          title: "Voice input requires HTTPS",
          description: "Voice recognition only works on secure connections.",
          variant: "destructive"
        });
        setIsSupported(false);
        setIsInitialized(true);
        return;
      }

      try {
      const recognition = new SpeechRecognition();
        // Improved settings for better accuracy and reduced latency
        recognition.continuous = true; // Enable continuous listening
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 3; // Increase alternatives for better accuracy
        
        // Add timing settings to prevent premature cutoff
        if ('webkitSpeechRecognition' in window) {
          // @ts-ignore - WebKit specific settings
          recognition.webkitGrammars = null;
          // @ts-ignore
          recognition.webkitContinuous = true;
        }

      recognition.onstart = () => {
          console.log('🎤 Speech recognition started');
        setIsListening(true);
          handleSpeechStart();
          toast({
            title: "Listening...",
            description: "Speak now! I'm listening to your voice.",
            duration: 3000 // Increased duration
          });
      };

      recognition.onresult = (event) => {
          console.log('📝 Speech recognition result:', event);
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
            const confidence = event.results[i][0].confidence;
            
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
              console.log(`✅ Final transcript: "${transcript}" (confidence: ${confidence})`);
          } else {
            interimTranscript += transcript;
            console.log(`🔄 Interim transcript: "${transcript}"`);
          }
        }
        
        // Only process final transcript and ensure minimum length
        if (finalTranscript.trim() && finalTranscript.trim().length > 1) {
            console.log(`🎉 Sending voice input: "${finalTranscript}"`);
            handleVoiceInput(finalTranscript.trim());
          recognition.stop();
        }
        
        // Continue listening if we only have interim results
        if (!finalTranscript && interimTranscript) {
          console.log('🔄 Still listening for complete phrase...');
        }
      };

      recognition.onend = () => {
          console.log('🛑 Speech recognition ended');
        setIsListening(false);
          handleSpeechEnd();
      };

      recognition.onerror = (event) => {
          console.error('❌ Speech recognition error:', event.error);
          setIsListening(false);
          handleSpeechEnd();
          
          let errorMessage = '';
          let toastVariant: "default" | "destructive" = "destructive";
          
          switch(event.error) {
            case 'no-speech':
              // Don't show error for no-speech, just silently restart
              console.log('🤫 No speech detected, stopping gracefully');
              return; // Don't show toast for this
            case 'audio-capture':
              errorMessage = 'Microphone error. Please check if your microphone is connected and working.';
              break;
            case 'not-allowed':
              errorMessage = 'Microphone access denied. Please allow microphone access and try again.';
              setHasPermission(false);
              break;
            case 'network':
              errorMessage = 'Network error. Please check your internet connection.';
              break;
            case 'service-not-allowed':
              errorMessage = 'Speech recognition service not allowed. Please try again.';
              break;
            case 'aborted':
              // Don't show error for aborted (user clicked stop)
              console.log('🛑 Speech recognition aborted by user');
              return;
            default:
              errorMessage = `Speech recognition error: ${event.error}`;
          }
          
          // Only show toast if we have an error message
          if (errorMessage) {
            toast({
              title: "Voice input error",
              description: errorMessage,
              variant: toastVariant
            });
          }
      };

      recognition.onspeechstart = () => {
          console.log('🗣️ Speech detected');
          // Clear any existing timeout when speech starts
          if (window.speechTimeout) {
            clearTimeout(window.speechTimeout);
          }
      };

      recognition.onspeechend = () => {
          console.log('🤫 Speech ended');
          // Add a short delay before stopping to catch any final words
          window.speechTimeout = setTimeout(() => {
            if (recognition && isListening) {
              console.log('⏰ Speech timeout reached, stopping recognition');
              recognition.stop();
            }
          }, 1500); // Wait 1.5 seconds after speech ends
      };

      recognitionRef.current = recognition;
        
        // Test microphone permission on component mount
        testMicrophonePermission();
        
      } catch (error) {
        console.error('❌ Failed to initialize speech recognition:', error);
        setIsSupported(false);
      }
    } else {
      console.log('❌ Speech Recognition not supported in this browser');
      toast({
        title: "Voice input not supported",
        description: "Please use Chrome, Edge, or Safari for voice input.",
        variant: "destructive"
      });
    }

    setIsInitialized(true);

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isInitialized, handleVoiceInput, handleSpeechStart, handleSpeechEnd, testMicrophonePermission, toast]);

  const toggleListening = async () => {
    if (!recognitionRef.current || !isSupported) {
      console.log('❌ Recognition not available');
      return;
    }

    if (isListening) {
      console.log('🛑 Stopping voice recognition...');
      recognitionRef.current.stop();
      return;
    }

    try {
      console.log('🎤 Requesting microphone permission...');
      
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone permission granted, starting speech recognition');
      setHasPermission(true);
      
      // Stop the stream immediately - we just needed permission
      stream.getTracks().forEach(track => track.stop());
      
      // Start speech recognition
        recognitionRef.current.start();
      
      } catch (error) {
      console.error('❌ Microphone permission denied:', error);
      setHasPermission(false);
      
      toast({
        title: "Microphone access required",
        description: "Please allow microphone access to use voice input. Click the microphone icon in your browser's address bar.",
        variant: "destructive",
        duration: 5000
      });
    }
  };

  // Show different states based on support and permission
  if (!isSupported) {
    return (
      <Button variant="outline" disabled className={cn("opacity-50", className)}>
        <Volume2 className="h-4 w-4" />
        <span className="sr-only">Voice not supported</span>
      </Button>
    );
  }

  if (hasPermission === false) {
    return (
      <Button
        variant="outline"
        onClick={toggleListening}
        className={cn("text-destructive hover:text-destructive", className)}
        title="Microphone permission required"
      >
        <AlertCircle className="h-4 w-4" />
        <span className="sr-only">Microphone permission required</span>
      </Button>
    );
  }

  return (
    <Button
      variant={isListening ? "default" : "outline"}
      onClick={toggleListening}
      className={cn(
        "relative transition-all duration-300",
        isListening ? "voice-button-listening" : "voice-button-idle",
        className
      )}
      title={isListening ? 'Stop listening' : 'Start voice input'}
    >
      {isListening ? (
        <Mic className="h-4 w-4" />
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