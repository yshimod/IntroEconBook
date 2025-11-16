from otree.api import *
import random

doc = """ ID末尾は実験者（サイコロ入力）．サイコロ99で終了． """


class C(BaseConstants):
    NAME_IN_URL = "ch3_3_repeated_infinite"
    PLAYERS_PER_GROUP = None

    NUM_SUPERGAME = 3
    NUM_ROUNDS = 100

    INSTRUCTIONS_TEMPLATE = "ch3_3_repeated_infinite/instructions.html"

    PAYOFF_A = cu(2)
    PAYOFF_B = cu(1)
    PAYOFF_C = cu(3)
    PAYOFF_D = cu(0)

    CHOICE_LABEL_1 = "A"
    CHOICE_LABEL_2 = "B"

    choice_list = [CHOICE_LABEL_1, CHOICE_LABEL_2]


class Subsession(BaseSubsession):
    idx_super_game = models.IntegerField()
    idx_sub_game = models.IntegerField()
    round_dice = models.IntegerField(initial=0)
    collapsed = models.BooleanField(initial=False)
    session_end = models.BooleanField(initial=False)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    is_experimenter = models.BooleanField(initial=False)
    round_dice_input = models.IntegerField(choices=list(range(1, 7)) + [99])

    flg_non_input = models.IntegerField(initial=0)
    flg_pair_non_input = models.IntegerField(initial=0)

    individual_choice = models.StringField(choices=C.choice_list)
    pair_choice = models.StringField()

    payoff_sup = models.CurrencyField()


# FUNCTIONS
def group_by_arrival_time_method(subsession: Subsession, waiting_players: list[Player]):
    players_per_group_gbatm = 2
    if len(waiting_players) >= players_per_group_gbatm:
        return random.sample(waiting_players, players_per_group_gbatm)


def creating_session(subsession: Subsession):
    if subsession.round_number == 1:
        subsession.idx_super_game = 1
        subsession.idx_sub_game = 1

    for p in subsession.get_players():
        if p.participant.vars.get("sequences_list") is None:
            p.participant.vars["sequences_list"] = {}
        p.participant.vars["sequences_list"]["infinite"] = [
            [] for _ in range(C.NUM_SUPERGAME)
        ]
        if p.id_in_subsession == subsession.session.num_participants:
            p.is_experimenter = True


def set_payoff(player: Player):
    payoff_matrix_p1 = {
        (C.CHOICE_LABEL_1, C.CHOICE_LABEL_1): C.PAYOFF_A,
        (C.CHOICE_LABEL_1, C.CHOICE_LABEL_2): C.PAYOFF_D,
        (C.CHOICE_LABEL_2, C.CHOICE_LABEL_1): C.PAYOFF_C,
        (C.CHOICE_LABEL_2, C.CHOICE_LABEL_2): C.PAYOFF_B,
    }
    payoff_matrix_p2 = {
        (C.CHOICE_LABEL_1, C.CHOICE_LABEL_1): C.PAYOFF_A,
        (C.CHOICE_LABEL_1, C.CHOICE_LABEL_2): C.PAYOFF_C,
        (C.CHOICE_LABEL_2, C.CHOICE_LABEL_1): C.PAYOFF_D,
        (C.CHOICE_LABEL_2, C.CHOICE_LABEL_2): C.PAYOFF_B,
    }
    other: Player = player.get_others_in_group()[0]
    player.pair_choice = other.individual_choice
    if other.flg_non_input == 1:
        player.flg_pair_non_input = 1

    if player.id_in_group == 1:
        player.payoff = payoff_matrix_p1[
            (player.individual_choice, other.individual_choice)
        ]
    else:
        player.payoff = payoff_matrix_p2[
            (other.individual_choice, player.individual_choice)
        ]


# PAGES
class EnterWaitPage(WaitPage):
    group_by_arrival_time = True

    @staticmethod
    def is_displayed(player: Player):
        return player.subsession.idx_sub_game == 1


