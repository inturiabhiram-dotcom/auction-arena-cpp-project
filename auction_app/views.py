from django.http import HttpResponse
from django.template import loader
from django import forms
from django.contrib.auth.models import User
from auction_app.forms import signup
from django.db import IntegrityError 
from django.contrib.auth import authenticate, login
from django.views import View
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.db.models import Q
from django.utils import timezone

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from .models import UserModel,UserModelManager,ItemModel,BidModel
from django.contrib.auth.hashers import check_password

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Max, OuterRef, Subquery
from django.utils.timezone import now

# all views here

def index(request):
    users = UserModel.objects.all().values()
    template = loader.get_template("index.html")
    context = {
        'users':users
    }
    return HttpResponse(template.render(context,request))

class signupView(View):
    def get(self, request, *args, **kwargs):
        form = signup()
        return render(request,"signup.html",{"form":form})
    
    def post(self, request, *args, **kwargs):
        form = signup(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data["password"])
            user.save()
            return redirect("login_page")
        return render(request,"signup.html",{"form":form})

class logoutView(View):
    def get(self, request, *args, **kwargs):
        return render(request, template_name="login.html")

class loginView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "login.html")

    def post(self, request, *args, **kwargs):

        username=request.POST.get("username")
        password=request.POST.get("password")

        try:
            user_obj = UserModel.objects.get(username=username)
            if check_password(password, user_obj.password):
                login(request, user_obj) 
                if user_obj.is_staff:
                    return redirect("admin_auctions_list")
                else:
                    return redirect("user_auctions_list")
            else:
                raise UserModel.DoesNotExist
        except UserModel.DoesNotExist:
            return render(request, "login.html", {"error": "Invalid Credentials"})


        print(f"Authenticated user: {user_obj}")
        if not user_obj:
            return render(request, "login.html", {"error": "Invalid Credentials"})

            login(request, user_obj)
            if user_obj.is_staff:
                return redirect("admin_auctions_list")
            else:
                return redirect("user_auctions_list")

class adminView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return render(request, template_name="admin_home.html")

class userView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return render(request, template_name="user_home.html")




class userAuctionsListView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        query = request.GET.get("query")
        
        # Always get model instances, not values
        if query:
            item_obj = ItemModel.objects.filter(
                Q(item_name__icontains=query) & Q(soldout_price=0)
            ).order_by('-id')
        else:
            item_obj = ItemModel.objects.filter(soldout_price=0).order_by('-id')
        
        # Convert to list of dictionaries with additional data
        item_list = []
        current_time = timezone.now()
        
        for obj in item_obj:
            # Debug prints
            print(f"Item: {obj.item_name}")
            print(f"Item ID: {obj.id}")
            print(f"Image field type: {type(obj.item_image)}")
            if obj.item_image:
                print(f"Image URL: {obj.item_image.url}")
                print(f"Image exists: {bool(obj.item_image)}")
            else:
                print("Image field is empty")
            
            # Get highest bid
            highest_bid = (
                BidModel.objects.filter(item_id=obj.id)
                .aggregate(Max("bid_amount"))["bid_amount__max"]
            )
            
            # Check auction status
            auction_status = "upcoming"
            if obj.auction_start_date and obj.auction_end_date:
                if obj.auction_start_date <= current_time <= obj.auction_end_date:
                    auction_status = "active"
                elif current_time > obj.auction_end_date:
                    auction_status = "ended"
            
            item_list.append({
                "id": obj.id,
                "item_name": obj.item_name,
                "item_description": obj.item_description,
                "item_image": obj.item_image,  # Keep as FileField instance
                "item_start_price": obj.item_start_price,
                "auction_start_date": obj.auction_start_date,
                "auction_end_date": obj.auction_end_date,
                "highest_bid": highest_bid if highest_bid is not None else 0.00,
                "auction_status": auction_status,
                "soldout_price": obj.soldout_price,
            })
            print(f"Highest Bid: {item_list[-1]['highest_bid']}")
            print(f"Auction Status: {auction_status}")
            print("---")
        
        return render(
            request,
            template_name="user_auctions_list.html",
            context={"item_list": item_list},
        )

    def post(self, request, *args, **kwargs):
        if request.POST.get("bidsubmit") and request.POST.get("item_id"):
            item_id = request.POST.get("item_id")
            item = get_object_or_404(ItemModel, id=item_id)
            
            # Check if auction has started
            if item.auction_start_date and item.auction_start_date > timezone.now():
                messages.warning(request, "Bidding is not allowed because the auction has not started yet.")
                return redirect("user_auctions_list")
            
            # Check if auction has ended
            if item.auction_end_date and item.auction_end_date < timezone.now():
                messages.warning(request, "Bidding is not allowed because the auction has already ended.")
                return redirect("user_auctions_list")
            
            # Check if item is sold out
            if item.soldout_price > 0:
                messages.warning(request, "This item has already been sold.")
                return redirect("user_auctions_list")
            
            return redirect("user_bid", item_id=item_id)
        
        return redirect("user_auctions_list")



