<div align="center">
    <img src="https://frappecloud.com/files/ERPNext%20-%20Ecommerce%20Integrations.png" height="128">
    <h2>Ecommerce Integrations for ERPNext</h2>

[![CI](https://github.com/frappe/ecommerce_integrations/actions/workflows/ci.yml/badge.svg)](https://github.com/frappe/ecommerce_integrations/actions/workflows/ci.yml)
  
</div>

### Currently supported integrations:

- Shopify - [User documentation](https://docs.erpnext.com/docs/v13/user/manual/en/erpnext_integration/shopify_integration)
  - Standard product import
  - **NEW**: Bulk product import using Shopify's Bulk Operations API
  - Order synchronization
  - Inventory management
  - Customer synchronization
- Unicommerce - [User Documentation](https://docs.erpnext.com/docs/v13/user/manual/en/erpnext_integration/unicommerce_integration)
- Zenoti - [User documentation](https://docs.erpnext.com/docs/v13/user/manual/en/erpnext_integration/zenoti_integration)
- Amazon - [User documentation](https://docs.erpnext.com/docs/v13/user/manual/en/erpnext_integration/amazon_integration)

### 🚀 New Features

#### Shopify Bulk Product Import
- Import large product catalogs efficiently using Shopify's Bulk Operations API
- Support for long-running imports (up to 10 days)
- Progress tracking and error handling
- Toggle between standard and bulk import modes
- Automatic retry mechanism for failed operations

### Installation

- Frappe Cloud Users can install [from Marketplace](https://frappecloud.com/marketplace/apps/ecommerce_integrations).
- Self Hosted users can install using Bench:

```bash
# Production installation
$ bench get-app ecommerce_integrations --branch main

# OR development install
$ bench get-app ecommerce_integrations --branch develop

# install on site
$ bench --site sitename install-app ecommerce_integrations
```

After installation follow user documentation for each integration to set it up.

### Contributing

- Follow general [ERPNext contribution guideline](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)
- Send PRs to `develop` branch only.

### Development setup

- Enable developer mode.
- If you want to use a tunnel for local development. Set `localtunnel_url` parameter in your site_config file with ngrok / localtunnel URL. This will be used in most places to register webhooks. Likewise, use this parameter wherever you're sending current site URL to integrations in development mode.

### Testing

The app includes comprehensive test coverage for all features, including the new bulk import functionality. To run tests:

```bash
# Install test dependencies
$ pip install -e ".[test]"

# Run tests
$ pytest ecommerce_integrations/shopify/tests/
```

#### License

GNU GPL v3.0