class Introduction(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Decision(Page):
    form_model = "player"
    form_fields = ["individual_choice"]

    # @staticmethod
    # def get_timeout_seconds(player: Player):
    #     if player.is_experimenter:
    #         return 0
    #     else:
    #         return 40

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.flg_non_input = 1
            player.individual_choice = random.choice(C.choice_list)


class ResultsWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        for p in group.get_players():
            set_payoff(p)


class Results(Page):
    # @staticmethod
    # def get_timeout_seconds(player: Player):
    #     if player.is_experimenter:
    #         return 0
    #     else:
    #         return 20

    @staticmethod
    def vars_for_template(player: Player):
        opponent: Player = player.get_others_in_group()[0]
        return dict(
            opponent=opponent,
            my_decision=player.individual_choice,
            opponent_decision=opponent.individual_choice,
        )


class RollDice(Page):
    form_model = "player"
    form_fields = ["round_dice_input"]

    @staticmethod
    def is_displayed(player: Player):
        return player.is_experimenter

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if timeout_happened:
            player.round_dice_input = random.randint(1, 6)

        ss: Subsession = player.subsession
        ss.round_dice = player.round_dice_input

        if (player.round_number < C.NUM_ROUNDS) and (ss.round_dice != 99):
            next_ss: Subsession = ss.in_round(player.round_number + 1)

            if ss.round_dice > 1:
                # スーパーゲーム継続
                next_ss.idx_super_game = ss.idx_super_game
                next_ss.idx_sub_game = ss.idx_sub_game + 1
            else:
                # スーパーゲーム終了
                ss.collapsed = True
                if ss.idx_super_game < C.NUM_SUPERGAME:
                    # 次のスーパーゲームへ
                    next_ss.idx_super_game = ss.idx_super_game + 1
                    next_ss.idx_sub_game = 1
                else:
                    # セッション終了
                    ss.session_end = True
        else:
            # トータルラウンド数に達した場合，セッション終了
            ss.collapsed = True
            ss.session_end = True


class WaitRollDice(WaitPage):
    wait_for_all_groups = True


class DiceResults(Page):
    timeout_seconds = 20

    @staticmethod
    def is_displayed(player: Player):
        return not player.subsession.collapsed


class EndOfSuperGame(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.subsession.collapsed:
            start_round = player.round_number - player.subsession.idx_sub_game + 1
            sequences = [
                [
                    p.individual_choice,
                    p.get_others_in_group()[0].individual_choice,
                ]
                for p in player.in_rounds(start_round, player.round_number)
            ]
            player.participant.vars["sequences_list"]["infinite"][
                player.subsession.idx_super_game - 1
            ] = sequences
            player.payoff_sup = sum(
                [p.payoff for p in player.in_rounds(start_round, player.round_number)]
            )
            return True
        else:
            return False

    @staticmethod
    def vars_for_template(player: Player):
        sequences = player.participant.vars["sequences_list"]["infinite"][
            player.subsession.idx_super_game - 1
        ]

        coop_rate_self = (
            sum([el[0] == C.CHOICE_LABEL_1 for el in sequences]) / len(sequences)
            if len(sequences) > 0
            else -1
        )
        coop_rate_other = (
            sum([el[1] == C.CHOICE_LABEL_1 for el in sequences]) / len(sequences)
            if len(sequences) > 0
            else -1
        )
        return dict(
            sequences=sequences,
            coop_rate_self=coop_rate_self,
            coop_rate_other=coop_rate_other,
            payoff_sup=player.payoff_sup,
        )

    @staticmethod
    def app_after_this_page(player: Player, upcoming_apps):
        if player.subsession.session_end and len(upcoming_apps) > 0:
            return upcoming_apps[0]


page_sequence = [
    EnterWaitPage,
    Introduction,
    Decision,
    ResultsWaitPage,
    Results,
    RollDice,
    WaitRollDice,
    DiceResults,
    EndOfSuperGame,
]
