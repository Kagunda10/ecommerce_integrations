# Copyright (c) 2021, Frappe and Contributors
# See LICENSE

import unittest
import pytest
from frappe.tests.utils import FrappeTestCase
from unittest.mock import patch

import frappe

from ecommerce_integrations.shopify.constants import (
    ADDRESS_ID_FIELD,
    CUSTOMER_ID_FIELD,
    FULLFILLMENT_ID_FIELD,
    ITEM_SELLING_RATE_FIELD,
    ORDER_ID_FIELD,
    ORDER_ITEM_DISCOUNT_FIELD,
    ORDER_NUMBER_FIELD,
    ORDER_STATUS_FIELD,
    SUPPLIER_ID_FIELD,
)

from .shopify_setting import setup_custom_fields
from ecommerce_integrations.shopify.doctype.shopify_setting.shopify_setting import (
    ShopifySetting,
)
from ecommerce_integrations.shopify.product_class import ShopifyProduct
from ecommerce_integrations.shopify.constants import SETTING_DOCTYPE


class TestShopifySetting(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        frappe.db.sql(
            """delete from `tabCustom Field`
			where name like '%shopify%'"""
        )

    def setUp(self):
        frappe.set_user("Administrator")
        self.setting = frappe.get_doc("Shopify Setting", "Shopify Setting")

    def test_custom_field_creation(self):
        setup_custom_fields()

        created_fields = frappe.get_all(
            "Custom Field",
            filters={"fieldname": ["LIKE", "%shopify%"]},
            fields="fieldName",
            as_list=True,
            order_by=None,
        )

        required_fields = set(
            [
                ADDRESS_ID_FIELD,
                CUSTOMER_ID_FIELD,
                FULLFILLMENT_ID_FIELD,
                ITEM_SELLING_RATE_FIELD,
                ORDER_ID_FIELD,
                ORDER_NUMBER_FIELD,
                ORDER_STATUS_FIELD,
                SUPPLIER_ID_FIELD,
                ORDER_ITEM_DISCOUNT_FIELD,
            ]
        )

        self.assertGreaterEqual(len(created_fields), 13)
        created_fields_set = {d[0] for d in created_fields}

        self.assertEqual(created_fields_set, required_fields)

    def test_validate_settings(self):
        """Test validation of required settings"""
        self.setting.enable_sync = 1
        self.setting.shopify_url = ""
        self.setting.password = ""
        self.setting.warehouse = ""
        self.setting.price_list = ""
        self.setting.weight_uom = ""

        with pytest.raises(frappe.ValidationError):
            self.setting.validate()

    def test_validate_webhooks(self):
        """Test validation of required webhooks"""
        self.setting.enable_sync = 1
        self.setting.webhooks = []

        with pytest.raises(frappe.ValidationError):
            self.setting.validate()

    def test_enable_bulk_import(self):
        """Test bulk import enablement"""
        self.setting.enable_bulk_import = 0
        assert not self.setting.enable_bulk_import()

        self.setting.enable_bulk_import = 1
        assert self.setting.enable_bulk_import()

    def test_import_products_bulk(self):
        """Test bulk product import"""
        self.setting.enable_sync = 1
        self.setting.enable_bulk_import = 1

        with pytest.raises(frappe.ValidationError):
            self.setting.import_products_bulk()

    def test_import_products_bulk_disabled(self):
        """Test bulk product import when disabled"""
        self.setting.enable_sync = 1
        self.setting.enable_bulk_import = 0

        with pytest.raises(frappe.ValidationError):
            self.setting.import_products_bulk()

    def test_import_products_bulk_integration_disabled(self):
        """Test bulk product import when integration is disabled"""
        self.setting.enable_sync = 0
        self.setting.enable_bulk_import = 1

        with pytest.raises(frappe.ValidationError):
            self.setting.import_products_bulk()
