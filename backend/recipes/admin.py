from django.contrib import admin

from . import models


class TagFilter(admin.SimpleListFilter):
    title = 'Теги'
    parameter_name = 'tag'

    def lookups(self, request, model_admin):
        tags = models.Tag.objects.all()
        return [(tag.slug, tag.name) for tag in tags]

    def queryset(self, request, queryset):
        tag_slug = self.value()
        if tag_slug:
            return queryset.filter(tags__slug=tag_slug)
        return queryset


class RecipeCompositionInline(admin.TabularInline):
    model = models.RecipeComposition
    extra = 0


class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username')


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('author', 'name')
    list_filter = (TagFilter,)
    inlines = (RecipeCompositionInline,)
    readonly_fields = ('favorited_count',)

    def favorited_count(self, obj):
        return obj.user_set.count()
    favorited_count.short_description = 'В избранном'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Recipe, RecipeAdmin)
admin.site.register(models.Tag)
admin.site.register(models.Ingredient, IngredientAdmin)
