from otree.api import *
import random

doc = """ """


class C(BaseConstants):
    NAME_IN_URL = "ch2_1_coordination"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3

    PAYOFF_A = cu(5)
    PAYOFF_B = cu(10)
    PAYOFF_C = cu(3)
    PAYOFF_D = cu(2)

    CHOICE_LIST = ["1", "2"]

    PAYOFF_MATRIX = {
        (CHOICE_LIST[0], CHOICE_LIST[0]): (PAYOFF_A, PAYOFF_B),
        (CHOICE_LIST[0], CHOICE_LIST[1]): (PAYOFF_D, PAYOFF_D),
        (CHOICE_LIST[1], CHOICE_LIST[0]): (PAYOFF_C, PAYOFF_C),
        (CHOICE_LIST[1], CHOICE_LIST[1]): (PAYOFF_B, PAYOFF_A),
    }

    Q1_SENTENCE = "相手が映画1を選んでいたら、あなたは何ポイント獲得しますか？"
    Q2_SENTENCE = "相手が映画2を選んでいたら、あなたは何ポイント獲得しますか？"


class Subsession(BaseSubsession):
    num_pairs = models.IntegerField(initial=0)
    num_pairs_AA = models.IntegerField(initial=0)
    num_pairs_AB = models.IntegerField(initial=0)
    num_pairs_BA = models.IntegerField(initial=0)
    num_pairs_BB = models.IntegerField(initial=0)


class Group(BaseGroup):
    sucsess_coordination = models.BooleanField()


class Player(BasePlayer):
    # 自身の意思決定
    individual_choice = models.StringField(
        choices=C.CHOICE_LIST,
    )
    flg_non_input = models.IntegerField(initial=0)

    # 相手の意思決定
    pair_choice = models.StringField()
    flg_pair_non_input = models.IntegerField(initial=0)

    # 相手はどちらを選ぶと思うか
    think_other_player_choice = models.StringField(
        choices=C.CHOICE_LIST,
        initial="",
    )

    # 意思決定の理由
    individual_choice_comment = models.LongStringField(
        label="",
        initial="",
    )

    # クイズ1
    q1 = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label=C.Q1_SENTENCE,
        choices=[
            [str(int(v)), str(v)]
            for v in [C.PAYOFF_A, C.PAYOFF_B, C.PAYOFF_C, C.PAYOFF_D]
        ],
    )
    score_q1 = models.BooleanField(initial=False)

    # クイズ2
    q2 = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label=C.Q2_SENTENCE,
        choices=[
            [str(int(v)), str(v)]
            for v in [C.PAYOFF_A, C.PAYOFF_B, C.PAYOFF_C, C.PAYOFF_D]
        ],
    )
    score_q2 = models.BooleanField(initial=False)


# FUNCTIONS
def creating_session(subsession: Subsession):
    subsession.group_randomly()


