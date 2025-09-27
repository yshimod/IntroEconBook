from otree.api import *
import random

doc = """
This is a one-shot "Prisoner's Dilemma". Two players are asked separately
whether they want to cooperate or defect. Their choices directly determine the
payoffs.
"""


class C(BaseConstants):
    NAME_IN_URL = "ch1_2_prisoner"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    INSTRUCTIONS_TEMPLATE = "ch1_2_prisoner/instructions.html"

    PAYOFF_A = cu(150)
    PAYOFF_B = cu(100)
    PAYOFF_C = cu(50)
    PAYOFF_D = cu(10)

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


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    individual_choice = models.StringField(
        choices=C.CHOICE_LIST,
    )
    # 相手の意思決定
    pair_choice = models.StringField()

    # 相手はどちらを選ぶと思うか
    think_other_player_choice = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        verbose_name="",
        choices=[
            ["Aを選ぶと予想する", "Aを選ぶと予想する"],
            ["Bを選ぶと予想する", "Bを選ぶと予想する"],
        ],
    )

    # 意思決定の理由
    individual_choice_comment = models.LongStringField(verbose_name="", initial="")

    flg_non_input = models.IntegerField(initial=0)
    flg_pair_non_input = models.IntegerField(initial=0)


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

    list_grp_results = [
        (
            g.get_player_by_id(1).individual_choice,
            g.get_player_by_id(2).individual_choice,
        )
        for g in subsession.get_groups()
    ]
    subsession.num_pairs = len(list_grp_results)
    subsession.num_pairs_AA = list_grp_results.count(
        (C.CHOICE_LIST[0], C.CHOICE_LIST[0])
    )
    subsession.num_pairs_AB = list_grp_results.count(
        (C.CHOICE_LIST[0], C.CHOICE_LIST[1])
    )
    subsession.num_pairs_BA = list_grp_results.count(
        (C.CHOICE_LIST[1], C.CHOICE_LIST[0])
    )
    subsession.num_pairs_BB = list_grp_results.count(
        (C.CHOICE_LIST[1], C.CHOICE_LIST[1])
    )


def set_payoff(player: Player):
    payoff_matrix = {
        (C.CHOICE_LIST[0], C.CHOICE_LIST[0]): C.PAYOFF_B,
        (C.CHOICE_LIST[0], C.CHOICE_LIST[1]): C.PAYOFF_D,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[0]): C.PAYOFF_A,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[1]): C.PAYOFF_C,
    }
    opponent: Player = player.get_others_in_group()[0]
    player.pair_choice = opponent.individual_choice
    if opponent.flg_non_input == 1:
        player.flg_pair_non_input = 1
    player.payoff = payoff_matrix[
        (player.individual_choice, opponent.individual_choice)
    ]


# PAGES
class Introduction(Page):
    timeout_seconds = 100


class Decision(Page):
    form_model = "player"
    form_fields = [
        "individual_choice",
        "think_other_player_choice",
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
        for p in subsession.get_players():
            set_payoff(p)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        opponent: Player = player.get_others_in_group()[0]
        return dict(
            opponent=opponent,
            same_choice=player.individual_choice == opponent.individual_choice,
            my_decision=player.field_display("individual_choice"),
            opponent_decision=opponent.field_display("individual_choice"),
        )

    # グラフ描画用
    @staticmethod
    def js_vars(player: Player):
        print("js_vars")
        sub: Subsession = player.subsession
        # 割合に計算
        if sub.num_A > 0:
            prop_num_A = round((sub.num_A / sub.num_participants) * 100, 2)
        else:
            prop_num_A = 0
        if sub.num_B > 0:
            prop_num_B = round((sub.num_B / sub.num_participants) * 100, 2)
        else:
            prop_num_B = 0

        print("ここから追加")
        # 割合に計算s
        if sub.num_pairs_AA > 0:
            prop_pair_num_AA = round((sub.num_pairs_AA / sub.num_pairs) * 100, 2)
        else:
            prop_pair_num_AA = 0
        if sub.num_pairs_AB > 0:
            prop_pair_num_AB = round((sub.num_pairs_AB / sub.num_pairs) * 100, 2)
        else:
            prop_pair_num_AB = 0
        if sub.num_pairs_BA > 0:
            prop_pair_num_BA = round((sub.num_pairs_BA / sub.num_pairs) * 100, 2)
        else:
            prop_pair_num_BA = 0
        if sub.num_pairs_BB > 0:
            prop_pair_num_BB = round((sub.num_pairs_BB / sub.num_pairs) * 100, 2)
        else:
            prop_pair_num_BB = 0

        return dict(
            num_participants=sub.num_participants,
            num_A=prop_num_A,
            num_B=prop_num_B,
            num_pairs=sub.num_pairs,
            num_AA=prop_pair_num_AA,
            num_AB=prop_pair_num_AB,
            num_BA=prop_pair_num_BA,
            num_BB=prop_pair_num_BB,
        )


class PreResults(Page):
    pass


page_sequence = [
    Introduction,
    Decision,
    ResultsWaitPage,
    PreResults,
    Results,
]
