from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = "ch1_1_risk"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    PROBLEMS = [150, 200, 250, 300, 350]
    FORCE_SINGLE_SWITCH = 0  # 0:off, 1:on

    WITH_BOT = False  # for testing


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Decision
    choice_r1 = models.StringField()
    choice_r2 = models.StringField()
    choice_r3 = models.StringField()
    choice_r4 = models.StringField()
    choice_r5 = models.StringField()
    choice_r_cntA = models.IntegerField()
    comment_r = models.LongStringField(label="どのように考えて意思決定をしましたか？")

    # Decision_3
    choice_u = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    comment_u = models.LongStringField(label="どのように考えて意思決定をしましたか？")

    # Decision_4
    choice_s = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    comment_s = models.LongStringField(label="どのように考えて意思決定をしましたか？")

    # Decision_5
    choice_e = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    comment_e = models.LongStringField(label="どのように考えて意思決定をしましたか？")


# FUNCTIONS


# PAGES
class Decision(Page):
    """
    実験 1.1 個人の意思決定 質問1～5（リスク態度）
    """

    form_model = "player"
    form_fields = [
        "choice_r1",
        "choice_r2",
        "choice_r3",
        "choice_r4",
        "choice_r5",
        "comment_r",
    ]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if C.WITH_BOT and timeout_happened:
            player.choice_r1 = random.choice(["A", "B"])
            player.choice_r2 = random.choice(["A", "B"])
            player.choice_r3 = random.choice(["A", "B"])
            player.choice_r4 = random.choice(["A", "B"])
            player.choice_r5 = random.choice(["A", "B"])
            player.comment_r = "bot"

        if (
            player.choice_r1
            and player.choice_r2
            and player.choice_r3
            and player.choice_r4
            and player.choice_r5
        ):
            player.choice_r_cntA = [
                player.choice_r1,
                player.choice_r2,
                player.choice_r3,
                player.choice_r4,
                player.choice_r5,
            ].count("A")


class Decision_3(Page):
    """
    実験 1.1 個人の意思決定 質問6（不確実性のある状況）
    """

    form_model = "player"
    form_fields = ["choice_u", "comment_u"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if C.WITH_BOT and timeout_happened:
            player.choice_u = random.choice(["A", "B"])
            player.comment_u = "bot"


class Decision_4(Page):
    """
    実験 1.1 個人の意思決定 質問7（スケールが大きくなった状況）
    """

    form_model = "player"
    form_fields = ["choice_s", "comment_s"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if C.WITH_BOT and timeout_happened:
            player.choice_s = random.choice(["A", "B"])
            player.comment_s = "bot"


class Decision_5(Page):
    """
    実験 1.1 個人の意思決定 質問8（確実にAを選ぶことで得をすることができる状況）
    """

    form_model = "player"
    form_fields = ["choice_e", "comment_e"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if C.WITH_BOT and timeout_happened:
            player.choice_e = random.choice(["A", "B"])
            player.comment_e = "bot"


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    def after_all_players_arrive(subsession: Subsession):
        players: list[Player] = subsession.get_players()
        session = subsession.session

        # Decision (q1--5)
        list_choice_r_cntA = [
            p.choice_r_cntA for p in players if p.field_maybe_none("choice_r_cntA")
        ]
        list_prop_A = []
        if len(list_choice_r_cntA) > 0:
            list_prop_A = [
                100 * list_choice_r_cntA.count(i) / len(list_choice_r_cntA)
                for i in range(6)
            ][::-1]
        session.vars["ch1_1__num_participants"] = len(list_choice_r_cntA)
        session.vars["ch1_1__list_prop_A"] = list_prop_A

        list_choice_r3 = [
            p.choice_r3 for p in players if p.field_maybe_none("choice_r3")
        ]
        prop_A_r3 = -1
        if len(list_choice_r3) > 0:
            prop_A_r3 = 100 * list_choice_r3.count("A") / len(list_choice_r3)
        session.vars["ch1_1__num_participants_r3"] = len(list_choice_r3)
        session.vars["ch1_1__prop_A_r3"] = prop_A_r3

        # Decision_3 (q6)
        list_choice_u = [p.choice_u for p in players if p.field_maybe_none("choice_u")]
        prop_A_u = -1
        if len(list_choice_u) > 0:
            prop_A_u = 100 * list_choice_u.count("A") / len(list_choice_u)
        session.vars["ch1_1__num_participants_u"] = len(list_choice_u)
        session.vars["ch1_1__prop_A_u"] = prop_A_u

        # Decision_4 (q7)
        list_choice_s = [p.choice_s for p in players if p.field_maybe_none("choice_s")]
        prop_A_s = -1
        if len(list_choice_s) > 0:
            prop_A_s = 100 * list_choice_s.count("A") / len(list_choice_s)
        session.vars["ch1_1__num_participants_s"] = len(list_choice_s)
        session.vars["ch1_1__prop_A_s"] = prop_A_s

        # Decision_5 (q8)
        list_choice_e = [p.choice_e for p in players if p.field_maybe_none("choice_e")]
        prop_A_e = -1
        if len(list_choice_e) > 0:
            prop_A_e = 100 * list_choice_e.count("A") / len(list_choice_e)
        session.vars["ch1_1__num_participants_e"] = len(list_choice_e)
        session.vars["ch1_1__prop_A_e"] = prop_A_e


class PreResults(Page):
    pass


class Results(Page):
    @staticmethod
    def js_vars(player: Player):
        return dict(
            num_participants=player.session.vars["ch1_1__num_participants"],
            list_prop_A=player.session.vars["ch1_1__list_prop_A"],
            num_participants_r3=player.session.vars["ch1_1__num_participants_r3"],
            prop_A_r3=player.session.vars["ch1_1__prop_A_r3"],
            num_participants_u=player.session.vars["ch1_1__num_participants_u"],
            prop_A_u=player.session.vars["ch1_1__prop_A_u"],
            num_participants_s=player.session.vars["ch1_1__num_participants_s"],
            prop_A_s=player.session.vars["ch1_1__prop_A_s"],
            num_participants_e=player.session.vars["ch1_1__num_participants_e"],
            prop_A_e=player.session.vars["ch1_1__prop_A_e"],
        )


page_sequence = [
    Decision,
    Decision_3,
    Decision_4,
    Decision_5,
    ResultsWaitPage,
    PreResults,
    Results,
]


def vars_for_admin_report(subsession: Subsession):
    js_vars = dict(
        num_participants=subsession.session.vars["ch1_1__num_participants"],
        list_prop_A=subsession.session.vars["ch1_1__list_prop_A"],
        num_participants_r3=subsession.session.vars["ch1_1__num_participants_r3"],
        prop_A_r3=subsession.session.vars["ch1_1__prop_A_r3"],
        num_participants_u=subsession.session.vars["ch1_1__num_participants_u"],
        prop_A_u=subsession.session.vars["ch1_1__prop_A_u"],
        num_participants_s=subsession.session.vars["ch1_1__num_participants_s"],
        prop_A_s=subsession.session.vars["ch1_1__prop_A_s"],
        num_participants_e=subsession.session.vars["ch1_1__num_participants_e"],
        prop_A_e=subsession.session.vars["ch1_1__prop_A_e"],
    )
    return dict(js_vars=js_vars)