def summarize_data(subsession: Subsession):
    list_grp_results = [
        (
            g.get_player_by_id(1).individual_choice,
            g.get_player_by_id(2).individual_choice,
        )
        for g in subsession.get_groups()
        if g.get_player_by_id(1).field_maybe_none("individual_choice")
        and g.get_player_by_id(2).field_maybe_none("individual_choice")
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


def set_payoff(group: Group):
    p1: Player = group.get_player_by_id(1)
    p2: Player = group.get_player_by_id(2)
    p1_choice = p1.field_maybe_none("individual_choice")
    p2_choice = p2.field_maybe_none("individual_choice")

    p1.pair_choice = p2_choice
    p2.pair_choice = p1_choice
    p1.flg_pair_non_input = p2.flg_non_input
    p2.flg_pair_non_input = p1.flg_non_input

    if p1_choice and p2_choice:
        p1.payoff, p2.payoff = C.PAYOFF_MATRIX[(p1_choice, p2_choice)]
        group.sucsess_coordination = p1_choice == p2_choice
    else:
        p1.payoff = -1
        p2.payoff = -1


def dump_js_vars(sub: Subsession):
    prop_pairs_AA = -1
    prop_pairs_AB = -1
    prop_pairs_BA = -1
    prop_pairs_BB = -1
    if sub.num_pairs > 0:
        prop_pairs_AA = (sub.num_pairs_AA / sub.num_pairs) * 100
        prop_pairs_AB = (sub.num_pairs_AB / sub.num_pairs) * 100
        prop_pairs_BA = (sub.num_pairs_BA / sub.num_pairs) * 100
        prop_pairs_BB = (sub.num_pairs_BB / sub.num_pairs) * 100

    return dict(
        num_pairs=sub.num_pairs,
        prop_pairs_AA=prop_pairs_AA,
        prop_pairs_AB=prop_pairs_AB,
        prop_pairs_BA=prop_pairs_BA,
        prop_pairs_BB=prop_pairs_BB,
    )


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Decision(Page):
    form_model = "player"

    @staticmethod
    def get_form_fields(player: Player):
        form_fields = [
            "individual_choice",
            "think_other_player_choice",
        ]
        if player.round_number == 1:
            form_fields.append("individual_choice_comment")
        return form_fields

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.flg_non_input = 1
            player.individual_choice = random.choice(C.CHOICE_LIST)


class Question(Page):
    form_model = "player"
    form_fields = [
        "q1",
        "q2",
    ]

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.field_maybe_none("individual_choice"):
            if player.id_in_group == 1:
                correct_q1, _ = C.PAYOFF_MATRIX[
                    (player.individual_choice, C.CHOICE_LIST[0])
                ]
                correct_q2, _ = C.PAYOFF_MATRIX[
                    (player.individual_choice, C.CHOICE_LIST[1])
                ]
            else:
                _, correct_q1 = C.PAYOFF_MATRIX[
                    (C.CHOICE_LIST[0], player.individual_choice)
                ]
                _, correct_q2 = C.PAYOFF_MATRIX[
                    (C.CHOICE_LIST[1], player.individual_choice)
                ]

            if player.field_maybe_none("q1"):
                player.score_q1 = player.q1 == str(int(correct_q1))
            if player.field_maybe_none("q2"):
                player.score_q2 = player.q2 == str(int(correct_q2))


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        summarize_data(subsession)
        for grp in subsession.get_groups():
            set_payoff(grp)


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        opponent: Player = player.get_others_in_group()[0]
        return dict(
            my_decision=player.field_maybe_none("individual_choice"),
            opponent_decision=opponent.field_maybe_none("individual_choice"),
        )

    @staticmethod
    def js_vars(player: Player):
        sub: Subsession = player.subsession
        return dump_js_vars(sub)


page_sequence = [
    Introduction,
    Decision,
    Question,
    ResultsWaitPage,
    Results,
]


def vars_for_admin_report(subsession: Subsession):
    list_sucsess_coordination = []
    prop_sucsess_coordination = -1
    list_sucsess_coordination = [
        int(grp.sucsess_coordination)
        for grp in subsession.get_groups()
        if grp.field_maybe_none("sucsess_coordination") is not None
    ]
    if list_sucsess_coordination:
        prop_sucsess_coordination = (
            100 * sum(list_sucsess_coordination) / len(list_sucsess_coordination)
        )

    list_comment = []
    if subsession.round_number == 1:
        list_comment = sorted(
            [
                [
                    p.id_in_group,
                    p.individual_choice,
                    p.think_other_player_choice,
                    p.pair_choice,
                    p.individual_choice_comment,
                ]
                for p in subsession.get_players()
            ]
        )

    list_perfect_score = []
    prop_perfect_score = -1
    if subsession.round_number == 1:
        list_perfect_score = [
            int(p.score_q1) * int(p.score_q2) for p in subsession.get_players()
        ]
        if list_perfect_score:
            prop_perfect_score = 100 * sum(list_perfect_score) / len(list_perfect_score)

    return dict(
        js_vars=dump_js_vars(subsession),
        prop_sucsess_coordination=prop_sucsess_coordination,
        list_comment=list_comment,
        prop_perfect_score=prop_perfect_score,
    )
