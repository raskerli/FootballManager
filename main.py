import pygame
import sys
import pickle
import os
import random
from config import *
from database import generate_teams, create_schedule, generate_free_agents
from models import Player, Team, LiveMatch, create_regen
from ui import Tab, Button
import views


class UCLManager:
    def __init__(self):
        pygame.init()
        # --- VIRTUAL RESOLUTION SETUP ---
        self.base_width = 1280
        self.base_height = 850
        self.virtual_surface = pygame.Surface((self.base_width, self.base_height))
        self.screen = pygame.display.set_mode((self.base_width, self.base_height), pygame.RESIZABLE)
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.is_fullscreen = False
        self.clock = pygame.time.Clock()

        self.restart_game(initial=True)

        # --- TABS SETUP ---
        # Starting x=50 to make room for the scroll button
        self.tabs = {
            'DASHBOARD': Tab("Dashboard", pygame.Rect(50, 100, 130, 50)),
            'SQUAD': Tab("Squad", pygame.Rect(190, 100, 130, 50)),
            'MARKET': Tab("Market", pygame.Rect(330, 100, 130, 50)),
            'TRAINING': Tab("Training", pygame.Rect(470, 100, 130, 50)),
            'SCOUTING': Tab("Scouting", pygame.Rect(610, 100, 130, 50)),
            'TEAMS': Tab("Teams", pygame.Rect(750, 100, 130, 50)),
            'STANDINGS': Tab("Table", pygame.Rect(890, 100, 130, 50)),
            'STATS': Tab("Stats", pygame.Rect(1030, 100, 130, 50)),
            'FIXTURES': Tab("Knockout", pygame.Rect(1170, 100, 130, 50)),
            'HISTORY': Tab("History", pygame.Rect(1310, 100, 130, 50))
        }

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.base_width, self.base_height), pygame.RESIZABLE)

    def calculate_scale(self):
        window_w, window_h = self.screen.get_size()
        scale_w = window_w / self.base_width
        scale_h = window_h / self.base_height
        self.scale_factor = min(scale_w, scale_h)
        new_w = int(self.base_width * self.scale_factor)
        new_h = int(self.base_height * self.scale_factor)
        self.offset_x = (window_w - new_w) // 2
        self.offset_y = (window_h - new_h) // 2

    def get_game_mouse_pos(self):
        mx, my = pygame.mouse.get_pos()
        mx -= self.offset_x
        my -= self.offset_y
        mx /= self.scale_factor
        my /= self.scale_factor
        return int(mx), int(my)

    def restart_game(self, initial=False):
        self.teams = generate_teams()
        self.free_agents = generate_free_agents(40)
        self.schedule = create_schedule(self.teams)
        self.my_team = None;
        self.champion = None
        self.current_year = 2026
        self.history_winners = []
        self.phase = "LEAGUE";
        self.matchday = 0;
        self.round_name = "";
        self.knockout_fixtures = []
        self.knockout_results = {};
        self.knockout_history = []
        self.history_page = 0
        self.leg = 1;
        self.leg1_scores = {}

        self.logs = ["Welcome to UCL Manager!"]
        self.state = 'SELECT';
        self.active_tab = 'DASHBOARD';
        self.message = "Select your club."
        self.scroll_y = 0;
        self.selected_player_idx = None;
        self.market_cache = []
        self.scout_results = []
        self.game_over = False;
        self.spectator_mode = False
        self.was_fired = False
        self.career_total_wins = 0;
        self.career_trophies = 0
        self.manager_rep = 50
        self.job_offers = []

        self.selected_view_team = None;
        self.market_search_query = "";
        self.market_filter_pos = "ALL"
        self.is_typing_search = False
        self.current_live_match = None

        # --- TAB SCROLL STATE ---
        self.tab_scroll = 0
        self.btn_tab_left = Button(5, 105, 30, 40, "<", BG_PANEL)
        self.btn_tab_right = Button(1245, 105, 30, 40, ">", BG_PANEL)

        # Initialize ALL buttons to None to prevent crashes
        self.btn_sim = None;
        self.btn_next_season = None
        self.btn_save = None;
        self.btn_load = None;
        self.btn_restart = None
        self.btn_scout_search = None;
        self.btn_sell = None;
        self.btn_sim_ko = None
        self.btn_spectate = None;
        self.btn_world_stats = None;
        self.btn_back = None
        self.btn_retire = None;
        self.btn_tac = None;
        self.btn_form = None

        self.market_buttons = [];
        self.squad_buttons = [];
        self.scouting_buttons = []
        self.team_view_buttons = [];
        self.market_filter_buttons = []
        self.match_control_buttons = [];
        self.knockout_buttons = [];
        self.job_buttons = []
        self.training_buttons = []

    def set_my_team(self, team):
        self.my_team = team;
        self.spectator_mode = False
        for p in self.my_team.squad: p.scouted = True
        self.state = 'GAME';
        self.active_tab = 'DASHBOARD';
        self.message = f"Managing {team.name}!"

    def start_spectator_mode(self):
        self.my_team = None;
        self.spectator_mode = True
        self.state = 'GAME';
        self.active_tab = 'DASHBOARD';
        self.message = "Spectator Mode Active."
        for t in self.teams:
            for p in t.squad: p.scouted = True

    def retire_career(self):
        self.game_over = True
        self.was_fired = False
        self.state = 'WINNER'
        self.message = "Career Retired."
        if self.my_team:
            for p in self.my_team.squad: p.grow()

    def check_sacking(self):
        if not self.spectator_mode and self.manager_rep < 10:
            self.game_over = True
            self.was_fired = True
            self.state = 'WINNER'
            self.message = "You have been SACKED!"

    def ensure_ai_squads(self):
        for t in self.teams:
            if len(t.squad) < 11:
                needed = 11 - len(t.squad)
                for _ in range(needed):
                    if self.free_agents:
                        p = self.free_agents.pop(0)
                        t.add_player(p)
                    else:
                        p = Player(f"Emerg. {t.name[:3]}", "CM", 65, 5, 20)
                        t.add_player(p)

    def simulate_ai_transfers(self):
        if not self.is_transfer_window_open(): return
        self.free_agents.sort(key=lambda x: x.raw_ovr, reverse=True)

        for t in self.teams:
            if not self.spectator_mode and t == self.my_team: continue

            if len(t.squad) > 20:
                worst_p = min(t.squad, key=lambda x: x.raw_ovr)
                if worst_p.raw_ovr < 75:
                    t.remove_player(worst_p);
                    t.budget += worst_p.value;
                    self.free_agents.append(worst_p)

            needs_gk = len([p for p in t.squad if p.pos == "GK"]) < 2
            needs_def = len([p for p in t.squad if p.pos in ["CB", "LB", "RB"]]) < 5
            needs_mid = len([p for p in t.squad if p.pos in ["CM", "CDM", "CAM"]]) < 5
            needs_fwd = len([p for p in t.squad if p.pos in ["ST", "LW", "RW"]]) < 3

            targets = []
            if needs_gk:
                targets = [p for p in self.free_agents if p.pos == "GK"]
            elif needs_def:
                targets = [p for p in self.free_agents if p.pos in ["CB", "LB", "RB"]]
            elif needs_mid:
                targets = [p for p in self.free_agents if p.pos in ["CM", "CDM", "CAM"]]
            elif needs_fwd:
                targets = [p for p in self.free_agents if p.pos in ["ST", "LW", "RW"]]

            if not targets:
                avg_ovr = t.get_xi_rating()
                targets = [p for p in self.free_agents if p.raw_ovr > avg_ovr + 2]

            if targets:
                for p in targets:
                    if t.budget >= p.value:
                        self.free_agents.remove(p);
                        t.add_player(p);
                        t.budget -= p.value
                        t.transfer_log.append(f"Signed {p.name} (${p.value}M)")
                        break

    def check_job_offers(self):
        self.job_offers = []
        possible_teams = []
        for t in self.teams:
            if t == self.my_team: continue
            team_rating = t.get_xi_rating()
            if self.manager_rep >= 90:
                possible_teams.append(t)
            elif self.manager_rep >= 80 and team_rating < 88:
                possible_teams.append(t)
            elif self.manager_rep >= 70 and team_rating < 84:
                possible_teams.append(t)
            elif self.manager_rep >= 50 and team_rating < 80:
                possible_teams.append(t)
            elif team_rating < 75:
                possible_teams.append(t)

        if possible_teams:
            count = min(3, len(possible_teams))
            self.job_offers = random.sample(possible_teams, count)

    def accept_job_offer(self, new_team):
        self.my_team = new_team
        for p in self.my_team.squad: p.scouted = True
        self.state = 'GAME';
        self.active_tab = 'DASHBOARD'
        self.start_new_season_logic()
        self.message = f"You are now the manager of {new_team.name}!"

    def start_new_season(self):
        if self.champion:
            self.history_winners.append((self.current_year, self.champion.name))
            self.champion.trophies += 1
            if self.my_team:
                rep_change = 0
                if self.champion == self.my_team:
                    self.career_trophies += 1;
                    rep_change += 15
                elif self.my_team.points > 10:
                    rep_change += 5
                elif self.my_team.points < 4:
                    rep_change -= 5
                self.manager_rep = max(0, min(100, self.manager_rep + rep_change))
                self.career_total_wins += self.my_team.won

        self.check_sacking()
        if self.game_over: return

        if not self.spectator_mode:
            self.check_job_offers()
            if self.job_offers:
                self.state = 'JOBS'
                return

        self.start_new_season_logic()

    def start_new_season_logic(self):
        self.current_year += 1
        self.matchday = 0;
        self.phase = "LEAGUE";
        self.round_name = "";
        self.knockout_fixtures = []
        self.knockout_results = {};
        self.knockout_history = []
        self.leg = 1;
        self.leg1_scores = {}

        self.logs = [f"--- SEASON {self.current_year} BEGINS ---"]
        self.champion = None;
        self.state = 'GAME';
        self.active_tab = 'DASHBOARD'

        retirements_log = []
        for t in self.teams:
            t.reset_stats()
            if t.pot == 1:
                t.budget += 150
            elif t.pot == 2:
                t.budget += 80
            else:
                t.budget += 40

            if t.pot == 1 and t.get_xi_rating() < 82:
                for p in t.squad: p.raw_ovr += 2

            for p in t.squad[:]:
                res = p.grow()
                if res == "RETIRED":
                    regen = create_regen(p)
                    self.free_agents.append(regen)
                    t.remove_player(p)
                    retirements_log.append(f"{p.name} ({t.name})")
                elif res and self.my_team and t == self.my_team:
                    self.logs.append(res)

        for p in self.free_agents[:]:
            if p.grow() == "RETIRED":
                self.free_agents.remove(p)
                self.free_agents.append(create_regen(p))

        if retirements_log: self.logs.extend(["RETIRED:"] + retirements_log[:3])
        self.ensure_ai_squads()
        self.schedule = create_schedule(self.teams)
        self.message = f"Welcome to {self.current_year}!"

    def is_transfer_window_open(self):
        return self.matchday == 0 or self.matchday == 4

    def execute_transfer(self, p):
        if self.spectator_mode or not self.is_transfer_window_open(): self.message = "Window Closed!"; return
        if self.my_team.budget >= p.value:
            for t in self.teams:
                if p in t.squad:
                    t.remove_player(p);
                    t.budget += p.value;
                    self.my_team.add_player(p);
                    self.my_team.budget -= p.value
                    t.transfer_log.append(f"Sold {p.name}");
                    self.my_team.transfer_log.append(f"Signed {p.name}")
                    self.message = f"Signed {p.name}!"
                    return
            if p in self.free_agents:
                self.free_agents.remove(p);
                self.my_team.add_player(p);
                self.my_team.budget -= p.value
                self.my_team.transfer_log.append(f"Signed {p.name} (Free Agent)")
                self.message = f"Signed Free Agent {p.name}!"
            elif p in self.scout_results:
                self.scout_results.remove(p);
                self.my_team.add_player(p);
                self.my_team.budget -= p.value
                self.my_team.transfer_log.append(f"Promoted {p.name} (Academy)")
                self.message = f"Signed Academy Player {p.name}!"
        else:
            self.message = "Not enough funds."

    def sell_player(self):
        if self.spectator_mode or self.selected_player_idx is None: return
        p = self.my_team.squad[self.selected_player_idx]
        if not self.is_transfer_window_open(): self.message = "Window Closed."; return
        self.my_team.remove_player(p);
        self.my_team.budget += p.value;
        self.free_agents.append(p)
        self.my_team.transfer_log.append(f"Sold {p.name} (${p.value}M)")
        self.selected_player_idx = None
        self.message = f"Sold {p.name} for ${p.value}M"

    def scout_reveal(self, player):
        if not self.spectator_mode and self.my_team.budget >= SCOUTING_COST:
            self.my_team.budget -= SCOUTING_COST;
            player.scouted = True
            self.message = f"Scouted {player.name}."
        else:
            self.message = f"Need ${SCOUTING_COST}M."

    def scout_search_youth(self):
        if not self.spectator_mode and self.my_team.budget >= YOUTH_SEARCH_COST:
            self.my_team.budget -= YOUTH_SEARCH_COST
            for _ in range(3):
                p = Player(f"Talent {random.randint(100, 999)}", random.choice(["ST", "CM", "CB"]),
                           random.randint(60, 80), random.randint(2, 15))
                p.scouted = True;
                self.scout_results.append(p)
            self.message = "Scouts returned with report."
        else:
            self.message = f"Need ${YOUTH_SEARCH_COST}M."

    def save_game(self):
        my_team_name = self.my_team.name if self.my_team else "SPECTATOR"
        data = {
            "teams": self.teams, "free_agents": self.free_agents, "schedule": self.schedule,
            "matchday": self.matchday, "phase": self.phase, "logs": self.logs,
            "knockout_fixtures": self.knockout_fixtures, "my_team_name": my_team_name,
            "year": self.current_year, "history": self.history_winners, "champion": self.champion,
            "scout_results": self.scout_results, "game_over": self.game_over, "was_fired": self.was_fired,
            "career_wins": self.career_total_wins, "career_trophies": self.career_trophies,
            "ko_results": self.knockout_results, "ko_history": self.knockout_history,
            "rep": self.manager_rep, "leg": self.leg, "leg1": self.leg1_scores
        }
        try:
            with open("savegame.pkl", "wb") as f:
                pickle.dump(data, f)
            self.message = "Game Saved!"
        except Exception as e:
            self.message = f"Error: {e}"

    def load_game(self):
        if not os.path.exists("savegame.pkl"): return
        try:
            with open("savegame.pkl", "rb") as f:
                data = pickle.load(f)
            self.teams = data["teams"];
            self.schedule = data["schedule"]
            self.free_agents = data.get("free_agents", [])
            self.matchday = data["matchday"];
            self.phase = data["phase"]
            self.logs = data["logs"];
            self.knockout_fixtures = data["knockout_fixtures"]
            self.current_year = data.get("year", 2026);
            self.history_winners = data.get("history", [])
            self.champion = data.get("champion", None);
            self.scout_results = data.get("scout_results", [])
            self.game_over = data.get("game_over", False);
            self.was_fired = data.get("was_fired", False)
            self.career_total_wins = data.get("career_wins", 0);
            self.career_trophies = data.get("career_trophies", 0)
            self.knockout_results = data.get("ko_results", {});
            self.knockout_history = data.get("ko_history", [])
            self.manager_rep = data.get("rep", 50)
            self.leg = data.get("leg", 1);
            self.leg1_scores = data.get("leg1", {})

            if data["my_team_name"] == "SPECTATOR":
                self.my_team = None; self.spectator_mode = True
            else:
                for t in self.teams:
                    if t.name == data["my_team_name"]: self.my_team = t; break

            self.state = 'GAME' if not self.champion else 'WINNER'
            self.active_tab = 'DASHBOARD';
            self.message = "Loaded Successfully!"
        except Exception as e:
            self.message = f"Load Error: {e}"

    # --- MATCH LOGIC ---
    def start_live_match(self, t1, t2, is_knockout=False, ko_index=None):
        can_pk = (self.round_name == "FINAL") if is_knockout else False
        self.current_live_match = LiveMatch(t1, t2, is_knockout=is_knockout, allow_pk=can_pk)
        self.current_live_match.ko_index = ko_index
        self.state = 'MATCH_LIVE'
        self.message = "Match Started!"

    def simulate_league_week(self):
        if not self.spectator_mode:
            if len(self.my_team.squad) < 11:
                self.message = "Need 11 players!"
                return
            for p in self.my_team.squad[:11]:
                if p.injury_duration > 0:
                    self.message = f"{p.name} injured!"
                    return
                if p.suspension_duration > 0:
                    self.message = f"{p.name} suspended!"
                    return

        self.ensure_ai_squads()
        if not self.spectator_mode: self.my_team.training_points = 1

        if self.matchday < 8:
            self.simulate_ai_transfers()
            for t in self.teams:
                # FIX: Only optimize AI teams so user lineup is not reset
                if self.spectator_mode or t != self.my_team:
                    t.optimize_lineup()
                    t.randomize_tactic()

            self.matchday += 1
            matches = self.schedule.get(self.matchday, [])
            if not matches: self.message = "Error: No matches found."

            user_match = None
            if not self.spectator_mode:
                for t1, t2 in matches:
                    if t1 == self.my_team:
                        user_match = (t1, t2); break
                    elif t2 == self.my_team:
                        user_match = (t2, t1); break

            if user_match:
                self.start_live_match(user_match[0], user_match[1])
                for t1, t2 in matches:
                    if t1 != self.my_team and t2 != self.my_team: t1.simulate_match(t2)
            else:
                for t1, t2 in matches: t1.simulate_match(t2)
                self.logs.append(f"Matchday {self.matchday} Simulated.")

        if self.matchday == 8: self.init_playoffs()

    def init_playoffs(self):
        self.phase = "KNOCKOUT";
        self.active_tab = 'FIXTURES';
        self.round_name = "Play-off Round"
        self.teams.sort(key=lambda x: (x.points, x.gd, x.gf), reverse=True)
        self.top8 = self.teams[:8];
        playoff_teams = self.teams[8:24]
        self.knockout_fixtures = [(playoff_teams[i], playoff_teams[15 - i]) for i in range(8)]
        self.knockout_results = {};
        self.leg = 1;
        self.leg1_scores = {}

    def simulate_all_knockouts(self):
        for i, (t1, t2) in enumerate(self.knockout_fixtures):
            if i not in self.knockout_results:
                self.simulate_single_knockout(i)
        self.message = "Round Simulated."

    def simulate_single_knockout(self, index):
        t1, t2 = self.knockout_fixtures[index]
        if self.spectator_mode or t1 != self.my_team: t1.optimize_lineup()
        if self.spectator_mode or t2 != self.my_team: t2.optimize_lineup()

        winner, res_str = t1.simulate_knockout(t2)
        try:
            parts = res_str.split(' ')
            score_part = [p for p in parts if '-' in p and p[0].isdigit()][0]
            h_s, a_s = map(int, score_part.split('-'))
        except:
            h_s, a_s = 0, 0

        if self.round_name == "FINAL":
            if winner is None:
                if random.random() > 0.5:
                    winner = t1;
                    res_str = res_str.replace("(Draw)", "") + f"(PK: {t1.name})"
                else:
                    winner = t2;
                    res_str = res_str.replace("(Draw)", "") + f"(PK: {t2.name})"
            self.knockout_results[index] = (winner, res_str, h_s, a_s)
        else:
            self.knockout_results[index] = (None, res_str, h_s, a_s)
        self.message = res_str

    def advance_knockout_round(self):
        if self.round_name == "FINAL":
            final_res = self.knockout_results[0]
            self.champion = final_res[0]
            self.state = 'WINNER'
            self.knockout_history.append((self.round_name, self.champion.name, final_res[1]))
            return

        if self.leg == 1:
            new_fixtures = []
            for i in range(len(self.knockout_fixtures)):
                t1, t2 = self.knockout_fixtures[i]
                res = self.knockout_results.get(i, (None, f"{t1.name} 0-0 {t2.name}", 0, 0))
                self.leg1_scores[i] = (res[2], res[3])
                self.knockout_history.append((f"{self.round_name} (L1)", "---", res[1]))
                new_fixtures.append((t2, t1))

            self.knockout_fixtures = new_fixtures
            self.knockout_results = {};
            self.leg = 2;
            self.message = "Leg 1 Finished."
            return

        winners = []
        for i in range(len(self.knockout_fixtures)):
            t2, t1 = self.knockout_fixtures[i]
            res_l2 = self.knockout_results.get(i, (None, f"{t2.name} 0-0 {t1.name}", 0, 0))
            l2_h, l2_a = res_l2[2], res_l2[3]
            l1_h, l1_a = self.leg1_scores.get(i, (0, 0))

            agg_1 = l1_h + l2_a;
            agg_2 = l1_a + l2_h
            winner_name = ""

            if agg_1 > agg_2:
                winners.append(t1); winner_name = t1.name
            elif agg_2 > agg_1:
                winners.append(t2); winner_name = t2.name
            else:
                if random.random() > 0.5:
                    winners.append(t1); winner_name = t1.name + " (PK)"
                else:
                    winners.append(t2); winner_name = t2.name + " (PK)"

            self.knockout_history.append(
                (f"{self.round_name} (L2)", winner_name, f"{res_l2[1]} (Agg: {agg_1}-{agg_2})"))

        self.leg = 1;
        self.leg1_scores = {}
        if self.round_name == "Play-off Round":
            self.round_name = "Round of 16"
            pool = self.top8 + winners
            pool.sort(key=lambda x: x.get_xi_rating(), reverse=True)
            self.knockout_fixtures = [(pool[i], pool[15 - i]) for i in range(8)]
        elif self.round_name == "Round of 16":
            self.round_name = "Quarter-Finals"
            self.knockout_fixtures = [(winners[i], winners[7 - i]) for i in range(4)]
        elif self.round_name == "Quarter-Finals":
            self.round_name = "Semi-Finals"
            self.knockout_fixtures = [(winners[0], winners[3]), (winners[1], winners[2])]
        elif self.round_name == "Semi-Finals":
            self.round_name = "FINAL"
            self.knockout_fixtures = [(winners[0], winners[1])]

        self.knockout_results = {}

    def run(self):
        while True:
            self.calculate_scale()
            self.virtual_surface.fill(BG_DARK)
            self.handle_events()

            if self.state == 'MATCH_LIVE':
                if self.current_live_match:
                    if not self.current_live_match.finished:
                        if random.random() < 0.15: self.current_live_match.update()
                    else:
                        m = self.current_live_match

                        # --- FIX: HEAL PLAYERS AFTER LIVE MATCH ---
                        # Reduce injury/suspension duration for players involved
                        for p in m.home.squad + m.away.squad:
                            if p.injury_duration > 0: p.injury_duration -= 1
                            if p.suspension_duration > 0: p.suspension_duration -= 1
                        # ------------------------------------------

                        if m.is_knockout:
                            h_s, a_s = m.home_score, m.away_score
                            winner = m.pk_winner if m.pk_winner else None

                            if self.round_name == "FINAL" and winner is None:
                                if h_s > a_s:
                                    winner = m.home
                                elif a_s > h_s:
                                    winner = m.away
                                else:
                                    winner = m.home if random.random() > 0.5 else m.away; m.pk_winner = winner

                            res_str = f"{m.home.name} {h_s}-{a_s} {m.away.name}"
                            if m.pk_winner: res_str += " (PK)"
                            self.knockout_results[m.ko_index] = (winner, res_str, h_s, a_s)
                        else:
                            h = m.home;
                            a = m.away
                            h.played += 1;
                            a.played += 1;
                            h.gf += m.home_score;
                            a.gf += m.away_score
                            h.gd = h.gf - h.ga;
                            a.gd = a.gf - a.ga
                            if m.home_score > m.away_score:
                                h.points += 3;
                                h.won += 1;
                                a.lost += 1;
                                h.update_form('W');
                                a.update_form('L')
                                if h == self.my_team:
                                    self.manager_rep = min(100, self.manager_rep + 1)
                                elif a == self.my_team:
                                    self.manager_rep = max(0, self.manager_rep - 2)
                            elif m.away_score > m.home_score:
                                a.points += 3;
                                a.won += 1;
                                h.lost += 1;
                                a.update_form('W');
                                h.update_form('L')
                                if a == self.my_team:
                                    self.manager_rep = min(100, self.manager_rep + 1)
                                elif h == self.my_team:
                                    self.manager_rep = max(0, self.manager_rep - 2)
                            else:
                                h.points += 1;
                                a.points += 1;
                                h.drawn += 1;
                                a.drawn += 1;
                                h.update_form('D');
                                a.update_form('D')

                            for p in h.squad: p.update_morale(p in m.home_xi, won=(m.home_score > m.away_score))
                            for p in a.squad: p.update_morale(p in m.away_xi, won=(m.away_score > m.home_score))
                            self.logs.insert(0, f"Result: {h.name} {m.home_score}-{m.away_score} {a.name}")

                        self.check_sacking()
                        if not self.game_over:
                            self.current_live_match = None;
                            self.state = 'GAME'
                        else:
                            self.current_live_match = None

                if self.state == 'MATCH_LIVE': views.draw_live_match(self.virtual_surface, self)

            elif self.state == 'SELECT':
                views.draw_select(self.virtual_surface, self)
            elif self.state == 'WINNER':
                views.draw_winner(self.virtual_surface, self)
            elif self.state == 'JOBS':
                views.draw_jobs(self.virtual_surface, self)
            elif self.state == 'WORLD_STATS':
                views.draw_world_stats(self.virtual_surface, self)
            else:
                views.draw_header(self.virtual_surface, self)
                # CORRECT DRAW ORDER: BG FIRST, THEN TABS
                views.draw_content_bg(self.virtual_surface)
                views.draw_tab_bar(self.virtual_surface, self)

                # DRAW ACTIVE CONTENT
                if self.active_tab == 'DASHBOARD':
                    views.draw_dashboard(self.virtual_surface, self)
                elif self.active_tab == 'SQUAD':
                    views.draw_squad(self.virtual_surface, self)
                elif self.active_tab == 'MARKET':
                    views.draw_market(self.virtual_surface, self)
                elif self.active_tab == 'TRAINING':
                    views.draw_training(self.virtual_surface, self)
                elif self.active_tab == 'SCOUTING':
                    views.draw_scouting(self.virtual_surface, self)
                elif self.active_tab == 'TEAMS':
                    views.draw_teams_view(self.virtual_surface, self)
                elif self.active_tab == 'STANDINGS':
                    views.draw_standings(self.virtual_surface, self)
                elif self.active_tab == 'STATS':
                    views.draw_season_stats(self.virtual_surface, self)
                elif self.active_tab == 'FIXTURES':
                    views.draw_knockout(self.virtual_surface, self)
                elif self.active_tab == 'HISTORY':
                    views.draw_history(self.virtual_surface, self)
                views.draw_footer(self.virtual_surface, self.message)

            scaled = pygame.transform.smoothscale(self.virtual_surface, (
            int(self.base_width * self.scale_factor), int(self.base_height * self.scale_factor)))
            self.screen.fill((0, 0, 0));
            self.screen.blit(scaled, (self.offset_x, self.offset_y))
            pygame.display.flip();
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11: self.toggle_fullscreen()
                if self.is_typing_search and self.active_tab == 'MARKET':
                    if event.key == pygame.K_BACKSPACE:
                        self.market_search_query = self.market_search_query[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.is_typing_search = False
                    else:
                        if len(self.market_search_query) < 20: self.market_search_query += event.unicode
                    self.refresh_market_cache()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: self.scroll_y = min(self.scroll_y + 40, 0)
                if event.button == 5: self.scroll_y = max(self.scroll_y - 40, -2000)
                if event.button == 1:
                    gx, gy = self.get_game_mouse_pos()
                    self.check_clicks((gx, gy))

    def check_clicks(self, pos):
        if self.state == 'MATCH_LIVE':
            for btn in self.match_control_buttons:
                if btn.is_clicked(pos):
                    if btn.text == "SKIP" and self.current_live_match:
                        while not self.current_live_match.finished: self.current_live_match.update()
                    elif btn.text == "TACTIC":
                        modes = ["Balanced", "Attack", "Park Bus", "Counter"]
                        self.my_team.current_tactic = modes[(modes.index(self.my_team.current_tactic) + 1) % 3]
            return

        if self.state == 'JOBS':
            for btn in self.job_buttons:
                if btn.is_clicked(pos):
                    data = btn.data
                    if data == "STAY":
                        self.start_new_season_logic()
                    else:
                        self.accept_job_offer(data)
            return

        if self.state == 'GAME':
            # 1. SCROLL BUTTONS
            if self.btn_tab_left.is_clicked(pos): self.tab_scroll = max(0, self.tab_scroll - 200); return
            if self.btn_tab_right.is_clicked(pos): self.tab_scroll = min(200, self.tab_scroll + 200); return

            # 2. CHECK TABS WITH OFFSET
            for k, tab in self.tabs.items():
                # Fix: using 'k' instead of 'key'
                check_rect = pygame.Rect(tab.rect.x - self.tab_scroll, tab.rect.y, tab.rect.width, tab.rect.height)
                if check_rect.collidepoint(pos):
                    self.active_tab = k;
                    self.scroll_y = 0;
                    self.selected_player_idx = None
                    if k != 'TEAMS': self.selected_view_team = None
                    if k == 'MARKET': self.refresh_market_cache()
                    return

            # 3. CONTENT CLICKS
            if self.active_tab == 'TRAINING':
                for btn in self.training_buttons:
                    if btn.is_clicked(pos): self.message = self.my_team.train_players(btn.data)
                return

            if self.active_tab == 'MARKET':
                if pygame.Rect(60, 220 + self.scroll_y, 300, 40).collidepoint(pos):
                    self.is_typing_search = True
                else:
                    self.is_typing_search = False

            if self.active_tab == 'DASHBOARD':
                if self.btn_sim and self.btn_sim.is_clicked(pos): self.simulate_league_week()
                if self.btn_save and self.btn_save.is_clicked(pos): self.save_game()
                if self.btn_restart and self.btn_restart.is_clicked(pos): self.restart_game()

            elif self.active_tab == 'SQUAD':
                if not self.spectator_mode:
                    if self.btn_tac and self.btn_tac.is_clicked(pos):
                        modes = ["Balanced", "Attack", "Park Bus", "Counter"]
                        self.my_team.current_tactic = modes[(modes.index(self.my_team.current_tactic) + 1) % 4]
                    if self.btn_form and self.btn_form.is_clicked(pos):
                        forms = ["4-3-3", "4-4-2", "3-5-2"]
                        self.my_team.current_formation = forms[(forms.index(self.my_team.current_formation) + 1) % 3]
                        self.my_team._cached_rating = None
                    # FIX: CHECK IF btn_sell EXISTS
                    if self.btn_sell and self.btn_sell.is_clicked(pos): self.sell_player()
                    for btn in self.squad_buttons:
                        if btn.is_clicked(pos):
                            if self.selected_player_idx is None:
                                self.selected_player_idx = btn.data
                            else:
                                self.my_team.squad[self.selected_player_idx], self.my_team.squad[btn.data] = \
                                self.my_team.squad[btn.data], self.my_team.squad[self.selected_player_idx]
                                self.selected_player_idx = None

            elif self.active_tab == 'MARKET':
                for btn in self.market_filter_buttons:
                    if btn.is_clicked(pos): self.market_filter_pos = btn.data; self.refresh_market_cache(); return
                for btn in self.market_buttons:
                    if btn.is_clicked(pos):
                        data = btn.data
                        if isinstance(data, dict) and data.get("type") == "reveal":
                            self.scout_reveal(data["player"])
                        else:
                            self.execute_transfer(data)
                        self.refresh_market_cache()

            elif self.active_tab == 'SCOUTING':
                if self.spectator_mode: return
                if self.btn_scout_search and self.btn_scout_search.is_clicked(pos): self.scout_search_youth()
                for btn in self.scouting_buttons:
                    if btn.is_clicked(pos): self.execute_transfer(btn.data)

            elif self.active_tab == 'TEAMS':
                for btn in self.team_view_buttons:
                    if btn.is_clicked(pos): self.selected_view_team = btn.data; self.scroll_y = 0

            elif self.active_tab == 'FIXTURES':
                for btn in self.knockout_buttons:
                    if btn.is_clicked(pos):
                        data = btn.data
                        if data == "NEXT":
                            self.advance_knockout_round()
                        elif data == "SIM_ALL":
                            self.simulate_all_knockouts()
                        elif data == "PREV_PAGE":
                            self.history_page = max(0, self.history_page - 1)
                        elif data == "NEXT_PAGE":
                            self.history_page += 1
                        elif isinstance(data, dict):
                            idx = data["index"]
                            t1, t2 = self.knockout_fixtures[idx]
                            if data["type"] == "LIVE":
                                self.start_live_match(t1, t2, is_knockout=True, ko_index=idx)
                            elif data["type"] == "SIM":
                                self.simulate_single_knockout(idx)

        if self.state == 'SELECT':
            if self.btn_load and self.btn_load.is_clicked(pos): self.load_game(); return
            if self.btn_spectate and self.btn_spectate.is_clicked(pos): self.start_spectator_mode(); return
            x, y = 80, 150 + self.scroll_y
            for i, team in enumerate(self.teams):
                r = pygame.Rect(x + (i % 4) * 280, y + (i // 4) * 70, 260, 60)
                if r.collidepoint(pos): self.set_my_team(team)

        elif self.state == 'WINNER':
            # FIX: Added Check if Buttons Exist before clicking
            if self.btn_world_stats and self.btn_world_stats.is_clicked(
                pos): self.state = 'WORLD_STATS'; self.scroll_y = 0; return
            if self.btn_retire and self.btn_retire.is_clicked(pos): self.retire_career(); return
            if self.game_over:
                if self.btn_restart and self.btn_restart.is_clicked(pos): self.restart_game()
            else:
                if self.btn_next_season and self.btn_next_season.is_clicked(pos): self.start_new_season()
                if self.btn_restart and self.btn_restart.is_clicked(pos): self.restart_game()

        elif self.state == 'WORLD_STATS':
            if self.btn_back and self.btn_back.is_clicked(pos): self.state = 'WINNER'; self.scroll_y = 0; return

    def refresh_market_cache(self):
        all_p = []
        for p in self.free_agents: all_p.append((p, type('obj', (object,), {'name': 'Free Agent'})))
        for t in self.teams:
            if not self.spectator_mode and t == self.my_team: continue
            for p in t.squad: all_p.append((p, t))
        all_p.sort(key=lambda x: x[0].raw_ovr, reverse=True)

        filtered = []
        search_lower = self.market_search_query.lower()
        for p, t in all_p:
            if self.market_filter_pos != "ALL":
                if self.market_filter_pos == "FWD" and p.pos not in ["ST", "LW", "RW", "CF"]: continue
                if self.market_filter_pos == "MID" and p.pos not in ["CM", "CDM", "CAM", "LM", "RM"]: continue
                if self.market_filter_pos == "DEF" and p.pos not in ["CB", "LB", "RB", "LWB", "RWB"]: continue
                if self.market_filter_pos == "GK" and p.pos != "GK": continue
            if search_lower:
                if search_lower not in p.name.lower(): continue
                filtered.append((p, t))
            else:
                filtered.append((p, t))

        self.market_cache = filtered[:60] if not search_lower else filtered


if __name__ == "__main__":
    UCLManager().run()
