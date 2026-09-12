from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, ScorePost, Season


class SignUpForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "display_name"]

class ScorePostForm(forms.ModelForm):
    LIMIT_BREAK_CHOICES = [("", "未設定")] + [(i, f"{i}凸") for i in range(6)]

    character_1_limit_break = forms.ChoiceField(
        choices=LIMIT_BREAK_CHOICES, required=False, label="使用キャラ1の凸数(任意)"
    )
    character_2_limit_break = forms.ChoiceField(
        choices=LIMIT_BREAK_CHOICES, required=False, label="使用キャラ2の凸数(任意)"
    )
    character_3_limit_break = forms.ChoiceField(
        choices=LIMIT_BREAK_CHOICES, required=False, label="使用キャラ3の凸数(任意)"
    )

    class Meta:
        model = ScorePost
        fields = [
            "boss",
            "score",
            "character_1",
            "character_2",
            "character_3",
            "mvp_slot",
            "character_1_limit_break",
            "character_2_limit_break",
            "character_3_limit_break",
            "badges_note",
            "disc_note",
            "preset_code",
        ]

        widgets = {
                    "badges_note": forms.Textarea(attrs={
                        "placeholder": 
                        "例:【カリン】虹貫通/虹SP/ダイダルバースト+3\n【オトハ】虹会心/虹SP\n【コゼット】魔痕+3/金SP",
                        "rows": 5,
                    }),
                    "disc_note": forms.Textarea(attrs={
                        "placeholder": "例:\n魔女の秘薬（無凸）/千変万花（無凸）/共に航る（2凸）",
                        "rows": 5,
                    }),
                    "preset_code": forms.TextInput(attrs={
                        "placeholder": "例: AAAAnQAAAIcAAACOMAbLYAI0gMAgAGyAwAwQ",
                        "rows": 2,
                    }),
                }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_season = Season.objects.first()
        if current_season:
            self.fields["boss"].queryset = current_season.bosses.all()

    def clean_character_1_limit_break(self):
        value = self.cleaned_data.get("character_1_limit_break")
        return int(value) if value != "" else None

    def clean_character_2_limit_break(self):
        value = self.cleaned_data.get("character_2_limit_break")
        return int(value) if value != "" else None

    def clean_character_3_limit_break(self):
        value = self.cleaned_data.get("character_3_limit_break")
        return int(value) if value != "" else None