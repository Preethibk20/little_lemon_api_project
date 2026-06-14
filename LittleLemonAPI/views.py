from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db import transaction
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import UserSerializer, CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.groups.filter(name='Manager').exists()
        )

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Delivery crew').exists()

class IsManagerOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.groups.filter(name='Manager').exists()
        )

# Categories
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]
    pagination_class = None

# Menu Items
class MenuItemsView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]

    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category = self.request.query_params.get('category')
        to_price = self.request.query_params.get('to_price')
        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('ordering')

        if category:
            # support filtering by slug or category title
            queryset = queryset.filter(category__slug=category)
        if to_price:
            queryset = queryset.filter(price__lte=to_price)
        if search:
            queryset = queryset.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            queryset = queryset.order_by(*ordering_fields)

        return queryset

class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrAdminOrReadOnly]

# Group Management - Manager
class ManagerGroupView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            group = Group.objects.get(name='Manager')
        except Group.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        users = group.user_set.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, created = Group.objects.get_or_create(name='Manager')
        group.user_set.add(user)
        return Response({'message': 'User added to Manager group'}, status=status.HTTP_201_CREATED)

class ManagerGroupDetailView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        try:
            group = Group.objects.get(name='Manager')
            group.user_set.remove(user)
            return Response({'message': 'User removed from Manager group'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'error': 'Group does not exist'}, status=status.HTTP_404_NOT_FOUND)

# Group Management - Delivery Crew
class DeliveryCrewGroupView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        try:
            group = Group.objects.get(name='Delivery crew')
        except Group.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)
        users = group.user_set.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, username=username)
        group, created = Group.objects.get_or_create(name='Delivery crew')
        group.user_set.add(user)
        return Response({'message': 'User added to Delivery crew group'}, status=status.HTTP_201_CREATED)

class DeliveryCrewGroupDetailView(APIView):
    permission_classes = [IsManager]

    def delete(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        try:
            group = Group.objects.get(name='Delivery crew')
            group.user_set.remove(user)
            return Response({'message': 'User removed from Delivery crew group'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'error': 'Group does not exist'}, status=status.HTTP_404_NOT_FOUND)

# Cart
class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        Cart.objects.filter(user=self.request.user).delete()
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)

# Orders
class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)

    def create(self, request, *args, **kwargs):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.price for item in cart_items)

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                total=total,
                status=False,
                date=timezone.now().date()
            )
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menuitem=item.menuitem,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    price=item.price
                )
            cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user)
        else:
            return Order.objects.filter(user=user)

    def update(self, request, *args, **kwargs):
        user = request.user
        order = self.get_object()

        is_manager = user.is_superuser or user.groups.filter(name='Manager').exists()
        is_delivery = user.groups.filter(name='Delivery crew').exists()

        if is_manager:
            return super().update(request, *args, **kwargs)
        elif is_delivery:
            if order.delivery_crew != user:
                return Response({'detail': 'Not authorized for this order.'}, status=status.HTTP_403_FORBIDDEN)

            status_val = request.data.get('status')
            if status_val is not None:
                if str(status_val).lower() in ['true', '1']:
                    order.status = True
                else:
                    order.status = False
                order.save()
                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({'detail': 'Only status update is allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'You do not have permission to update this order.'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        is_manager = user.is_superuser or user.groups.filter(name='Manager').exists()
        if not is_manager:
            return Response({'detail': 'You do not have permission to delete this order.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
