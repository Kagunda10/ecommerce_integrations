# Copyright (c) 2021, Frappe and contributors
# For license information, please see LICENSE

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils import get_datetime, cint, cstr
from shopify.collection import PaginatedIterator
from shopify.resources import Location

from ecommerce_integrations.controllers.setting import (
    ERPNextWarehouse,
    IntegrationWarehouse,
    SettingController,
)
from ecommerce_integrations.shopify import connection
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
from ecommerce_integrations.shopify.utils import (
    ensure_old_connector_is_disabled,
    migrate_from_old_connector,
    create_shopify_log,
)
from ecommerce_integrations.shopify.product_class import ShopifyProduct


class ShopifySetting(SettingController):
    def is_enabled(self) -> bool:
        return cint(self.enable_sync) == 1

    def validate(self):
        ensure_old_connector_is_disabled()

        if self.shopify_url:
            self.shopify_url = self.shopify_url.replace("https://", "")
        self._handle_webhooks()
        self._validate_warehouse_links()
        self._initalize_default_values()

        if self.is_enabled():
            setup_custom_fields()

        self.validate_settings()
        self.validate_webhooks()

    def on_update(self):
        if self.is_enabled() and not self.is_old_data_migrated:
            migrate_from_old_connector()

        if self.has_value_changed("enable_sync"):
            if self.enable_sync:
                self.register_webhooks()
            else:
                self.unregister_webhooks()

    def _handle_webhooks(self):
        if self.is_enabled() and not self.webhooks:
            new_webhooks = connection.register_webhooks(
                self.shopify_url, self.get_password("password")
            )

            if not new_webhooks:
                msg = _("Failed to register webhooks with Shopify.") + "<br>"
                msg += _("Please check credentials and retry.") + " "
                msg += _("Disabling and re-enabling the integration might also help.")
                frappe.throw(msg)

            for webhook in new_webhooks:
                self.append(
                    "webhooks", {"webhook_id": webhook.id, "method": webhook.topic}
                )

        elif not self.is_enabled():
            connection.unregister_webhooks(
                self.shopify_url, self.get_password("password")
            )

            self.webhooks = list()  # remove all webhooks

    def _validate_warehouse_links(self):
        for wh_map in self.shopify_warehouse_mapping:
            if not wh_map.erpnext_warehouse:
                frappe.throw(_("ERPNext warehouse required in warehouse map table."))

    def _initalize_default_values(self):
        if not self.last_inventory_sync:
            self.last_inventory_sync = get_datetime("1970-01-01")

    @frappe.whitelist()
    @connection.temp_shopify_session
    def update_location_table(self):
        """Fetch locations from shopify and add it to child table so user can
        map it with correct ERPNext warehouse."""

        self.shopify_warehouse_mapping = []
        for locations in PaginatedIterator(Location.find()):
            for location in locations:
                self.append(
                    "shopify_warehouse_mapping",
                    {
                        "shopify_location_id": location.id,
                        "shopify_location_name": location.name,
                    },
                )

    def get_erpnext_warehouses(self) -> list[ERPNextWarehouse]:
        return [wh_map.erpnext_warehouse for wh_map in self.shopify_warehouse_mapping]

    def get_erpnext_to_integration_wh_mapping(
        self,
    ) -> dict[ERPNextWarehouse, IntegrationWarehouse]:
        return {
            wh_map.erpnext_warehouse: wh_map.shopify_location_id
            for wh_map in self.shopify_warehouse_mapping
        }

    def get_integration_to_erpnext_wh_mapping(
        self,
    ) -> dict[IntegrationWarehouse, ERPNextWarehouse]:
        return {
            wh_map.shopify_location_id: wh_map.erpnext_warehouse
            for wh_map in self.shopify_warehouse_mapping
        }

    def validate_settings(self):
        if self.enable_sync:
            if not self.shopify_url:
                frappe.throw(_("Shopify URL is required"))
            if not self.password:
                frappe.throw(_("Password is required"))
            if not self.warehouse:
                frappe.throw(_("Warehouse is required"))
            if not self.price_list:
                frappe.throw(_("Price List is required"))
            if not self.weight_uom:
                frappe.throw(_("Weight UOM is required"))

    def validate_webhooks(self):
        if self.enable_sync:
            if not self.webhooks:
                frappe.throw(_("Webhooks are required"))

    def register_webhooks(self):
        try:
            connection.register_webhooks(
                self.shopify_url, self.get_password("password")
            )
            create_shopify_log(
                status="Success",
                message="Webhooks registered successfully",
                response_data={},
            )
        except Exception as e:
            create_shopify_log(
                status="Error",
                message=f"Failed to register webhooks: {str(e)}",
                response_data={"error": str(e)},
            )
            frappe.throw(_("Failed to register webhooks: {0}").format(str(e)))

    def unregister_webhooks(self):
        try:
            connection.unregister_webhooks(
                self.shopify_url, self.get_password("password")
            )
            create_shopify_log(
                status="Success",
                message="Webhooks unregistered successfully",
                response_data={},
            )
        except Exception as e:
            create_shopify_log(
                status="Error",
                message=f"Failed to unregister webhooks: {str(e)}",
                response_data={"error": str(e)},
            )
            frappe.throw(_("Failed to unregister webhooks: {0}").format(str(e)))

    def enable_bulk_import(self) -> bool:
        return cint(self.enable_bulk_import) == 1

    def import_products_bulk(self) -> None:
        """Import all products from Shopify using bulk operations API"""
        if not self.is_enabled():
            frappe.throw(_("Shopify integration is not enabled"))
        if not self.enable_bulk_import():
            frappe.throw(_("Bulk import is not enabled"))

        try:
            ShopifyProduct.import_products_bulk()
        except Exception as e:
            create_shopify_log(
                status="Error",
                message=f"Bulk product import failed: {str(e)}",
                response_data={"error": str(e)},
            )
            frappe.throw(_("Bulk product import failed: {0}").format(str(e)))


