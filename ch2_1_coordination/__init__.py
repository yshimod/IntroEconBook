from otree.api import *
import random

doc = """ """


class C(BaseConstants):
    NAME_IN_URL = "ch2_1_coordination"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    PAYOFF_A = cu(5)
    PAYOFF_B = cu(10)
    PAYOFF_C = cu(3)
    PAYOFF_D = cu(2)

    CHOICE_LIST = ["A", "B"]


class Subsession(BaseSubsession):
    num_participants = models.IntegerField(initial=0)
    num_A = models.IntegerField(initial=0)
    num_B = models.IntegerField(initial=0)

    num_pairs = models.IntegerField(initial=0)
    num_pairs_AA = models.IntegerField(initial=0)
    num_pairs_AB = models.IntegerField(initial=0)
    num_pairs_BA = models.IntegerField(initial=0)
    num_pairs_BB = models.IntegerField(initial=0)

    err_message = models.StringField()
    pair_err_message = models.StringField()


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # 自身の意思決定
    individual_choice = models.StringField(
        choices=[["A", "A"], ["B", "B"]],
        doc="""This player's decision""",
        widget=widgets.RadioSelect,
    )
    flg_non_input = models.IntegerField(initial=0)

    # 相手の意思決定
    pair_choice = models.StringField()
    flg_pair_non_input = models.IntegerField(initial=0)
    # 相手のグループID
    pair_id = models.IntegerField(initial=0)

    # 相手はどちらを選ぶと思うか
    think_other_player_choice = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        verbose_name="",
        choices=[
            ["Aを選ぶと予想する", "映画1を選ぶと予想する"],
            ["Bを選ぶと予想する", "映画2を選ぶと予想する"],
        ],
    )

    # 意思決定の理由
    individual_choice_comment = models.LongStringField(verbose_name="", initial="")

    # 相手の予想のの理由
    think_other_player_choice_comment = models.LongStringField(
        verbose_name="", initial=""
    )

    # 相手が映画１を選んだ際に、あなたは何ポイント獲得しますか？
    q1 = models.StringField(
        # widget=widgets.RadioSelectHorizontal,
        verbose_name="",
        choices=[
            ["5", "5"],
            ["10", "10"],
            ["2", "2"],
            ["3", "3"],
        ],
    )

    # 相手が映画2を選んだ際に、あなたは何ポイント獲得しますか？
    q2 = models.StringField(
        # widget=widgets.RadioSelectHorizontal,
        verbose_name="",
        choices=[
            ["5", "5"],
            ["10", "10"],
            ["2", "2"],
            ["3", "3"],
        ],
    )


# FUNCTIONS
def keisan(player: Player):
    sub = player.subsession
    if player.individual_choice != "":
        # グラフ用集計
        sub.num_participants += 1
        s = player.individual_choice
        if s == "A":
            sub.num_A += 1
        elif s == "B":
            sub.num_B += 1
        else:
            sub.err_message = "エラーあり"
    else:
        player.flg_non_input = 1
        player.individual_choice = random.choice(C.CHOICE_LIST)


def graph_pair(player: Player):
    sub = player.subsession
    sub.num_pairs += 1
    # グラフ用集計
    s = player.individual_choice
    sp = player.pair_choice
    if (s == "A") and (sp == "A"):
        sub.num_pairs_AA += 1
    elif (s == "A") and (sp == "B"):
        sub.num_pairs_AB += 1
    elif (s == "B") and (sp == "A"):
        sub.num_pairs_BA += 1
    elif (s == "B") and (sp == "B"):
        sub.num_pairs_BB += 1
    else:
        sub.pair_err_message = "エラーあり"


def set_payoff(player: Player):
    payoff_matrix_p1 = {
        ("A", "A"): C.PAYOFF_A,
        ("A", "B"): C.PAYOFF_D,
        ("B", "A"): C.PAYOFF_C,
        ("B", "B"): C.PAYOFF_B,
    }
    payoff_matrix_p2 = {
        ("A", "A"): C.PAYOFF_B,
        ("A", "B"): C.PAYOFF_D,
        ("B", "A"): C.PAYOFF_C,
        ("B", "B"): C.PAYOFF_A,
    }
    opponent: Player = player.get_others_in_group()[0]
    player.pair_choice = opponent.individual_choice
    player.pair_id = opponent.id_in_group
    if opponent.flg_non_input == 1:
        player.flg_pair_non_input = 1

    print(player.individual_choice, opponent.individual_choice)
    if player.id_in_group == 1:
        player.payoff = payoff_matrix_p1[
            (player.individual_choice, opponent.individual_choice)
        ]
    else:
        player.payoff = payoff_matrix_p2[
            (opponent.individual_choice, player.individual_choice)
        ]
    print(player.id_in_group, player.payoff)


# PAGES
class Introduction(Page):
    # timeout_seconds = 100
    pass


class Decision(Page):
    form_model = "player"
    form_fields = [
        "individual_choice",
        "individual_choice_comment",
    ]


class Question(Page):
    form_model = "player"
    form_fields = [
        "q1",
        "q2",
        "think_other_player_choice",
        "think_other_player_choice_comment",
    ]


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        for p in subsession.get_players():
            keisan(p)
        for p in subsession.get_players():
            set_payoff(p)
        for p in subsession.get_players():
            graph_pair(p)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        opponent: Player = player.get_others_in_group()[0]

        if player.individual_choice == "A":
            disp_my_decision = "映画1"
        else:
            disp_my_decision = "映画2"

        if opponent.individual_choice == "A":
            disp_opponent_decision = "映画1"
        else:
            disp_opponent_decision = "映画2"

        print(disp_my_decision)
        return dict(
            opponent=opponent,
            same_choice=player.individual_choice == opponent.individual_choice,
            my_decision=disp_my_decision,
            opponent_decision=disp_opponent_decision,
        )

    @staticmethod
    def js_vars(player: Player):
        print("js_vars")
        sub = player.subsession
        # 割合に計算
        if sub.num_A > 0:
            prop_A = round((sub.num_A / sub.num_participants) * 100, 2)
        else:
            prop_A = 0
        if sub.num_B > 0:
            prop_B = round((sub.num_B / sub.num_participants) * 100, 2)
        else:
            prop_B = 0

        print("ここから追加")
        # 割合に計算s
        if sub.num_pairs_AA > 0:
            prop_pairs_AA = round((sub.num_pairs_AA / sub.num_pairs) * 100, 2)
        else:
            prop_pairs_AA = 0
        if sub.num_pairs_AB > 0:
            prop_pairs_AB = round((sub.num_pairs_AB / sub.num_pairs) * 100, 2)
        else:
            prop_pairs_AB = 0
        if sub.num_pairs_BA > 0:
            prop_pairs_BA = round((sub.num_pairs_BA / sub.num_pairs) * 100, 2)
        else:
            prop_pairs_BA = 0
        if sub.num_pairs_BB > 0:
            prop_pairs_BB = round((sub.num_pairs_BB / sub.num_pairs) * 100, 2)
        else:
            prop_pairs_BB = 0

        return dict(
            num_participants=sub.num_participants,
            prop_A=prop_A,
            prop_B=prop_B,
            num_pairs=sub.num_pairs,
            prop_pairs_AA=prop_pairs_AA,
            prop_pairs_AB=prop_pairs_AB,
            prop_pairs_BA=prop_pairs_BA,
            prop_pairs_BB=prop_pairs_BB,
        )


class PreResults(Page):
    pass


page_sequence = [
    Introduction,
    Decision,
    Question,
    ResultsWaitPage,
    PreResults,
    Results,
]
