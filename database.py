import json
import os
import random
from models import Team, Player


def fill_bench_with_youth(team):
    needed = 15 - len(team.squad)
    if needed <= 0: return
    positions = ["CB", "CM", "ST", "GK", "RW"]
    for i in range(needed):
        pos = positions[i % len(positions)]
        age = random.randint(16, 19)
        team.add_player(Player(f"{team.name[:3]} Youth {i + 1}", pos, 70, 10, age))


def generate_free_agents(count=30):
    """Generates a list of players without a team for the market."""
    free_agents = []
    positions = ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LW", "RW", "ST"]
    names = ["Silva", "Santos", "Kim", "Muller", "Schmidt", "Dubois", "Ferrari", "Rossi", "Popov", "Ivanov", "Smith",
             "Jones", "Tanaka", "Sato", "Garcia", "Lopez"]

    for _ in range(count):
        name = f"{random.choice(names)} {random.randint(1, 99)}"
        pos = random.choice(positions)
        # Random age is still needed here for generated players
        age = random.randint(18, 35)
        ovr = int(random.triangular(70, 88, 76))
        val = int((ovr - 60) * 1.5)
        if val < 1: val = 1

        p = Player(name, pos, ovr, val, age)
        p.scouted = False
        free_agents.append(p)

    return free_agents


def generate_teams():
    if not os.path.exists("teams.json"):
        print("Error: teams.json not found!")
        return []
    with open("teams.json", "r") as f:
        data = json.load(f)

    teams = []
    for t_data in data:
        new_team = Team(t_data["name"], t_data["budget"], t_data["pot"])
        for p_data in t_data["squad"]:
            # CHANGED: Use age from JSON (default to 25 if missing)
            age = p_data.get("age", 25)
            p = Player(p_data["name"], p_data["pos"], p_data["ovr"], p_data["value"], age)
            p.scouted = False
            new_team.add_player(p)

        fill_bench_with_youth(new_team)
        teams.append(new_team)
    return teams


def create_schedule(teams):
    schedule = {}
    history = {t.name: set() for t in teams}
    for week in range(1, 9):
        week_matches = []
        teams_to_pair = teams[:]
        random.shuffle(teams_to_pair)
        success = False
        attempts = 0
        while not success and attempts < 20:
            temp_matches = []
            pool = teams_to_pair[:]
            random.shuffle(pool)
            valid_week = True
            while pool:
                if len(pool) == 1: valid_week = False; break
                t1 = pool.pop()
                found = False
                for i, t2 in enumerate(pool):
                    if t2.name not in history[t1.name]:
                        pool.pop(i);
                        temp_matches.append((t1, t2));
                        found = True;
                        break
                if not found: valid_week = False; break
            if valid_week:
                week_matches = temp_matches
                for t1, t2 in week_matches:
                    history[t1.name].add(t2.name);
                    history[t2.name].add(t1.name)
                success = True
            else:
                attempts += 1
        if not success: return create_schedule(teams)
        schedule[week] = week_matches
    return schedule