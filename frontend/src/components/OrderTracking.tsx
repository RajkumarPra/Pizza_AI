import { useState, useEffect } from 'react';
import { Clock, CheckCircle, Truck, Pizza, User, History, Package, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';

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
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [previousOrderStatuses, setPreviousOrderStatuses] = useState<{[key: string]: string}>({});

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
      // First get user-specific orders
      const userResponse = await fetch(`${API_BASE}/user/${encodeURIComponent(userEmail)}/orders`);
      if (userResponse.ok) {
        const userData = await userResponse.json();
        const userOrders = userData.all_orders || [];
        
        // Also get all orders with updated status
        const statusResponse = await fetch(`${API_BASE}/orders/status-updates`);
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          const allUpdatedOrders = statusData.orders || [];
          
          // Merge user orders with updated status
          const updatedUserOrders = userOrders.map((userOrder: any) => {
            const updatedOrder = allUpdatedOrders.find((updated: any) => 
              updated.order_id === userOrder.order_id || updated.id === userOrder.order_id
            );
            return updatedOrder || userOrder;
          });
          
          // Check for status changes
          updatedUserOrders.forEach((order: any) => {
            const orderId = order.order_id || order.id;
            const currentStatus = order.status;
            const previousStatus = previousOrderStatuses[orderId];
            
            if (previousStatus && previousStatus !== currentStatus) {
              // Status changed - show notification
              console.log(`🔄 Order ${orderId} status changed from ${previousStatus} to ${currentStatus}`);
              // You could add a toast notification here
            }
          });
          
          // Update previous statuses
          const newStatuses: {[key: string]: string} = {};
          updatedUserOrders.forEach((order: any) => {
            const orderId = order.order_id || order.id;
            newStatuses[orderId] = order.status;
          });
          setPreviousOrderStatuses(newStatuses);
          
          setUserOrderHistory(updatedUserOrders);
          setLastUpdated(new Date());
        } else {
          // Fallback to just user orders
          setUserOrderHistory(userOrders);
          setLastUpdated(new Date());
        }
      }
    } catch (error) {
      console.error('Failed to load user order history:', error);
    } finally {
      setLoading(false);
    }
  };

  // Combine and sort all orders by timestamp (most recent first)
  const allOrders = [...orders, ...userOrderHistory].sort((a, b) => {
    const dateA = new Date(a.timestamp || a.created_at || 0);
    const dateB = new Date(b.timestamp || b.created_at || 0);
    return dateB.getTime() - dateA.getTime();
  });

  // Separate active orders from completed orders
  const activeOrders = allOrders.filter(order => {
    const status = order.status || 'placed';
    return ['placed', 'preparing', 'cooking'].includes(status);
  });

  const completedOrders = allOrders.filter(order => {
    const status = order.status || 'delivered';
    return ['ready', 'delivered'].includes(status);
  });

  // Poll for status updates every 5 seconds for active orders
  useEffect(() => {
    if (!userEmail) return;

    const interval = setInterval(() => {
      loadUserOrderHistory();
    }, 5000); // Poll every 5 seconds for more responsive updates

    return () => clearInterval(interval);
  }, [userEmail]);

  // Get the most recent active order for prominent display
  const latestActiveOrder = activeOrders[0];

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
              {(() => {
                try {
                  const date = new Date(order.timestamp);
                  if (isNaN(date.getTime())) {
                    return 'Order placed recently';
                  }
                  return `${date.toLocaleDateString()} at ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
                } catch (error) {
                  return 'Order placed recently';
                }
              })()}
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

  // If no active orders and no completed orders, show welcome message
  if (activeOrders.length === 0 && completedOrders.length === 0 && !loading) {
    return (
      <Card className="text-center py-12">
        <CardContent>
          <Pizza className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <CardTitle className="mb-2">No Orders Yet</CardTitle>
          <CardDescription className="mb-4">
            {userName ? `${userName}, you haven't placed any orders yet.` : "You haven't placed any orders yet."}
          </CardDescription>
          <p className="text-sm text-muted-foreground mb-4">
            When you place an order, you'll be able to track its progress here!
          </p>
          <Button 
            onClick={() => window.location.hash = 'menu'}
            className="bg-gradient-primary hover:opacity-90"
          >
            Browse Our Menu
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center">
            <Truck className="h-4 w-4 text-primary-foreground" />
          </div>
                  <div>
          <h2 className="text-xl font-semibold">Order Tracking</h2>
          <p className="text-sm text-muted-foreground">
            {activeOrders.length > 0 
              ? (userName ? `${userName}'s active orders` : 'Track your active pizza orders')
              : (userName ? `${userName}'s order history` : 'Your order history')
            }
            {lastUpdated && (
              <span className="block text-xs text-green-600 mt-1">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        
        {/* Manual refresh button */}
        <Button 
          onClick={loadUserOrderHistory}
          disabled={loading}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <div className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}>
            {loading ? '⟳' : '↻'}
          </div>
          {loading ? 'Updating...' : 'Refresh Now'}
        </Button>
        </div>
        

      </div>

      {/* No Active Orders Message */}
      {activeOrders.length === 0 && completedOrders.length > 0 && (
        <Card className="text-center py-8">
          <CardContent>
            <Package className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <CardTitle className="mb-2">No Active Orders</CardTitle>
            <CardDescription className="mb-4">
              {userName ? `${userName}, you don't have any active orders right now.` : "You don't have any active orders right now."}
            </CardDescription>
            <p className="text-sm text-muted-foreground mb-4">
              Check your completed orders below, or place a new order!
            </p>
            <Button 
              onClick={() => window.location.hash = 'menu'}
              className="bg-gradient-primary hover:opacity-90"
            >
              Place New Order
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Active Orders Section */}
      {activeOrders.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 rounded-full">
              <Clock className="h-4 w-4 text-green-600" />
              <span className="text-sm font-semibold text-green-700">
                Active Orders ({activeOrders.length})
              </span>
            </div>
            <div className="flex items-center gap-1 text-xs text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Live Updates</span>
            </div>
          </div>
          
          {/* Show all active orders */}
          {activeOrders.map((order, index) => (
            <div key={order.order_id || order.id || index} className={index === 0 ? "ring-2 ring-green-200 rounded-lg" : ""}>
              <OrderCard 
                order={{
                  ...order, 
                  id: order.order_id || order.id,
                  status: order.status || 'placed',
                  items: order.items || [],
                  total: order.total_price || order.total || 0,
                  estimatedTime: order.eta || order.estimatedTime || 25,
                  timestamp: new Date(order.timestamp || order.created_at || Date.now())
                }} 
                isActive={index === 0} 
              />
            </div>
          ))}
        </div>
      )}

      {/* Order History - Collapsible */}
      {completedOrders.length > 0 && (
        <Collapsible open={isHistoryOpen} onOpenChange={setIsHistoryOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="outline" className="w-full justify-between">
              <div className="flex items-center gap-2">
                <History className="h-4 w-4 text-gray-500" />
                <span>Completed Orders ({completedOrders.length})</span>
              </div>
              {isHistoryOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </CollapsibleTrigger>
          
          <CollapsibleContent className="space-y-4 mt-4">
            {completedOrders.map((order, index) => (
              <div key={order.order_id || order.id || index} className="opacity-80">
                <OrderCard 
                  order={{
                    ...order, 
                    id: order.order_id || order.id,
                    status: order.status || 'delivered',
                    items: order.items || [],
                    total: order.total_price || order.total || 0,
                    estimatedTime: order.eta || order.estimatedTime || 0,
                    timestamp: new Date(order.timestamp || order.created_at || Date.now())
                  }} 
                />
              </div>
            ))}
          </CollapsibleContent>
        </Collapsible>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
            <p className="text-sm text-muted-foreground">Loading order history...</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};