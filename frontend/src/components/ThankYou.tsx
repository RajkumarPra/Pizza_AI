import { useState, useEffect } from 'react';
import { CheckCircle, Pizza, Clock, MapPin, User } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface OrderItem {
  id: string;
  name: string;
  size: string;
  price: number;
  quantity: number;
}

interface Order {
  id: string;
  items: OrderItem[];
  status: string;
  total: number;
  estimatedTime: number | string;
  timestamp: Date;
}

interface ThankYouProps {
  order: Order;
  userName?: string;
  onViewTracking: () => void;
}

const ThankYou = ({ order, userName, onViewTracking }: ThankYouProps) => {
  const [showAnimation, setShowAnimation] = useState(false);
  const [currentStage, setCurrentStage] = useState(0);
  
  const stages = [
    { icon: CheckCircle, label: "Order Confirmed", color: "text-green-500" },
    { icon: Pizza, label: "Preparing", color: "text-orange-500" },
    { icon: Clock, label: "Cooking", color: "text-blue-500" },
    { icon: MapPin, label: "Ready for Delivery", color: "text-purple-500" }
  ];

  useEffect(() => {
    setShowAnimation(true);
    
    // Simulate progression through stages
    const progressInterval = setInterval(() => {
      setCurrentStage(prev => {
        if (prev < stages.length - 1) {
          return prev + 1;
        } else {
          clearInterval(progressInterval);
          // Auto navigate to tracking after animation
          setTimeout(() => {
            onViewTracking();
          }, 3000);
          return prev;
        }
      });
    }, 2000);

    return () => clearInterval(progressInterval);
  }, [onViewTracking, stages.length]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
      <Card className={`w-full max-w-md transform transition-all duration-1000 ${
        showAnimation ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
      }`}>
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 p-3 bg-green-100 rounded-full w-fit">
            <CheckCircle className="h-12 w-12 text-green-500" />
          </div>
          <CardTitle className="text-2xl text-green-600 mb-2">
            🎉 Thank You{userName ? `, ${userName}` : ''}!
          </CardTitle>
          <p className="text-gray-600">
            Your order has been placed successfully at Pizza Planet!
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Order Summary */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-800 mb-3">Order Summary</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Order #</span>
                <Badge variant="outline">{order.id}</Badge>
              </div>
              {order.items.map((item, index) => (
                <div key={index} className="flex justify-between items-center">
                  <span className="text-sm">{item.name} ({item.size})</span>
                  <span className="text-sm font-medium">${item.price.toFixed(2)}</span>
                </div>
              ))}
              <div className="border-t pt-2 flex justify-between items-center font-bold">
                <span>Total</span>
                <span>${order.total.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Progress Animation */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-800 text-center">
              Preparing your pizza...
            </h3>
            <div className="space-y-3">
              {stages.map((stage, index) => {
                const Icon = stage.icon;
                const isActive = index <= currentStage;
                const isCurrent = index === currentStage;
                
                return (
                  <div
                    key={index}
                    className={`flex items-center space-x-3 transition-all duration-500 ${
                      isActive ? 'opacity-100' : 'opacity-40'
                    }`}
                  >
                    <div className={`p-2 rounded-full ${
                      isActive ? 'bg-orange-100' : 'bg-gray-100'
                    } ${isCurrent ? 'animate-pulse' : ''}`}>
                      <Icon className={`h-5 w-5 ${
                        isActive ? stage.color : 'text-gray-400'
                      }`} />
                    </div>
                    <span className={`text-sm ${
                      isActive ? 'text-gray-800 font-medium' : 'text-gray-500'
                    }`}>
                      {stage.label}
                    </span>
                    {isCurrent && (
                      <div className="ml-auto">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-orange-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* ETA */}
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <Clock className="h-6 w-6 text-blue-500 mx-auto mb-2" />
            <p className="text-sm text-blue-700">
              Estimated delivery: <span className="font-bold">
                {typeof order.estimatedTime === 'string' ? order.estimatedTime : `${order.estimatedTime} minutes`}
              </span>
            </p>
          </div>

          {/* Auto redirect message */}
          <p className="text-xs text-gray-500 text-center">
            Redirecting to order tracking in a few seconds...
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ThankYou; 