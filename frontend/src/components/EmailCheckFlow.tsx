import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Mail, User, Pizza } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface EmailCheckFlowProps {
  onUserConfirmed: (email: string, name?: string) => void;
}

interface UserData {
  email: string;
  name?: string;
  exists: boolean;
  orders_count: number;
  last_order_date?: string;
}

const API_BASE = 'http://localhost:8001/api';

export const EmailCheckFlow = ({ onUserConfirmed }: EmailCheckFlowProps) => {
  const [step, setStep] = useState<'email' | 'name' | 'loading'>('email');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [userData, setUserData] = useState<UserData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const isValidEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const checkEmail = async () => {
    if (!isValidEmail(email)) {
      toast({
        title: "Invalid email",
        description: "Please enter a valid email address.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    setStep('loading');

    try {
      const response = await fetch(`${API_BASE}/user/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        const data: UserData = await response.json();
        setUserData(data);
        
        if (data.exists && data.name) {
          // User exists with name, proceed directly
          toast({
            title: `Welcome back, ${data.name}!`,
            description: data.orders_count > 0 
              ? `We found ${data.orders_count} order${data.orders_count > 1 ? 's' : ''} in your history.`
              : "Ready to place your first order with Pizza Planet?",
            duration: 3000,
          });
          onUserConfirmed(email, data.name);
        } else if (data.exists && !data.name) {
          // User exists but no name, ask for name
          toast({
            title: "Welcome back to Pizza Planet!",
            description: "We remember your email. Could you tell us your name?",
          });
          setStep('name');
        } else {
          // New user, ask for name
          toast({
            title: "Welcome to Pizza Planet!",
            description: "We'd love to know your name for a personalized experience.",
          });
          setStep('name');
        }
      } else {
        throw new Error('Failed to check email');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to check email. Please try again.",
        variant: "destructive"
      });
      setStep('email');
    } finally {
      setIsLoading(false);
    }
  };

  const saveUserData = async () => {
    if (!name.trim()) {
      toast({
        title: "Name required",
        description: "Please enter your name.",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/user/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, name: name.trim() })
      });

      if (response.ok) {
        toast({
          title: `Welcome ${name}!`,
          description: "Glad to have you at Pizza Planet! Let's get you some delicious pizza!",
          duration: 3000,
        });
        onUserConfirmed(email, name.trim());
      } else {
        throw new Error('Failed to save user data');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save your information. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    checkEmail();
  };

  const handleNameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveUserData();
  };

  const skipName = () => {
    onUserConfirmed(email);
  };

  if (step === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-red-50">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center space-y-4">
              <Pizza className="h-12 w-12 text-orange-500 animate-spin" />
              <p className="text-lg font-medium">Checking your information...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (step === 'email') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-red-50">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <Pizza className="h-16 w-16 text-orange-500" />
            </div>
            <CardTitle className="text-2xl font-bold">Welcome to Pizza Planet!</CardTitle>
            <CardDescription>
              Enter your email to get started with personalized ordering and track your deliveries.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your.email@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
                disabled={isLoading}
              >
                Continue
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (step === 'name') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-red-50">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <User className="h-16 w-16 text-orange-500" />
            </div>
            <CardTitle className="text-2xl font-bold">
              {userData?.exists ? "Welcome back!" : "Nice to meet you!"}
            </CardTitle>
            <CardDescription>
              {userData?.exists 
                ? "We remember your email. What should we call you?"
                : "What's your name? We'd love to personalize your pizza experience."
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleNameSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Your Name
                </Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Button 
                  type="submit" 
                  className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
                  disabled={isLoading}
                >
                  Save & Continue
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  className="w-full"
                  onClick={skipName}
                  disabled={isLoading}
                >
                  Skip for now
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
}; 