test_coupon_create_success = {
    "expire_date": "2026-04-10",
  "sale_percent": 10,
  "usage_amount": 5,
  "minimum_price": 100,
  "id": "CPTESTING"
}

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

create_account_manager_success = {
    "username": "manager_123",
    "password": "123456",
    "type": 2,
    "employee_info": {
        "ssn": "123456789",
        "phonenumber": "09910433142",
        "realname": "Nguyen Van A",
        "email": "manager@example.com",
        "dob": "1990-01-01"
    },
    "account_status": "ACTIVE"
}
staff_fetch_all = {
    "id": "",
    "index": 0,
    "size": 7
}

staff_fetch_oneaccount = {
    "id": "manager_123",
    "index": 0,
    "size": 7
}

staff_fetch_id_readStaffProfile = {
    "id": "slove"
}

staff_fetch_id_readStaffProfile_IdNotExist = {
    "id": "not"
}

edit_staff_account = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
    "payload": {
        "username": "manager_test",
        "password": "123456"
    }
}

edit_staff_account_blankUsername = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
    "payload": {
        "username": "",
        "password": "123456"
    }
}

edit_staff_account_blankpassword = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
    "payload": {
        "username": "manager_test",
        "password": ""
    }
}

edit_staff_account_wrongId = {
    "params": {
        "id": "wrong"
    },
    "payload": {
        "username": "manager_test",
        "password": "123456"
    }
}

edit_staff_account_infos_valid = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
        "payload": {
  "ssn": "001648456784",
  "phonenumber": "0157426048",
  "realname": "string",
  "email": "user@example.com",
  "dob": "2000-04-16"
}
}

edit_staff_account_infos_invalidSsn = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
        "payload": {
  "ssn": "0123",
  "phonenumber": "0157426048",
  "realname": "string",
  "email": "user@example.com",
  "dob": "2000-04-16"
}
}

edit_staff_account_infos_invalidEmail = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
        "payload": {
  "ssn": "0123",
  "phonenumber": "0157426048",
  "realname": "string",
  "email": "user",
  "dob": "2000-04-16"
}
}

edit_staff_account_infos_valid = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
        "payload": {
  "ssn": "001648456784",
  "phonenumber": "015742",
  "realname": "string",
  "email": "user@example.com",
  "dob": "2000-04-16"
}
}
edit_staff_account_infos_invalid_phone = {
    "params": {
        "id": "8a223f34-aa8b-4c41-91db-c6c629dbe727"
    },
        "payload": {
  "ssn": "001648456784",
  "phonenumber": "01576048",
  "realname": "string",
  "email": "user@example.com",
  "dob": "2000-04-16"
}
}

test_blog_create_success = {
    "title": "testblogcreatesucess",
    "description": "test desc",
    "markdown_text": "test markdown",
    "infos": {
        "Serve": "4 - 5 people"
        }
    }

test_blog_create_blank_title = {
    "title": "",
    "description": "test desc",
    "markdown_text": "test markdown",
    "infos": {
        "Serve": "4 - 5 people"
        }
    }

test_blog_create_blank_descripton = {
    "title": "testblogcreatesucess",
    "description": "",
    "markdown_text": "test markdown",
    "infos": {
        "Serve": "4 - 5 people"
        }
    }

edit_blog_success = {
    "params": {
        "id": "4d3e0483-c967-4fc1-802c-9872801b01a2"
    },
  "payload": {
  "title": "test",
  "description": "test",
  "markdown_text": "test",
  "infos": {
    "serving": "2 people"
}
}
}

edit_blog_blank_title = {
    "params": {
        "id": "4d3e0483-c967-4fc1-802c-9872801b01a2"
    },
        "payload": {
  "title": "test",
  "description": "test",
  "markdown_text": "test",
  "infos": {
    "serving": "2 people"
}
}
}

edit_blog_blank_description = {
    "params": {
        "id": "4d3e0483-c967-4fc1-802c-9872801b01a2"
    },
        "payload": {
  "title": "test",
  "description": "",
  "markdown_text": "test",
  "infos": {
    "serving": "2 people"
}
}
}

edit_blog_blank_markdown_text = {
    "params": {
        "id": "4d3e0483-c967-4fc1-802c-9872801b01a2"
    },
        "payload": {
  "title": "test",
  "description": "test",
  "markdown_text": "",
  "infos": {
    "serving": "2 people"
}
}
}

test_comment_fetch_all = {
    "index": 0,
    "size": 7
}

