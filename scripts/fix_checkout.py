#!/usr/bin/env python3

filepath = "/var/www/hypernexus.site/checkout.html"

with open(filepath, "r") as f:
    content = f.read()

# Fix the API endpoint
content = content.replace("/api/billing/create-checkout", "/api/v1/billing/checkout")

# Fix the request body - replace the old body with the new one
old_body = "body: JSON.stringify({ email, name, priceId: 'price_XXXXXXXXXXXX' }) // Replace with your Stripe price ID"
new_body = """body: JSON.stringify({
                        tier: 'HYPERNEXUS_PROFESSIONAL_LICENSE',
                        seats: 1,
                        success_url: 'https://hypernexus.site/success.html',
                        cancel_url: 'https://hypernexus.site/checkout.html'
                    })"""

content = content.replace(old_body, new_body)

# Fix the response handling
old_response = "if (res.ok && data.sessionId) {\n                    const result = await stripe.redirectToCheckout({ sessionId: data.sessionId });\n                    if (result.error) {\n                        errorEl.textContent = result.error.message;\n                        errorEl.style.display = 'block';\n                    }\n                } else {"
new_response = "if (res.ok && data.url) {\n                    window.location.href = data.url;\n                } else {"

content = content.replace(old_response, new_response)

# Remove the Stripe.js script tag since we don't need it anymore
content = content.replace('<script src="https://js.stripe.com/v3/"></script>\n', "")

# Remove the stripe initialization
content = content.replace(
    "const stripe = Stripe('pk_live_XXXXXXXXXXXXXXXXXXXXXXXX'); // Replace with your Stripe publishable key\n",
    "",
)

with open(filepath, "w") as f:
    f.write(content)

print("Fixed checkout.html successfully")
