import json
from main import db, Item

order_items_json = '[{"id": null, "item_id": 1, "quantity": 2}]'
order_items = json.loads(order_items_json)

# Get the item details for each order item
for item in order_items:
    item_id = item['item_id']
    item_details = Item.query.get(item_id)

    # Do something with the item details
    print(item_details.name)
    print(item_details.price)
    print(item_details.detailed_description)