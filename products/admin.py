# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib import admin

from products.models import PackageCartridge, PackageCartridgeRecipe, \
    CartridgeRecipe, Supply, SupplyLocation, SuppliesCategory, Cartridge, \
    ExtraIngredient, Presentation


@admin.register(SuppliesCategory)
class AdminSuppliesCategory(admin.ModelAdmin):
    list_display = ('name', 'image',)


@admin.register(SupplyLocation)
class AdminSupplyLocation(admin.ModelAdmin):
    list_display = ('location', 'branch_office',)


@admin.register(Supply)
class AdminSupply(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'supplier')
    list_display_links = ('id', 'name')
    ordering = ['name']


class CartridgeRecipeInline(admin.TabularInline):
    model = CartridgeRecipe
    extra = 0


class ExtraIngredientInline(admin.TabularInline):
    model = ExtraIngredient
    extra = 0


@admin.register(Cartridge)
class AdminCartridge(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'category', 'is_active','created_at', 'get_image', 'image')
    list_display_links = ('id', 'name')
    list_editable = ('price', 'image', 'category', 'is_active',)
    inlines = [CartridgeRecipeInline, ExtraIngredientInline]
    ordering = ['name']

@admin.register(Presentation)
class AdminPresentation(admin.ModelAdmin):
    list_display = ('id','supply', 'measurement_quantity', 'measurement_unit')
    ordering = ['supply']


class PackageCartridgeRecipeInline(admin.TabularInline):
    model = PackageCartridgeRecipe
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'cartridge':
            kwargs['queryset'] = Cartridge.objects.order_by('name')
        return super(PackageCartridgeRecipeInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(PackageCartridge)
class AdminPackageCartridge(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'is_active', 'package_recipe')
    list_display_links = ('id', 'name')
    list_editable = ('price', 'is_active',)
    inlines = [PackageCartridgeRecipeInline]
    ordering = ['name']
