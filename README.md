# Kitchen Display Module

> **Note**: This module is currently disabled.

Kitchen Display System (KDS) for managing order preparation, station routing, and kitchen workflow.

## Features

- Real-time kitchen display for incoming orders
- Ready queue for completed orders awaiting pickup
- Kitchen station management (prep, grill, fry, etc.)
- Order history with audit trail
- Configurable timer with warning and critical thresholds
- Auto-accept and auto-bump capabilities
- Sound notifications for new orders and rush orders
- Color-coded order status indicators
- Per-hub display and notification settings
- Detailed order action logging (received, accepted, started, bumped, completed, served, recalled, cancelled, priority changed)

## Installation

This module is installed automatically via the ERPlora Marketplace.

**Dependencies**: Requires `orders` module.

## Configuration

Access settings via: **Menu > Kitchen > Settings**

Configurable options include:

- **Display**: Auto-accept orders, show timer, warning/critical time thresholds, items per page, auto-refresh interval
- **Sound**: Enable/disable sound notifications for new orders and rush orders
- **Auto-bump**: Enable automatic bumping with configurable delay
- **Color coding**: Enable/disable color-coded order status

## Usage

Access via: **Menu > Kitchen**

### Views

| View | URL | Description |
|------|-----|-------------|
| Display | `/m/kitchen/display/` | Real-time kitchen display with active orders |
| Ready | `/m/kitchen/ready/` | Orders ready for pickup or serving |
| Stations | `/m/kitchen/stations/` | Manage kitchen stations |
| History | `/m/kitchen/history/` | View completed order history |
| Settings | `/m/kitchen/settings/` | Configure KDS display and notification settings |

## Models

| Model | Description |
|-------|-------------|
| `KitchenSettings` | Per-hub configuration for display options, sound notifications, auto-bump behavior, and color coding (singleton per hub) |
| `KitchenOrderLog` | Audit trail for kitchen order actions, tracking which user performed what action on which order/item at which station |

## Permissions

| Permission | Description |
|------------|-------------|
| `kitchen.view_kitchensettings` | View kitchen display settings |
| `kitchen.change_kitchensettings` | Modify kitchen display settings |
| `kitchen.view_kitchenorderlog` | View kitchen order action logs |

## Integration with Other Modules

- **orders**: Kitchen stations, orders, and station routing are defined in the orders module. The kitchen module references `orders.Order`, `orders.OrderItem`, and `orders.KitchenStation` models.

## License

MIT

## Author

ERPlora Team - support@erplora.com