def setup_custom_fields():
    custom_fields = {
        "Item": [
            dict(
                fieldname=ITEM_SELLING_RATE_FIELD,
                label="Shopify Selling Rate",
                fieldtype="Currency",
                insert_after="standard_rate",
            )
        ],
        "Customer": [
            dict(
                fieldname=CUSTOMER_ID_FIELD,
                label="Shopify Customer Id",
                fieldtype="Data",
                insert_after="series",
                read_only=1,
                print_hide=1,
            )
        ],
        "Supplier": [
            dict(
                fieldname=SUPPLIER_ID_FIELD,
                label="Shopify Supplier Id",
                fieldtype="Data",
                insert_after="supplier_name",
                read_only=1,
                print_hide=1,
            )
        ],
        "Address": [
            dict(
                fieldname=ADDRESS_ID_FIELD,
                label="Shopify Address Id",
                fieldtype="Data",
                insert_after="fax",
                read_only=1,
                print_hide=1,
            )
        ],
        "Sales Order": [
            dict(
                fieldname=ORDER_ID_FIELD,
                label="Shopify Order Id",
                fieldtype="Small Text",
                insert_after="title",
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_NUMBER_FIELD,
                label="Shopify Order Number",
                fieldtype="Small Text",
                insert_after=ORDER_ID_FIELD,
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_STATUS_FIELD,
                label="Shopify Order Status",
                fieldtype="Small Text",
                insert_after=ORDER_NUMBER_FIELD,
                read_only=1,
                print_hide=1,
            ),
        ],
        "Sales Order Item": [
            dict(
                fieldname=ORDER_ITEM_DISCOUNT_FIELD,
                label="Shopify Discount per unit",
                fieldtype="Float",
                insert_after="discount_and_margin",
                read_only=1,
            ),
        ],
        "Delivery Note": [
            dict(
                fieldname=ORDER_ID_FIELD,
                label="Shopify Order Id",
                fieldtype="Small Text",
                insert_after="title",
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_NUMBER_FIELD,
                label="Shopify Order Number",
                fieldtype="Small Text",
                insert_after=ORDER_ID_FIELD,
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_STATUS_FIELD,
                label="Shopify Order Status",
                fieldtype="Small Text",
                insert_after=ORDER_NUMBER_FIELD,
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=FULLFILLMENT_ID_FIELD,
                label="Shopify Fulfillment Id",
                fieldtype="Small Text",
                insert_after="title",
                read_only=1,
                print_hide=1,
            ),
        ],
        "Sales Invoice": [
            dict(
                fieldname=ORDER_ID_FIELD,
                label="Shopify Order Id",
                fieldtype="Small Text",
                insert_after="title",
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_NUMBER_FIELD,
                label="Shopify Order Number",
                fieldtype="Small Text",
                insert_after=ORDER_ID_FIELD,
                read_only=1,
                print_hide=1,
            ),
            dict(
                fieldname=ORDER_STATUS_FIELD,
                label="Shopify Order Status",
                fieldtype="Small Text",
                insert_after=ORDER_ID_FIELD,
                read_only=1,
                print_hide=1,
            ),
        ],
    }

    create_custom_fields(custom_fields)
