import pygame
import os
from config import *
from ui import get_font, Button, draw_card, FORMATION_COORDS


# --- SHARED HELPERS ---
def draw_content_bg(screen):
    pygame.draw.rect(screen, BG_DARK, (0, 80, SCREEN_WIDTH, SCREEN_HEIGHT - 110))


def draw_header(screen, game):
    pygame.draw.rect(screen, BG_HEADER, (0, 0, SCREEN_WIDTH, 80))
    pygame.draw.line(screen, (30, 40, 60), (0, 80), (SCREEN_WIDTH, 80), 2)

    if game.spectator_mode:
        screen.blit(get_font(36, True).render("SPECTATOR MODE", True, TEXT_WHITE), (30, 15))
        screen.blit(get_font(16).render(f"Observing League | {game.current_year}", True, ACCENT_GOLD), (32, 55))
    else:
        screen.blit(get_font(36, True).render(game.my_team.name, True, TEXT_WHITE), (30, 15))
        # Updated header to show Reputation
        info_txt = f"OVR: {game.my_team.get_xi_rating()}  |  ${game.my_team.budget}M  |  Rep: {game.manager_rep}"
        screen.blit(get_font(16).render(info_txt, True, ACCENT_CYAN), (32, 55))

    col = ACCENT_GREEN if game.phase == "LEAGUE" else ACCENT_RED
    pygame.draw.rect(screen, col, (SCREEN_WIDTH - 180, 25, 150, 30), border_radius=15)
    screen.blit(get_font(14, True).render(game.phase, True, BG_DARK), (SCREEN_WIDTH - 160, 32))


