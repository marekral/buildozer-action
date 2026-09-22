import time
import colorsys
import random
import tkinter as tk


# ============================================================
# NASTAVENIA PLOCHY A DISPLEJA
# ============================================================

CELL_SIZE = 12          # Veľkosť jednej bunky v pixeloch
VIEW_COLS = 45          # Viditeľná šírka (stĺpce)
VIEW_ROWS = 80          # Viditeľná výška (riadky)

MAP_ROWS = 240          # Celkový počet riadkov mriežky
MAP_COLS = 135          # Celkový počet stĺpcov mriežky

PERCENTO_PRAHU = 0.90   # Prah pre čistenie (90 %)
FAREBNY_KROK = 10       # Krok farebného odtieňa pre novú sadu generácií
MAX_STAGNACIA = 10


# ============================================================
# GLOBÁLNE PREMENNÉ
# ============================================================

g = 0
plocha = []
stagnacia = 0

# Pozícia kamery (ľavý horný roh viditeľného výrezu v mriežke)
cam_x = max(0, (MAP_COLS - VIEW_COLS) // 2)
cam_y = max(0, (MAP_ROWS - VIEW_ROWS) // 2)


# ============================================================
# TETRIS
# ============================================================

tetris_x = cam_x + VIEW_COLS // 2
tetris_y = cam_y + VIEW_ROWS // 2

aktualny_tvar = []

tetris_stav_blikania = True
posledne_bliknutie = 0
posledna_evolucia = 0

# Drag stav
is_dragging_block = False
is_panning_map = False

drag_offset_x = 0
drag_offset_y = 0

start_mouse_x = 0
start_mouse_y = 0
start_cam_x = 0
start_cam_y = 0


# ============================================================
# TVARY
# ============================================================

ZOZNAM_TVAROV = [
    [(0, -1), (0, 0), (0, 1), (0, 2)],        # I
    [(0, 0), (0, 1), (1, 0), (1, 1)],          # O
    [(0, -1), (0, 0), (0, 1), (1, 0)],         # T
    [(0, 0), (0, 1), (1, -1), (1, 0)],         # S
    [(0, -1), (0, 0), (1, 0), (1, 1)],         # Z
    [(0, -1), (0, 0), (0, 1), (1, -1)],        # J
    [(0, -1), (0, 0), (0, 1), (1, 1)],         # L
    [(0, -2), (0, -1), (0, 0), (0, 1), (0, 2)],  # I5
    [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)],  # X
    [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2)],   # V
    [(0, -1), (0, 0), (0, 1), (1, 0), (2, 0)],  # T5
    [(0, 0), (1, 0), (1, 1), (0, -1), (-1, -1)],  # W
    [(0, 0), (0, -1), (-1, -1), (0, 1), (1, 1)],  # Z5
    [(0, 0), (0, -1), (-1, 0), (0, 1), (1, 1)],  # F
    [(0, -1), (0, 0), (0, 1), (0, 2), (1, -1)],  # L5
    [(0, 0), (0, 1), (1, 0), (1, 1), (0, -1)],  # P
    [(0, -1), (0, 0), (1, 0), (1, 1), (1, 2)],  # N
    [(0, -1), (0, 0), (0, 1), (0, 2), (1, 0)],  # Y
    [(0, -1), (0, 0), (0, 1), (1, -1), (1, 1)]   # U
]


# ============================================================
# FARBA PODĽA GENERÁCIE
# ============================================================

KROK_ZMENY_FARBY = 100     # Každých 100 generácií sa zmení farba
KONTRASTNY_SKOK = 137.5   # Stupne na farebnom kruhu (zabezpečí výrazne odlišnú farbu)


def farba_podla_generacie(gen):
    skupina_generacii = gen // KROK_ZMENY_FARBY
    
    # Výpočet výrazne odlišného odtieňa (Hue) na kruhu 0.0 - 1.0
    h = ((skupina_generacii * KONTRASTNY_SKOK) % 360) / 360.0
    
    # Maximálna sýtosť a jas pre žiarivé kontrastné farby
    r, g_, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
    return (int(r * 255), int(g_ * 255), int(b * 255))


def rgb_to_hex(rgb):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'


def inic(rows, cols):
    vysl = []
    default_farba = farba_podla_generacie(0)
    for i in range(rows):
        riadok = [default_farba if random.randrange(5) == 1 else None for _ in range(cols)]
        vysl.append(riadok)
    return vysl


def novy_tetris_objekt():
    global tetris_x, tetris_y, aktualny_tvar
    global tetris_stav_blikania, posledne_bliknutie

    tetris_x = cam_x + VIEW_COLS // 2
    tetris_y = cam_y + VIEW_ROWS // 2
    aktualny_tvar = random.choice(ZOZNAM_TVAROV)
    tetris_stav_blikania = True
    posledne_bliknutie = time.time()


def ziskaj_bunku_tetrisu(r, s):
    for dr, ds in aktualny_tvar:
        if tetris_y + dr == r and tetris_x + ds == s:
            return 'green' if tetris_stav_blikania else 'blue'
    return None


