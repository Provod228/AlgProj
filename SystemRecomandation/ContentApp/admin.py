from django.contrib import admin

from ContentApp.models import Content, Category, Favorite, Rating, CategoryContent

# Register your models here.

admin.site.register(Category)
admin.site.register(Favorite)
admin.site.register(Rating)
admin.site.register(CategoryContent)

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    exclude = ['slug']