def draw_footer(screen, message):
    pygame.draw.rect(screen, BG_HEADER, (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
    screen.blit(get_font(14).render(f"STATUS: {message}", True, TEXT_GRAY), (15, SCREEN_HEIGHT - 24))


# --- TAB BAR (NEW) ---
def draw_tab_bar(screen, game):
    m_pos = game.get_game_mouse_pos()

    # Draw Tab Bar Background
    pygame.draw.rect(screen, BG_HEADER, (0, 100, 1280, 50))

    # Draw Scroll Buttons
    game.btn_tab_left.draw(screen, m_pos)
    game.btn_tab_right.draw(screen, m_pos)

    # Draw Tabs with Offset
    # We define a "clip" area so tabs don't draw over the buttons
    clip_rect = pygame.Rect(40, 100, 1200, 50)
    screen.set_clip(clip_rect)

    for k, tab in game.tabs.items():
        tab.selected = (game.active_tab == k)
        # Create a temporary shifted rect for drawing
        drawn_rect = pygame.Rect(tab.rect.x - game.tab_scroll, tab.rect.y, tab.rect.width, tab.rect.height)

        # Manually draw the tab using the shifted rect
        col = ACCENT_GOLD if tab.selected else BG_PANEL
        pygame.draw.rect(screen, col, drawn_rect, border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), drawn_rect, 2, border_top_left_radius=10, border_top_right_radius=10)

        txt_col = BG_DARK if tab.selected else TEXT_GRAY
        txt = get_font(18, True).render(tab.text, True, txt_col)
        screen.blit(txt, txt.get_rect(center=drawn_rect.center))

    screen.set_clip(None)  # Reset clipping


# --- SCREEN FUNCTIONS ---

def draw_dashboard(screen, game):
    m_pos = game.get_game_mouse_pos()
    draw_card(screen, pygame.Rect(40, 170, 400, 220))
    screen.blit(get_font(14, True).render("NEXT FIXTURE", True, ACCENT_GOLD), (60, 190))

    if game.matchday < 8:
        if game.spectator_mode:
            screen.blit(get_font(24, True).render("LEAGUE ROUND", True, TEXT_WHITE), (60, 220))
            screen.blit(get_font(24, True).render(f"Matchday {game.matchday + 1}", True, TEXT_WHITE), (60, 260))
            btn_txt = "SIMULATE WEEK"
        else:
            next_opp = "TBD"
            opp_obj = None
            if (game.matchday + 1) in game.schedule:
                for t1, t2 in game.schedule[game.matchday + 1]:
                    if t1 == game.my_team:
                        next_opp = t2.name; opp_obj = t2
                    elif t2 == game.my_team:
                        next_opp = t1.name; opp_obj = t1

            screen.blit(get_font(24, True).render(game.my_team.name, True, TEXT_WHITE), (60, 220))
            screen.blit(get_font(16).render("vs", True, TEXT_GRAY), (60, 250))
            screen.blit(get_font(24, True).render(next_opp, True, TEXT_WHITE), (60, 275))

            if opp_obj:
                screen.blit(
                    get_font(14).render(f"Scout Report: Expecting '{opp_obj.current_tactic}'", True, ACCENT_RED),
                    (60, 310))

            btn_txt = f"PLAY MATCHDAY {game.matchday + 1}"

        game.btn_sim = Button(60, 340, 360, 40, btn_txt, ACCENT_CYAN, font_size=18)
    else:
        status = "KNOCKOUTS" if game.phase == "KNOCKOUT" else "SEASON END"
        screen.blit(get_font(24).render(status, True, TEXT_WHITE), (60, 240))
        game.btn_sim = Button(60, 320, 360, 50, "CONTINUE", TEXT_GRAY)
        if game.phase != "KNOCKOUT": game.btn_sim.active = False
    game.btn_sim.draw(screen, m_pos)

    if not game.spectator_mode:
        s_labels = ["WINS", "GOALS", "POINTS"]
        s_vals = [game.my_team.won, game.my_team.gf, game.my_team.points]
        s_cols = [ACCENT_GREEN, ACCENT_GOLD, TEXT_WHITE]
        for i in range(3):
            x = 460 + (i * 260)
            draw_card(screen, pygame.Rect(x, 170, 240, 100))
            screen.blit(get_font(14).render(s_labels[i], True, TEXT_GRAY), (x + 20, 185))
            screen.blit(get_font(48, True).render(str(s_vals[i]), True, s_cols[i]), (x + 20, 210))
    else:
        draw_card(screen, pygame.Rect(460, 170, 760, 100))
        screen.blit(get_font(20).render("You are watching the simulation.", True, TEXT_GRAY), (480, 210))

    draw_card(screen, pygame.Rect(460, 290, 760, 100))
    screen.blit(get_font(14, True).render("GAME CONTROLS", True, TEXT_GRAY), (480, 305))
    game.btn_save = Button(480, 335, 150, 40, "SAVE GAME", ACCENT_GREEN, font_size=14)
    game.btn_save.draw(screen, m_pos)
    game.btn_restart = Button(650, 335, 150, 40, "MAIN MENU", ACCENT_RED, font_size=14)
    game.btn_restart.draw(screen, m_pos)

    draw_card(screen, pygame.Rect(40, 410, 1180, 380))
    screen.blit(get_font(18, True).render("LEAGUE NEWS", True, ACCENT_CYAN), (60, 430))
    pygame.draw.line(screen, TEXT_MUTED, (60, 460), (1180, 460), 1)
    for i, log in enumerate(game.logs[:9]):
        col = TEXT_GRAY
        if "[GOAL]" in log:
            col = ACCENT_GREEN
        elif "[INJURY]" in log:
            col = ACCENT_RED
        elif "---" in log:
            col = ACCENT_GOLD
        elif "Big Match" in log:
            col = TEXT_WHITE
        elif "RETIRED" in log:
            col = ACCENT_RED
        screen.blit(get_font(15).render(f"• {log}", True, col), (60, 475 + i * 32))


def draw_squad(screen, game):
    if game.spectator_mode:
        screen.blit(get_font(30).render("SQUAD VIEW DISABLED IN SPECTATOR MODE", True, TEXT_GRAY), (300, 400))
        return

    m_pos = game.get_game_mouse_pos()
    game.squad_buttons = []
    scroll = game.scroll_y

    # Left Panel
    draw_card(screen, pygame.Rect(40, 170 + scroll, 300, 620))
    screen.blit(get_font(20, True).render("TACTICS BOARD", True, ACCENT_GOLD), (60, 190 + scroll))

    tac_map = {"Attack": ACCENT_RED, "Park Bus": ACCENT_CYAN, "Counter": ACCENT_GOLD, "Balanced": ACCENT_GREEN}
    c_tac = tac_map.get(game.my_team.current_tactic, TEXT_WHITE)
    game.btn_tac = Button(60, 230 + scroll, 260, 40, f"STYLE: {game.my_team.current_tactic}", c_tac)
    game.btn_tac.draw(screen, m_pos)

    game.btn_form = Button(60, 280 + scroll, 260, 40, f"FORM: {game.my_team.current_formation}", BG_HEADER)
    game.btn_form.draw(screen, m_pos)

    pygame.draw.line(screen, TEXT_MUTED, (60, 340 + scroll), (320, 340 + scroll), 1)
    if game.selected_player_idx is not None:
        p = game.my_team.squad[game.selected_player_idx]
        screen.blit(get_font(18, True).render("SELECTED", True, TEXT_GRAY), (60, 360 + scroll))
        screen.blit(get_font(24, True).render(p.name, True, TEXT_WHITE), (60, 390 + scroll))

        m_col = ACCENT_GREEN if p.morale > 80 else (ACCENT_RED if p.morale < 40 else ACCENT_GOLD)
        m_txt = "Happy" if p.morale > 80 else ("Unhappy" if p.morale < 40 else "Okay")
        screen.blit(get_font(16).render(f"Morale: {m_txt} ({p.morale})", True, m_col), (60, 425 + scroll))
        screen.blit(get_font(16).render(f"Leader: {p.leadership} | Nat: {p.nationality}", True, TEXT_GRAY),
                    (60, 450 + scroll))

        status_text = "Fit"
        col_st = ACCENT_GREEN
        if p.injury_duration > 0:
            status_text = f"Injured ({p.injury_duration} wks)"
            col_st = ACCENT_RED
        elif p.suspension_duration > 0:
            status_text = "Suspended"
            col_st = ACCENT_RED

        screen.blit(get_font(16).render(status_text, True, col_st), (60, 475 + scroll))

        game.btn_sell = Button(60, 520 + scroll, 260, 40, "SELL PLAYER", ACCENT_RED)
        game.btn_sell.draw(screen, m_pos)
    else:
        screen.blit(get_font(14, True).render("Select a player...", True, TEXT_MUTED), (60, 380 + scroll))

    # --- HORIZONTAL PITCH DRAWING ---
    pitch_x, pitch_y = 360, 170 + scroll
    pitch_w, pitch_h = 880, 620

    # Grass
    pygame.draw.rect(screen, PITCH_DARK, (pitch_x, pitch_y, pitch_w, pitch_h), border_radius=15)
    # Stripes
    for i in range(0, pitch_w, 100):
        if (i // 100) % 2 == 0:
            s = pygame.Surface((100, pitch_h))
            s.set_alpha(30);
            s.fill((0, 0, 0))
            screen.blit(s, (pitch_x + i, pitch_y))

    # Lines (White)
    pygame.draw.rect(screen, (220, 220, 220), (pitch_x, pitch_y, pitch_w, pitch_h), 3, border_radius=15)

    # Center Line (Vertical in Horizontal View)
    mid_x = pitch_x + pitch_w // 2
    pygame.draw.line(screen, (220, 220, 220), (mid_x, pitch_y), (mid_x, pitch_y + pitch_h), 3)

    # Center Circle
    mid_y = pitch_y + pitch_h // 2
    pygame.draw.circle(screen, (220, 220, 220), (mid_x, mid_y), 70, 3)

    # Goal Boxes (Left and Right)
    box_w, box_h = 100, 250
    # Left Box
    pygame.draw.rect(screen, (220, 220, 220), (pitch_x, mid_y - box_h // 2, box_w, box_h), 3)
    # Right Box
    pygame.draw.rect(screen, (220, 220, 220), (pitch_x + pitch_w - box_w, mid_y - box_h // 2, box_w, box_h), 3)

    # DRAW PLAYERS (Horizontal)
    coords = FORMATION_COORDS.get(game.my_team.current_formation, FORMATION_COORDS["4-3-3"])
    for i, p in enumerate(game.my_team.squad[:11]):
        if i >= len(coords): break
        ox, oy = coords[i]  # 0-100 values

        # Scale 0-100 to pitch dimensions
        bx = pitch_x + int((ox / 100) * (pitch_w - 110)) + 10  # Offset to keep inside
        by = pitch_y + int((oy / 100) * (pitch_h - 40)) + 10

        col = ACCENT_GOLD if game.selected_player_idx == i else BG_PANEL

        icon = "🏥" if p.injury_duration > 0 else ("🟥" if p.suspension_duration > 0 else "")
        btn_text = f"{icon}{p.pos} {p.name[:10]} ({p.age})"

        pygame.draw.circle(screen, (0, 0, 0, 100), (bx + 55, by + 40), 10)  # Shadow

        btn = Button(bx, by, 110, 35, btn_text, col, data=i, font_size=11)
        btn.draw(screen, m_pos)
        game.squad_buttons.append(btn)

        # OVR Pill
        eff = getattr(p, 'effective_ovr', p.raw_ovr)
        pill_col = ACCENT_GREEN if eff >= p.raw_ovr else ACCENT_RED
        pygame.draw.rect(screen, pill_col, (bx + 35, by + 40, 40, 16), border_radius=8)
        val = get_font(12, True).render(str(int(eff)), True, BG_DARK)
        screen.blit(val, val.get_rect(center=(bx + 55, by + 48)))

    # SUBS
    subs_start_y = 820 + scroll
    screen.blit(get_font(20, True).render("SUBSTITUTES", True, TEXT_WHITE), (370, subs_start_y - 25))
    subs = game.my_team.squad[11:]
    for i, p in enumerate(subs):
        row = i // 6;
        col = i % 6
        bx = 370 + (col * 145);
        by = subs_start_y + (row * 45)
        c = ACCENT_GOLD if game.selected_player_idx == i + 11 else BG_PANEL

        icon = "🏥" if p.injury_duration > 0 else ("🟥" if p.suspension_duration > 0 else "")
        btn_text = f"{icon}{p.pos} {p.name[:10]} ({p.age})"

        btn = Button(bx, by, 140, 35, btn_text, c, data=i + 11, font_size=12)
        btn.draw(screen, m_pos)
        game.squad_buttons.append(btn)


def draw_live_match(screen, game):
    m_pos = game.get_game_mouse_pos()
    game.match_control_buttons = []
    match = game.current_live_match
    if not match: return

    draw_card(screen, pygame.Rect(340, 120, 600, 160))
    progress_w = 560
    pygame.draw.rect(screen, (50, 50, 50), (360, 135, progress_w, 6), border_radius=3)
    fill_w = int(progress_w * (match.minute / 90))
    pygame.draw.rect(screen, ACCENT_GREEN, (360, 135, fill_w, 6), border_radius=3)

    screen.blit(get_font(36, True).render(match.home.name, True, TEXT_WHITE), (360, 160))
    t2_surf = get_font(36, True).render(match.away.name, True, TEXT_WHITE)
    screen.blit(t2_surf, (920 - t2_surf.get_width(), 160))

    h_tac = f"({match.home.current_tactic})"
    a_tac = f"({match.away.current_tactic})"
    screen.blit(get_font(14).render(h_tac, True, TEXT_GRAY), (360, 200))
    screen.blit(get_font(14).render(a_tac, True, TEXT_GRAY), (920 - get_font(14).size(a_tac)[0], 200))

    score_txt = f"{match.home_score} - {match.away_score}"
    time_txt = f"{match.minute}'"
    s_surf = get_font(60, True).render(score_txt, True, ACCENT_GOLD)
    t_surf = get_font(30).render(time_txt, True, ACCENT_CYAN)

    screen.blit(s_surf, s_surf.get_rect(center=(640, 190)))
    screen.blit(t_surf, t_surf.get_rect(center=(640, 240)))

    bar_w = 500
    pygame.draw.rect(screen, (50, 50, 50), (390, 260, bar_w, 10), border_radius=5)
    home_w = int(bar_w * (match.momentum / 100))
    pygame.draw.rect(screen, ACCENT_CYAN, (390, 260, home_w, 10), border_top_left_radius=5, border_bottom_left_radius=5)
    screen.blit(get_font(12).render("Momentum", True, TEXT_GRAY), (610, 275))

    draw_card(screen, pygame.Rect(340, 310, 600, 400))
    screen.blit(get_font(18, True).render("LIVE COMMENTARY", True, TEXT_GRAY), (360, 330))
    pygame.draw.line(screen, TEXT_MUTED, (360, 360), (920, 360), 1)
    y = 380
    for min, msg, type in reversed(match.logs[-8:]):
        col = TEXT_WHITE
        if type == "GOAL":
            col = ACCENT_GOLD
        elif type == "SAVE":
            col = ACCENT_GREEN
        elif type == "DEF":
            col = ACCENT_RED
        screen.blit(get_font(16).render(f"{min}' {msg}", True, col), (360, y))
        y += 35

    btn_skip = Button(1000, 750, 200, 60, "SKIP", ACCENT_RED)
    btn_skip.draw(screen, m_pos)
    game.match_control_buttons.append(btn_skip)

    if not game.spectator_mode:
        btn_tac = Button(80, 750, 200, 60, f"TACTIC", ACCENT_CYAN)
        btn_tac.draw(screen, m_pos)
        game.match_control_buttons.append(btn_tac)
        screen.blit(get_font(16).render(f"Current: {game.my_team.current_tactic}", True, TEXT_WHITE), (80, 820))


def draw_market(screen, game):
    m_pos = game.get_game_mouse_pos()
    game.market_buttons = []
    game.market_filter_buttons = []
    is_open = game.is_transfer_window_open()
    status_txt = "OPEN" if is_open else "CLOSED"
    col_status = ACCENT_GREEN if is_open else ACCENT_RED
    draw_card(screen, pygame.Rect(40, 170 + game.scroll_y, 1200, 100))
    screen.blit(get_font(16, True).render(f"TRANSFER WINDOW: {status_txt}", True, col_status),
                (60, 185 + game.scroll_y))

    search_rect = pygame.Rect(60, 220 + game.scroll_y, 300, 40)
    box_col = (70, 80, 100) if game.is_typing_search else (50, 60, 80)
    border_col = ACCENT_CYAN if game.is_typing_search else TEXT_GRAY
    pygame.draw.rect(screen, box_col, search_rect, border_radius=5)
    pygame.draw.rect(screen, border_col, search_rect, 2, border_radius=5)

    txt = game.market_search_query
    if game.is_typing_search and (pygame.time.get_ticks() // 500) % 2 == 0: txt += "|"
    screen.blit(get_font(18).render(txt if txt else "Search name...", True, TEXT_WHITE), (70, 230 + game.scroll_y))

    filters = ["ALL", "FWD", "MID", "DEF", "GK"]
    x_btn = 380
    for f in filters:
        is_active = (game.market_filter_pos == f)
        col = ACCENT_CYAN if is_active else BG_DARK
        btn = Button(x_btn, 220 + game.scroll_y, 80, 40, f, col, data=f, font_size=14)
        btn.draw(screen, m_pos)
        game.market_filter_buttons.append(btn)
        x_btn += 90

    headers = ["NAME", "POS", "AGE", "OVR", "VALUE", "ACTION"]
    xs = [70, 320, 420, 520, 720, 930]
    pygame.draw.rect(screen, BG_HEADER, (40, 290 + game.scroll_y, 1200, 40), border_top_left_radius=10,
                     border_top_right_radius=10)
    for h, x in zip(headers, xs): screen.blit(get_font(14, True).render(h, True, TEXT_GRAY), (x, 302 + game.scroll_y))

    if not game.market_cache: game.refresh_market_cache()
    y = 330 + game.scroll_y
    row_h = 55
    for i, (p, t) in enumerate(game.market_cache):
        if y > 750: break
        if y < 280: y += row_h; continue
        row_col = BG_PANEL if i % 2 == 0 else BG_DARK
        pygame.draw.rect(screen, row_col, (40, y, 1200, row_h))
        vals = [p.name, p.pos, str(p.age), p.get_display_ovr(), f"${p.value}M"]
        cols = [TEXT_WHITE, TEXT_GRAY, TEXT_GRAY, ACCENT_CYAN, ACCENT_GREEN]
        for j, (v, x) in enumerate(zip(vals, xs[:-1])):
            screen.blit(get_font(16).render(v, True, cols[j]), (x, y + 18))

        if game.spectator_mode: y += row_h; continue

        can_buy = game.my_team.budget >= p.value and is_open
        if not p.scouted:
            can_scout = game.my_team.budget >= SCOUTING_COST
            btn = Button(940, y + 10, 140, 35, f"SCOUT ${SCOUTING_COST}M", ACCENT_GOLD if can_scout else BG_PANEL,
                         data={"type": "reveal", "player": p}, font_size=12)
            if not can_scout: btn.active = False
            btn.draw(screen, m_pos)
            game.market_buttons.append(btn)
        else:
            btn = Button(940, y + 10, 140, 35, "SIGN" if is_open else "CLOSED", ACCENT_GREEN if can_buy else BG_PANEL,
                         data=p, font_size=12)
            if not can_buy or not is_open: btn.active = False
            btn.draw(screen, m_pos)
            if can_buy: game.market_buttons.append(btn)
        y += row_h


# --- TRAINING ---
def draw_training(screen, game):
    if game.spectator_mode: return
    m_pos = game.get_game_mouse_pos()
    game.training_buttons = []

    draw_card(screen, pygame.Rect(40, 170, 1200, 100))
    screen.blit(get_font(24, True).render(f"WEEKLY TRAINING POINTS: {game.my_team.training_points}", True, ACCENT_GOLD),
                (60, 205))

    labels = [("ATTACK DRILL", "FWDs gain OVR", "ATTACK"),
              ("DEFENSIVE SHAPE", "DEFs gain OVR", "DEFENSE"),
              ("PHYSIO & RECOVERY", "Heal Injuries / Boost Morale", "PHYSIO")]

    for i, (title, desc, data) in enumerate(labels):
        x = 40 + (i * 410)
        draw_card(screen, pygame.Rect(x, 300, 380, 200), color=BG_PANEL)
        screen.blit(get_font(20, True).render(title, True, ACCENT_CYAN), (x + 20, 320))
        screen.blit(get_font(16).render(desc, True, TEXT_WHITE), (x + 20, 360))

        btn = Button(x + 20, 420, 340, 50, "TRAIN", ACCENT_GREEN, data=data)
        if game.my_team.training_points <= 0: btn.active = False
        btn.draw(screen, m_pos)
        game.training_buttons.append(btn)


def draw_scouting(screen, game):
    if game.spectator_mode: return
    m_pos = game.get_game_mouse_pos()
    game.scouting_buttons = []
    scroll = game.scroll_y
    draw_card(screen, pygame.Rect(40, 170 + scroll, 300, 300))
    screen.blit(get_font(20, True).render("YOUTH SEARCH", True, ACCENT_CYAN), (60, 190 + scroll))
    screen.blit(get_font(14).render(f"Cost: ${YOUTH_SEARCH_COST}M. Finds 3 players.", True, TEXT_GRAY),
                (60, 230 + scroll))
    can_search = game.my_team.budget >= YOUTH_SEARCH_COST
    game.btn_scout_search = Button(60, 260 + scroll, 260, 50, "SEND SCOUTS", ACCENT_GOLD if can_search else BG_DARK)
    if not can_search: game.btn_scout_search.active = False
    game.btn_scout_search.draw(screen, m_pos)

    y = 240 + scroll
    if not game.scout_results: screen.blit(get_font(16).render("No active reports.", True, TEXT_MUTED), (390, y))
    for p in game.scout_results:
        draw_card(screen, pygame.Rect(380, y, 840, 60), color=BG_DARK, border=True)
        info = f"{p.name} ({p.age}y)  |  {p.pos}  |  OVR: {p.raw_ovr}  |  POT: {p.potential}"
        screen.blit(get_font(18, True).render(info, True, TEXT_WHITE), (400, y + 20))
        screen.blit(get_font(16).render(f"Val: ${p.value}M", True, ACCENT_GREEN), (900, y + 20))
        can_buy = game.my_team.budget >= p.value
        btn = Button(1100, y + 10, 100, 40, "SIGN", ACCENT_GREEN if can_buy else BG_PANEL, data=p)
        if not can_buy: btn.active = False
        btn.draw(screen, m_pos)
        if can_buy: game.scouting_buttons.append(btn)
        y += 70


def draw_teams_view(screen, game):
    m_pos = game.get_game_mouse_pos()
    game.team_view_buttons = []
    scroll = game.scroll_y
    draw_card(screen, pygame.Rect(40, 170 + scroll, 300, 620))
    screen.blit(get_font(20, True).render("ALL CLUBS", True, ACCENT_CYAN), (60, 190 + scroll))
    y = 230 + scroll
    for t in game.teams:
        col = ACCENT_GOLD if t == game.selected_view_team else BG_PANEL
        btn = Button(50, y, 280, 40, t.name, col, data=t, font_size=16)
        btn.draw(screen, m_pos)
        game.team_view_buttons.append(btn)
        y += 45
    draw_card(screen, pygame.Rect(360, 170 + scroll, 880, 620))
    t = game.selected_view_team
    if not t:
        screen.blit(get_font(20).render("Select a team to view details.", True, TEXT_GRAY), (400, 200 + scroll))
        return
    screen.blit(get_font(30, True).render(t.name, True, TEXT_WHITE), (390, 200 + scroll))
    screen.blit(get_font(20).render(f"Budget: ${t.budget}M  |  OVR: {t.get_xi_rating()}", True, ACCENT_GOLD),
                (390, 240 + scroll))
    y_list = 280 + scroll
    for p in t.squad:
        screen.blit(get_font(16).render(p.pos, True, ACCENT_CYAN), (390, y_list))
        screen.blit(get_font(16).render(p.name, True, TEXT_WHITE), (450, y_list))
        screen.blit(get_font(16).render(str(p.raw_ovr), True, TEXT_WHITE), (700, y_list))
        screen.blit(get_font(16).render(str(p.age), True, TEXT_GRAY), (760, y_list))
        y_list += 25
    hist_x = 850
    screen.blit(get_font(18, True).render("HISTORY LOG", True, ACCENT_GREEN), (hist_x, 280 + scroll))
    y_hist = 310 + scroll
    for log in t.transfer_log[-12:]:
        screen.blit(get_font(12).render(f"> {log}", True, TEXT_GRAY), (hist_x, y_hist))
        y_hist += 20


def draw_season_stats(screen, game):
    all_players = []
    for t in game.teams:
        for p in t.squad: all_players.append((p, t.name))
    top_goals = sorted(all_players, key=lambda x: x[0].goals, reverse=True)[:10]
    top_assists = sorted(all_players, key=lambda x: x[0].assists, reverse=True)[:10]
    gks = [x for x in all_players if x[0].pos == "GK"]
    top_saves = sorted(gks, key=lambda x: x[0].saves, reverse=True)[:10]
    scroll = game.scroll_y
    cols = [("GOLDEN BOOT (Goals)", top_goals, 40), ("PLAYMAKER (Assists)", top_assists, 450),
            ("GOLDEN GLOVE (Saves)", top_saves, 860)]
    for title, data, x_off in cols:
        draw_card(screen, pygame.Rect(x_off, 170 + scroll, 380, 600))
        screen.blit(get_font(20, True).render(title, True, ACCENT_GOLD), (x_off + 20, 190 + scroll))
        y = 230 + scroll
        for i, (p, t_name) in enumerate(data, 1):
            if y > 750: break
            if "Goals" in title:
                val = p.goals
            elif "Assists" in title:
                val = p.assists
            else:
                val = p.saves
            screen.blit(get_font(16, True).render(f"{i}. {p.name}", True, TEXT_WHITE), (x_off + 20, y))
            screen.blit(get_font(14).render(f"{t_name}", True, TEXT_GRAY), (x_off + 20, y + 20))
            screen.blit(get_font(24, True).render(str(val), True, ACCENT_CYAN), (x_off + 320, y + 5))
            pygame.draw.line(screen, BG_DARK, (x_off + 10, y + 45), (x_off + 370, y + 45), 1)
            y += 55


def draw_standings(screen, game):
    y = 170 + game.scroll_y
    headers = ["POS", "TEAM", "PL", "W-D-L", "GD", "PTS"];
    xs = [60, 140, 450, 600, 800, 1000]
    draw_card(screen, pygame.Rect(40, 170 + game.scroll_y, 1200, 620))
    pygame.draw.rect(screen, BG_HEADER, (40, 170 + game.scroll_y, 1200, 50), border_top_left_radius=12,
                     border_top_right_radius=12)
    for h, x in zip(headers, xs): screen.blit(get_font(16, True).render(h, True, TEXT_GRAY), (x, 185 + game.scroll_y))
    teams = sorted(game.teams, key=lambda x: (x.points, x.gd), reverse=True)
    for i, t in enumerate(teams, 1):
        y_pos = 220 + (i - 1) * 50 + game.scroll_y
        if y_pos > 750 or y_pos < 220: continue
        bg = BG_PANEL if i % 2 == 0 else BG_DARK
        if t == game.my_team: bg = (40, 50, 20)
        pygame.draw.rect(screen, bg, (40, y_pos, 1200, 50))
        num_col = TEXT_GRAY
        if i <= 8:
            num_col = ACCENT_GREEN
        elif i > 24:
            num_col = ACCENT_RED
        vals = [str(i), t.name, str(t.played), f"{t.won}-{t.drawn}-{t.lost}", str(t.gd), str(t.points)]
        for j, (v, x) in enumerate(zip(vals, xs)):
            c = num_col if j == 0 else TEXT_WHITE
            if j == 5: c = ACCENT_GOLD
            screen.blit(get_font(16, j == 1).render(v, True, c), (x, y_pos + 15))


# --- NEW: JOB OFFER SCREEN ---
def draw_jobs(screen, game):
    m_pos = game.get_game_mouse_pos()
    screen.fill(BG_DARK)
    game.job_buttons = []

    t = get_font(40, True).render("JOB OFFERS", True, ACCENT_GOLD)
    screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 80)))
    sub = get_font(20).render("Your performance has attracted attention.", True, TEXT_WHITE)
    screen.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 130)))

    draw_card(screen, pygame.Rect(SCREEN_WIDTH // 2 - 200, 180, 400, 100), color=BG_PANEL)
    screen.blit(get_font(24, True).render(f"STAY AT {game.my_team.name}", True, ACCENT_CYAN),
                (SCREEN_WIDTH // 2 - 180, 200))
    btn_stay = Button(SCREEN_WIDTH // 2 + 80, 210, 100, 40, "ACCEPT", ACCENT_GREEN, data="STAY")
    btn_stay.draw(screen, m_pos)
    game.job_buttons.append(btn_stay)

    y = 320
    for team in game.job_offers:
        draw_card(screen, pygame.Rect(SCREEN_WIDTH // 2 - 200, y, 400, 100), color=BG_PANEL)
        screen.blit(get_font(24, True).render(team.name, True, TEXT_WHITE), (SCREEN_WIDTH // 2 - 180, y + 20))
        info = f"Bud: ${team.budget}M | OVR: {team.get_xi_rating()}"
        screen.blit(get_font(16).render(info, True, TEXT_GRAY), (SCREEN_WIDTH // 2 - 180, y + 60))
        btn = Button(SCREEN_WIDTH // 2 + 80, y + 30, 100, 40, "ACCEPT", ACCENT_GOLD, data=team)
        btn.draw(screen, m_pos)
        game.job_buttons.append(btn)
        y += 120


def draw_knockout(screen, game):
    m_pos = game.get_game_mouse_pos()
    game.knockout_buttons = []
    scroll = game.scroll_y
    draw_card(screen, pygame.Rect(40, 170 + scroll, 1200, 60))
    leg_text = f" - LEG {game.leg}" if game.round_name != "FINAL" and game.round_name != "" else ""
    screen.blit(get_font(24, True).render(f"STAGE: {game.round_name}{leg_text}", True, ACCENT_CYAN), (60, 185 + scroll))

    if game.phase == "LEAGUE":
        screen.blit(get_font(20).render("Knockout phase begins after Matchday 8.", True, TEXT_GRAY), (60, 240 + scroll))
        return

    draw_card(screen, pygame.Rect(40, 250 + scroll, 400, 500))
    screen.blit(get_font(20, True).render("ROAD TO FINAL", True, ACCENT_GOLD), (60, 270 + scroll))
    pygame.draw.line(screen, TEXT_MUTED, (60, 300 + scroll), (420, 300 + scroll), 1)

    items_per_page = 14
    start_idx = game.history_page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = game.knockout_history[start_idx:end_idx]

    hy = 320 + scroll
    for round_name, winner_name, score_str in page_items:
        c_win = ACCENT_GOLD if game.my_team and winner_name == game.my_team.name else TEXT_GRAY
        txt = f"{round_name[:3]}: {winner_name} ({score_str})"
        screen.blit(get_font(14).render(txt, True, c_win), (50, hy))
        hy += 25

    if game.history_page > 0:
        btn_prev = Button(50, 710 + scroll, 60, 30, "<", BG_PANEL, data="PREV_PAGE")
        btn_prev.draw(screen, m_pos);
        game.knockout_buttons.append(btn_prev)
    if len(game.knockout_history) > end_idx:
        btn_next_pg = Button(350, 710 + scroll, 60, 30, ">", BG_PANEL, data="NEXT_PAGE")
        btn_next_pg.draw(screen, m_pos);
        game.knockout_buttons.append(btn_next_pg)

    y = 250 + scroll
    all_played = True
    for i, (t1, t2) in enumerate(game.knockout_fixtures):
        draw_card(screen, pygame.Rect(460, y, 780, 80), color=BG_DARK)
        result_data = game.knockout_results.get(i)
        if result_data:
            winner, score_str, h_s, a_s = result_data
            c1 = ACCENT_GREEN if h_s > a_s else TEXT_WHITE
            c2 = ACCENT_GREEN if a_s > h_s else TEXT_WHITE
            screen.blit(get_font(20, True).render(t1.name, True, c1), (480, y + 30))
            screen.blit(get_font(20, True).render(f"{h_s} - {a_s}", True, ACCENT_GOLD), (780, y + 30))
            screen.blit(get_font(20, True).render(t2.name, True, c2), (900, y + 30))
            if "PK" in score_str: screen.blit(get_font(14).render("PK", True, ACCENT_RED), (830, y + 10))
        else:
            all_played = False
            screen.blit(get_font(20, True).render(t1.name, True, TEXT_WHITE), (480, y + 30))
            screen.blit(get_font(16).render("vs", True, TEXT_MUTED), (800, y + 32))
            screen.blit(get_font(20, True).render(t2.name, True, TEXT_WHITE), (850, y + 30))
            if not game.spectator_mode and (t1 == game.my_team or t2 == game.my_team):
                btn_live = Button(1050, y + 20, 80, 40, "WATCH", ACCENT_GREEN, data={"type": "LIVE", "index": i})
                btn_live.draw(screen, m_pos);
                game.knockout_buttons.append(btn_live)
                btn_sim = Button(1140, y + 20, 80, 40, "SIM", BG_PANEL, data={"type": "SIM", "index": i})
                btn_sim.draw(screen, m_pos);
                game.knockout_buttons.append(btn_sim)
            else:
                btn_live = Button(1050, y + 20, 80, 40, "WATCH", ACCENT_CYAN, data={"type": "LIVE", "index": i})
                btn_live.draw(screen, m_pos);
                game.knockout_buttons.append(btn_live)
                btn_sim = Button(1140, y + 20, 80, 40, "SIM", BG_PANEL, data={"type": "SIM", "index": i})
                btn_sim.draw(screen, m_pos);
                game.knockout_buttons.append(btn_sim)
        y += 90

    if all_played:
        btn_next = Button(750, y + 20, 200, 50, "NEXT ROUND", ACCENT_GOLD, data="NEXT")
        btn_next.draw(screen, m_pos);
        game.knockout_buttons.append(btn_next)
    else:
        btn_sim_all = Button(750, y + 20, 200, 50, "QUICK SIM ROUND", ACCENT_CYAN, data="SIM_ALL")
        btn_sim_all.draw(screen, m_pos);
        game.knockout_buttons.append(btn_sim_all)


def draw_history(screen, game):
    draw_card(screen, pygame.Rect(40, 170 + game.scroll_y, 1200, 620))
    screen.blit(get_font(24, True).render("HALL OF FAME", True, ACCENT_GOLD), (70, 200 + game.scroll_y))
    y = 250 + game.scroll_y
    for year, winner in game.history_winners:
        draw_card(screen, pygame.Rect(70, y, 600, 50), color=BG_DARK)
        screen.blit(get_font(20, True).render(str(year), True, ACCENT_CYAN), (90, y + 15))
        screen.blit(get_font(20).render(winner, True, TEXT_WHITE), (200, y + 15))
        y += 60


def draw_select(screen, game):
    m_pos = game.get_game_mouse_pos()
    screen.fill(BG_DARK)
    screen.blit(get_font(40, True).render("Select Your Club", True, ACCENT_CYAN), (50, 50))
    x, y = 80, 150 + game.scroll_y
    for i, team in enumerate(game.teams):
        r = pygame.Rect(x + (i % 4) * 280, y + (i // 4) * 70, 260, 60)
        if r.bottom < 0 or r.top > SCREEN_HEIGHT: continue
        if r.collidepoint(m_pos):
            draw_card(screen, r, color=ACCENT_CYAN)
            screen.blit(get_font(18, True).render(team.name, True, BG_DARK), (r.x + 20, r.y + 20))
        else:
            draw_card(screen, r, color=BG_PANEL)
            screen.blit(get_font(18, True).render(team.name, True, TEXT_WHITE), (r.x + 20, r.y + 20))
    if os.path.exists("savegame.pkl"):
        game.btn_load = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 100, 300, 50, "LOAD SAVED GAME", ACCENT_GREEN)
        game.btn_load.draw(screen, m_pos)
    game.btn_spectate = Button(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 160, 300, 50, "WATCH MODE (SPECTATOR)",
                               ACCENT_GOLD)
    game.btn_spectate.draw(screen, m_pos)


def draw_winner(screen, game):
    m_pos = game.get_game_mouse_pos()
    screen.fill(BG_DARK)
    pygame.draw.circle(screen, (50, 40, 10), (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 300)

    if game.game_over:
        if game.was_fired:
            t = get_font(80, True).render("YOU HAVE BEEN SACKED", True, ACCENT_RED)
            n = get_font(30, True).render("Your reputation fell too low.", True, TEXT_WHITE)
        else:
            t = get_font(80, True).render("LEGENDARY CAREER", True, ACCENT_GOLD)
            n = get_font(30, True).render(
                f"Career Stats: {game.career_total_wins} Wins | {game.career_trophies} UCL Trophies", True, TEXT_WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 100)))
        screen.blit(n, n.get_rect(center=(SCREEN_WIDTH // 2, 180)))
        rep_txt = get_font(24).render(f"Final Manager Reputation: {game.manager_rep}/100", True, ACCENT_CYAN)
        screen.blit(rep_txt, rep_txt.get_rect(center=(SCREEN_WIDTH // 2, 220)))
        game.btn_world_stats = Button(SCREEN_WIDTH // 2 - 150, 520, 300, 60, "VIEW WORLD STATS", ACCENT_GOLD,
                                      font_size=20)
        game.btn_world_stats.draw(screen, m_pos)
        game.btn_restart = Button(SCREEN_WIDTH // 2 - 150, 600, 300, 60, "START NEW CAREER", ACCENT_CYAN, font_size=24)
        game.btn_restart.draw(screen, m_pos)
    else:
        t = get_font(80, True).render("CHAMPIONS", True, ACCENT_GOLD)
        n = get_font(100, True).render(game.champion.name, True, TEXT_WHITE)
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 250)))
        screen.blit(n, n.get_rect(center=(SCREEN_WIDTH // 2, 400)))
        game.btn_world_stats = Button(SCREEN_WIDTH // 2 - 150, 520, 300, 50, "VIEW WORLD STATS", ACCENT_GOLD,
                                      font_size=18)
        game.btn_world_stats.draw(screen, m_pos)
        game.btn_next_season = Button(SCREEN_WIDTH // 2 - 150, 600, 300, 60, "NEXT SEASON", ACCENT_GREEN, font_size=24)
        game.btn_next_season.draw(screen, m_pos)
        game.btn_retire = Button(SCREEN_WIDTH // 2 - 150, 680, 300, 40, "RETIRE CAREER", ACCENT_RED, font_size=18)
        game.btn_retire.draw(screen, m_pos)
        game.btn_restart = Button(SCREEN_WIDTH // 2 - 150, 740, 300, 40, "MAIN MENU", BG_PANEL, font_size=18)
        game.btn_restart.draw(screen, m_pos)


def draw_world_stats(screen, game):
    scroll = game.scroll_y
    m_pos = game.get_game_mouse_pos()
    draw_card(screen, pygame.Rect(40, 50, 1200, 750))
    screen.blit(get_font(36, True).render("WORLD STATS REPORT", True, ACCENT_CYAN), (60, 70))
    screen.blit(get_font(20).render("Club Performance Summary", True, TEXT_GRAY), (60, 110))
    game.btn_back = Button(1100, 70, 100, 40, "BACK", ACCENT_RED)
    game.btn_back.draw(screen, m_pos)
    y_start = 160
    pygame.draw.rect(screen, BG_HEADER, (60, y_start, 1160, 40))
    headers = ["CLUB", "TROPHIES", "BEST PLAYER (OVR)", "LEGEND (Goals)"]
    xs = [80, 400, 600, 900]
    for h, x in zip(headers, xs):
        screen.blit(get_font(16, True).render(h, True, TEXT_GRAY), (x, y_start + 10))
    y = y_start + 50 + scroll
    sorted_teams = sorted(game.teams, key=lambda t: (t.trophies, t.get_xi_rating()), reverse=True)
    for t in sorted_teams:
        if y > 780: break
        if y < 200: y += 50; continue
        pygame.draw.rect(screen, BG_PANEL, (60, y, 1160, 45))
        best_p = max(t.squad, key=lambda p: p.raw_ovr) if t.squad else None
        legend_p = max(t.squad, key=lambda p: p.career_goals) if t.squad else None
        col = ACCENT_GOLD if t == game.my_team else TEXT_WHITE
        screen.blit(get_font(18, True).render(t.name, True, col), (xs[0], y + 12))
        screen.blit(get_font(18, True).render(str(t.trophies), True, ACCENT_CYAN), (xs[1] + 20, y + 12))
        if best_p: screen.blit(get_font(16).render(f"{best_p.name} ({best_p.raw_ovr})", True, TEXT_WHITE),
                               (xs[2], y + 12))
        if legend_p: screen.blit(get_font(16).render(f"{legend_p.name} ({legend_p.career_goals})", True, ACCENT_GREEN),
                                 (xs[3], y + 12))
        y += 50
