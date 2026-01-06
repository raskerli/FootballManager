import random
from config import NATIONALITIES

# --- TACTICAL LOGIC ---
# (My Tactic, Opponent Tactic) -> Bonus for ME
TACTICAL_MATCHUPS = {
    ("Attack", "Park Bus"): 15,  # Overwhelm the turtle
    ("Attack", "Counter"): -15,  # Get caught on break
    ("Park Bus", "Counter"): 15,  # Deny space
    ("Park Bus", "Attack"): -15,  # Get battered
    ("Counter", "Attack"): 15,  # Exploit high line
    ("Counter", "Park Bus"): -15,  # Nowhere to run
    # Balanced is neutral
}

# --- FORMATION DATABASE ---
FORMATIONS_DB = {
    "4-3-3": {
        0: ["GK"],
        1: ["LB", "LWB", "DF", "CB"], 2: ["CB", "DF", "CDM"], 3: ["CB", "DF", "CDM"], 4: ["RB", "RWB", "DF", "CB"],
        5: ["CDM", "CM", "MF"], 6: ["CM", "CAM", "MF"], 7: ["CM", "CAM", "MF"],
        8: ["LW", "LM", "LF", "FW", "ST"], 9: ["ST", "CF", "FW"], 10: ["RW", "RM", "RF", "FW", "ST"]
    },
    "4-4-2": {
        0: ["GK"],
        1: ["LB", "LWB", "DF"], 2: ["CB", "DF"], 3: ["CB", "DF"], 4: ["RB", "RWB", "DF"],
        5: ["LM", "LW", "MF"], 6: ["CM", "CDM", "CAM"], 7: ["CM", "CDM", "CAM"], 8: ["RM", "RW", "MF"],
        9: ["ST", "CF", "FW"], 10: ["ST", "CF", "FW"]
    },
    "3-5-2": {
        0: ["GK"],
        1: ["CB", "DF", "CDM"], 2: ["CB", "DF"], 3: ["CB", "DF", "CDM"],
        4: ["LM", "LWB", "LW"], 5: ["CDM", "CM"], 6: ["CM", "CAM"], 7: ["CDM", "CM"], 8: ["RM", "RWB", "RW"],
        9: ["ST", "CF", "FW"], 10: ["ST", "CF", "FW"]
    }
}


class Player:
    def __init__(self, name, position, ovr, value, age=None):
        self.name = name
        self.pos = position
        self.raw_ovr = ovr
        self.value = value
        self.effective_ovr = ovr
        self.age = age if age else random.randint(18, 34)
        self.potential = self.raw_ovr + random.randint(0, 10) if self.age < 24 else self.raw_ovr

        # Status
        self.injury_duration = 0
        self.suspension_duration = 0
        self.scouted = False

        # Human Elements
        self.nationality = random.choice(NATIONALITIES)
        self.morale = 80
        self.leadership = random.randint(10, 99)
        self.unhappy_months = 0

        # Stats
        self.goals = 0;
        self.assists = 0;
        self.tackles = 0;
        self.saves = 0;
        self.matches_played = 0
        self.career_goals = 0;
        self.career_assists = 0;
        self.career_played = 0;
        self.career_saves = 0

    def get_display_ovr(self):
        if self.scouted: return str(self.raw_ovr)
        variance = random.randint(2, 5)
        return f"{max(40, self.raw_ovr - variance)}-{min(99, self.raw_ovr + variance)}"

    def is_available(self):
        return self.injury_duration == 0 and self.suspension_duration == 0

    def grow(self):
        self.career_goals += self.goals;
        self.career_assists += self.assists
        self.career_played += self.matches_played;
        self.career_saves += self.saves
        self.goals = 0;
        self.assists = 0;
        self.tackles = 0;
        self.saves = 0;
        self.matches_played = 0

        self.age += 1
        self.morale = min(100, self.morale + 10)

        if self.injury_duration > 0: self.injury_duration = 0
        if self.suspension_duration > 0: self.suspension_duration = 0

        if self.age >= 34:
            chance = (self.age - 32) * 0.10
            if self.raw_ovr > 85: chance -= 0.2
            if random.random() < chance: return "RETIRED"

        if self.age < 24 and self.raw_ovr < self.potential:
            growth = random.randint(1, 4)
            self.raw_ovr += growth
            self.value += growth * 2
            return f"Improved to {self.raw_ovr} (+{growth})"
        elif 24 <= self.age <= 30:
            if random.random() > 0.7 and self.raw_ovr < self.potential:
                self.raw_ovr += 1
                return f"Improved to {self.raw_ovr} (+1)"
        elif self.age > 31:
            decline = random.randint(1, 3)
            self.raw_ovr -= decline
            self.value = int(self.value * 0.7)
            return f"Declined to {self.raw_ovr} (-{decline})"
        return None

    def update_morale(self, played_match, won=False):
        if played_match:
            self.morale = min(100, self.morale + (3 if won else 1))
            self.unhappy_months = 0
        else:
            self.morale = max(0, self.morale - 5)
            if self.morale < 30: self.unhappy_months += 1

    def __repr__(self):
        return f"{self.name} ({self.raw_ovr})"


