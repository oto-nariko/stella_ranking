from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime
from django.utils import timezone



class CustomUser(AbstractUser):
    """
    カスタムユーザーのモデル
    """
    display_name = models.CharField(
        max_length=30, verbose_name="表示名（ランキングで表示される名前）"
    )
    is_banned = models.BooleanField(default=False, verbose_name="投稿禁止フラグ")

    def __str__(self):
        return self.display_name

    class Meta:
        verbose_name = "ユーザー"
        verbose_name_plural = "ユーザー"


class Character(models.Model):
    """
    キャラクターのモデル
    """
    ATTRIBUTE_CHOICES = [
        ("fire", "火属性"),
        ("water", "水属性"),
        ("wind", "風属性"),
        ("light", "光属性"),
        ("dark", "闇属性"),
        ("earth", "地属性"),
    ]
    name = models.CharField(max_length=50, verbose_name="キャラクター名")
    attribute = models.CharField(
        max_length=10, choices=ATTRIBUTE_CHOICES, verbose_name="属性"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "キャラクター"
        verbose_name_plural = "キャラクター"


class Season(models.Model):
    """
    シーズンのモデル
    """
    name = models.CharField(max_length=50, verbose_name="シーズン名")
    start_date = models.DateField(verbose_name="開始日")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "シーズン"
        verbose_name_plural = "シーズン"
        ordering = ["-start_date"]  # 開始日が新しい順に並べる

    @property
    def submission_deadline(self):
        """このシーズンの投稿締切日時（開始月の翌月1日 午前5時）を返す"""
        year = self.start_date.year
        month = self.start_date.month + 1
        if month > 12:
            month = 1
            year += 1
        naive_deadline = datetime(year, month, 1, 5, 0, 0)
        return timezone.make_aware(naive_deadline)

    def is_open_for_submission(self):
        """現在、このシーズンへの投稿がまだ受け付けられるかどうか"""
        return timezone.now() <= self.submission_deadline

    @classmethod
    def get_current_season(cls):
        """現在の日付時点で、開始しているシーズンの中で一番新しいものを返す"""
        return cls.objects.filter(start_date__lte=timezone.now().date()).first()


class Boss(models.Model):
    """
    ボスのモデル
    """
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="bosses", verbose_name="シーズン"
    )
    name = models.CharField(max_length=50, verbose_name="ボス名")
    recommended_attribute_1 = models.CharField(
        max_length=10,
        choices=Character.ATTRIBUTE_CHOICES,
        verbose_name="推奨属性1"
    )
    recommended_attribute_2 = models.CharField(
        max_length=10,
        choices=Character.ATTRIBUTE_CHOICES,
        verbose_name="推奨属性2"
    )
    resistance_attribute = models.CharField(
        max_length=10,
        choices=Character.ATTRIBUTE_CHOICES,
        verbose_name="耐性属性"
    )
    def __str__(self):
        return f"{self.season} - {self.name}"

    class Meta:
        verbose_name = "ボス"
        verbose_name_plural = "ボス"


