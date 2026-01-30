# RUNTIME CONTEXT — Provided by Application Tool

## ACTIVE DATA
- Database: prodotti_xeel_shop
- Source tool: product-list

## AVAILABLE WIDGETS
- electronics-carousel (max 6 products, single category)
- electronics-list (compact list, supports “Buy all”)
- electronics-albums
- electronics-shop
- electronics-map
- shopping-cart
- solution_bundle_recommendations
- cross_sell_recommendations (max 4 items)

## CURRENT STATE
- Current screen: {{screen_name}}
- User intent: {{intent}}
- Cart status: {{cart_state}}
- Price preference: {{price_mode | none}}

## UI CONSTRAINTS
- Do not mix categories inside `electronics-carousel`
- Show essential products before accessories
- Accessories should be proposed only after main products or in cart