def je_ziva(prvok):
    return isinstance(prvok, tuple)


def je_cierne(prvok):
    if isinstance(prvok, int) and prvok > 0:
        vek_smrti = min(prvok, 250)
        return int(255 * (1 - (vek_smrti - 1) / 99)) <= 0
    return False


# ============================================================
# KRESLENIE
# ============================================================

def kresli(tab, d=CELL_SIZE):
    canvas.delete('all')

    pocet_zivych = 0
    pocet_ciernych = 0

    tetris_mnozina = {(tetris_y + dr, tetris_x + ds) for dr, ds in aktualny_tvar}
    farba_tetris_current = 'green' if tetris_stav_blikania else 'blue'

    for vr in range(VIEW_ROWS):
        r = cam_y + vr
        if r < 0 or r >= MAP_ROWS:
            continue

        for vs in range(VIEW_COLS):
            s = cam_x + vs
            if s < 0 or s >= MAP_COLS:
                continue

            x = vs * d + 5
            y = vr * d + 5

            if (r, s) in tetris_mnozina:
                farba = farba_tetris_current
            else:
                prvok = tab[r][s]
                if isinstance(prvok, tuple):
                    farba = rgb_to_hex(prvok)
                    pocet_zivych += 1
                elif isinstance(prvok, int) and prvok > 0:
                    vek_smrti = min(prvok, 250)
                    intenzita = int(255 * (1 - (vek_smrti - 1) / 99))
                    if intenzita <= 0:
                        intenzita = 0
                        pocet_ciernych += 1
                    farba = rgb_to_hex((intenzita, intenzita, intenzita))
                else:
                    farba = 'white'

            canvas.create_rectangle(
                x, y, x + d, y + d, fill=farba, outline='lightgray'
            )

    # UI Informácie
    canvas.create_text(15, 15, text=f"Gen: {g}", anchor="w", fill="red", font=("Arial", 11, "bold"))
    canvas.create_text(15, 32, text=f"Kamera: [{cam_x}, {cam_y}]", anchor="w", fill="black", font=("Arial", 9))
    canvas.create_text(VIEW_COLS * CELL_SIZE - 15, 15, text="Blok = Presun bloku", anchor="e", fill="red", font=("Arial", 8, "bold"))
    canvas.create_text(VIEW_COLS * CELL_SIZE - 15, 30, text="Plocha = Posun mapy", anchor="e", fill="gray", font=("Arial", 8))


# ============================================================
# NOVÁ GENERÁCIA
# ============================================================

def nova_generacia(p):
    global g, stagnacia
    g += 1
    nova = [[None] * MAP_COLS for _ in range(MAP_ROWS)]
    nova_farba = farba_podla_generacie(g)
    zmeny = False

    # Evolúcia buniek
    for r in range(1, MAP_ROWS - 1):
        p_row = p[r]
        p_prev = p[r - 1]
        p_next = p[r + 1]
        nova_row = nova[r]

        for s in range(1, MAP_COLS - 1):
            ps = (
                (1 if isinstance(p_prev[s-1], tuple) else 0) +
                (1 if isinstance(p_prev[s], tuple) else 0) +
                (1 if isinstance(p_prev[s+1], tuple) else 0) +
                (1 if isinstance(p_row[s-1], tuple) else 0) +
                (1 if isinstance(p_row[s+1], tuple) else 0) +
                (1 if isinstance(p_next[s-1], tuple) else 0) +
                (1 if isinstance(p_next[s], tuple) else 0) +
                (1 if isinstance(p_next[s+1], tuple) else 0)
            )

            stary_prvok = p_row[s]
            is_alive = isinstance(stary_prvok, tuple)

            if ps == 3:
                nova_row[s] = nova_farba
            elif ps == 2 and is_alive:
                nova_row[s] = stary_prvok
            else:
                if is_alive:
                    nova_row[s] = 1
                elif isinstance(stary_prvok, int):
                    nova_row[s] = stary_prvok + 1 if stary_prvok < 100 else 100
                else:
                    nova_row[s] = None

            if nova_row[s] != stary_prvok:
                zmeny = True

    # Prah na čistenie (90% kapacity danej dimenzie)
    prah_riadku = PERCENTO_PRAHU * MAP_COLS  # 90% zo 135 = 121.5
    prah_stlpca = PERCENTO_PRAHU * MAP_ROWS  # 90% z 240 = 216.0

    riadky_na_ozivenie = [r for r in range(MAP_ROWS) if sum(1 for s in range(MAP_COLS) if je_cierne(nova[r][s])) >= prah_riadku]
    
    stlpe_na_ozivenie = []
    for s in range(MAP_COLS):
        cnt = sum(1 for r in range(MAP_ROWS) if je_cierne(nova[r][s]))
        if cnt >= prah_stlpca:
            stlpe_na_ozivenie.append(s)

    if riadky_na_ozivenie or stlpe_na_ozivenie:
        for r in range(MAP_ROWS):
            r_row = nova[r]
            is_r_revive = r in riadky_na_ozivenie
            for s in range(MAP_COLS):
                if is_r_revive or s in stlpe_na_ozivenie:
                    r_row[s] = nova_farba

    if zmeny:
        stagnacia = 0
    else:
        stagnacia += 1

    if stagnacia >= MAX_STAGNACIA:
        zmeny = False
        for r in range(MAP_ROWS):
            r_row = nova[r]
            for s in range(MAP_COLS - 1):
                if isinstance(r_row[s], tuple) and not isinstance(r_row[s + 1], tuple):
                    r_row[s + 1] = nova_farba
                    stagnacia = 0
                    zmeny = True
                    break
            if zmeny:
                break

    return nova


