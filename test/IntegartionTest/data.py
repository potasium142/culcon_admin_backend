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

product_update_info = {
  "day_before_expiry": 10,
  "description": "short desc",
  "article_md": "test article_md update",
  "instructions": [
    "update instuctions"
  ],
  "infos": {
    "weight": "800g"
  }
}

product_update_info_blankDayExpiry = {
  "day_before_expiry": None,
  "description": "short desc",
  "article_md": "test article_md update",
  "instructions": [
    "update instuctions"
  ],
  "infos": {
    "weight": "800g"
  }
}


product_update_info_ExpiredDayEualZero = {
  "day_before_expiry": 0,
  "description": "short desc",
  "article_md": "test article_md update",
  "instructions": [
    "update instuctions"
  ],
  "infos": {
    "weight": "800g"
  }
}

product_update_info_ExpiredDayNegative = {
  "day_before_expiry": -10,
  "description": "short desc",
  "article_md": "test article_md update",
  "instructions": [
    "update instuctions"
  ],
  "infos": {
    "weight": "800g"
  }
}

product_update_info_BlankKeyInfo = {
  "day_before_expiry": -10,
  "description": "short desc",
  "article_md": "test article_md update",
  "instructions": [
    "update instuctions"
  ],
  "infos": {
    "": "800g"
  }
}

product_update_quantity_valid = {
    "prod_id": "VEG_Potato",
    "quantity": 50,
    "in_price": 15000
}

product_update_quantity_missing_price = {
    "prod_id": "VEG_Potato",
    "quantity": 20,
    "in_price": None  
}

product_update_quantity_missing_prodId = {
    "prod_id": "",
    "quantity": 20,
    "in_price": 100  
}

product_update_quantity_missing_quantity = {
    "prod_id": "VEG_Potato",
    "quantity": None,
    "in_price": 15000
}

product_update_quantity_quantityNegative = {
    "prod_id": "VEG_Potato",
    "quantity": -10,
    "in_price": 15000
}

product_update_quantity_inPriceNegative = {
    "prod_id": "VEG_Potato",
    "quantity": 10,
    "in_price": -15000
}

# data.py

product_update_price_valid = {
    "product_id": "VEG_Potato",
    "price": 1000,
    "sale_percent": 10
}

product_update_price_Negative_price = {
    "product_id": "VEG_Potato",
    "price": -500,
    "sale_percent": 10
}

product_update__price_Negative_salePercent = {
    "product_id": "VEG_Potato",
    "price": 1000,
    "sale_percent": -10
}

product_update_price_blank_productId = {
    "product_id": "",
    "price": 1000,
    "sale_percent": 10
}

product_update_price_blank_price = {
    "product_id": "",
    "price": 1000,
    "sale_percent": 10
}

product_update_price_blank_sale_percent = {
    "product_id": "",
    "price": 1000,
    "sale_percent": None
}

product_history_stock_valid = {
    "prod_id" : "VEG_Potato",
    "index" : 0,
    "size" : 7
}

product_history_stock_prodId_notExist = {
    "prod_id" : "notexist",
    "index" : 0,
    "size" : 7
}

product_history_price_valid = {
    "prod_id" : "VEG_Potato",
    "index" : 0,
    "size" : 7
}

product_history_price_prodId_notExist = {
    "prod_id" : "notexist",
    "index" : 0,
    "size" : 7
}
main_image_path_mealkit = "test/IntegartionTest/image_test/1_BaconWrappedVeggies.jpg"
additional_image_path_mealkit = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"
additional_image_path_mealkit2 = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"