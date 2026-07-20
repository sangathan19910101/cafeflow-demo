class MenuService:

    @staticmethod
    def toggle_category(category):

        category.is_active = (
            not category.is_active
        )

        category.save(
            update_fields=[
                "is_active",
            ]
        )

        return category

    @staticmethod
    def toggle_item_availability(item):

        item.is_available = (
            not item.is_available
        )

        item.save(
            update_fields=[
                "is_available",
            ]
        )

        return item
