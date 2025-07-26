import { Pizza, Plus, Leaf, Beef } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export interface MenuItem {
  id: string;
  name: string;
  size: string;
  price: number;
  description?: string;
  category: 'veg' | 'non-veg';
  aliases?: string[];
}

interface MenuComponentProps {
  onAddToOrder: (item: MenuItem) => void;
  category?: 'all' | 'veg' | 'non-veg' | 'drinks' | 'sides';
  menuItems?: MenuItem[];
}

export const MenuComponent = ({ 
  onAddToOrder, 
  category = 'all',
  menuItems = []
}: MenuComponentProps) => {
  
  const filterItemsByCategory = (items: MenuItem[], cat: string) => {
    if (cat === 'all') return items;
    return items.filter(item => item.category === cat);
  };

  const getCategoryIcon = (cat: string) => {
    switch (cat) {
      case 'veg':
        return <Leaf className="h-4 w-4" />;
      case 'non-veg':
        return <Beef className="h-4 w-4" />;
      default:
        return <Pizza className="h-4 w-4" />;
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'veg':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'non-veg':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const renderMenuItems = (items: MenuItem[]) => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((item) => (
        <Card key={item.id} className="group hover:shadow-lg transition-all duration-300 border-border/50">
            <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-lg font-semibold group-hover:text-primary transition-colors truncate">
                  {item.name}
                </CardTitle>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <Badge variant="outline" className={getCategoryColor(item.category)}>
                    {getCategoryIcon(item.category)}
                    <span className="ml-1 capitalize">{item.category === 'non-veg' ? 'Non-Veg' : item.category}</span>
                  </Badge>
                  <Badge variant="secondary" className="text-xs">
                    {item.size}
                  </Badge>
                </div>
              </div>
              <div className="flex-shrink-0">
                <div className="text-xl font-bold text-primary whitespace-nowrap">
                  ${item.price.toFixed(2)}
                </div>
                </div>
              </div>
            </CardHeader>
          
          {item.description && (
            <CardContent className="pt-0 pb-3">
              <CardDescription className="text-sm text-muted-foreground leading-relaxed">
                {item.description}
              </CardDescription>
            </CardContent>
          )}
          
          <CardFooter className="pt-0">
              <Button 
                onClick={() => onAddToOrder(item)}
              className="w-full bg-gradient-primary hover:opacity-90 transition-all duration-200 group-hover:scale-105"
              size="lg"
              >
              <Plus className="h-4 w-4 mr-2" />
                Add to Order
              </Button>
            </CardFooter>
          </Card>
      ))}
    </div>
  );

  const vegItems = filterItemsByCategory(menuItems, 'veg');
  const nonVegItems = filterItemsByCategory(menuItems, 'non-veg');

  if (category !== 'all') {
    const filteredItems = filterItemsByCategory(menuItems, category);
    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2 flex items-center justify-center gap-2">
            {getCategoryIcon(category)}
            {category === 'veg' ? 'Vegetarian Pizzas' : 
             category === 'non-veg' ? 'Non-Vegetarian Pizzas' : 
             category.charAt(0).toUpperCase() + category.slice(1)}
          </h2>
          <p className="text-muted-foreground">
            {filteredItems.length} pizza{filteredItems.length !== 1 ? 's' : ''} available
          </p>
        </div>
        {renderMenuItems(filteredItems)}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2 flex items-center justify-center gap-2">
          <Pizza className="h-6 w-6" />
          Our Pizza Menu
        </h2>
        <p className="text-muted-foreground">Choose from our delicious pizza selection</p>
      </div>
      
      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all">All Pizzas ({menuItems.length})</TabsTrigger>
          <TabsTrigger value="veg">
            <Leaf className="h-4 w-4 mr-1" />
            Vegetarian ({vegItems.length})
          </TabsTrigger>
          <TabsTrigger value="non-veg">
            <Beef className="h-4 w-4 mr-1" />
            Non-Vegetarian ({nonVegItems.length})
              </TabsTrigger>
        </TabsList>
        
        <TabsContent value="all" className="mt-6">
          {renderMenuItems(menuItems)}
        </TabsContent>

        <TabsContent value="veg" className="mt-6">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-green-700 mb-2">🌱 Vegetarian Pizzas</h3>
              <p className="text-sm text-muted-foreground">Fresh, flavorful, and completely vegetarian</p>
            </div>
            {renderMenuItems(vegItems)}
          </div>
        </TabsContent>

        <TabsContent value="non-veg" className="mt-6">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-red-700 mb-2">🍖 Non-Vegetarian Pizzas</h3>
              <p className="text-sm text-muted-foreground">Protein-packed and full of flavor</p>
            </div>
            {renderMenuItems(nonVegItems)}
          </div>
          </TabsContent>
      </Tabs>
    </div>
  );
};