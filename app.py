from quipubase import Collection


class Item(Collection):
    price: float
    qty: int
    name: str


item = Item(name="pete", price=20, qty=1)
item.create()
items = Item.find(price=20.0)
print(list(items))
