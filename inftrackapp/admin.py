from django.contrib import admin

# Register your models here. /?$
admin.site.register(models.TrackablePerson)
admin.site.register(models.TrackingTag)
admin.site.register(models.TagAssignmentEvent)
admin.site.register(models.StatusChangeEvent)
admin.site.register(models.TagPosition)
