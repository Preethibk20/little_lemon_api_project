from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from LittleLemonAPI.models import Category, MenuItem, Cart, Order, OrderItem

class LittleLemonAPITests(APITestCase):

    def setUp(self):
        # Create groups
        self.manager_group = Group.objects.create(name='Manager')
        self.crew_group = Group.objects.create(name='Delivery crew')

        # Create users
        self.admin_user = User.objects.create_superuser('adminuser', 'admin@example.com', 'adminpass')
        self.manager_user = User.objects.create_user('manageruser', 'manager@example.com', 'managerpass')
        self.manager_group.user_set.add(self.manager_user)
        
        self.crew_user = User.objects.create_user('crewuser', 'crew@example.com', 'crewpass')
        self.crew_group.user_set.add(self.crew_user)

        self.customer_user = User.objects.create_user('customeruser', 'customer@example.com', 'customerpass')

        # Create initial data
        self.category_starters = Category.objects.create(slug='starters', title='Starters')
        self.category_mains = Category.objects.create(slug='mains', title='Mains')

        self.item_hummus = MenuItem.objects.create(
            title='Hummus', price=5.00, featured=True, category=self.category_starters
        )
        self.item_chicken = MenuItem.objects.create(
            title='Lemon Chicken', price=12.00, featured=False, category=self.category_mains
        )
        self.item_fish = MenuItem.objects.create(
            title='Grilled Fish', price=15.00, featured=False, category=self.category_mains
        )

    # 1. The admin can assign users to the manager group
    # 2. You can access the manager group with an admin token
    def test_admin_manage_manager_group(self):
        self.client.force_authenticate(user=self.admin_user)
        # GET manager group list
        response = self.client.get('/api/groups/manager/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'manageruser')

        # Add customer to manager group
        response = self.client.post('/api/groups/manager/users/', {'username': 'customeruser'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.customer_user.groups.filter(name='Manager').exists())

        # Remove customer from manager group
        response = self.client.delete(f'/api/groups/manager/users/{self.customer_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.customer_user.groups.filter(name='Manager').exists())

    # 3. The admin can add menu items
    # 4. The admin can add categories
    def test_admin_add_menu_and_categories(self):
        self.client.force_authenticate(user=self.admin_user)
        # Add category
        response = self.client.post('/api/categories/', {'slug': 'desserts', 'title': 'Desserts'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)

        # Add menu item
        response = self.client.post('/api/menu-items/', {
            'title': 'Baklava', 'price': '4.50', 'category_id': Category.objects.get(slug='desserts').id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MenuItem.objects.count(), 4)

    # 5. Managers can log in
    # 12. Customers can log in using their username and password and get access tokens
    # 11. Customers can register
    def test_user_authentication_flows(self):
        # Register a new customer
        response = self.client.post('/api/users/', {
            'username': 'newcustomer', 'password': 'newpass12345', 'email': 'new@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Login customer
        response = self.client.post('/api/token/login/', {
            'username': 'newcustomer', 'password': 'newpass12345'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

        # Login manager
        response = self.client.post('/api/token/login/', {
            'username': 'manageruser', 'password': 'managerpass'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    # 6. Managers can update the item of the day
    def test_manager_update_item_of_the_day(self):
        self.client.force_authenticate(user=self.manager_user)
        # Update hummus featured flag (item of the day)
        response = self.client.patch(f'/api/menu-items/{self.item_hummus.id}/', {'featured': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item_hummus.refresh_from_db()
        self.assertFalse(self.item_hummus.featured)

    # 7. Managers can assign users to the delivery crew
    def test_manager_assign_delivery_crew(self):
        self.client.force_authenticate(user=self.manager_user)
        # Add customer to delivery crew
        response = self.client.post('/api/groups/delivery-crew/users/', {'username': 'customeruser'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.customer_user.groups.filter(name='Delivery crew').exists())

        # Remove customer from delivery crew
        response = self.client.delete(f'/api/groups/delivery-crew/users/{self.customer_user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.customer_user.groups.filter(name='Delivery crew').exists())

    # 8. Managers can assign orders to the delivery crew
    def test_manager_assign_order_to_delivery_crew(self):
        # Create an order
        order = Order.objects.create(
            user=self.customer_user, total=12.00, status=False, date='2026-06-14'
        )
        self.client.force_authenticate(user=self.manager_user)
        
        # Assign delivery crew
        response = self.client.patch(f'/api/orders/{order.id}/', {'delivery_crew_id': self.crew_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.delivery_crew, self.crew_user)

    # 9. The delivery crew can access orders assigned to them
    # 10. The delivery crew can update an order as delivered
    def test_delivery_crew_order_access_and_delivery(self):
        # Create order assigned to crew
        order = Order.objects.create(
            user=self.customer_user, total=12.00, status=False, date='2026-06-14', delivery_crew=self.crew_user
        )
        # Create order not assigned to crew
        order2 = Order.objects.create(
            user=self.customer_user, total=15.00, status=False, date='2026-06-14'
        )

        self.client.force_authenticate(user=self.crew_user)
        # GET assigned orders
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], order.id)

        # Update order status to delivered
        response = self.client.patch(f'/api/orders/{order.id}/', {'status': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertTrue(order.status)

        # Trying to update someone else's order (should return 403 or 404 since it's filtered out of queryset)
        response = self.client.patch(f'/api/orders/{order2.id}/', {'status': True})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # 13. Customers can browse all categories
    # 14. Customers can browse all the menu items at once
    # 15. Customers can browse menu items by category
    # 16. Customers can paginate menu items
    # 17. Customers can sort menu items by price
    def test_customer_browsing_features(self):
        self.client.force_authenticate(user=self.customer_user)
        
        # Browse all categories
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Browse all menu items at once
        response = self.client.get('/api/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Pagination should be active with page size 2
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

        # Browse menu items by category
        response = self.client.get('/api/menu-items/', {'category': 'starters'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # It paginates so check result size
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Hummus')

        # Sort menu items by price (ascending: price; descending: -price)
        response = self.client.get('/api/menu-items/', {'ordering': 'price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Hummus') # 5.00
        self.assertEqual(response.data['results'][1]['title'], 'Lemon Chicken') # 12.00

        # Sort descending
        response = self.client.get('/api/menu-items/', {'ordering': '-price'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['title'], 'Grilled Fish') # 15.00
        self.assertEqual(response.data['results'][1]['title'], 'Lemon Chicken') # 12.00

    # 18. Customers can add menu items to the cart
    # 19. Customers can access previously added items in the cart
    def test_customer_cart_flows(self):
        self.client.force_authenticate(user=self.customer_user)

        # Add hummus to cart (quantity 2)
        response = self.client.post('/api/cart/menu-items/', {
            'menuitem_id': self.item_hummus.id, 'quantity': 2
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['price'], '10.00')

        # Access cart
        response = self.client.get('/api/cart/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['menuitem']['title'], 'Hummus')

        # Clear cart
        response = self.client.delete('/api/cart/menu-items/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Cart.objects.filter(user=self.customer_user).count(), 0)

    # 20. Customers can place orders
    # 21. Customers can browse their own orders
    def test_customer_order_placement_and_browsing(self):
        self.client.force_authenticate(user=self.customer_user)

        # Add to cart
        self.client.post('/api/cart/menu-items/', {'menuitem_id': self.item_hummus.id, 'quantity': 2})
        self.client.post('/api/cart/menu-items/', {'menuitem_id': self.item_chicken.id, 'quantity': 1})

        # Place order
        response = self.client.post('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order_id = response.data['id']
        self.assertEqual(response.data['total'], '22.00') # (5.00*2) + 12.00

        # Cart should be empty
        self.assertEqual(Cart.objects.filter(user=self.customer_user).count(), 0)

        # Browse their own orders
        response = self.client.get('/api/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], order_id)

        # Trying to retrieve this order as another customer (should return 404 since it's filtered out of queryset)
        other_customer = User.objects.create_user('othercust', 'other@example.com', 'otherpass')
        self.client.force_authenticate(user=other_customer)
        response = self.client.get(f'/api/orders/{order_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