from django.http import JsonResponse
from currency_converter_lib import convert_currency

def convert_to_euro_api(request):
    amount = request.GET.get("amount")

    try:
        amount = float(amount)
        converted = convert_currency(amount, "USD")
        return JsonResponse({"converted": round(converted, 2)})
    except:
        return JsonResponse({"error": "Invalid amount"}, status=400)


import boto3
from django.conf import settings

sns_client = boto3.client("sns", region_name="us-east-1")


class userBidView(View):

    @method_decorator(login_required)
    def get(self, request, item_id, *args, **kwargs):
        item = get_object_or_404(ItemModel, id=item_id)

        highest_bid_aggregate = BidModel.objects.filter(item_id=item_id).aggregate(Max('bid_amount'))
        highest_bid_amount = highest_bid_aggregate['bid_amount__max']

        highest_bid = None
        if highest_bid_amount:
            highest_bid = BidModel.objects.filter(item_id=item_id, bid_amount=highest_bid_amount).first()

        if timezone.now() > item.auction_end_date:
            messages.warning(request, 'This auction has already ended.')
            return redirect("user_auctions_list")

        if item.auction_start_date and timezone.now() < item.auction_start_date:
            messages.info(request, 'This auction has not started yet.')
            return redirect("user_auctions_list")

        return render(request, 'user_bid.html', {
            'item': item,
            'highest_bid': highest_bid,
            'highest_bid_amount': highest_bid_amount,
        })


    def post(self, request, item_id, *args, **kwargs):
        item = get_object_or_404(ItemModel, id=item_id)

        if not request.user.is_authenticated:
            messages.info(request, 'You must be logged in to place a bid.')
            return redirect("user_bid", item_id=item_id)

        try:
            bid_amount = float(request.POST.get('bid_amount'))
        except (TypeError, ValueError):
            messages.info(request, 'Invalid bid amount')
            return redirect("user_bid", item_id=item_id)

        if request.user.user_credit < bid_amount:
            messages.info(request, 'You do not have enough credit to place this bid')
            return redirect("user_bid", item_id=item_id)

        highest_bid = item.bids.aggregate(Max('bid_amount'))['bid_amount__max']

        if highest_bid is None and bid_amount <= item.item_start_price:
            messages.info(request, 'Bid must be higher than start price.')
            return redirect("user_bid", item_id=item_id)
        elif highest_bid is not None and bid_amount <= highest_bid:
            messages.info(request, 'Bid must be higher than the current highest bid.')
            return redirect("user_bid", item_id=item_id)

        try:
            new_bid = BidModel.objects.create(
                item=item,
                bidder=request.user.id,
                bid_amount=bid_amount
            )

            request.user.user_credit -= bid_amount
            request.user.save()

            # SNS Notification
            message = f"""
            New Bid Placed!
            
            Item: {item.item_name}
            Bid Amount: {bid_amount}
            Bidder: {request.user.username}
            Auction Ends: {item.auction_end_date}
            """

            sns_client.publish(
                TopicArn=settings.SNS_TOPIC_ARN,
                Subject="New Bid Placed",
                Message=message
            )

            return redirect('user_auctions_list')

        except IntegrityError as e:
            return HttpResponse(f"Error IntegrityError placing bid: {str(e)}", status=500)
        except Exception as e:
            return HttpResponse(f"Error Exception placing bid: {str(e)}", status=500)





class userAddCreditsView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        user_id = request.user.id

        user_obj = request.user   
        return render(
            request,
            template_name="user_add_credits.html",
            context={"user_obj": user_obj}
        )

    def post(self, request, *args, **kwargs):
        user_id = request.user.id

        user_obj = request.user  
        credits_to_add = request.POST.get("credits")
        if credits_to_add:
            try:
                user_obj.user_credit += int(credits_to_add)
                user_obj.save()
                print("User credits updated successfully!")
                
                trigger_email_lambda(
                action="ADD_CREDIT",
                email=request.user.email,
                username=request.user.username,
                amount=credits_to_add
                )
                
            except ValueError:
                print("Invalid credit value.")
        return render(
            request,
            template_name="user_add_credits.html",
            context={"user_obj": user_obj}
        )
        
