from otree.api import *
import random

doc = """ """


class C(BaseConstants):
    NAME_IN_URL = "ch2_4_extensive"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 4

    PAYOFF_A = cu(20)
    PAYOFF_B = cu(-10)
    PAYOFF_C = cu(10)
    PAYOFF_D = cu(30)

    CHOICE_LIST = ["A", "B"]
    CHOICE_LABEL = "キャンパス"


class Subsession(BaseSubsession):
    num_pairs = models.IntegerField(initial=0)
    num_pairs_AA = models.IntegerField(initial=0)
    num_pairs_AB = models.IntegerField(initial=0)
    num_pairs_BA = models.IntegerField(initial=0)
    num_pairs_BB = models.IntegerField(initial=0)


class Group(BaseGroup):
    # First mover (P1)
    p1_decision = models.StringField(
        choices=C.CHOICE_LIST,
    )
    flg_non_input_p1 = models.IntegerField(initial=0)
    individual_choice_comment_p1 = models.LongStringField(
        label="【質問】なぜあなたはその選択肢を選んだのか、理由を教えてください。"
    )

    # Second mover (P2)
    p2_decision = models.StringField(
        choices=C.CHOICE_LIST,
    )
    flg_non_input_p2 = models.IntegerField(initial=0)
    individual_choice_comment_p2 = models.LongStringField(
        label="【質問】なぜあなたはその選択肢を選んだのか、理由を教えてください。"
    )


class Player(BasePlayer):
    pass


# FUNCTIONS
def creating_session(subsession: Subsession):
    subsession.group_randomly()


def summarize_data(subsession: Subsession):
    list_grp_results = [
        (
            g.p1_decision,
            g.p2_decision,
        )
        for g in subsession.get_groups()
        if g.field_maybe_none("p1_decision") and g.field_maybe_none("p2_decision")
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
    payoff_matrix = {
        (C.CHOICE_LIST[0], C.CHOICE_LIST[0]): C.PAYOFF_B,
        (C.CHOICE_LIST[0], C.CHOICE_LIST[1]): C.PAYOFF_D,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[0]): C.PAYOFF_A,
        (C.CHOICE_LIST[1], C.CHOICE_LIST[1]): C.PAYOFF_C,
    }
    p1: Player = group.get_player_by_id(1)
    p2: Player = group.get_player_by_id(2)

    p1_choice = group.field_maybe_none("p1_decision")
    p2_choice = group.field_maybe_none("p2_decision")

    if p1_choice and p2_choice:
        p1.payoff = payoff_matrix[(p1_choice, p2_choice)]
        p2.payoff = payoff_matrix[(p2_choice, p1_choice)]
    else:
        p1.payoff = -1
        p2.payoff = -1


def dump_js_vars(sub: Subsession):
    return dict(
        num_pairs=sub.num_pairs,
        num_pairs_AA=sub.num_pairs_AA,
        num_pairs_AB=sub.num_pairs_AB,
        num_pairs_BA=sub.num_pairs_BA,
        num_pairs_BB=sub.num_pairs_BB,
    )


# PAGES
class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class First_mover(Page):
    form_model = "group"

    @staticmethod
    def get_form_fields(group: Group):
        form_fields = ["p1_decision"]
        if group.round_number == 1:
            form_fields.append("individual_choice_comment_p1")
        return form_fields

    @staticmethod
    def is_displayed(player: Player):
        return player.id_in_group == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        group: Group = player.group
        if timeout_happened:
            group.flg_non_input_p1 = 1
            group.p1_decision = random.choice(C.CHOICE_LIST)


class WaitForFirstMover(WaitPage):
    pass


class Second_mover(Page):
    form_model = "group"

    @staticmethod
    def get_form_fields(group: Group):
        form_fields = ["p2_decision"]
        if group.round_number == 1:
            form_fields.append("individual_choice_comment_p2")
        return form_fields

    @staticmethod
    def is_displayed(player: Player):
        return player.id_in_group == 2

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        group: Group = player.group
        if timeout_happened:
            group.flg_non_input_p2 = 1
            group.p2_decision = random.choice(C.CHOICE_LIST)


class ResultsWaitPage(WaitPage):
    wait_for_all_groups = True

    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        summarize_data(subsession)
        for g in subsession.get_groups():
            set_payoff(g)


class Results(Page):
    @staticmethod
    def js_vars(player: Player):
        return dump_js_vars(player.subsession)


page_sequence = [
    Introduction,
    First_mover,
    WaitForFirstMover,
    Second_mover,
    ResultsWaitPage,
    Results,
]


def vars_for_admin_report(subsession: Subsession):
    list_comment = []
    if subsession.round_number == 1:
        list_comment = sorted(
            [
                [
                    g.p1_decision,
                    g.individual_choice_comment_p1,
                    g.p2_decision,
                    g.individual_choice_comment_p2,
                ]
                for g in subsession.get_groups()
            ],
            key=lambda x: (x[0], x[2]),
        )

    return dict(
        js_vars=dump_js_vars(subsession),
        list_comment=list_comment,
    )


def custom_export(players: list[Player]):
    yield [
        "session.code",
        "round_number",
        "id_in_subsession",
        "p1_decision",
        "p2_decision",
    ]

    for p in players:
        if p.id_in_group == 1:
            g: Group = p.group
            yield [
                p.session.code,
                p.round_number,
                g.id_in_subsession,
                g.p1_decision,
                g.p2_decision,
            ]
