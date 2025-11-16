from otree.api import *
import random

doc = """ """


class C(BaseConstants):
    NAME_IN_URL = "ch3_0_shortandlong"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2

    CHOICE_LIST = ["A", "B"]

    CHOICE_LABEL_1 = "仕事する"
    CHOICE_LABEL_2 = "仕事しない"


class Subsession(BaseSubsession):
    num_participants = models.IntegerField(initial=0)
    num_A = models.IntegerField(initial=0)
    num_B = models.IntegerField(initial=0)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    individual_choice = models.StringField(
        choices=[
            [C.CHOICE_LIST[0], C.CHOICE_LABEL_1],
            [C.CHOICE_LIST[1], C.CHOICE_LABEL_2],
        ],
        label="【質問1】あなたが企業の担当者だとすると、[{}][{}]どちらを選びますか？".format(
            C.CHOICE_LABEL_1, C.CHOICE_LABEL_2
        ),
        widget=widgets.RadioSelectHorizontal,
    )
    flg_non_input = models.IntegerField(initial=0)

    # 意思決定の理由
    individual_choice_comment = models.LongStringField(
        label="【質問2】なぜあなたはその選択肢を選んだのか、理由を教えてください。"
    )


# FUNCTIONS
def summarize_data(subsession: Subsession):
    list_choices = [
        p.individual_choice
        for p in subsession.get_players()
        if p.field_maybe_none("individual_choice")
    ]
    subsession.num_participants = len(list_choices)
    subsession.num_A = list_choices.count(C.CHOICE_LIST[0])
    subsession.num_B = list_choices.count(C.CHOICE_LIST[1])


def dump_js_vars(sub: Subsession):
    prop_A = -1
    prop_B = -1
    if sub.num_participants > 0:
        prop_A = (sub.num_A / sub.num_participants) * 100
        prop_B = (sub.num_B / sub.num_participants) * 100

    return dict(
        num_participants=sub.num_participants,
        prop_A=prop_A,
        prop_B=prop_B,
    )


# PAGES
class Introduction(Page):
    # timeout_seconds = 100
    pass


class Decision(Page):
    # timeout_seconds = 180
    form_model = "player"
    form_fields = [
        "individual_choice",
        "individual_choice_comment",
    ]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.flg_non_input = 1
            player.individual_choice = random.choice(C.CHOICE_LIST)


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        summarize_data(subsession)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            my_decision=player.field_display("individual_choice"),
        )

    @staticmethod
    def js_vars(player: Player):
        return dump_js_vars(player.subsession)


page_sequence = [
    Introduction,
    Decision,
    ResultsWaitPage,
    Results,
]


def vars_for_admin_report(subsession: Subsession):
    list_comment = []
    if subsession.round_number == 1:
        list_comment = sorted(
            [
                [
                    p.individual_choice,
                    p.individual_choice_comment,
                ]
                for p in subsession.get_players()
            ]
        )

    return dict(
        js_vars=dump_js_vars(subsession),
        list_comment=list_comment,
    )
