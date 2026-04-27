from django.shortcuts import render

# Create your views here.
from django.shorcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import django.core.exceptions import PermissionDenied
from .models import Product
from .forms import ProductForm

def _require_vendor(user):
    """
    This check runs in multiple views (create, update, delete).
    One function = one place to change if the rule ever changes.
    Raises PermissionDenied instead of returning False
    so the view doesn't need an if/else — it either passes or stops.
    :param user:
    :return:
    """
    if not user.is_vendor:
        raise PermissionDenied

def product_list(request):
    """
    WHY select_related('vendor', 'category')?
    Without it, Django fires a separate SQL query for every product
    to fetch its vendor and category — called an N+1 query.
    With it, Django fetches everything in ONE query using a SQL JOIN.
    On 100 products: 1 query vs 201 queries.
    :param request:
    :return:
    """

    products = (
        Product.objects
        .select_related('vendor', 'category') # join request
        .order_by('-created_at')
    )
    return render(request, 'products/product_list.html', {'products': products})

@login_required #redirect to login page if user is not authenticated
def product_create(request):
    """
    WHY check vendor BEFORE processing the form?
    Fail fast — don't process, validate, or touch the DB
    if the user has no right to be here in the first place.
    """
    _require_vendor(request.user)

    if request.method == 'POST':
        form = ProductForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            product = form.save(commit=False) # get object in memory, don't save yet
            product.vendor = request.user # owner is assigned server-side and never from form
            product.save()
            return redirect('product_list')

        else:
            form = ProductForm()

        return render(request,'products/product_form.html',{'form': form})

@login_required
def product_update(request,slug):
    """

    :param request:
    :return:
    """
    product = get_object_or_404(Product, slug=slug)
    _require_vendor(request.user)