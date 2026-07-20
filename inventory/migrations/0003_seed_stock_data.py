from django.db import migrations


def seed_stock_categories(apps, schema_editor):
    StockCategory = apps.get_model("inventory", "StockCategory")
    categories = [
        ("Vegetables", "Fresh vegetables and greens"),
        ("Fruits", "Fresh fruits"),
        ("Dairy", "Milk, cream, cheese, butter and other dairy products"),
        ("Meat & Poultry", "Chicken, mutton, fish and other meats"),
        ("Bakery", "Bread, buns, pastries and baked goods"),
        ("Beverages", "Soft drinks, juices, and bottled beverages"),
        ("Dry Goods", "Rice, flour, pasta, grains and dry staples"),
        ("Spices & Condiments", "Spices, sauces, pickles and seasonings"),
        ("Cleaning Supplies", "Cleaning and sanitation products"),
        ("Packaging", "Takeaway boxes, bags, and packaging materials"),
    ]
    for name, desc in categories:
        StockCategory.objects.get_or_create(name=name, defaults={"description": desc})


def seed_stock_units(apps, schema_editor):
    StockUnit = apps.get_model("inventory", "StockUnit")
    units = [
        ("Kilogram", "kg"),
        ("Gram", "g"),
        ("Liter", "L"),
        ("Milliliter", "ml"),
        ("Piece", "pc"),
        ("Pack", "pack"),
        ("Box", "box"),
        ("Dozen", "dz"),
        ("Bottle", "btl"),
        ("Bag", "bag"),
    ]
    for name, abbrev in units:
        StockUnit.objects.get_or_create(name=name, defaults={"abbreviation": abbrev})


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_alter_stockmovement_movement_type_stocktransfer"),
    ]

    operations = [
        migrations.RunPython(seed_stock_categories),
        migrations.RunPython(seed_stock_units),
    ]
