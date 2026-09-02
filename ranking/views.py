from django.views.generic import TemplateView, DetailView, CreateView
from django.urls import reverse_lazy
from .forms import SignUpForm, ScorePostForm
from .models import Season, Boss, ScorePost
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DeleteView
from django.core.paginator import Paginator
from django.conf import settings


class HomeView(TemplateView):
    template_name = "ranking/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        season_id = self.request.GET.get("season")
        if season_id:
            current_season = Season.objects.filter(id=season_id).first()
        else:
            current_season = Season.objects.first()

        context["season"] = current_season
        context["all_seasons"] = Season.objects.all()
        context["bosses"] = current_season.bosses.all() if current_season else []

        not_recommended_only = self.request.GET.get("filter") == "non_recommended"
        context["not_recommended_only"] = not_recommended_only

        boss_id = self.request.GET.get("boss")
        selected_boss = None
        if boss_id:
            selected_boss = Boss.objects.filter(id=boss_id, season=current_season).first()
        context["selected_boss"] = selected_boss

        if not current_season:
            full_ranking = []
        elif selected_boss:
            full_ranking = ScorePost.get_boss_ranking(
                selected_boss, not_recommended_only=not_recommended_only
            )
        else:
            full_ranking = ScorePost.get_combined_ranking(
                current_season, not_recommended_only=not_recommended_only
            )

        # ここからページネーション（100件ごと）
        paginator = Paginator(full_ranking, 100)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        # 「順位」は現在のページの何行目か、ではなく全体の中の順位なので、開始位置を渡す
        context["rank_start"] = page_obj.start_index()

        my_rank = None
        my_score = None
        if self.request.user.is_authenticated:
            for i, (user, value) in enumerate(full_ranking, start=1):
                if user == self.request.user:
                    my_rank = i
                    my_score = value.score if selected_boss else value
                    break
        context["my_rank"] = my_rank
        context["my_page"] = ((my_rank - 1) // 100) + 1 if my_rank else None
        context["my_score"] = my_score

        return context

class ScorePostDetailView(DetailView):
    model = ScorePost
    template_name = "ranking/score_post_detail.html"
    context_object_name = "post"


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "ranking/signup.html"
    success_url = reverse_lazy("ranking:login")  # サインアップ後にログインページにリダイレクト


class ScorePostCreateView(LoginRequiredMixin, CreateView):
    form_class = ScorePostForm
    template_name = "ranking/score_post_form.html"
    login_url = "ranking:login"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_banned:
            messages.error(request, "投稿が制限されています。")
            return redirect("ranking:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.screenshot_url = self.request.POST.get("screenshot_url")
        form.instance.damage_stats_screenshot_url = self.request.POST.get("damage_stats_screenshot_url")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("ranking:score_post_detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["supabase_url"] = settings.SUPABASE_URL
        context["supabase_key"] = settings.SUPABASE_PUBLISHABLE_KEY
        return context


class MyPageView(LoginRequiredMixin, ListView):
    model = ScorePost
    template_name = "ranking/mypage.html"
    context_object_name = "posts"
    login_url = "ranking:login"

    def get_queryset(self):
        return ScorePost.objects.filter(user=self.request.user)


class ScorePostDeleteView(LoginRequiredMixin, DeleteView):
    model = ScorePost
    template_name = "ranking/score_post_confirm_delete.html"
    success_url = reverse_lazy("ranking:mypage")
    login_url = "ranking:login"

    def get_queryset(self):
        return ScorePost.objects.filter(user=self.request.user)