import pygame

# Initialize font module immediately
pygame.font.init()

# SCREEN SETTINGS
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 850
FPS = 60

# --- COLORS (THE FULL PALETTE) ---
BG_DARK = (10, 15, 30)        # Almost black blue (Main BG)
BG_PANEL = (20, 28, 48)       # Slightly lighter blue (Cards)
BG_HEADER = (13, 20, 40)      # Header Bar

# ACCENTS
ACCENT_CYAN = (0, 255, 245)   # UCL Cyan (Highlights)
ACCENT_GOLD = (255, 215, 0)   # Champions Gold (Stars/Wins)
ACCENT_RED = (235, 60, 60)    # Danger/Sell
ACCENT_GREEN = (46, 204, 113) # Success/Buy

# TEXT
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (145, 155, 175)
TEXT_MUTED = (80, 90, 110)

# PITCH COLORS
PITCH_DARK = (34, 139, 34)
PITCH_LIGHT = (40, 160, 40)
PITCH_LINE = (200, 200, 200, 150) # Semi-transparent white

# --- ALIASES FOR COMPATIBILITY (Vital for avoiding errors) ---
BG_LIGHT = BG_PANEL
SUCCESS = ACCENT_GREEN
DANGER = ACCENT_RED
WARNING = ACCENT_GOLD
WHITE = TEXT_WHITE

# --- GAME ECONOMY CONSTANTS ---
SCOUTING_COST = 2       # Cost to reveal 1 player
YOUTH_SEARCH_COST = 10  # Cost to find new players
MATCH_SPEED = 5         # Speed of live match ticks

# --- DATA: NATIONALITIES ---
NATIONALITIES = [
    "Spain", "England", "France", "Germany", "Brazil", "Argentina", "Italy",
    "Portugal", "Netherlands", "Belgium", "Croatia", "Uruguay", "Japan",
    "USA", "South Korea", "Senegal", "Morocco", "Nigeria", "Colombia",
    "Denmark", "Norway", "Sweden", "Poland", "Turkey", "Ukraine", "Serbia"
]

# --- FONT HELPER ---
def get_font(size, bold=False):
    # Try distinct modern fonts in order of preference
    fonts = ["Segoe UI", "Helvetica Neue", "Roboto", "Arial"]
    for f in fonts:
        try:
            return pygame.font.SysFont(f, size, bold=bold)
        except:
            continue
    # Fallback
    return pygame.font.SysFont("Arial", size, bold=bold)