class ScorePost(models.Model):
    """
    スコア投稿のモデル
    """
    MVP_SLOT_CHOICES = [
        (1, "使用キャラ1"),
        (2, "使用キャラ2"),
        (3, "使用キャラ3"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="score_posts", verbose_name="投稿者"
    )
    boss = models.ForeignKey(
        Boss, on_delete=models.CASCADE, related_name="score_posts", verbose_name="ボス"
    )
    score = models.PositiveIntegerField(verbose_name="スコア")

    character_1 = models.ForeignKey(
        Character, on_delete=models.PROTECT, related_name="+", verbose_name="使用キャラ1"
    )
    character_2 = models.ForeignKey(
        Character, on_delete=models.PROTECT, related_name="+", verbose_name="使用キャラ2"
    )
    character_3 = models.ForeignKey(
        Character, on_delete=models.PROTECT, related_name="+", verbose_name="使用キャラ3"
    )
    mvp_slot = models.PositiveSmallIntegerField(
        choices=MVP_SLOT_CHOICES, verbose_name="MVPキャラの枠"
    )
    character_1_limit_break = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="使用キャラ1の凸数(任意)"
    )
    character_2_limit_break = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="使用キャラ2の凸数(任意)"
    )
    character_3_limit_break = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="使用キャラ3の凸数(任意)"
    )
    badges_note = models.TextField(blank=True, verbose_name="徽章（任意）")
    disc_note = models.TextField(blank=True, verbose_name="ロスレコ（任意）")
    preset_code = models.CharField(
        max_length=100, blank=True, verbose_name="記録プリセットコード（任意）"
    )

    screenshot_url = models.URLField(verbose_name="最終スコア画面のスクショURL")
    damage_stats_screenshot_url = models.URLField(verbose_name="ダメージ統計画面のスクショURL")
    posted_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")

    is_flagged = models.BooleanField(default=False, verbose_name="不正フラグ")
    is_hidden = models.BooleanField(default=False, verbose_name="非表示フラグ")

    def __str__(self):
        return f"{self.user} - {self.boss} - {self.score}点"

    @property
    def mvp_character(self):
        #MVPキャラのCharacterインスタンスを返す
        return {1: self.character_1, 2: self.character_2, 3: self.character_3}[self.mvp_slot]

    @classmethod
    def get_boss_ranking(cls, boss, attribute_filter=None):
        """
        指定したボスのランキングを、ユーザーごとの最高スコアの投稿で降順に返す。
        attribute_filter:
            None                → 絞り込みなし（全属性対象）
            "not_recommended"   → MVPキャラが推奨属性でない投稿のみ対象
            "fire"などの属性コード → MVPキャラがその属性の投稿のみ対象
        戻り値: [(CustomUser, ScorePost), ...] のリスト
        """
        posts = cls.objects.filter(boss=boss, is_flagged=False, is_hidden=False)

        if attribute_filter == "not_recommended":
            recommended = [boss.recommended_attribute_1, boss.recommended_attribute_2]
            posts = [p for p in posts if p.mvp_character.attribute not in recommended]
        elif attribute_filter:
            posts = [p for p in posts if p.mvp_character.attribute == attribute_filter]

        best_posts = {}
        for p in posts:
            if p.user not in best_posts or p.score > best_posts[p.user].score:
                best_posts[p.user] = p

        return sorted(best_posts.items(), key=lambda item: item[1].score, reverse=True)

    @classmethod
    def get_combined_ranking(cls, season, attribute_filter=None):
        """
        指定したシーズンの全ボスについて、ユーザーごとの合算スコアを降順で返す。
        未投稿のボスは0点として扱う。
        """
        bosses = season.bosses.all()

        per_boss_scores = []
        for boss in bosses:
            ranking = {
                user: post.score
                for user, post in cls.get_boss_ranking(boss, attribute_filter=attribute_filter)
            }
            per_boss_scores.append(ranking)

        all_users = set()
        for ranking in per_boss_scores:
            all_users.update(ranking.keys())

        combined = {}
        for user in all_users:
            total = sum(ranking.get(user, 0) for ranking in per_boss_scores)
            combined[user] = total

        return sorted(combined.items(), key=lambda item: item[1], reverse=True)

    class Meta:
        verbose_name = "スコア投稿"
        verbose_name_plural = "スコア投稿"
        ordering = ["-posted_at"]  # 投稿日時が新しい順に並べる


class Report(models.Model):
    """
    通報のモデル
    """
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="reports", verbose_name="通報者"
    )
    score_post = models.ForeignKey(
        ScorePost, on_delete=models.CASCADE, related_name="reports", verbose_name="通報対象の投稿"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="通報日時")

    def __str__(self):
        return f"{self.user} → {self.score_post}"

    class Meta:
        verbose_name = "通報"
        verbose_name_plural = "通報"
        unique_together = ["user", "score_post"]