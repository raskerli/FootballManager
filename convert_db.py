# convert_db.py
import json
from database import generate_teams


def export_to_json():
    print("Generating teams from python code...")
    teams = generate_teams()

    data = []
    for team in teams:
        team_dict = {
            "name": team.name,
            "budget": team.budget,
            "pot": team.pot,
            "squad": []
        }

        for p in team.squad:
            # Don't save auto-generated youth players if you don't want to
            # But for this export, let's save everyone
            p_data = {
                "name": p.name,
                "pos": p.pos,
                "ovr": p.raw_ovr,
                "value": p.value
            }
            team_dict["squad"].append(p_data)

        data.append(team_dict)

    with open("teams.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Successfully exported {len(teams)} teams to 'teams.json'!")


if __name__ == "__main__":
    export_to_json()