from otree.api import *
import random

doc = """ """


class C(BaseConstants):
    NAME_IN_URL = "ch2_3_chicken"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1

    PAYOFF_A = cu(20)
    PAYOFF_B = cu(-10)
    PAYOFF_C = cu(10)
    PAYOFF_D = cu(30)

    CHOICE_LIST = ["A", "B"]
    CHOICE_LABEL = "キャンパス"

    PAYOFF_MATRIX = {
        (CHOICE_LIST[0], CHOICE_LIST[0]): PAYOFF_B,
        (CHOICE_LIST[0], CHOICE_LIST[1]): PAYOFF_D,
        (CHOICE_LIST[1], CHOICE_LIST[0]): PAYOFF_A,
        (CHOICE_LIST[1], CHOICE_LIST[1]): PAYOFF_C,
    }

    Q1_SENTENCE = (
        "【クイズ1】 相手がキャンパスAを選んでいたら、あなたは何ポイント獲得しますか？"
    )
    Q2_SENTENCE = (
        "【クイズ2】 相手がキャンパスBを選んでいたら、あなたは何ポイント獲得しますか？"
    )


class Subsession(BaseSubsession):
    num_participants = models.IntegerField(initial=0)
    num_A = models.IntegerField(initial=0)
    num_B = models.IntegerField(initial=0)

    num_pairs = models.IntegerField(initial=0)
    num_pairs_AA = models.IntegerField(initial=0)
    num_pairs_AB = models.IntegerField(initial=0)
    num_pairs_BB = models.IntegerField(initial=0)


class Group(BaseGroup):
    pass


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
            for v in [C.PAYOFF_B, C.PAYOFF_D, C.PAYOFF_A, C.PAYOFF_C]
        ],
    )
    correct_q1 = models.StringField()
    score_q1 = models.BooleanField(initial=False)

    # クイズ2
    q2 = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label=C.Q2_SENTENCE,
        choices=[
            [str(int(v)), str(v)]
            for v in [C.PAYOFF_B, C.PAYOFF_D, C.PAYOFF_A, C.PAYOFF_C]
        ],
    )
    correct_q2 = models.StringField()
    score_q2 = models.BooleanField(initial=False)


# FUNCTIONS
def creating_session(subsession: Subsession):
    subsession.group_randomly()


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
        if g.get_player_by_id(1).field_maybe_none("individual_choice")
        and g.get_player_by_id(2).field_maybe_none("individual_choice")
    ]
    subsession.num_pairs = len(list_grp_results)
    subsession.num_pairs_AA = list_grp_results.count(
        (C.CHOICE_LIST[0], C.CHOICE_LIST[0])
    )
    subsession.num_pairs_BB = list_grp_results.count(
        (C.CHOICE_LIST[1], C.CHOICE_LIST[1])
    )
    subsession.num_pairs_AB = subsession.num_pairs - (
        subsession.num_pairs_AA + subsession.num_pairs_BB
    )


def set_payoff(player: Player):
    opponent: Player = player.get_others_in_group()[0]

    p_choice = player.field_maybe_none("individual_choice")
    o_choice = opponent.field_maybe_none("individual_choice")

    player.pair_choice = o_choice
    player.flg_pair_non_input = opponent.flg_non_input

    if p_choice and o_choice:
        player.payoff = C.PAYOFF_MATRIX[(p_choice, o_choice)]
    else:
        player.payoff = -1


def dump_js_vars(sub: Subsession):
    prop_A = -1
    prop_B = -1
    if sub.num_participants > 0:
        prop_A = (sub.num_A / sub.num_participants) * 100
        prop_B = (sub.num_B / sub.num_participants) * 100

    prop_pairs_AA = -1
    prop_pairs_AB = -1
    prop_pairs_BB = -1
    if sub.num_pairs > 0:
        prop_pairs_AA = (sub.num_pairs_AA / sub.num_pairs) * 100
        prop_pairs_AB = (sub.num_pairs_AB / sub.num_pairs) * 100
        prop_pairs_BB = (sub.num_pairs_BB / sub.num_pairs) * 100

    return dict(
        num_participants=sub.num_participants,
        prop_A=prop_A,
        prop_B=prop_B,
        num_pairs=sub.num_pairs,
        prop_pairs_AA=prop_pairs_AA,
        prop_pairs_AB=prop_pairs_AB,
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
            correct_q1 = C.PAYOFF_MATRIX[(player.individual_choice, C.CHOICE_LIST[0])]
            correct_q2 = C.PAYOFF_MATRIX[(player.individual_choice, C.CHOICE_LIST[1])]

            player.correct_q1 = str(int(correct_q1))
            player.correct_q2 = str(int(correct_q2))

            if player.field_maybe_none("q1"):
                player.score_q1 = player.q1 == player.correct_q1
            if player.field_maybe_none("q2"):
                player.score_q2 = player.q2 == player.correct_q2


class Quiz_Feedback(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            results=[
                {
                    "question": C.Q1_SENTENCE,
                    "player_answer": player.field_maybe_none("q1"),
                    "correct_answer": player.field_maybe_none("correct_q1"),
                    "score": "正解" if player.score_q1 else "不正解",
                },
                {
                    "question": C.Q2_SENTENCE,
                    "player_answer": player.field_maybe_none("q2"),
                    "correct_answer": player.field_maybe_none("correct_q2"),
                    "score": "正解" if player.score_q2 else "不正解",
                },
            ]
        )


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
            my_decision=player.field_maybe_none("individual_choice"),
            opponent_decision=opponent.field_maybe_none("individual_choice"),
        )

    @staticmethod
    def js_vars(player: Player):
        return dump_js_vars(player.subsession)


page_sequence = [
    Introduction,
    Decision,
    Question,
    Quiz_Feedback,
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
        list_comment=list_comment,
        prop_perfect_score=prop_perfect_score,
    )
