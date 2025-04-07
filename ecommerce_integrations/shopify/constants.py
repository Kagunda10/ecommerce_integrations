# Copyright (c) 2021, Frappe and contributors
# For license information, please see LICENSE

"""Constants used in Shopify integration."""

MODULE_NAME = "shopify"

SETTING_DOCTYPE = "Shopify Setting"  # moved to setting_constants.py

ITEM_SELLING_RATE_FIELD = "shopify_selling_rate"
SUPPLIER_ID_FIELD = "shopify_supplier_id"
CUSTOMER_ID_FIELD = "shopify_customer_id"
ADDRESS_ID_FIELD = "shopify_address_id"
ORDER_ID_FIELD = "shopify_order_id"
ORDER_NUMBER_FIELD = "shopify_order_number"
ORDER_STATUS_FIELD = "shopify_order_status"
ORDER_ITEM_DISCOUNT_FIELD = "shopify_item_discount"
FULLFILLMENT_ID_FIELD = "shopify_fulfillment_id"

SHOPIFY_VARIANTS_ATTR_LIST = ["option1", "option2", "option3"]

# ERPNext already defines the default UOMs from Shopify but names are different
WEIGHT_TO_ERPNEXT_UOM_MAP = {
    "g": "Gram",
    "kg": "Kg",
}
