from rest_framework import serializers
from django.contrib.auth.models import User, Group
from .models import Category, MenuItem, Cart, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']

class CartSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(),
        source='menuitem',
        write_only=True
    )

    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'user': {'read_only': True},
            'unit_price': {'read_only': True},
            'price': {'read_only': True},
        }

    def validate(self, attrs):
        # We need the user from request context
        user = self.context['request'].user
        menuitem = attrs['menuitem']
        quantity = attrs['quantity']
        
        if quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
            
        attrs['user'] = user
        attrs['unit_price'] = menuitem.price
        attrs['price'] = menuitem.price * quantity
        return attrs

class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    delivery_crew_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        source='delivery_crew',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'delivery_crew_id', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['user', 'total', 'date', 'order_items']
