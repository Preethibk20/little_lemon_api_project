from django.urls import path, include
from . import views

urlpatterns = [
    # Djoser Authentication and User endpoints
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),

    # Categories
    path('categories', views.CategoriesView.as_view(), name='categories'),
    path('categories/', views.CategoriesView.as_view()),

    # Menu Items
    path('menu-items', views.MenuItemsView.as_view(), name='menu-items'),
    path('menu-items/', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.MenuItemDetailView.as_view(), name='menu-item-detail'),
    path('menu-items/<int:pk>/', views.MenuItemDetailView.as_view()),

    # Group Management - Manager
    path('groups/manager/users', views.ManagerGroupView.as_view(), name='manager-group-users'),
    path('groups/manager/users/', views.ManagerGroupView.as_view()),
    path('groups/manager/users/<int:pk>', views.ManagerGroupDetailView.as_view(), name='manager-group-user-detail'),
    path('groups/manager/users/<int:pk>/', views.ManagerGroupDetailView.as_view()),

    # Group Management - Delivery Crew
    path('groups/delivery-crew/users', views.DeliveryCrewGroupView.as_view(), name='delivery-crew-users'),
    path('groups/delivery-crew/users/', views.DeliveryCrewGroupView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryCrewGroupDetailView.as_view(), name='delivery-crew-user-detail'),
    path('groups/delivery-crew/users/<int:pk>/', views.DeliveryCrewGroupDetailView.as_view()),

    # Cart
    path('cart/menu-items', views.CartView.as_view(), name='cart-menu-items'),
    path('cart/menu-items/', views.CartView.as_view()),

    # Orders
    path('orders', views.OrderView.as_view(), name='orders'),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:pk>', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view()),
]
