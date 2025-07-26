import { useState, useEffect } from 'react';
import { Clock, CheckCircle, Truck, Pizza, User, History, Package } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';

export type OrderStatus = 'placed' | 'preparing' | 'cooking' | 'ready' | 'delivered';

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
  status: OrderStatus;
  total: number;
  estimatedTime: number;
  timestamp: Date;
  progress?: number;
}

interface OrderTrackingProps {
  orders: Order[];
  userEmail?: string;
  userName?: string;
  onOrderSelect?: (orderId: string) => void;
}

const API_BASE = 'http://localhost:8001/api';

export const OrderTracking = ({ orders, userEmail, userName, onOrderSelect }: OrderTrackingProps) => {
  const [userOrderHistory, setUserOrderHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Load user-specific order history
  useEffect(() => {
    if (userEmail) {
      loadUserOrderHistory();
    }
  }, [userEmail]);

  const loadUserOrderHistory = async () => {
    if (!userEmail) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/user/${encodeURIComponent(userEmail)}/orders`);
      if (response.ok) {
        const data = await response.json();
        setUserOrderHistory(data.all_orders || []);
      }
    } catch (error) {
      console.error('Failed to load user order history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: OrderStatus) => {
    switch (status) {
      case 'placed':
        return <CheckCircle className="h-5 w-5 text-blue-500" />;
      case 'preparing':
        return <Clock className="h-5 w-5 text-yellow-500" />;
      case 'cooking':
        return <Pizza className="h-5 w-5 text-orange-500" />;
      case 'ready':
        return <Package className="h-5 w-5 text-green-500" />;
      case 'delivered':
        return <Truck className="h-5 w-5 text-green-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: OrderStatus) => {
    switch (status) {
      case 'placed':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'preparing':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'cooking':
        return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'ready':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'delivered':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const StatusProgressBar = ({ statusProgression }: { statusProgression?: any }) => {
    if (!statusProgression) return null;

    return (
      <div className="space-y-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Order Progress</span>
          <span className="text-sm text-gray-500">{statusProgression.progress_percentage}%</span>
        </div>
        
        <Progress 
          value={statusProgression.progress_percentage} 
          className="w-full h-2"
        />
        
        <div className="grid grid-cols-5 gap-1 text-xs">
          {statusProgression.steps?.map((step: any, index: number) => (
            <div 
              key={index} 
              className={`text-center ${step.completed ? 'text-green-600' : 'text-gray-400'}`}
            >
              <div className={`text-lg ${step.active ? 'animate-pulse' : ''}`}>
                {step.emoji}
              </div>
              <div className="mt-1">{step.label}</div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const getStatusMessage = (status: OrderStatus) => {
    switch (status) {
      case 'placed':
        return 'Your order has been placed and confirmed!';
      case 'preparing':
        return 'Our chefs are preparing your delicious pizza!';
      case 'cooking':
        return 'Your pizza is cooking in our wood-fired oven!';
      case 'ready':
        return 'Your order is ready for pickup/delivery!';
      case 'delivered':
        return 'Your order has been delivered. Enjoy!';
      default:
        return 'Processing your order...';
    }
  };

  // Order Card Component
  const OrderCard = ({ order, isActive = false }: { order: any, isActive?: boolean }) => (
    <Card className={`${isActive ? 'ring-2 ring-blue-500 bg-blue-50' : ''}`}>
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              {getStatusIcon(order.status)}
              Order #{order.order_id}
            </CardTitle>
            <CardDescription className="mt-1">
              {new Date(order.timestamp).toLocaleDateString()} at{' '}
              {new Date(order.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </CardDescription>
          </div>
          <Badge className={getStatusColor(order.status)}>
            {order.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Order Items */}
        <div className="space-y-2">
          {order.items?.map((item: any, index: number) => (
            <div key={index} className="flex justify-between items-center text-sm">
              <span>{item.name} ({item.size})</span>
              <span className="font-medium">${item.price?.toFixed(2)}</span>
            </div>
          ))}
          <div className="border-t pt-2 flex justify-between items-center font-bold">
            <span>Total</span>
            <span>${order.total_price?.toFixed(2)}</span>
          </div>
        </div>

        {/* Status Progress Bar */}
        {order.status_progression && (
          <StatusProgressBar statusProgression={order.status_progression} />
        )}

        {/* ETA Display */}
        {order.eta && order.status !== 'delivered' && (
          <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
            <Clock className="h-4 w-4 text-blue-500" />
            <div className="text-sm">
              <span className="text-blue-700 font-medium">ETA: </span>
              <span className="text-blue-600">{order.eta}</span>
            </div>
          </div>
        )}

        {/* Status Message */}
        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
          {getStatusMessage(order.status)}
        </div>
      </CardContent>
    </Card>
  );

  // Separate current and completed orders
  const currentOrders = userOrderHistory.filter(order => 
    ['placed', 'preparing', 'cooking', 'ready'].includes(order.status)
  );
  
  const completedOrders = userOrderHistory.filter(order => 
    ['delivered', 'completed'].includes(order.status)
  );

  // If no orders and no user order history, show welcome message
  if (orders.length === 0 && userOrderHistory.length === 0 && !loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <div className="mx-auto mb-4 p-3 bg-orange-100 rounded-full w-fit">
              <Pizza className="h-12 w-12 text-orange-500" />
            </div>
            <CardTitle className="text-xl text-orange-600">
              Welcome{userName ? `, ${userName}` : ''}!
            </CardTitle>
            <CardDescription className="text-base mt-2">
              You don't have any ongoing orders yet. Ready to try one of our delicious specials? 🍕
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={() => window.location.hash = 'menu'}
              className="w-full bg-orange-500 hover:bg-orange-600"
            >
              Browse Our Menu
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // If no user email, show general tracking
  if (!userEmail) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Order Tracking</h2>
          <p className="text-muted-foreground">Track your pizza orders in real-time</p>
        </div>
        
        {orders.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center">
              <Pizza className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No orders to track</h3>
              <p className="text-muted-foreground">Place an order to start tracking!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {orders.map((order) => (
              <OrderCard key={order.id} order={order} />
            ))}
          </div>
        )}
      </div>
    );
  }

  // Show personalized tracking for logged-in users
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2 flex items-center justify-center gap-2">
          <User className="h-6 w-6" />
          {userName ? `${userName}'s Orders` : 'Your Orders'}
        </h2>
        <p className="text-muted-foreground">Track and manage your pizza orders</p>
      </div>

      {/* No orders message */}
      {userOrderHistory.length === 0 && (
        <Card className="border-dashed border-2">
          <CardContent className="pt-6 text-center">
            <Pizza className="h-16 w-16 mx-auto mb-4 text-orange-500" />
            <h3 className="text-lg font-semibold mb-2">
              Welcome{userName ? `, ${userName}` : ''}! 🍕
            </h3>
            <p className="text-muted-foreground mb-4">
              Looks like you haven't placed an order yet. Let us know if you're craving something!
            </p>
            <Button 
              className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
              onClick={() => window.location.hash = '#menu'}
            >
              View Menu
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Current Orders */}
      {orders.length > 0 && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Pizza className="h-5 w-5 text-orange-500" />
              Your Current Order is Being Prepared!
            </h2>
            <div className="space-y-4">
              {orders.map((order) => (
                <OrderCard key={order.id} order={order} isActive={true} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* User Order History */}
      {userOrderHistory.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <History className="h-5 w-5 text-gray-500" />
            Order History
          </h3>
          <div className="space-y-4">
            {userOrderHistory.map((order) => (
              <OrderCard key={order.order_id} order={order} isActive={false} />
            ))}
          </div>
        </div>
      )}
      
      {loading && (
        <Card>
          <CardContent className="pt-6 text-center">
            <Pizza className="h-8 w-8 mx-auto mb-2 text-orange-500 animate-spin" />
            <p className="text-muted-foreground">Loading your orders...</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};