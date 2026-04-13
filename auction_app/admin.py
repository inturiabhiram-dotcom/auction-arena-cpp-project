from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserModel, ItemModel, BidModel

class UserModelAdmin(UserAdmin):
    model = UserModel
    list_display = ('username','phone','email', 'firstname', 'lastname','user_credit','is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('firstname', 'lastname', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    exclude = ('date_joined',)

admin.site.register(UserModel, UserModelAdmin)

class ItemModelAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'owner_name', 'item_start_price', 'auction_start_date', 'auction_end_date', 'soldout_price', 'user_id')
    list_filter = ('auction_start_date', 'auction_end_date', 'owner_name', 'user_id')
    search_fields = ('item_name', 'owner_name', 'item_description', 'highest_bid')
    ordering = ('auction_start_date',)


admin.site.register(ItemModel, ItemModelAdmin)


class BidModelAdmin(admin.ModelAdmin):
    list_display = ('item', 'bidder', 'bid_amount', 'bid_time')
    list_filter = ('bid_time', 'item', 'bidder')
    search_fields = ('item__item_name', 'bidder__username')
    ordering = ('-bid_time',)  # Display bids from latest to oldest

admin.site.register(BidModel, BidModelAdmin)