class userOwnBidsView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):

        bid_queryset = BidModel.objects.filter(bidder=request.user.id).order_by('-bid_time')

        bid_details = []
        for bid in bid_queryset:
            bid_details.append({
                "item_image": bid.item.item_image if bid.item.item_image else None,
                "item_name": bid.item.item_name,
                "start_price": bid.item.item_start_price,
                "highest_bid": BidModel.objects.filter(item=bid.item)
                                                .aggregate(Max("bid_amount"))["bid_amount__max"],
                "your_bid": bid.bid_amount,
                "closing_date": bid.item.auction_end_date,
            })

        won_queryset = BidModel.objects.filter(
            bidder=request.user.id,
            bid_amount=Subquery(
                BidModel.objects.filter(item_id=OuterRef('item_id'))
                                .order_by('-bid_amount')
                                .values('bid_amount')[:1]
            ),
            item__auction_end_date__lt=now()
        )

        won_details = []
        for win in won_queryset:
            won_details.append({
                "item_image": win.item.item_image if win.item.item_image else None,
                "item_name": win.item.item_name,
                "start_price": win.item.item_start_price,
                "winning_bid": win.bid_amount,
                "closing_date": win.item.auction_end_date,
            })
            
        
        trigger_email_lambda(
        action="AUCTION_WIN",
        email=request.user.email,
        username=request.user.username,
        item_name=win.item.item_name,
        winning_price=float(win.bid_amount)
        )
        

        return render(
            request,
            "user_view_own_bids.html",
            context={
                "bid_details": bid_details,
                "won_details": won_details,
            }
        )



import requests

API_GATEWAY_URL = "https://c6xxmeddpk.execute-api.us-east-1.amazonaws.com/default/email-notifier-lambda"