# ============================================================
# MYŠ: POSÚVANIE MAPY A PRESÚVANIE BLOKU
# ============================================================

def on_mouse_down(event):
    global is_dragging_block, is_panning_map
    global drag_offset_x, drag_offset_y
    global start_mouse_x, start_mouse_y, start_cam_x, start_cam_y

    col = (event.x - 5) // CELL_SIZE + cam_x
    row = (event.y - 5) // CELL_SIZE + cam_y

    zasah = any(tetris_y + dr == row and tetris_x + ds == col for dr, ds in aktualny_tvar)

    if zasah:
        is_dragging_block = True
        drag_offset_x = col - tetris_x
        drag_offset_y = row - tetris_y
    else:
        is_panning_map = True
        start_mouse_x = event.x
        start_mouse_y = event.y
        start_cam_x = cam_x
        start_cam_y = cam_y


def on_mouse_drag(event):
    global tetris_x, tetris_y, cam_x, cam_y

    if is_dragging_block:
        col = (event.x - 5) // CELL_SIZE + cam_x
        row = (event.y - 5) // CELL_SIZE + cam_y

        novy_x = col - drag_offset_x
        novy_y = row - drag_offset_y

        min_ds = min(ds for dr, ds in aktualny_tvar)
        max_ds = max(ds for dr, ds in aktualny_tvar)
        min_dr = min(dr for dr, ds in aktualny_tvar)
        max_dr = max(dr for dr, ds in aktualny_tvar)

        tetris_x = max(-min_ds, min(MAP_COLS - 1 - max_ds, novy_x))
        tetris_y = max(-min_dr, min(MAP_ROWS - 1 - max_dr, novy_y))
        kresli(plocha)

    elif is_panning_map:
        dx = (event.x - start_mouse_x) // CELL_SIZE
        dy = (event.y - start_mouse_y) // CELL_SIZE

        cam_x = max(0, min(MAP_COLS - VIEW_COLS, start_cam_x - dx))
        cam_y = max(0, min(MAP_ROWS - VIEW_ROWS, start_cam_y - dy))

        tetris_x = cam_x + VIEW_COLS // 2
        tetris_y = cam_y + VIEW_ROWS // 2

        kresli(plocha)


def on_mouse_up(event):
    global is_dragging_block, is_panning_map
    if is_dragging_block:
        is_dragging_block = False
        ukonci_umiestnovanie()
    elif is_panning_map:
        is_panning_map = False


def ukonci_umiestnovanie():
    global plocha
    farba_bloku = farba_podla_generacie(g)

    for dr, ds in aktualny_tvar:
        r, s = tetris_y + dr, tetris_x + ds
        if 0 <= r < MAP_ROWS and 0 <= s < MAP_COLS:
            plocha[r][s] = farba_bloku

    novy_tetris_objekt()
    kresli(plocha)


# ============================================================
# OKNO (TKINTER)
# ============================================================

root = tk.Tk()
root.title("Bio-Tetris Pentomino - 240x135 (90%)")

canvas = tk.Canvas(
    root,
    width=(VIEW_COLS * CELL_SIZE + 10),
    height=(VIEW_ROWS * CELL_SIZE + 10)
)
canvas.pack()

canvas.bind("<ButtonPress-1>", on_mouse_down)
canvas.bind("<B1-Motion>", on_mouse_drag)
canvas.bind("<ButtonRelease-1>", on_mouse_up)

plocha = inic(MAP_ROWS, MAP_COLS)
novy_tetris_objekt()
posledna_evolucia = time.time()
kresli(plocha)


# ============================================================
# HERNÁ SLUČKA
# ============================================================

def herna_slucka():
    global plocha, posledna_evolucia
    aktualny_cas = time.time()

    global tetris_stav_blikania, posledne_bliknutie
    if aktualny_cas - posledne_bliknutie >= 0.2:
        tetris_stav_blikania = not tetris_stav_blikania
        posledne_bliknutie = aktualny_cas

    if aktualny_cas - posledna_evolucia >= 0.2:
        plocha = nova_generacia(plocha)
        posledna_evolucia = aktualny_cas

    kresli(plocha)
    root.after(30, herna_slucka)


herna_slucka()
root.mainloop()