from django.contrib import admin

from .models import Invoice, Payment, Plan, Subscription, WebhookEvent

admin.site.register(Plan)
admin.site.register(Payment)
admin.site.register(Subscription)
admin.site.register(Invoice)
admin.site.register(WebhookEvent)
