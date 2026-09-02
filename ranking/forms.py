from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, ScorePost, Season


class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "display_name"]

class ScorePostForm(forms.ModelForm):
    class Meta:
        model = ScorePost
        fields = [
            "boss",
            "score",
            "character_1",
            "character_2",
            "character_3",
            "mvp_slot",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_season = Season.objects.first()
        if current_season:
            self.fields["boss"].queryset = current_season.bosses.all()