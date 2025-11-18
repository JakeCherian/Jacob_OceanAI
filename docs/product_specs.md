# Product Specifications

## Discount Codes
- The discount code `SAVE15` applies a 15% discount to the cart subtotal.

## Shipping Costs
- Standard shipping is free.
- Express shipping costs $10.

## Cart and Pricing
- Subtotal is the sum of (`quantity * unit_price`) across all items in the cart.
- Total is `subtotal - discount + shipping`.

## Validation Rules
- Name, Email, and Address are required fields.
- Email must be valid.

## Payment
- Payment methods available: Credit Card and PayPal.
- The "Pay Now" button completes payment if the form is valid and the total is greater than zero.