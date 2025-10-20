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
        widget=widgets.RadioSelectHorizontal,
        label="【質問】あなたの相手はどちらを選ぶと思いますか？",
        choices=[
            [v, "{}{}を選ぶと予想する".format(C.CHOICE_LABEL, v)] for v in C.CHOICE_LIST
        ],
    )

    # 意思決定の理由
    individual_choice_comment = models.LongStringField(
        label="【質問】なぜあなたはその選択肢を選んだのか、理由を教えてください。"
    )

    # 相手の予想の理由
    think_other_player_choice_comment = models.LongStringField(
        label="【質問】なぜあなたは、相手がその選択肢を選ぶと思ったのか、理由を教えてください。"
    )

    # クイズ1
    q1 = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="【理解度確認クイズ】 相手が{}{}を選んでいたら、あなたは何ポイント獲得しますか？".format(
            C.CHOICE_LABEL, C.CHOICE_LIST[0]
        ),
        choices=[C.PAYOFF_B, C.PAYOFF_D, C.PAYOFF_A, C.PAYOFF_C],
    )

    # クイズ2
    q2 = models.StringField(
        widget=widgets.RadioSelectHorizontal,
        label="【理解度確認クイズ】 相手が{}{}を選んでいたら、あなたは何ポイント獲得しますか？".format(
            C.CHOICE_LABEL, C.CHOICE_LIST[1]
        ),
        choices=[C.PAYOFF_B, C.PAYOFF_D, C.PAYOFF_A, C.PAYOFF_C],
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
    payoff_matrix = {
        (C.CHOICE_LIST[0], C.CHOICE_LIST[0]): C.PAYOFF_B,
        (C.CHOICE_LIST[0], C.CHOICE_LIST[1]): C.PAYOFF_D,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[0]): C.PAYOFF_A,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[1]): C.PAYOFF_C,
    }
    opponent: Player = player.get_others_in_group()[0]

    p_choice = player.field_maybe_none("individual_choice")
    o_choice = opponent.field_maybe_none("individual_choice")

    player.pair_choice = o_choice
    player.flg_pair_non_input = opponent.flg_non_input

    if p_choice and o_choice:
        player.payoff = payoff_matrix[(p_choice, o_choice)]
    else:
        player.payoff = -1


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
        "think_other_player_choice",
        "think_other_player_choice_comment",
    ]


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        summarize_data(subsession)
        for p in subsession.get_players():
            set_payoff(p)


class PreResults(Page):
    pass


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


page_sequence = [
    Introduction,
    Decision,
    Question,
    ResultsWaitPage,
    PreResults,
    Results,
]