def create_regen(retired_player):
    name = f"{retired_player.name} Jr" if "Jr" not in retired_player.name else retired_player.name
    pos = retired_player.pos
    ovr = random.randint(70, 78)
    val = random.randint(15, 40)
    age = random.randint(16, 19)
    regen = Player(name, pos, ovr, val, age)
    regen.nationality = retired_player.nationality
    regen.potential = max(88, retired_player.raw_ovr + random.randint(0, 5))
    regen.scouted = False
    return regen


class Team:
    def __init__(self, name, budget, pot):
        self.name = name;
        self.budget = budget;
        self.pot = pot;
        self.squad = []
        self.current_tactic = "Balanced";
        self.current_formation = "4-3-3"
        self._cached_rating = None;
        self._last_squad_signature = None
        self.reset_stats();
        self.recent_form = [];
        self.transfer_log = [];
        self.trophies = 0;
        self.captain_index = 0

        # Training System
        self.training_points = 1

    def reset_stats(self):
        self.played = 0;
        self.points = 0;
        self.won = 0;
        self.drawn = 0;
        self.lost = 0
        self.gf = 0;
        self.ga = 0;
        self.gd = 0

    def add_player(self, player):
        player.scouted = True; self.squad.append(player); self._cached_rating = None

    def remove_player(self, player):
        if player in self.squad: self.squad.remove(player); self._cached_rating = None

    def randomize_tactic(self):
        """AI picks a tactic randomly each week."""
        self.current_tactic = random.choice(["Balanced", "Attack", "Park Bus", "Counter"])

    def train_players(self, type):
        """Uses training points to boost stats or heal."""
        if self.training_points <= 0: return "No Training Points left!"

        count = 0
        if type == "ATTACK":
            targets = [p for p in self.squad if p.pos in ["ST", "LW", "RW", "CAM", "CF"]]
            for p in targets:
                if random.random() < 0.4: p.raw_ovr += 1; count += 1
        elif type == "DEFENSE":
            targets = [p for p in self.squad if p.pos in ["CB", "LB", "RB", "CDM", "GK"]]
            for p in targets:
                if random.random() < 0.4: p.raw_ovr += 1; count += 1
        elif type == "PHYSIO":
            for p in self.squad:
                if p.injury_duration > 0: p.injury_duration = 0; count += 1
                p.morale = min(100, p.morale + 10)

        self.training_points -= 1
        self._cached_rating = None
        if count == 0 and type != "PHYSIO": return "Training complete. No immediate gains."
        return f"Training complete! {count} players improved/healed."

    def optimize_lineup(self):
        available = [p for p in self.squad if p.is_available()]
        available.sort(key=lambda x: x.raw_ovr, reverse=True)
        gks = [p for p in available if p.pos == "GK"]
        defs = [p for p in available if p.pos in ["CB", "LB", "RB", "LWB", "RWB"]]
        mids = [p for p in available if p.pos in ["CM", "CDM", "CAM", "LM", "RM"]]
        fwds = [p for p in available if p.pos in ["ST", "CF", "LW", "RW"]]

        xi = []
        if gks: xi.append(gks.pop(0))
        for _ in range(4):
            if defs: xi.append(defs.pop(0))
        for _ in range(3):
            if mids: xi.append(mids.pop(0))
        for _ in range(3):
            if fwds: xi.append(fwds.pop(0))

        rem = gks + defs + mids + fwds
        rem.sort(key=lambda x: x.raw_ovr, reverse=True)
        while len(xi) < 11 and rem: xi.append(rem.pop(0))

        unavailable = [p for p in self.squad if not p.is_available()]
        self.squad = xi + rem + unavailable
        self._cached_rating = None

    def get_xi_rating(self):
        current_starters = self.squad[:11]
        signature = (self.current_formation, tuple(p.name for p in current_starters), self.captain_index)
        if self._cached_rating is not None and self._last_squad_signature == signature: return self._cached_rating
        if not self.squad: return 70

        total = 0;
        valid = FORMATIONS_DB.get(self.current_formation, FORMATIONS_DB["4-3-3"])
        capt = self.squad[self.captain_index] if len(self.squad) > self.captain_index else self.squad[0]
        ldr = 0.05 if capt.leadership > 85 else 0.0

        for i, p in enumerate(current_starters):
            if not p.is_available():
                p.effective_ovr = 10
            else:
                pen = 0.0
                if p.pos not in valid.get(i, []):
                    if p.pos == "GK" or i == 0:
                        pen = 0.95
                    else:
                        pen = 0.15
                base = p.raw_ovr * (1.0 - pen) * (0.9 + p.morale / 500)
                chem = 2 if i > 0 and current_starters[i - 1].nationality == p.nationality else 0
                p.effective_ovr = int(base + chem + (base * ldr))
            total += p.effective_ovr
        self._cached_rating = total // len(current_starters);
        self._last_squad_signature = signature
        return self._cached_rating

    def get_form_bonus(self):
        s = 0
        for r in self.recent_form[-5:]: s += (2 if r == 'W' else (-2 if r == 'L' else 0))
        return s

    def update_form(self, result):
        self.recent_form.append(result)
        if len(self.recent_form) > 5: self.recent_form.pop(0)

    def simulate_match(self, opponent):
        # AI Tactics for Sim
        if opponent.current_tactic == "Balanced": opponent.randomize_tactic()

        # Calculate Tactical Bonus
        my_bonus = TACTICAL_MATCHUPS.get((self.current_tactic, opponent.current_tactic), 0)
        opp_bonus = TACTICAL_MATCHUPS.get((opponent.current_tactic, self.current_tactic), 0)

        logs = [];
        mins = 90;
        s_sc = 0;
        o_sc = 0
        m_xi = self.squad[:11];
        o_xi = opponent.squad[:11]
        for p in m_xi: p.matches_played += 1
        for p in o_xi: p.matches_played += 1

        all_players = m_xi + o_xi
        for p in all_players:
            if random.random() < 0.002:
                p.injury_duration = random.randint(2, 8);
                logs.append(f"[INJURY] {p.name}")
            if random.random() < 0.001:
                p.suspension_duration = 1;
                logs.append(f"[RED CARD] {p.name}")

        my_rate = self.get_xi_rating() + self.get_form_bonus() + my_bonus
        op_rate = opponent.get_xi_rating() + opponent.get_form_bonus() + opp_bonus

        base_chance = 0.06
        my_att_chance = base_chance * (1 + ((my_rate - op_rate) / 200))
        op_att_chance = base_chance * (1 - ((my_rate - op_rate) / 200))

        for minute in range(1, mins + 1, 2):
            roll = random.random()
            if roll < my_att_chance:
                att = random.choice(m_xi);
                def_ = random.choice(o_xi);
                gk = o_xi[0]
                if def_.effective_ovr + random.randint(0, 25) > att.effective_ovr + random.randint(0, 20):
                    pass
                elif gk.effective_ovr + random.randint(0, 30) > att.effective_ovr + random.randint(0, 25):
                    gk.saves += 1
                else:
                    s_sc += 1; att.goals += 1; logs.append(f"{minute}' [GOAL] {att.name}")
            elif roll < my_att_chance + op_att_chance:
                att = random.choice(o_xi);
                def_ = random.choice(m_xi);
                gk = m_xi[0]
                if def_.effective_ovr + random.randint(0, 25) > att.effective_ovr + random.randint(0, 20):
                    pass
                elif gk.effective_ovr + random.randint(0, 30) > att.effective_ovr + random.randint(0, 25):
                    gk.saves += 1
                else:
                    o_sc += 1; att.goals += 1; logs.append(f"{minute}' [GOAL] {att.name}")

        self.played += 1;
        opponent.played += 1
        self.gf += s_sc;
        self.ga += o_sc;
        self.gd = self.gf - self.ga
        opponent.gf += o_sc;
        opponent.ga += s_sc;
        opponent.gd = opponent.gf - opponent.ga

        if s_sc > o_sc:
            self.points += 3; self.won += 1; opponent.lost += 1; self.update_form('W'); opponent.update_form('L')
        elif o_sc > s_sc:
            opponent.points += 3; opponent.won += 1; self.lost += 1; self.update_form('L'); opponent.update_form('W')
        else:
            self.points += 1; opponent.points += 1; self.drawn += 1; opponent.drawn += 1; self.update_form(
                'D'); opponent.update_form('D')

        for p in self.squad + opponent.squad:
            if p.injury_duration > 0: p.injury_duration -= 1
            if p.suspension_duration > 0: p.suspension_duration -= 1

        return f"{self.name} {s_sc}-{o_sc} {opponent.name}", logs

    def simulate_knockout(self, opponent):
        if opponent.current_tactic == "Balanced": opponent.randomize_tactic()

        my_bonus = TACTICAL_MATCHUPS.get((self.current_tactic, opponent.current_tactic), 0)
        opp_bonus = TACTICAL_MATCHUPS.get((opponent.current_tactic, self.current_tactic), 0)

        my_rate = self.get_xi_rating() + my_bonus
        op_rate = opponent.get_xi_rating() + opp_bonus

        diff = (my_rate - op_rate) + random.randint(-3, 3)
        g_a = max(0, int(random.gauss(1.4, 1.0) + diff / 15))
        g_b = max(0, int(random.gauss(1.4, 1.0) - diff / 15))
        res = f"{self.name} {g_a}-{g_b} {opponent.name}"
        if g_a > g_b: return self, res
        if g_b > g_a: return opponent, res
        return None, res + " (Draw)"


