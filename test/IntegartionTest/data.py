mealkit_valid_data = {
    "product_name": "Bacon Wrapped Veggies test",
    "product_type": "MK",
    "day_before_expiry": 5,
    "description": "A delicious and easy-to-make appetizer featuring crispy bacon wrapped around fresh mini cucumbers and carrots.",
    "article_md": "Great Value Thick Sliced Bacon (10 slices) Fresh Mini Cucumbers (2 pieces) Fresh Whole Carrots (2 pieces) Fresh Italian Parsley (for garnish)",
    "instructions": [
        "Wash and cut the mini cucumbers and carrots into long sticks (about 3-4 inches).",
        "Wrap each vegetable stick with a slice of bacon and secure it with a toothpick."
    ],
    "infos": {
        "Servings": "4-5 people",
        "Preparation Time": "20 minutes"
    },
    "ingredients": {
        "Bacon": 10,
        "Mini Cucumbers": 2,
        "Carrots": 2,
        "Parsley": 1
    }
}
mealkit_no_product_name = {
    **mealkit_valid_data, #** dùng để unpacking thằng sau dấu * và ghi đè nội dung lên nó
    "product_name": ""
}

mealkit_no_product_type = {
    **mealkit_valid_data,
    "product_type": ""
}

mealkit_no_day_before = {
    **mealkit_valid_data,
    "day_before_expiry": None
}

mealkit_no_desc = {
    **mealkit_valid_data,
    "description": ""
}

mealkit_no_article = {
    **mealkit_valid_data,
    "article_md": ""
}
mealkit_no_infos = {
    **mealkit_valid_data,
      "infos": {
        "": "",
        "": ""
  }
}
mealkit_no_ingredients = {
    **mealkit_valid_data,
      "ingredients": {
        "": "",
        "": ""
  }
}
fetch_ingredients_valid_params = {
    "search": "Great Value Ground",
    "index": 0,
    "size": 7
}

fetch_ingredients_not_found_params = {
    "search": "Not Exist",
    "index": 0,
    "size": 7
}

coupon_disable_sucess = {
    "coupon_id": "CPTEST"
}



main_image_path_mealkit = "test/IntegartionTest/image_test/1_BaconWrappedVeggies.jpg"
additional_image_path_mealkit = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"
additional_image_path_mealkit2 = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"