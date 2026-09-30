from django.urls import path
from .views.inventory import inventory, get_item_by_id
from apps.inventory.api import inventory as api


urlpatterns = [
    path('', inventory, name='inventory'),
    path('get_item_by_id/<int:inv_id>/', get_item_by_id, name='get_item_by_id'),
]

urlpatterns += [
    path('api/save_update_inventory', api.save_update_inventory, name='save_update_inventory'),
    path('api/delete_inventory_item/<int:inv_id>/', api.delete_inventory, name='delete_inventory'),
]