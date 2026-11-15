from django.contrib import admin
from project25.models import *

admin.site.register(User)
admin.site.register(Group)
admin.site.register(Currency)
admin.site.register(Payment)
admin.site.register(Share)