test_comment_fetch_all_normalStatus = {
    "status": "NORMAL",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_reportedStatus = {
    "status": "REPORTED",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_deletedStatus = {
    "status": "DELETED",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_normalStatus_typePost = {
    "status": "NORMAL",
    "type": "POST",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_reportedStatus_typePost = {
    "status": "REPORTED",
    "type": "POST",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_deletedStatus_typePost = {
    "status": "DELETED",
    "type": "POST",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_normalStatus_typePeply = {
    "status": "NORMAL",
    "type": "REPLY",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_reportedStatus_typePeply = {
    "status": "REPORTED",
    "type": "REPLY",
    "index": 0,
    "size": 7
}

test_comment_fetch_all_deletedStatus_typePeply = {
    "status": "DELETED",
    "type": "REPLY",
    "index": 0,
    "size": 7
}

test_comment_fetch_oneBlog = {
    "id": "4d3e0483-c967-4fc1-802c-9872801b01a2",
    "index": 0,
    "size": 7
}

test_customer_fetch_all = {
    "id": "",
    "index": 0,
    "size": 7
}

test_customer_fetch_cart = {
    "id": "5b802711-51d6-4d9a-809f-6d145b98505e",
    "index": 0,
    "size": 7
}

test_customer_fetch_infos = {
    "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
}

test_customer_fetch_order = {
    "id": "5b802711-51d6-4d9a-809f-6d145b98505e",
    "index": 0,
    "size": 7
}

test_customer_edit_status_banned = {
    "id": "5b802711-51d6-4d9a-809f-6d145b98505e",
    "status": "BANNED"
}

test_customer_edit_status_normal = {
    "id": "5b802711-51d6-4d9a-809f-6d145b98505e",
    "status": "NORMAL"
}

test_customer_edit_account_success = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
        "username": "testaccount",
        "password": "123456"
    }
}

test_customer_edit_account_blankUsername = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
        "username": "",
        "password": "123456"
    }
}

test_customer_edit_account_blankPassword = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
        "username": "testaccount",
        "password": ""
    }
}

test_customer_edit_account_infos_valid = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
  "email": "test@example.com",
  "address": "test address",
  "phone": "0217903941",
  "profile_description": "test profile desc",
  "profile_name": "testaccount"
    }
}

test_customer_edit_account_infos_invalid_email = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
  "email": "test@example",
  "address": "test address",
  "phone": "0217903941",
  "profile_description": "test profile desc",
  "profile_name": "testaccount"
    }
}

test_customer_edit_account_infos_invalid_phone = {
    "params": {
        "id": "5b802711-51d6-4d9a-809f-6d145b98505e"
    },
    "payload": {
  "email": "test@example@gmail.com",
  "address": "test address",
  "phone": "021790",
  "profile_description": "test profile desc",
  "profile_name": "testaccount"
    }
}

test_order_fetch_all = {
    "index": 0,
    "size": 7
}

test_order_fetch_all_onConfirm = {
    "status": "ON_CONFIRM",
    "index": 0,
    "size": 7
}

test_order_fetch_all_ON_PROCESSING = {
    "status": "ON_PROCESSING",
    "index": 0,
    "size": 7
}
test_order_fetch_all_ON_SHIPPING = {
    "status": "ON_SHIPPING",
    "index": 0,
    "size": 7
}
test_order_fetch_all_SHIPPED = {
    "status": "SHIPPED",
    "index": 0,
    "size": 7
}
test_order_fetch_all_DELIVERED = {
    "status": "DELIVERED",
    "index": 0,
    "size": 7
}
test_order_fetch_all_CANCELLED = {
    "status": "CANCELLED",
    "index": 0,
    "size": 7
}

test_order_fetch_status_onConfirm = {
    "status": "ON_CONFIRM",
    "index": 0,
    "size": 7
}

test_order_fetch_status_ON_PROCESSING = {
    "status": "ON_PROCESSING",
    "index": 0,
    "size": 7
}
test_order_fetch_status_ON_SHIPPING = {
    "status": "ON_SHIPPING",
    "index": 0,
    "size": 7
}
test_order_fetch_status_SHIPPED = {
    "status": "SHIPPED",
    "index": 0,
    "size": 7
}
test_order_fetch_status_DELIVERED = {
    "status": "DELIVERED",
    "index": 0,
    "size": 7
}
test_order_fetch_status_CANCELLED = {
    "status": "CANCELLED",
    "index": 0,
    "size": 7
}

test_order_fetch_infos = {
    "id": "df968698-8f95-4ff9-a3c8-c4bb4b620247"
}

test_order_fetch_items = {
    "id": "df968698-8f95-4ff9-a3c8-c4bb4b620247",
    "index": 0,
    "size": 7
}

test_order_accept = {
    "id": "41c9da8a-bbeb-437a-bdd8-e574a4f50962"
}

test_order_ship = {
    "id": "41c9da8a-bbeb-437a-bdd8-e574a4f50962"
}

test_order_cancel = {
    "id": "41c9da8a-bbeb-437a-bdd8-e574a4f50962"
}
main_image_path_blog = "test/IntegartionTest/image_test/1_BaconWrappedVeggies.jpg"
main_image_path_mealkit = "test/IntegartionTest/image_test/1_BaconWrappedVeggies.jpg"
additional_image_path_mealkit = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"
additional_image_path_mealkit2 = "test/IntegartionTest/image_test/main_BaconWrappedVeggies.jpg"