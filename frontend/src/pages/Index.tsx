import { useState, useEffect, useCallback } from 'react';
import { Pizza, MessageSquare } from 'lucide-react';
import { ChatInterface, ChatMessage } from '@/components/ChatInterface';
import { MenuComponent, MenuItem } from '@/components/MenuComponent';
import { OrderTracking, OrderStatus } from '@/components/OrderTracking';
import { EmailCheckFlow } from '@/components/EmailCheckFlow';
import ThankYou from '@/components/ThankYou';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

const API_BASE = 'http://localhost:8001/api'; // MCP Server

interface OrderItem extends MenuItem {
  quantity: number;
}

interface Order {
  id: string;
  items: OrderItem[];
  status: OrderStatus;
  total: number;
  estimatedTime: number;
  timestamp: Date;
}

const Index = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentView, setCurrentView] = useState<'chat' | 'menu' | 'track' | 'schedule' | 'thankyou'>('menu');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentOrder, setCurrentOrder] = useState<OrderItem[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [awaitingOrderNumber, setAwaitingOrderNumber] = useState(false);
  const [menuCategory, setMenuCategory] = useState<'all' | 'veg' | 'non-veg'>('all');
  const [recentOrder, setRecentOrder] = useState<Order | null>(null);
  const [menuItems, setMenuItems] = useState<MenuItem[]>([]);
  const [showThankYou, setShowThankYou] = useState(false);
  
  // User management state
  const [userEmail, setUserEmail] = useState<string>('');
  const [userName, setUserName] = useState<string>('');
  const [isUserConfirmed, setIsUserConfirmed] = useState(false);
  const [userOrderHistory, setUserOrderHistory] = useState<any[]>([]);
  
  const { toast } = useToast();

  // Handle user confirmation from email check flow
  const handleUserConfirmed = useCallback(async (email: string, name?: string) => {
    setUserEmail(email);
    setUserName(name || '');
    setIsUserConfirmed(true);
    
    // Store in localStorage for future visits
    localStorage.setItem('pizza_ai_email', email);
    if (name) {
      localStorage.setItem('pizza_ai_name', name);
    }
    
    // Load user order history
    try {
      const response = await fetch(`${API_BASE}/user/${encodeURIComponent(email)}/orders`);
      if (response.ok) {
        const orderData = await response.json();
        setUserOrderHistory(orderData.all_orders || []);
        
        // Set orders for tracking
        const formattedOrders: Order[] = orderData.all_orders.map((order: any) => ({
          id: order.order_id,
          items: order.items.map((item: any) => ({ ...item, quantity: 1 })),
          status: order.status,
          total: order.total_price,
          estimatedTime: 25,
          timestamp: new Date()
        }));
        setOrders(formattedOrders);
        
        // Set most recent order
        if (formattedOrders.length > 0) {
          setRecentOrder(formattedOrders[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load user order history:', error);
    }

    // Get personalized greeting and add to chat
    try {
      const greetingResponse = await fetch(`${API_BASE}/user/${encodeURIComponent(email)}/greeting?context=returning`);
      if (greetingResponse.ok) {
        const greetingData = await greetingResponse.json();
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          type: 'bot',
          content: greetingData.greeting,
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Failed to get personalized greeting:', error);
      const greeting = name ? `Welcome back, ${name}! How can I help you today?` : "Welcome! How can I help you today?";
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        type: 'bot',
        content: greeting,
        timestamp: new Date()
      }]);
    }
  }, []);

  // Check for stored user data on component mount
  useEffect(() => {
    const storedEmail = localStorage.getItem('pizza_ai_email');
    const storedName = localStorage.getItem('pizza_ai_name');
    
    if (storedEmail) {
      handleUserConfirmed(storedEmail, storedName || undefined);
    }
  }, [handleUserConfirmed]);

  // Load menu from backend
  useEffect(() => {
    const loadMenu = async () => {
      try {
        const response = await fetch(`${API_BASE}/menu`);
        if (response.ok) {
          const data = await response.json();
          console.log('📡 MCP Menu Response:', data);
          setMenuItems(data.pizzas || []);
        }
      } catch (error) {
        console.error('Failed to load menu:', error);
        toast({
          title: "Error loading menu",
          description: "Please check your connection and try again.",
          variant: "destructive"
        });
      }
    };

    loadMenu();
  }, [toast]);

  // Live status simulation for recent orders
  useEffect(() => {
    if (!recentOrder) return;

    const statusFlow: OrderStatus[] = ['placed', 'preparing', 'cooking', 'ready'];
    let currentStatusIndex = statusFlow.indexOf(recentOrder.status);

    const interval = setInterval(() => {
      if (currentStatusIndex < statusFlow.length - 1) {
        currentStatusIndex++;
        const newStatus = statusFlow[currentStatusIndex];
        const newEstimatedTime = Math.max(0, recentOrder.estimatedTime - 5);
        
        setRecentOrder(prev => prev ? {
          ...prev,
          status: newStatus,
          estimatedTime: newEstimatedTime
        } : null);

        // Update in orders array too
        setOrders(prev => prev.map(order => 
          order.id === recentOrder.id 
            ? { ...order, status: newStatus, estimatedTime: newEstimatedTime }
            : order
        ));

        // Add status update message
        const statusMessages = {
          preparing: `Great news! Your order #${recentOrder.id} is now being prepared by our kitchen team.`,
          cooking: `Your order #${recentOrder.id} is now cooking in the oven! 🔥`,
          ready: `Excellent! Your order #${recentOrder.id} is ready for delivery! 🚚`
        };

        if (statusMessages[newStatus]) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            type: 'bot',
            content: statusMessages[newStatus],
            timestamp: new Date()
          }]);
        }
      } else {
        clearInterval(interval);
      }
    }, 8000); // Update every 8 seconds

    return () => clearInterval(interval);
  }, [recentOrder]);

  const addMessage = useCallback((content: string, type: 'user' | 'bot', intent?: string, suggestedItems?: any[]) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      intent,
      suggestedItems,
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const createInstantOrder = useCallback(async (item: MenuItem) => {
    try {
      const response = await fetch(`${API_BASE}/order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: [item.name],
          address: "123 Main Street", // Default address for demo
          phone: "555-0123", // Default phone for demo
          user_id: "frontend_user",
          email: userEmail || "guest@pizza-planet.com"
        })
      });

      if (response.ok) {
        const orderData = await response.json();
        console.log('📡 MCP Order Response:', orderData);
        
    const newOrder: Order = {
          id: orderData.order_id,
      items: [{ ...item, quantity: 1 }],
      status: 'placed',
          total: orderData.total_price,
          estimatedTime: orderData.estimated_time || "being calculated", // Use dynamic ETA
      timestamp: new Date()
    };

    setOrders(prev => [...prev, newOrder]);
    setRecentOrder(newOrder);
    setCurrentOrder([]); // Clear any existing cart
    setCurrentView('track');

    toast({
      title: "Order placed instantly! 🎉",
      description: `${item.name} (${item.size}) - $${item.price.toFixed(2)}`,
      duration: 4000,
    });

    return newOrder;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to place order');
      }
    } catch (error) {
      console.error('Error creating order:', error);
      toast({
        title: "Error placing order",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive"
      });
      return null;
    }
  }, [toast, userEmail]);

  const handleAddToOrder = useCallback((item: MenuItem) => {
    const existingItem = currentOrder.find(orderItem => orderItem.id === item.id);
    
    if (existingItem) {
      setCurrentOrder(prev => 
        prev.map(orderItem => 
          orderItem.id === item.id 
            ? { ...orderItem, quantity: orderItem.quantity + 1 }
            : orderItem
        )
      );
    } else {
      setCurrentOrder(prev => [...prev, { ...item, quantity: 1 }]);
    }

    toast({
      title: "Added to order!",
      description: `${item.name} (${item.size}) - $${item.price.toFixed(2)}`,
    });

    // Add bot response
    addMessage(`Great! I've added ${item.name} (${item.size}) to your order. Your current total is $${
      (currentOrder.reduce((sum, item) => sum + (item.price * item.quantity), 0) + item.price).toFixed(2)
    }. Would you like to add anything else?`, 'bot');
  }, [currentOrder, addMessage, toast]);

  const handleSendMessage = useCallback(async (message: string) => {
    addMessage(message, 'user');
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          user_id: 'frontend_user',
          context: {
            email: userEmail,
            name: userName
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('📡 MCP Chat Response:', data);

        // Add bot response with suggested items if available
        addMessage(data.response, 'bot', data.intent, data.suggested_items);

        // Handle view changes and actions based on MCP response
        switch (data.action) {
          case 'show_menu':
            setCurrentView('menu');
            if (data.context?.category) {
              setMenuCategory(data.context.category);
            }
            break;
            
          case 'show_tracking':
            // If order data is provided in context, navigate directly
            if (data.context?.order_data) {
      setCurrentView('track');
      setAwaitingOrderNumber(false);
            } else if (data.context?.agent_used === 'scheduler_agent') {
              // If scheduler agent was used but no order found, stay in chat
              setAwaitingOrderNumber(false);
            } else {
              // Waiting for order number
              setAwaitingOrderNumber(true);
            }
            break;
            
          case 'show_schedule':
            setCurrentView('schedule');
            break;
            
          case 'await_confirmation':
            // MCP backend is awaiting confirmation - no additional action needed
            // The pending order is stored in the backend
            break;
            
          case 'order_placed':
            // Order was successfully placed through MCP
            if (data.context?.order_data && data.context?.order_id) {
              const orderData = data.context.order_data;
              const newOrder: Order = {
                id: orderData.id,
                items: orderData.items.map((item: any) => ({ ...item, quantity: 1 })),
                status: orderData.status,
                total: orderData.total_price,
                estimatedTime: orderData.estimated_time || "being calculated", // Use dynamic ETA
                timestamp: new Date()
              };
              
              setOrders(prev => [...prev, newOrder]);
              setRecentOrder(newOrder);
              setCurrentOrder([]); // Clear any pending order
              setShowThankYou(true);
              setCurrentView('thankyou'); // Show thank you page first
              
              toast({
                title: "Order placed successfully! 🎉",
                description: `Order #${newOrder.id} - Total: $${newOrder.total.toFixed(2)}`,
                duration: 4000,
              });
            }
            break;
            
          case 'confirm_order':
          case 'process_order':
            // Handle legacy order confirmation (keeping for backward compatibility)
            if (data.suggested_items && data.suggested_items.length === 1) {
              const orderItem = data.suggested_items[0];
              const menuItem = menuItems.find(item => 
                item.id === orderItem.id || 
                (item.name === orderItem.name && item.size === orderItem.size)
              );
              
              if (menuItem) {
                // Store the pending order item for confirmation
                setCurrentOrder([{ ...menuItem, quantity: 1 }]);
              }
            }
            break;
            
          case 'show_healthy_options':
        setCurrentView('menu');
            setMenuCategory('veg'); // Show vegetarian options for health queries
        break;
        }

        // Handle tracking with automatic order ID detection
        if (data.intent === 'track' && data.context?.order_id) {
          // Order was found and tracking info provided - show it directly
          setCurrentView('track');
          setAwaitingOrderNumber(false);
        }

      } else {
        throw new Error('Failed to get response from MCP server');
      }
    } catch (error) {
      console.error('Error communicating with MCP server:', error);
      addMessage('I apologize, but I had trouble processing your request. Please try again or let me know how else I can help!', 'bot');
    }

    setIsProcessing(false);
  }, [addMessage, currentOrder, createInstantOrder, menuItems, userEmail, userName]);

  const handleVoiceInput = useCallback((text: string) => {
    toast({
      title: "Voice input received",
      description: `"${text}"`,
    });
    handleSendMessage(text);
  }, [handleSendMessage, toast]);

  const placeOrder = useCallback(async () => {
    if (currentOrder.length === 0) return;

    try {
      // Send just the pizza names, not formatted strings
      const itemNames = currentOrder.map(item => item.name);
      
      const response = await fetch(`${API_BASE}/order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          items: itemNames,
          address: "123 Main Street", // Default address for demo
          phone: "555-0123", // Default phone for demo
          user_id: "frontend_user",
          email: userEmail || "guest@pizza-planet.com"
        })
      });

      if (response.ok) {
        const orderData = await response.json();

    const total = currentOrder.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const newOrder: Order = {
          id: orderData.order_id,
      items: currentOrder,
      status: 'placed',
      total,
          estimatedTime: orderData.estimated_time || "being calculated", // Use dynamic ETA
      timestamp: new Date()
    };

    setOrders(prev => [...prev, newOrder]);
    setRecentOrder(newOrder);
    setCurrentOrder([]);
    setCurrentView('track');

    toast({
      title: "Order placed successfully!",
      description: `Order #${newOrder.id} - Total: $${total.toFixed(2)}`,
    });

    addMessage(`Perfect! Your order has been placed. Order #${newOrder.id} for $${total.toFixed(2)}. I'll track it for you!`, 'bot');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to place order');
      }
    } catch (error) {
      console.error('Error placing order:', error);
      toast({
        title: "Error placing order",
        description: error instanceof Error ? error.message : "Please try again.",
        variant: "destructive"
      });
    }
  }, [currentOrder, toast, addMessage, userEmail]);

  const handleViewTracking = useCallback(() => {
    setShowThankYou(false);
    setCurrentView('track');
  }, []);

  const handleLogout = useCallback(() => {
    // Clear localStorage
    localStorage.removeItem('pizza_ai_email');
    localStorage.removeItem('pizza_ai_name');
    
    // Clear all state
    setUserEmail('');
    setUserName('');
    setIsUserConfirmed(false);
    setUserOrderHistory([]);
    setOrders([]);
    setRecentOrder(null);
    setMessages([]);
    setCurrentOrder([]);
    setShowThankYou(false);
    setCurrentView('menu');
    
    // Show confirmation toast
    toast({
      title: "Logged out successfully!",
      description: "You can now sign in with a different account.",
      duration: 3000,
    });
  }, [toast]);

  const handleClearUserData = useCallback(() => {
    // Clear localStorage
    localStorage.removeItem('pizza_ai_email');
    localStorage.removeItem('pizza_ai_name');
    
    // Clear all state
    setUserEmail('');
    setUserName('');
    setIsUserConfirmed(false);
    setUserOrderHistory([]);
    setOrders([]);
    setRecentOrder(null);
    setMessages([]);
    setCurrentOrder([]);
    setShowThankYou(false);
    setCurrentView('menu');
    
    // Show confirmation toast
    toast({
      title: "User data cleared!",
      description: "You can now test with a new user.",
      duration: 3000,
    });
  }, [toast]);

  // Show email check flow if user is not confirmed
  if (!isUserConfirmed) {
    return <EmailCheckFlow onUserConfirmed={handleUserConfirmed} />;
  }

  // Show thank you page after order confirmation
  if (showThankYou && recentOrder) {
    return (
      <ThankYou 
        order={recentOrder} 
        userName={userName} 
        onViewTracking={handleViewTracking}
      />
    );
  }



  const renderActionPanel = () => {
    switch (currentView) {
      case 'menu':
        return (
          <div className="space-y-4">
            <MenuComponent onAddToOrder={handleAddToOrder} category={menuCategory} menuItems={menuItems} />
            
            {currentOrder.length > 0 && (
              <Card className="border-primary/20 bg-primary/5">
                <CardHeader>
                  <CardTitle className="text-lg">Current Order</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 mb-4">
                    {currentOrder.map((item) => (
                      <div key={item.id} className="flex justify-between text-sm">
                        <span>{item.quantity}x {item.name} ({item.size})</span>
                        <span>${(item.price * item.quantity).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between font-bold text-lg border-t pt-2">
                    <span>Total:</span>
                    <span>${currentOrder.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}</span>
                  </div>
                  <Button 
                    onClick={placeOrder}
                    className="w-full mt-4 bg-gradient-primary hover:opacity-90"
                  >
                    Place Order
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        );
      
      case 'track':
        return (
          <OrderTracking
            orders={orders}
            userEmail={userEmail}
            userName={userName}
          />
        );
      
      case 'schedule':
        return (
          <Card>
            <CardHeader>
              <CardTitle>Schedule Delivery</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                Delivery scheduling feature coming soon! For now, our standard delivery time is 25-30 minutes.
              </p>
              <Button 
                onClick={() => setCurrentView('menu')}
                className="bg-gradient-primary hover:opacity-90"
              >
                Order Now for Standard Delivery
              </Button>
            </CardContent>
          </Card>
        );
      
      case 'chat':
      default:
        return (
          <Card className="h-full flex items-center justify-center">
            <CardContent className="text-center py-12">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h3 className="font-semibold mb-2">Welcome to Pizza AI!</h3>
              <p className="text-muted-foreground mb-4">
                Use the chat panel on the left to interact with me, or explore our menu and tracking options here.
              </p>
              <div className="flex gap-2 justify-center">
                <Button 
                  onClick={() => setCurrentView('menu')}
                  className="bg-gradient-primary hover:opacity-90"
                >
                  Browse Menu
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => setCurrentView('track')}
                >
                  Track Orders
                </Button>
              </div>
            </CardContent>
          </Card>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-warm">
      {/* Header */}
      <header className="bg-card border-b border-border/50 shadow-elegant">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-primary flex items-center justify-center">
                <Pizza className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Pizza AI</h1>
                <p className="text-sm text-muted-foreground">
                  {userName ? `Welcome back, ${userName}!` : 'Your intelligent pizza assistant'}
                </p>
              </div>
            </div>
            
            {/* Navigation and User Actions */}
            <div className="flex items-center gap-3">
              <div className="flex gap-2">
                <Button
                  variant={currentView === 'menu' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentView('menu')}
                >
                  Menu
                </Button>
                <Button
                  variant={currentView === 'track' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setCurrentView('track')}
                >
                  Track
                </Button>
              </div>
              
              {/* User Info and Logout */}
              {userName && (
                <div className="flex items-center gap-2 ml-4 pl-4 border-l border-border/50">
                  <span className="text-sm text-muted-foreground">
                    Hi, <span className="font-medium text-foreground">{userName}</span>
                  </span>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleLogout}
                    className="text-muted-foreground hover:text-red-600 hover:border-red-300"
                  >
                    Logout
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 h-[calc(100vh-140px)]">
        <div className="grid lg:grid-cols-2 gap-6 h-full">
          {/* Chat Panel */}
          <Card className="shadow-elegant border-border/50 flex flex-col min-h-0">
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              onVoiceInput={handleVoiceInput}
              isProcessing={isProcessing}
              className="h-full"
            />
          </Card>

          {/* Action Panel */}
          <Card className="shadow-elegant border-border/50 flex flex-col min-h-0">
            <CardContent className="p-6 h-full overflow-auto chat-scrollbar">
              {renderActionPanel()}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Index;