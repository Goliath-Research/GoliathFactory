# Accounting adapters

GoliathFactory syncs POs and receipts to external GL/AP systems through a small Python adapter interface. **No credentials ship in this repository.**

## Interface

Module: `goliath_factory.accounting`

| Method | Purpose |
| --- | --- |
| `health_check()` | Validate env configuration |
| `push_purchase_order(payload)` | Export PO header/lines after `inv` approval |
| `push_receipt(payload)` | Export receipt / vendor bill after receive |

Implementations:

| Adapter | Module | When to use |
| --- | --- | --- |
| QuickBooks Online | `quickbooks_online.QuickBooksOnlineAdapter` | Pilot shops already on QBO (recommended first) |
| ERPNext | `erpnext.ErpNextAdapter` | Free self-hosted GL for buyers without accounting |

Workers (Phase 3+) should select an adapter via deployment config, e.g. `MFG_ACCOUNTING_ADAPTER=quickbooks_online`.

## Environment variables

### QuickBooks Online

| Variable | Description |
| --- | --- |
| `MFG_QBO_CLIENT_ID` | Intuit OAuth client id |
| `MFG_QBO_CLIENT_SECRET` | Intuit OAuth client secret |
| `MFG_QBO_REFRESH_TOKEN` | Refresh token for the company connection |
| `MFG_QBO_REALM_ID` | QuickBooks company (realm) id |
| `MFG_QBO_ENV` | `sandbox` (default) or `production` |

### ERPNext

| Variable | Description |
| --- | --- |
| `MFG_ERPNEXT_BASE_URL` | Site root URL |
| `MFG_ERPNEXT_API_KEY` | Frappe API key |
| `MFG_ERPNEXT_API_SECRET` | Frappe API secret |

Adapters in this repo return **`stub_ready`** payloads until a deployment wires real HTTP calls.
