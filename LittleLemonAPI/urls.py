from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token
urlpatterns = [
    path('menu-items/', views.MenuItemView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItem.as_view()),
    path('api-token-auth/', obtain_auth_token),
    path('groups/manager/users/', views.ManagerView.as_view()),
    path('groups/manager/users/<int:pk>', views.SingleManagerView.as_view()),
    path('groups/delivery-crew/users/', views.DelieveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.SingleDelieveryCrewView.as_view()),
    path('cart/menu-items/', views.CartView.as_view()),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
    #path('x/', views.x)
]

