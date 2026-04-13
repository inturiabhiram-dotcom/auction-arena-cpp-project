from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Max

class UserModelManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('The Email field must be set')
        user = self.model(username=username, email=email)
        user.set_password(password)  # Hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(username, email, password)
        user.is_admin = True  # Set admin status for superuser
        user.is_staff = True  # Mark the user as staff (required for admin access)
        user.is_superuser = True  # Mark the user as a superuser
        user.save(using=self._db)
        return user



class UserModel(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=False)
    firstname = models.CharField(max_length=255, blank=True)
    lastname = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    user_credit = models.IntegerField(default=0, null=True, blank=True)
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserModelManager()

    groups = models.ManyToManyField('auth.Group', related_name='user_groups', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='user_permissions', blank=True)

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.firstname} {self.lastname}"

    def get_short_name(self):
        return self.firstname

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin


# Item Model
def get_default_user():
    user = get_user_model().objects.first()
    if not user:
        raise ValueError("No users found in the database!")
    return user



class ItemModel(models.Model):

    owner_name = models.CharField(max_length=250)
    item_name = models.CharField(max_length=250)
    item_description = models.CharField(max_length=250)
    item_image = models.ImageField(upload_to="pictures/")
    item_start_price = models.DecimalField(max_digits=10, decimal_places=2)
    auction_start_date = models.DateTimeField()
    auction_end_date = models.DateTimeField()
    soldout_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.0)

    user_id = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        default=get_default_user,
        db_column='user_id'
    )

    def __str__(self):
        return f"{self.item_name} owned by {self.owner_name}"

class BidModel(models.Model):
    item = models.ForeignKey(
        ItemModel,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    bidder = models.IntegerField(default=0)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bid_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.bidder.username} on {self.item.item_name} - {self.bid_amount}"

    class Meta:
        ordering = ['-bid_amount']  # Default ordering by highest bid