class LiveMatch:
    def __init__(self, home_team, away_team, is_knockout=False, allow_pk=False):
        self.home = home_team;
        self.away = away_team
        self.is_knockout = is_knockout;
        self.allow_pk = allow_pk
        self.minute = 0;
        self.home_score = 0;
        self.away_score = 0;
        self.logs = []
        self.momentum = 50;
        self.finished = False;
        self.pk_winner = None;
        self.ko_index = None
        self.home_xi = self.home.squad[:11];
        self.away_xi = self.away.squad[:11]

        # Apply Tactical Bonuses
        h_bonus = TACTICAL_MATCHUPS.get((self.home.current_tactic, self.away.current_tactic), 0)
        a_bonus = TACTICAL_MATCHUPS.get((self.away.current_tactic, self.home.current_tactic), 0)

        self.h_rating = self.home.get_xi_rating() + h_bonus
        self.a_rating = self.away.get_xi_rating() + a_bonus

        if h_bonus > 5:
            self.momentum = 60
        elif a_bonus > 5:
            self.momentum = 40

    def update(self):
        if self.finished: return
        if self.minute >= 90:
            if self.allow_pk and self.home_score == self.away_score:
                self.logs.append((90, "Time up! Penalties...", "MID"))
                if random.random() > 0.5:
                    self.pk_winner = self.home; self.logs.append((90, f"{self.home.name} wins PK!", "GOAL"))
                else:
                    self.pk_winner = self.away; self.logs.append((90, f"{self.away.name} wins PK!", "GOAL"))
            self.finished = True;
            return

        self.minute += 1

        if random.random() < 0.002:
            victim = random.choice(self.home_xi + self.away_xi)
            victim.injury_duration = random.randint(2, 6)
            self.logs.append((self.minute, f"INJURY! {victim.name} is down.", "DEF"))

        if random.random() < 0.001:
            offender = random.choice(self.home_xi + self.away_xi)
            offender.suspension_duration = 1
            team_name = self.home.name if offender in self.home_xi else self.away.name
            self.logs.append((self.minute, f"RED CARD! {offender.name} sent off!", "DEF"))
            if team_name == self.home.name:
                self.h_rating -= 15
            else:
                self.a_rating -= 15

        diff = self.h_rating - self.a_rating
        swing = random.randint(-8, 8) + (diff / 15)
        self.momentum = max(10, min(90, self.momentum + swing))

        if self.momentum > 65:
            self.attempt_attack(self.home, self.away, True)
        elif self.momentum < 35:
            self.attempt_attack(self.away, self.home, False)

    def attempt_attack(self, att_team, def_team, is_home):
        if random.random() > 0.35: return
        att = random.choice(att_team.squad[:11]);
        defe = random.choice(def_team.squad[:11]);
        gk = def_team.squad[0]
        if defe.effective_ovr + random.randint(0, 25) > att.effective_ovr + random.randint(0, 20):
            defe.tackles += 1;
            self.logs.append((self.minute, f"{defe.name} tackles {att.name}", "DEF"));
            self.momentum += (-15 if is_home else 15)
        elif gk.effective_ovr + random.randint(0, 30) > att.effective_ovr + random.randint(0, 25):
            gk.saves += 1;
            self.logs.append((self.minute, f"Save by {gk.name}", "SAVE"))
        else:
            if is_home:
                self.home_score += 1
            else:
                self.away_score += 1
            att.goals += 1;
            self.logs.append((self.minute, f"GOAL! {att.name}", "GOAL"));
            self.momentum = 50