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
    NUM_ROUNDS = 5

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

    series_prop_A = [-1] * sub.round_number
    for ss_t in sub.in_rounds(1, sub.round_number):
        if ss_t.num_participants > 0:
            series_prop_A[ss_t.round_number - 1] = (
                100 * ss_t.num_A / ss_t.num_participants
            )

    return dict(
        num_participants=sub.num_participants,
        prop_A=prop_A,
        prop_B=prop_B,
        num_pairs=sub.num_pairs,
        prop_pairs_AA=prop_pairs_AA,
        prop_pairs_AB=prop_pairs_AB,
        prop_pairs_BB=prop_pairs_BB,
        series_prop_A=series_prop_A,
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
        if (player.round_number == 1) or (player.round_number == C.NUM_ROUNDS):
            form_fields.append("individual_choice_comment")
        return form_fields

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
            my_decision=player.field_maybe_none("individual_choice"),
            opponent_decision=opponent.field_maybe_none("individual_choice"),
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
    if subsession.round_number == 1 or subsession.round_number == C.NUM_ROUNDS:
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

    return dict(
        js_vars=dump_js_vars(subsession),
        list_comment=list_comment,
        show_series=(C.NUM_ROUNDS > 1 and subsession.round_number == C.NUM_ROUNDS),
    )


def custom_export(players: list[Player]):
    yield [
        "session.code",
        "id_in_subsession",
        "round_number",
        "group.id_in_subsession",
        "id_in_group",
        "individual_choice",
        "think_other_player_choice",
        "pair_choice",
    ]

    for p in players:
        yield [
            p.session.code,
            p.id_in_subsession,
            p.round_number,
            p.group.id_in_subsession,
            p.id_in_group,
            p.individual_choice,
            p.think_other_player_choice,
            p.pair_choice,
        ]
