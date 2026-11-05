# GoliathFactory portal views

Static HTML frames for tablet-friendly shop-floor and quality workflows. GoliathApp resolves `portal."NodeInfos"."FrameKey"` through `portal/frames.json` (same pattern as [GoliathCrop](https://github.com/Goliath-Research/GoliathCrop/tree/main/portal)).

## Local preview

Serve the `portal/` directory over HTTP and open `views/shell.html`, or load a frame directly (for example `views/shop-floor.html?work_order_id=101`). Without `window.GOLIATH_SESSION`, views read `static/demo-fixtures.json`.

## Frames

| FrameKey | View |
| --- | --- |
| `mfg.work_order.list_open` | Work order board |
| `mfg.traveler_step.by_work_order` | Shop-floor traveler (start → sign-off) |
| `mfg.inspection_result.by_lot` | Inspection entry |
| `mfg.ncr.list_open` | NCR queue and MRB disposition |
| `mfg.lot.genealogy` | Lot trace tree + CoC stub action |
| `mfg.inv.receive_stub` | Receiving hook (until GoliathApp `inv` merges) |
| `mfg.label.traveler_print` | Printable traveler label (browser print) |

API helpers live in `static/mfg-api.js` (`MfgPortal.runSemanticRequest`, `MfgPortal.runAction`).
