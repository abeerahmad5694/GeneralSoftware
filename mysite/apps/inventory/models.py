from django.db import models

# Create your models here.


class ItemBrand(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


class ItemCompany(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


class ItemCategory(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class ItemSubCategory(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class ItemType(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class Unit(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name




class Inventory(models.Model):
    company = models.ForeignKey('configuration.Company', on_delete=models.CASCADE, default=None)
    branch = models.ForeignKey('configuration.Branch', on_delete=models.CASCADE, default=None)

    inv_id = models.AutoField(primary_key=True)

    prod_name = models.CharField(max_length=255, default=None)
    prod_name_ur = models.CharField(
        max_length=500, null=True, blank=True, default=None,
        verbose_name="Urdu Item Name",
        help_text="آئٹم کا اردو نام — Nastaleeq font will be used in Urdu/Bilingual invoices.",
    )
    alias_name = models.CharField(max_length=255, null=True, blank=True, default=None)

    ws_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    ws_disc_per = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None)

    market_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    last_pur_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)

    base_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    base_uom = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='base_inv')
    base_disc_per = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None)
    min_base_sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)

    carton_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    carton_uom = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='carton_inv')
    carton_qty = models.IntegerField(null=True, blank=True, default=None)
    carton_disc_per = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None)

    dzn_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=None)
    dzn_uom = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='dzn_inv')
    dzn_qty = models.IntegerField(null=True, blank=True, default=None)
    dzn_disc_per = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, default=None)

    date = models.DateField(null=True, blank=True, default=None)
    dateent = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.CharField(max_length=100, null=True, blank=True, default=None)
    updated_by = models.CharField(max_length=100, null=True, blank=True, default=None)

    barcode = models.CharField(max_length=255, null=True, blank=True, default=None)
    manualbc = models.CharField(max_length=255, null=True, blank=True, default=None)
    barcode2 = models.CharField(max_length=255, null=True, blank=True, default=None)

    manufacturer = models.ForeignKey(ItemCompany, on_delete=models.CASCADE ,null=True,blank=True,default=None)
    brand = models.ForeignKey(ItemBrand, on_delete=models.CASCADE ,null=True,blank=True,default=None)
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE ,null=True,blank=True,default=None)
    subcategory = models.ForeignKey(ItemSubCategory, on_delete=models.CASCADE ,null=True,blank=True,default=None)

    active = models.BooleanField(null=True, blank=True, default=True)
    is_deleted = models.BooleanField(null=True, blank=True, default=False)


    min_stock = models.IntegerField(null=True, blank=True, default=None)
    max_stock = models.IntegerField(null=True, blank=True, default=None)
    reorder = models.IntegerField(null=True, blank=True, default=None)

    product_location = models.CharField(max_length=255, null=True, blank=True, default=None)

    expiry_date = models.DateField(null=True, blank=True, default=None)

    remaining_qty = models.IntegerField(null=True, blank=True, default=None)

    bal_qty = models.IntegerField(null=True, blank=True, default=0)
    # last_pur_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)

    sold_qty = models.IntegerField(null=True, blank=True, default=None)
    sold_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)

    purchase_qty = models.IntegerField(null=True, blank=True, default=None)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)

    salesman_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)

    def __str__(self):
        return self.prod_name or f"Product {self.inv_id}"

    class Meta:
        indexes = [
            models.Index(fields=['company', 'barcode'], name='idx_inv_comp_bar'),
            models.Index(fields=['company', 'manualbc'], name='idx_inv_comp_mbc'),
            models.Index(fields=['company', 'barcode2'], name='idx_inv_comp_b2'),
            models.Index(fields=['company', 'inv_id'], name='idx_inv_comp_invid'),
            models.Index(fields=['company', 'alias_name'], name='idx_inv_comp_alias'),
            models.Index(fields=['company', 'prod_name'], name='idx_inv_comp_prod'),
        ]




# -- Add this once in mysql for full text index in mysql
# ALTER TABLE inventory_inventory ADD FULLTEXT(prod_name, alias_name);