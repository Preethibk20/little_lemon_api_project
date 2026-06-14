import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LittleLemon.settings')
django.setup()

from django.contrib.auth.models import User, Group
from LittleLemonAPI.models import Category, MenuItem

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword123')
    print("Superuser 'admin' created.")

# Create groups
manager_group, _ = Group.objects.get_or_create(name='Manager')
delivery_group, _ = Group.objects.get_or_create(name='Delivery crew')
print("Groups 'Manager' and 'Delivery crew' verified/created.")

# Create standard users
def get_or_create_user(username, password, group=None):
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username, f'{username}@example.com', password)
        if group:
            group.user_set.add(user)
        print(f"User '{username}' created.")
        return user
    else:
        user = User.objects.get(username=username)
        if group:
            group.user_set.add(user)
        print(f"User '{username}' exists.")
        return user

manager_user = get_or_create_user('manageruser', 'managerpassword123', manager_group)
crew_user = get_or_create_user('crewuser', 'crewpassword123', delivery_group)
customer_user = get_or_create_user('customeruser', 'customerpassword123')

# Seed categories
categories = [
    {'slug': 'starters', 'title': 'Starters'},
    {'slug': 'mains', 'title': 'Mains'},
    {'slug': 'desserts', 'title': 'Desserts'},
]
for cat_data in categories:
    cat, created = Category.objects.get_or_create(slug=cat_data['slug'], defaults={'title': cat_data['title']})
    if created:
        print(f"Category '{cat.title}' created.")

# Seed menu items
try:
    mains = Category.objects.get(slug='mains')
    starters = Category.objects.get(slug='starters')
    desserts = Category.objects.get(slug='desserts')

    menu_items = [
        {'title': 'Hummus', 'price': 5.00, 'category': starters, 'featured': True},
        {'title': 'Greek Salad', 'price': 8.50, 'category': starters, 'featured': False},
        {'title': 'Lemon Chicken', 'price': 12.00, 'category': mains, 'featured': True},
        {'title': 'Grilled Fish', 'price': 15.00, 'category': mains, 'featured': False},
        {'title': 'Baklava', 'price': 4.50, 'category': desserts, 'featured': False},
    ]

    for item in menu_items:
        mi, created = MenuItem.objects.get_or_create(
            title=item['title'],
            defaults={'price': item['price'], 'category': item['category'], 'featured': item['featured']}
        )
        if created:
            print(f"MenuItem '{mi.title}' created.")
except Exception as e:
    print(f"Error seeding menu items: {e}")
