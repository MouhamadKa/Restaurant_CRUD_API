from django.shortcuts import render
from .models import User, MenuItem, Cart, Order, OrderItem
from .serializers import UserSerializer, MenuItemSerializer, CartSerializer, OrderSerializer, \
    OrderSerializerforStatusandDelivery, OrderSerializerforStatus
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import Group
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


# Create your views here.
class MenuItemView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    filterset_fields = ['price', 'featured']
    search_fields = ['title', 'category__title'] 
    
    
    # I didn't add category_title it to filterset_fields above to use 'category' in the url instead of 'category__tittle'
    def get_queryset(self):
        queryset = MenuItem.objects.all()
        # queryset = super().get_queryset() # Get the initial queryset
        category_title = self.request.query_params.get('category')
        if category_title:
            queryset = queryset.filter(category__title__icontains=category_title)
        to_price = self.request.query_params.get('to_price')
        if to_price:
            queryset = queryset.filter(price__lte=to_price)
        from_price = self.request.query_params.get('from_price')
        if from_price:
            queryset = queryset.filter(price__gte=from_price)
            
        return queryset
    
    
    def post(self, request):
        #print(self.request.user.groups.filter(name="Manager").exists())
        if not request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message" :"You don't have permission to create a menu item."}, 
                status.HTTP_401_UNAUTHORIZED
            )

        menuitems = self.request.data
        serializeditems = MenuItemSerializer(data=menuitems)
        serializeditems.is_valid(raise_exception=True)
        serializeditems.save()
        return Response(serializeditems.data, status=status.HTTP_201_CREATED)
        
    
    
class SingleMenuItem(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    
    def put(self, request, pk=None):
        if not request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message" :"You don't have permission to update this item."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        # Get the MenuItem object
        menu_item = get_object_or_404(MenuItem, id=pk)

        # Serialize the updated data
        serialized_item = MenuItemSerializer(menu_item, data=request.data)

        # Validate and save the updated data
        if serialized_item.is_valid():
            serialized_item.save()
            return Response(serialized_item.data, status=status.HTTP_200_OK)
        else:
            return Response(serialized_item.errors, status=status.HTTP_400_BAD_REQUEST) 
        
        
    def patch(self, request, pk=None):
        # Check if the user is in the 'Manager' group
        if not self.request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message" :"You don't have permission to update this item."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get the MenuItem object
        menu_item = get_object_or_404(MenuItem, pk=pk)

        # Serialize the updated data with partial=True
        serialized_item = MenuItemSerializer(menu_item, data=request.data, partial=True)

        # Validate and save the updated data
        if serialized_item.is_valid():
            serialized_item.save()
            return Response(serialized_item.data, status=status.HTTP_200_OK)
        else:
            return Response(serialized_item.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, pk=None):
        # Check if the user is in the 'Manager' group
        if not self.request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message": "You don't have permission to delete this item."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get the MenuItem object
        menu_item = get_object_or_404(MenuItem, pk=pk)

        # Delete the MenuItem object
        menu_item.delete()

        return Response({"message": "Menu item deleted successfully."})

class ManagerView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Manager')
    serializer_class = UserSerializer
    filterset_fields = ['first_name', 'last_name', 'username']
    search_fields =  ['first_name', 'last_name', 'username']
    
    def get_queryset(self):
        if not self.request.user.groups.filter(name="Manager").exists():
            raise PermissionDenied("You don't have permission to access this resource.")
            
        queryset = super().get_queryset()  # Get the initial queryset
        return queryset
    
    def post(self, request):
        #print(self.request.user.groups.filter(name="Manager").exists())
        if not self.request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message" :"You don't have permission to do this action."}, 
                status.HTTP_401_UNAUTHORIZED
            )

        # Fetch the username from request data
        username = self.request.data.get('username')
        user_instance = User.objects.filter(username=username).first()
        manager_group = Group.objects.get(name='Manager')
        serialized_user = UserSerializer(data=request.data)

        if user_instance:
            # If the user exists, assign it to the Manager group
            user_instance.groups.add(manager_group)
            return Response("added to manager group.")
        else:
            # If the user doesn't exist, create a new user and assign it to the Manager group
            serialized_user.is_valid(raise_exception=True)
            user_instance = serialized_user.save()
            user_instance.groups.add(manager_group)

            return Response(serialized_user.data, status=status.HTTP_201_CREATED)


