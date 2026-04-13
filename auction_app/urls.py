# myapp/urls.py

from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('data/',views.index, name = 'mytest'),
    path('',views.loginView.as_view(), name="login_page"),
    path('signup/',views.signupView.as_view(), name="signup_page"),
    path('login/',views.loginView.as_view(), name="login_page"),
    path('logout/',views.loginView.as_view(), name="logout_page"),
    path('admin_home/',views.adminView.as_view(), name="admin_home"),
    
    #---------------------- user paths -------------------------# 
    path('user_home/',views.userView.as_view(), name="user_home"),
    path('all_auctions/',views.userAuctionsListView.as_view(), name="user_auctions_list"),
    path('all_auctions_bid/<int:item_id>/',views.userAuctionsListView.as_view(), name="user_auctions_bid"),
    path('bid/<int:item_id>/',views.userBidView.as_view(), name="user_bid"),
    path('add_credits/',views.userAddCreditsView.as_view(), name="user_add_credits"),
    path('user_all_bids/',views.userOwnBidsView.as_view(), name="user_all_bids"),
    
    
    #---------------------- admin paths -------------------------# 
    path('auctions_list/',views.adminAuctionsListView.as_view(), name="admin_auctions_list"),
    path('users_list/',views.adminUsersListView.as_view(), name="admin_users_list"),
    path('add_item/',views.adminAddItemView.as_view(), name="admin_add_item"),
    path('add_item/<int:item_id>/', views.adminAddItemView.as_view(), name='admin_add_item_with_id'),
    path('admin_all_bids/',views.adminAllBids.as_view(), name="admin_all_bids"),
    path('item_details/<int:item_id>/',views.adminItemDetailView.as_view(), name="item_details"),
    
    path("api/convert-euro/", views.convert_to_euro_api, name="convert_euro_api"),


]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

