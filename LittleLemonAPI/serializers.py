from datetime import timezone
import datetime
from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'              
                 
        extra_kwargs = {
            'slug' : {
                'validators' : [UniqueValidator(queryset = Category.objects.all())] 
            },
            
            'title' : {
                'validators' : [UniqueValidator(queryset = Category.objects.all())]
            },
        }
        
class MenuItemSerializer(serializers.ModelSerializer):
    title = serializers.CharField(
        max_length=255, 
        validators = [UniqueValidator(queryset = MenuItem.objects.all())]
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, min_value=1)
    
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']
        
        extra_kwargs = {
            'price' : {'min_value' : 1.0}
        }
        
class CartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True, min_value=1)
    unit_price = serializers.SerializerMethodField(method_name='get_unit_price', read_only=True)
    quantity = serializers.IntegerField()
    price = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price', 'user_id', 'menuitem_id']
        
        extra_kwargs = {
            'quantity' : {'min_value' : 1},
            'unit_price' : {'min_value' : 1.0},
        }
    
    def get_unit_price(self, obj):
        menuitem_id = obj.menuitem_id
        #print('menuitem_id: ', menuitem_id)
        if menuitem_id is not None:
            return obj.unit_price
        return None
    
    def get_price(self, obj):
        unit_price = obj.unit_price
        quantity = obj.quantity

        # print(unit_price)      
        # print(quantity)    
        return unit_price * quantity
        
        
class OrderSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    user_id = serializers.IntegerField(write_only=True, min_value=1)
    delivery_crew = serializers.PrimaryKeyRelatedField(read_only=True)
    total = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=1.0)
    date = serializers.DateField(default=datetime.datetime.now())
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'user_id', 'delivery_crew', 'status', 'total', 'date']
        

class OrderSerializerforStatusandDelivery(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status', 'delivery_crew']
        
        
class OrderSerializerforStatus(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        


class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True)
    order_id = serializers.IntegerField(write_only=True)
    menuitem = serializers.PrimaryKeyRelatedField(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)
    price = serializers.SerializerMethodField(method_name='calculate_price')
    
    class Meta:
        model = OrderItem
        fields = ['order', 'order_id', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        
        extra_kwargs = {
            'quantity' : {'min_value':1},
            'unit_price' : {'min_value':1.0},
            'validators' : UniqueTogetherValidator(
                queryset = OrderItem.objects.all(),
                fields = ['order_id', 'menuitem_id']
            )
        }
        
    def calculate_price(self, item:OrderItem):
        return item.unit_price * item.quantity 