class SingleManagerView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def delete(self, request, pk=None):
        # Check if the user is in the 'Manager' group
        if not self.request.user.groups.filter(name="Manager").exists():
            return Response(
                {"message": "You don't have permission to delete this item."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get the User object and add it to the 'manager' group
        user = get_object_or_404(User, pk=pk)
        manager_group = Group.objects.get(name="Manager")
        user.groups.remove(manager_group)

        return Response({"message": "Removed from manager group."}, status=status.HTTP_204_NO_CONTENT)
    
    
class DelieveryCrewView(generics.ListCreateAPIView):
    queryset = User.objects.filter(groups__name='Delivery Crew')
    serializer_class = UserSerializer
    
    def post(self, request):
        if not self.request.user.groups.filter(name='Manager').exists():
            return Response(
                {"message" : "you don't have permissions to perform this action."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        username = request.data.get('username')
        user_instance = User.objects.filter(username=username).first()
        delivery_crew_group = Group.objects.get(name='Delivery Crew')
        serialized_user = UserSerializer(data=request.data)
        
        if user_instance:
            user_instance.groups.add(delivery_crew_group)
            return Response("added to delivery crew group.", status=status.HTTP_200_OK)
                
        serialized_user.is_valid(raise_exception=True)
        serialized_user.save()
        return Response(serialized_user.data, status=status.HTTP_201_CREATED)
    
    
class SingleDelieveryCrewView(generics.DestroyAPIView):
    queryset = User.objects.filter(groups__name='Delivery Crew')
    serializer_class = UserSerializer
    
    def delete(self, request, pk=None):
        if not self.request.user.groups.filter(name='Manager'):
            raise PermissionDenied("You don't have permission to access this resource.")
            
        user = get_object_or_404(User, id=pk)
        delivery_crew = Group.objects.get(name='Delivery Crew')
        user.groups.remove(delivery_crew)
        return Response({"message": "Removed from delivry crew group."}, status=status.HTTP_204_NO_CONTENT)
        
    
class CartView(generics.ListCreateAPIView, generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    #! Find How to check if it not manager or deelivery using id
    #* Better way founded
    
    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists() or \
            self.request.user.groups.filter(name='Delivery Crew').exists():
                raise PermissionDenied("You don't have permission to access this resource.") 
                
        queryset = Cart.objects.filter(user=self.request.user)
        return queryset
        
    def post(self ,reqest):
        # print(self.request.user.groups.filter(name='Manager').exists())
        # print(self.request.user.groups.filter(name='Manager').exists())
        if self.request.user.groups.filter(name='Manager').exists() or \
            self.request.user.groups.filter(name='Delivery Crew').exists():
                return Response(
                    {"message" : "you don't have permissions to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
        cart = self.request.data
        serialized_cart = CartSerializer(data=cart)
        serialized_cart.is_valid(raise_exception=True)
        serialized_cart.save(user=self.request.user)
        return Response(serialized_cart.data, status=status.HTTP_201_CREATED)   
    
    def delete(self, request):
        if self.request.user.groups.filter(name='Manager').exists() or \
            self.request.user.groups.filter(name='Delivery Crew').exists():
                return Response(
                    {"message" : "you don't have permissions to perform this action."},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        user = request.user
        # Retrieve all carts for the specified user
        carts = Cart.objects.filter(user=user)


        # Check if any carts exist
        if carts.exists():
            # Delete all carts for the specified user
            carts.delete()
            return Response({'message': 'Carts deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'message': 'No carts found for the specified user'}, status=status.HTTP_404_NOT_FOUND)
    

class OrderView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    ordering_fields = ['total', 'date']
    filterset_fields = ['user', 'status']
    search_fields = ['user', 'delivery_crew'] 
    

    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            queryset = Order.objects.all()
        
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            delivery = self.request.user
            queryset = Order.objects.filter(delivery_crew=delivery)
        
        else:
            user = self.request.user
            queryset = Order.objects.filter(user=user)
            
        return queryset
    
    def post(self, request):
        # Fetching cart items for the current user
        cart_items = Cart.objects.filter(user=request.user)
        # print(cart_items.exists())
        
        if cart_items.exists():
            # Creating an order instance
            order_instance = Order.objects.create(user=request.user, total=0)  # Assuming total will be updated later

            # Creating order items from cart items
            order_items_data = []
            total_price = 0
            for cart_item in cart_items:
                order_item_data = {
                    'order': order_instance,
                    'menuitem': cart_item.menuitem,
                    'quantity': cart_item.quantity,
                    'unit_price': cart_item.unit_price,
                    'price': cart_item.price
                }
                total_price += cart_item.price
                order_items_data.append(order_item_data)

            # Bulk create order items
            OrderItem.objects.bulk_create([OrderItem(**data) for data in order_items_data])

            # Update order total
            order_instance.total = total_price
            order_instance.save()

            # Clear the user's cart after placing the order
            cart_items.delete()

            # Serialize the order and return the response
            serialized_order = OrderSerializer(order_instance)
            return Response(serialized_order.data, status=status.HTTP_201_CREATED)
        
        else:
            return Response(
                {"message":"No items in the Cart"},
                status=status.HTTP_404_NOT_FOUND
            )

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        pk = self.kwargs.get('pk')
        order = get_object_or_404(Order, id=pk)
        if order.user == self.request.user:
            querset = OrderItem.objects.filter(order=order)
            # print(querset.exists())
            if querset.exists():
                return querset
            else:
                raise PermissionDenied("No OrderItem matches the given query.") 
            
        else:
            raise PermissionDenied("You don't have permission to access this resource.") 
           
    def put(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        
        # Check if user belongs to 'Manager' group
        if request.user.groups.filter(name='Manager').exists():
            # Allow editing of 'status' and 'delivery_crew' attributes
            serialized_order = OrderSerializerforStatusandDelivery(order, data=request.data)
            if serialized_order.is_valid():
                serialized_order.save()
                return Response(serialized_order.data, status=status.HTTP_200_OK)
            else:
                return Response(serialized_order.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If user belongs to 'Delivery Crew' group, allow editing of 'status' only
        elif request.user.groups.filter(name='Delivery Crew').exists():
            # Allow editing of 'status' attribute only
            serialized_order = OrderSerializerforStatus(order, data=request.data)
            if serialized_order.is_valid():
                serialized_order.save()
                return Response(serialized_order.data, status=status.HTTP_200_OK)
            else:
                return Response(serialized_order.errors, status=status.HTTP_400_BAD_REQUEST)
        
            
    def patch(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        
        # Check if user belongs to 'Manager' group
        if request.user.groups.filter(name='Manager').exists():
            # Allow editing of 'status' and 'delivery_crew' attributes
            serialized_order = OrderSerializerforStatusandDelivery(order, data=request.data, partial=True)
            if serialized_order.is_valid():
                serialized_order.save()
                return Response(serialized_order.data, status=status.HTTP_200_OK)
            else:
                return Response(serialized_order.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If user belongs to 'Delivery Crew' group, allow editing of 'status' only
        elif request.user.groups.filter(name='Delivery Crew').exists():
            # Allow editing of 'status' attribute only
            serialized_order = OrderSerializerforStatus(order, data=request.data, partial=True)
            if serialized_order.is_valid():
                serialized_order.save()
                return Response(serialized_order.data, status=status.HTTP_200_OK)
            else:
                return Response(serialized_order.errors, status=status.HTTP_400_BAD_REQUEST)
            
    def delete(self, request, pk):
        order = get_object_or_404(Order, id=pk)
        order.delete()
        
            
            
