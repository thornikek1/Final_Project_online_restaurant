import requests
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render, get_object_or_404
from .models import Product
from django.http import JsonResponse, HttpResponseBadRequest
import json
import logging
logger = logging.getLogger(__name__)



API_BASE_URL = "https://restaurant.stepprojects.ge/api"

def get_cart_count():
    basket = requests.get(f"{API_BASE_URL}/Baskets/GetAll").json()
    return sum(item['quantity'] for item in basket)

def dish_list(request):
    categories = requests.get(f"{API_BASE_URL}/Categories/GetAll").json()
    products = requests.get(f"{API_BASE_URL}/Products/GetAll").json()

    # Filtering logic
    category_id = request.GET.get('category_id')
    vegeterian = request.GET.get('vegeterian')
    nuts = request.GET.get('nuts')
    spiciness = request.GET.get('spiciness')

    params = {}
    if category_id:
        params['categoryId'] = category_id
    if vegeterian:
        params['vegeterian'] = vegeterian
    if nuts:
        params['nuts'] = nuts
    if spiciness:
        params['spiciness'] = spiciness

    if params:
        products = requests.get(f"{API_BASE_URL}/Products/GetFiltered", params=params).json()

    context = {
        'categories': categories,
        'products': products,
        'cart_count': get_cart_count()
    }
    return render(request, 'restaurant/dish_list.html', context)

def cart(request):
    basket = requests.get(f"{API_BASE_URL}/Baskets/GetAll").json()
    total_price = sum(item['quantity'] * item['price'] for item in basket)
    context = {
        'basket': basket,
        'total_price': total_price
    }
    return render(request, 'restaurant/cart.html', context)


@csrf_exempt
def add_to_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

        csrf_token = request.headers.get('X-CSRFToken', '')
        quantity = 1
        price = float(product.price)

        payload = {
            "quantity": quantity,
            "price": price,
            "productId": int(product_id)
        }

        url = f"{API_BASE_URL}/Baskets/AddToBasket"
        headers = {
            'Content-Type': 'application/json',
            'accept': 'application/json',
            'X-CSRFToken': csrf_token
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response_data = response.json()

            if response.status_code == 201:
                # Fetch updated cart count
                cart_count = get_cart_count()

                # Retrieve data for dish list page
                categories = requests.get(f"{API_BASE_URL}/Categories/GetAll").json()
                products = requests.get(f"{API_BASE_URL}/Products/GetAll").json()

                context = {
                    'categories': categories,
                    'products': products,
                    'cart_count': cart_count
                }
                return render(request, 'restaurant/dish_list.html', context)
            else:
                return JsonResponse({'error': 'Failed to add to cart', 'details': response_data}, status=response.status_code)
        
        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': str(e)}, status=500)
        except ValueError:
            return JsonResponse({'error': 'Invalid response from API'}, status=500)
    
    return HttpResponseBadRequest('Invalid request method')


@csrf_exempt
def update_cart(request):
    if request.method == 'PUT':  # Ensure the method is 'PUT'
        try:
            # Assuming the request body contains JSON data
            data = json.loads(request.body.decode('utf-8'))
            quantity = data.get('quantity')
            product_id = data.get('product_id')  # Ensure this matches the HTML form input name

            if not (quantity and product_id):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Prepare payload for updating basket
            payload = {
                "quantity": int(quantity),
                "productId": int(product_id)
            }

            # Send PUT request to update basket
            update_response = requests.put(f"{API_BASE_URL}/Baskets/UpdateBasket/", json=payload)
            update_response.raise_for_status()

            return JsonResponse({'success': 'Quantity updated successfully'})

        except requests.exceptions.HTTPError as http_err:
            return JsonResponse({'error': f'HTTP error occurred: {http_err}'}, status=500)

        except requests.exceptions.RequestException as req_err:
            return JsonResponse({'error': f'Request exception occurred: {req_err}'}, status=500)

        except (KeyError, ValueError, json.JSONDecodeError) as json_err:
            return JsonResponse({'error': f'JSON parsing error occurred: {json_err}'}, status=500)

    return HttpResponseBadRequest('Invalid request method')




@csrf_exempt
def remove_from_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        if product_id:
            api_url = f"{API_BASE_URL}/Baskets/DeleteProduct/{product_id}"

            # Make the DELETE request
            response = requests.delete(api_url)

            if response.status_code == 204:
                return JsonResponse({'success': 'Product removed from cart'})
            else:
                return JsonResponse({'error': 'Failed to remove from cart'}, status=response.status_code)
        else:
            return JsonResponse({'error': 'Product ID not provided'}, status=400)

    return HttpResponseBadRequest('Invalid request method')


