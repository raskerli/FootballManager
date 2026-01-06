import pygame
from config import *


# --- FONT HELPER ---
def get_font(size, bold=False):
    """Returns a system font or default font if system font fails."""
    try:
        return pygame.font.SysFont("Arial", size, bold=bold)
    except:
        return pygame.font.Font(None, size)


# --- BUTTON CLASS ---
class Button:
    def __init__(self, x, y, w, h, text, color, text_color=TEXT_WHITE, font_size=16, data=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font = get_font(font_size, True)
        self.data = data
        self.active = True
        self.hovered = False

    def draw(self, surface, mouse_pos=None):
        """
        Draws the button.
        Args:
            surface: The pygame surface to draw on.
            mouse_pos: The (x, y) tuple of the CORRECTED mouse position.
                       If None, falls back to raw pygame.mouse.get_pos().
        """
        if not self.active:
            # Draw disabled state (dimmed/grayed out)
            dim_color = (self.color[0] // 2, self.color[1] // 2, self.color[2] // 2)
            pygame.draw.rect(surface, dim_color, self.rect, border_radius=6)
            txt_surf = self.font.render(self.text, True, (100, 100, 100))
            surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))
            return

        # HOVER LOGIC FIX
        # Use the passed mouse_pos if available (fixes resizing bugs)
        if mouse_pos:
            self.hovered = self.rect.collidepoint(mouse_pos)
        else:
            self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

        # Determine Color (Lighten if hovered)
        draw_col = self.color
        if self.hovered:
            # Create a lighter version of the base color
            draw_col = (min(255, self.color[0] + 30), min(255, self.color[1] + 30), min(255, self.color[2] + 30))

        # Draw Button Body
        pygame.draw.rect(surface, draw_col, self.rect, border_radius=6)

        # Draw Border (White if hovered, Dark Gray if not)
        border_col = TEXT_WHITE if self.hovered else (50, 50, 50)
        pygame.draw.rect(surface, border_col, self.rect, 2, border_radius=6)

        # Draw Text
        txt_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        """Checks if the button is clicked given a specific mouse position."""
        return self.active and self.rect.collidepoint(pos)


# --- TAB CLASS ---
class Tab:
    def __init__(self, text, rect):
        self.text = text
        self.rect = rect
        self.selected = False

    def draw(self, surface):
        # Background Color
        col = ACCENT_GOLD if self.selected else BG_PANEL

        # Draw Tab Shape
        pygame.draw.rect(surface, col, self.rect, border_top_left_radius=10, border_top_right_radius=10)

        # Draw Border
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_top_left_radius=10, border_top_right_radius=10)

        # Draw Text
        txt_col = BG_DARK if self.selected else TEXT_GRAY
        txt = get_font(18, True).render(self.text, True, txt_col)
        surface.blit(txt, txt.get_rect(center=self.rect.center))


# --- HELPER FUNCTIONS ---
def draw_card(surface, rect, color=BG_PANEL, border=False):
    """Draws a rounded card/panel background."""
    pygame.draw.rect(surface, color, rect, border_radius=10)
    if border:
        pygame.draw.rect(surface, (60, 70, 90), rect, 2, border_radius=10)


# --- FORMATION COORDINATES (HORIZONTAL PITCH) ---
# These coordinates are normalized (0-100).
# X=0 is the Goal Line (Left), X=100 is the Opponent Goal (Right).
# Y=0 is Top Touchline, Y=100 is Bottom Touchline.
FORMATION_COORDS = {
    "4-3-3": [
        (6, 50),  # 0: GK (Far Left)
        (22, 15), (22, 38), (22, 62), (22, 85),  # 1-4: DEF (LB, CB, CB, RB)
        (40, 25), (58, 50), (40, 75),  # 5-7: MID (LCM, CAM, RCM) -> CAM pushed to X=58
        (75, 15), (80, 50), (75, 85)  # 8-10: FWD (LW, ST, RW)
    ],
    "4-4-2": [
        (6, 50),  # GK
        (22, 15), (22, 38), (22, 62), (22, 85),  # DEF
        (45, 15), (45, 38), (45, 62), (45, 85),  # MID
        (75, 35), (75, 65)  # ST
    ],
    "3-5-2": [
        (6, 50),  # GK
        (22, 25), (20, 50), (22, 75),  # 3 CBs
        (40, 10), (45, 30), (40, 50), (45, 70), (40, 90),  # 5 Mids (Wingbacks wide, CMs central)
        (75, 35), (75, 65)  # 2 ST
    ]
}