def trigger_email_lambda(action, email, username, **extra_data):
    payload = {
        "action": action,
        "email": email,
        "username": username
    }

    payload.update(extra_data)

    try:
        response = requests.post(API_GATEWAY_URL, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print("Lambda call failed:", str(e))
        return None


class adminAuctionsListView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        query = request.GET.get("query")
        
        # Get model instances instead of values() to maintain proper FileField objects
        if query:
            item_queryset = ItemModel.objects.filter(
                item_name__icontains=query
            ).order_by('-id')
        else:
            item_queryset = ItemModel.objects.all().order_by('-id')
        
        # Convert to list of dictionaries with proper image URLs
        item_list = []
        for obj in item_queryset:
            highest_bid = (
                BidModel.objects.filter(item_id=obj.id)
                .aggregate(Max("bid_amount"))["bid_amount__max"]
            )
            
            # Build dictionary with proper image URL
            item_dict = {
                "id": obj.id,
                "item_name": obj.item_name,
                "item_image": obj.item_image,  # Keep as FileField object for URL access
                "item_start_price": obj.item_start_price,
                "auction_end_date": obj.auction_end_date,
                "highest_bid": highest_bid if highest_bid is not None else 0.00,
                "soldout_price": obj.soldout_price,
                "auction_start_date": obj.auction_start_date,
            }
            item_list.append(item_dict)
            
        
        return render(
            request,
            template_name="admin_auctions_list.html",
            context={"item_list": item_list},
        )

    def post(self, request, *args, **kwargs):
        if request.POST.get("deletesubmit") and request.POST.get("item_id"):
            item_id = request.POST.get("item_id")
            item = get_object_or_404(ItemModel, id=item_id)
            
            # Check if auction has already started
            if item.auction_start_date and item.auction_start_date <= timezone.now():
                messages.warning(request, "Deleting is not allowed because the auction has already started.")
                return redirect("admin_auctions_list")
            else:
                # Delete the item and its associated image from S3
                try:
                    # Delete image from storage if it exists
                    if item.item_image:
                        item.item_image.delete(save=False)
                    item.delete()
                    messages.success(request, "Item deleted successfully.")
                except Exception as e:
                    messages.error(request, f"Error deleting item: {str(e)}")
                return redirect("admin_auctions_list")
        
        if request.POST.get("editsubmit") and request.POST.get("item_id"):
            item_id = request.POST.get("item_id")
            item = get_object_or_404(ItemModel, id=item_id)
            
            # Check if auction has already started
            if item.auction_start_date and item.auction_start_date <= timezone.now():
                messages.warning(request, "Editing is not allowed because the auction has already started.")
                return redirect("admin_auctions_list")
            else:
                return redirect("admin_add_item_with_id", item_id=item_id)
        
        return redirect("admin_auctions_list")



class adminItemDetailView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        item_id = kwargs.get('item_id')
        item = get_object_or_404(ItemModel, id=item_id)
        
        # Get highest bid
        highest_bid_aggregate = BidModel.objects.filter(item_id=item_id).aggregate(Max("bid_amount"))
        highest_bid = highest_bid_aggregate["bid_amount__max"]
        
        # Get total number of bids
        total_bids = BidModel.objects.filter(item_id=item_id).count()
        
        # Get all bids for history
        all_bids = BidModel.objects.filter(item_id=item_id).order_by('-bid_amount', 'bid_time')
        
        # Check if auction has ended
        current_time = timezone.now()
        is_auction_ended = False
        winner_name = None
        soldout_price = item.soldout_price
        
        if item.auction_end_date and current_time > item.auction_end_date:
            is_auction_ended = True
            
            if highest_bid:
                # Update soldout price if not already set
                if not soldout_price or soldout_price == 0:
                    soldout_price = highest_bid
                    item.soldout_price = soldout_price
                    item.save()
                
                # Get the winning bid
                winning_bid = BidModel.objects.filter(
                    item_id=item_id, 
                    bid_amount=highest_bid
                ).order_by('bid_time').first()
                
                if winning_bid and winning_bid.bidder:
                    winner_name = winning_bid.bidder.username
                else:
                    winner_name = "No winner (error retrieving winner)"
            else:
                winner_name = "No winner (no bids placed)"
    
        
        # Prepare context with all data
        context = {
            'item': item,
            'highest_bid': highest_bid if highest_bid else 0,
            'total_bids': total_bids,
            'all_bids': all_bids,
            'is_auction_ended': is_auction_ended,
            'winner_name': winner_name,
            'soldout_price': soldout_price,
            'current_time': current_time,
            'MEDIA_URL': settings.MEDIA_URL,  # Pass MEDIA_URL to template
        }
        
        return render(request, 'admin_item_details.html', context)

class adminUsersListView(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        users = UserModel.objects.filter(is_staff=False, is_superuser=False).values()
        context = {
            'users':users
        }
        return render(request, template_name="admin_users_list.html",context=context)

import boto3
from django.conf import settings

s3 = boto3.client("s3")

def upload_to_s3(file):
    bucket_name = "x24315851-s3"
    s3.upload_fileobj(file, bucket_name, file.name)
    return file.name



from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import ItemModel


class adminAddItemView(View):

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        item_obj = None
        item_id = kwargs.get("item_id")

        if item_id:
            item_obj = (
                ItemModel.objects.filter(id=item_id)
                .values()
                .first()
            )

        return render(
            request,
            "admin_add_item.html",
            {"item_obj": item_obj},
        )

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):

        item_id = kwargs.get("item_id")
        image_file = request.FILES.get("itemimage")

        if item_id:
            item_obj = ItemModel.objects.get(id=item_id)

            item_obj.item_name = request.POST.get("itemname")
            item_obj.owner_name = request.POST.get("ownername")
            item_obj.item_description = request.POST.get("description")
            item_obj.item_start_price = request.POST.get("startprice")
            item_obj.auction_start_date = request.POST.get("startdate")
            item_obj.auction_end_date = request.POST.get("enddate")

            if image_file:
                item_obj.item_image = image_file   # uploaded to S3

            item_obj.save()

        else:
            ItemModel.objects.create(
                item_name=request.POST.get("itemname"),
                owner_name=request.POST.get("ownername"),
                item_image=image_file,   # uploaded to S3
                item_description=request.POST.get("description"),
                item_start_price=request.POST.get("startprice"),
                auction_start_date=request.POST.get("startdate"),
                auction_end_date=request.POST.get("enddate"),
            )

        return redirect("admin_auctions_list")




class adminAllBids(View):
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        all_bids = BidModel.objects.all().order_by('-bid_time')

        bid_details = []
        for bid in all_bids:
            bid_details.append({
                "bid_id": bid.id,
                "item_image": bid.item.item_image.url if bid.item.item_image else None,
                "item_name": bid.item.item_name,
                "bidder": UserModel.objects.get(id=bid.bidder).username if UserModel.objects.filter(id=bid.bidder).exists() else "Unknown",
                "bid_amount": bid.bid_amount,
                "bid_date_time": bid.bid_time,
            })

        return render(request, "admin_all_bids.html", {"bid_details": bid_details})

