from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = "ch1_1_risk"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    PROBLEMS = [150, 200, 250, 300, 350]
    FORCE_SINGLE_SWITCH = 0  # 0:off, 1:on


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Decision
    q1 = models.StringField()
    q2 = models.StringField()
    q3 = models.StringField()
    q4 = models.StringField()
    q5 = models.StringField()
    cnt_A = models.IntegerField()
    individual_choice_r_comment = models.LongStringField(
        label="どのように考えて意思決定をしましたか？"
    )

    # Decision_3
    u_individual_choice = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    individual_choice_u_comment = models.LongStringField(
        label="どのように考えて意思決定をしましたか？"
    )

    # Decision_4
    s_individual_choice = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    individual_choice_s_comment = models.LongStringField(
        label="どのように考えて意思決定をしましたか？"
    )

    # Decision_5
    e_individual_choice = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="この時あなたは、A、Bのどちらを選びますか？",
        choices=[
            ["A", "Aを選ぶ"],
            ["B", "Bを選ぶ"],
        ],
    )
    individual_choice_e_comment = models.LongStringField(
        label="どのように考えて意思決定をしましたか？"
    )


# FUNCTIONS
def keiosan_ratio(num_A, num_B, num_participants):
    # 割合に計算
    if num_A > 0:
        prop_num_A = round((num_A / num_participants) * 100, 2)
    else:
        prop_num_A = 0
    if num_B > 0:
        prop_num_B = round((num_B / num_participants) * 100, 2)
    else:
        prop_num_B = 0
    return prop_num_A, prop_num_B


# PAGES
class Decision(Page):
    """
    実験 1.1 個人の意思決定 質問1～5
    """

    form_model = "player"
    form_fields = ["q1", "q2", "q3", "q4", "q5", "individual_choice_r_comment"]

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.q1 and player.q2 and player.q3 and player.q4 and player.q5:
            player.cnt_A = [
                player.q1,
                player.q2,
                player.q3,
                player.q4,
                player.q5,
            ].count("A")


class Decision_3(Page):
    """
    実験 1.1 個人の意思決定 質問6
    """

    form_model = "player"
    form_fields = ["u_individual_choice", "individual_choice_u_comment"]


class Decision_4(Page):
    """
    実験 1.1 個人の意思決定 質問7
    """

    form_model = "player"
    form_fields = ["s_individual_choice", "individual_choice_s_comment"]


class Decision_5(Page):
    """
    実験 1.1 個人の意思決定 質問8
    """

    form_model = "player"
    form_fields = ["e_individual_choice", "individual_choice_e_comment"]


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    def after_all_players_arrive(subsession: Subsession):
        players: list[Player] = subsession.get_players()
        session = subsession.session

        # Decision (q1--5)
        list_num_A = [p.cnt_A for p in players if p.field_maybe_none("cnt_A")]
        prop_num_A = []
        if len(list_num_A) > 0:
            prop_num_A = [
                100 * list_num_A.count(i) / len(list_num_A) for i in range(6)
            ][::-1]
        session.vars["prop_num_A"] = prop_num_A

        # Decision_3:不確実性の質問グラフ
        print("Decision_3:不確実性の質問グラフ")
        num_participants_u = 0
        u_count_A = 0
        u_count_B = 0
        for p in players:
            u = p.u_individual_choice
            if u != "":
                num_participants_u += 1
                if u == "A":
                    u_count_A += 1
                elif u == "B":
                    u_count_B += 1

        u_prop_num_A, u_prop_num_B = keiosan_ratio(
            u_count_A, u_count_B, num_participants_u
        )
        print("Decision_3:不確実性の質問グラフー", u_prop_num_A, u_prop_num_B)
        session.vars["num_participants_u"] = num_participants_u
        session.vars["u_prop_num_A"] = u_prop_num_A
        session.vars["u_prop_num_B"] = u_prop_num_B

        # Decision_4:10倍の質問グラフ
        num_participants_s = 0
        s_count_A = 0
        s_count_B = 0
        for p in players:
            s = p.s_individual_choice
            if s != "":
                num_participants_s += 1
                if s == "A":
                    s_count_A += 1
                elif s == "B":
                    s_count_B += 1

        s_prop_num_A, s_prop_num_B = keiosan_ratio(
            s_count_A, s_count_B, num_participants_s
        )
        print("Decision_4:10倍の質問グラフー", s_prop_num_A, s_prop_num_B)
        session.vars["num_participants_s"] = num_participants_s
        session.vars["s_prop_num_A"] = s_prop_num_A
        session.vars["s_prop_num_B"] = s_prop_num_B

        # 期待値が高い質問グラフ
        num_participants_e = 0
        e_count_A = 0
        e_count_B = 0
        for p in players:
            e = p.e_individual_choice
            if e != "":
                num_participants_e += 1
                if e == "A":
                    e_count_A += 1
                elif e == "B":
                    e_count_B += 1

        e_prop_num_A, e_prop_num_B = keiosan_ratio(
            e_count_A, e_count_B, num_participants_e
        )
        print("期待値が高い質問グラフー", e_prop_num_A, e_prop_num_B)
        session.vars["num_participants_e"] = num_participants_e
        session.vars["e_prop_num_A"] = e_prop_num_A
        session.vars["e_prop_num_B"] = e_prop_num_B


class PreResults(Page):
    pass


class Results(Page):
    # グラフ描画用
    @staticmethod
    def js_vars(player: Player):
        return dict(
            num_participants=player.session.num_participants,
            prop_num_A=player.session.vars["prop_num_A"],
            num_participants_u=player.session.vars["num_participants_u"],
            u_numA=player.session.vars["u_prop_num_A"],
            u_numB=player.session.vars["u_prop_num_B"],
            num_participants_s=player.session.vars["num_participants_s"],
            s_numA=player.session.vars["s_prop_num_A"],
            s_numB=player.session.vars["s_prop_num_B"],
            num_participants_e=player.session.vars["num_participants_e"],
            e_numA=player.session.vars["e_prop_num_A"],
            e_numB=player.session.vars["e_prop_num_B"],
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
