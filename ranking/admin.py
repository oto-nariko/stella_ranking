from django.contrib import admin
from django.utils.html import format_html
from .models import Character, Season, Boss, CustomUser, ScorePost


admin.site.register(Character)
admin.site.register(Season)
admin.site.register(Boss)

"""
ユーザーの管理画面のカスタマイズ
"""
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["username", "display_name", "is_banned", "is_staff", "date_joined"]
    list_filter = ["is_banned", "is_staff"]
    actions = ["ban_users", "unban_users"]

    @admin.action(description="選択したユーザーをBANする")
    def ban_users(self, request, queryset):
        queryset.update(is_banned=True)

    @admin.action(description="選択したユーザーのBANを解除する")
    def unban_users(self, request, queryset):
        queryset.update(is_banned=False)

"""
スコア投稿の管理画面のカスタマイズ
"""
@admin.register(ScorePost)
class ScorePostAdmin(admin.ModelAdmin):
    list_display = ["user", "boss", "score", "screenshot_thumbnails", "is_flagged", "is_hidden", "posted_at"]
    list_filter = ["is_flagged", "is_hidden", "boss"]
    actions = ["mark_as_flagged", "unmark_as_flagged"]

    def screenshot_thumbnails(self, obj):
        return format_html(
            '<img src="{}" style="height: 60px; margin-right: 4px;" />'
            '<img src="{}" style="height: 60px;" />',
            obj.screenshot_url,
            obj.damage_stats_screenshot_url,
        )
    screenshot_thumbnails.short_description = "証拠スクショ（左:スコア／右:ダメージ統計）"

    @admin.action(description="選択した投稿に不正フラグを立てる")
    def mark_as_flagged(self, request, queryset):
        queryset.update(is_flagged=True)

    @admin.action(description="選択した投稿の不正フラグを解除する")
    def unmark_as_flagged(self, request, queryset):
        queryset.update(is_flagged=False)
