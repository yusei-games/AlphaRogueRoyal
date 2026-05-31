import heapq
import pyxel
import random
import traceback
import datetime
from pathlib import Path
from collections import deque

MAP_W, MAP_H = 80, 80
MAX_ROOMS, MIN_ROOMS = 18, 14
WALL, FLOOR, POISON = '#', '.', 'p'

SCR_W  = 320
SCR_H  = 240
VP_W   = 40    # 表示タイル数 横 (40 * 8px = 320px)
VP_H   = 20    # 表示タイル数 縦 (20 * 8px = 160px)
CHAR_W = 8     # 美咲ゴシック 全角 1文字 = 8px
CHAR_H = 8     # 1行 = 8px
HUD_Y     = VP_H * CHAR_H   # 160 — HUD開始 Y 座標
LOG_LINES = 28              # ログオーバーレイの最大表示行数

_BG     = 0
_FLOOR  = 1
_WALL   = 5
_WHITE  = 7
_RED    = 8
_YELLOW = 10
_GREEN  = 11
_CYAN   = 12
_PINK   = 14
_DIM    = 5
_POISON = 2

POISON_INTERVAL = 60   # ターン数ごとに毒が1波拡大（30から倍増→半速）

DIFF_NAMES     = ['EASY', 'NORMAL', 'HARD', 'HELL']
DIFF_INTERVALS = [100, 80, 70, 65]
DIFF_COLORS    = [11, 7, 10, 8]   # _GREEN, _WHITE, _YELLOW, _RED
DIFF_POTIONS   = [18, 12, 10, 8]

SFX_CH       = 0
MUSIC_CH     = 1
BGM_CH       = 2
SND_KILL     = 55
SND_POISON   = 56
SND_TITLE    = 57
SND_GAMEOVER = 58
SND_CLEAR    = 59
SND_POTION   = 60
SND_LEGENDARY = 61
SND_HIT      = 62
SND_LEVELUP  = 63
SND_BGM      = 54

WEAPONS = [
    {'key': 'weapon_dagger',     'atk':  6, 'price':   40},
    {'key': 'weapon_sword',      'atk': 16, 'price':  250},
    {'key': 'weapon_axe',        'atk': 30, 'price':  700},
    {'key': 'weapon_greatsword', 'atk': 45, 'price': 1200},
]

LEGENDARY_SWORD = {'key': 'weapon_legendary', 'atk': 60}

# 毎ターン動く(1)か3ターンに1回(3)か
ENEMY_MOVE_INTERVALS: dict[str, int] = {
    'S': 1, 'F': 1, 'Q': 1,
}

# ─── i18n ─────────────────────────────────────────────────

_lang: str = 'en'

STRINGS: dict = {
    'ja': {
        # weapons
        'weapon_dagger':     'ダガー',
        'weapon_sword':      'ソード',
        'weapon_axe':        'アックス',
        'weapon_greatsword': 'グレートソード',
        'weapon_legendary':  '伝説の剣',
        # game log
        'msg_start':          'Zを倒せばクリア！弱い敵でLvを上げよう。',
        'msg_poison_spread':  '毒の沼地が広がった！',
        'msg_poison_dead':    '毒の沼地で力尽きた…',
        'msg_poison_dmg':     '毒の沼地！-2HP HP:{hp}/{mhp}',
        'msg_kill':           '{L}を撃破！+{xp}XP +{gold}G',
        'msg_levelup':        '★Lv.{lv}! HP:{hp} ATK:{atk} DEF:{dfn}',
        'msg_potion':         'ポーションを飲んだ！HP全回復(+{healed})',
        'msg_attack_hit':     '{L}に{dmg}ダメ！HP:{hp}/{mhp}',
        'msg_enemy_atk_dead': '{L}の攻撃！{dmg}ダメ HP:0/{mhp}',
        'msg_player_dead':    'あなたは倒れた…',
        'msg_enemy_atk':      '{L}の攻撃！{dmg}ダメ HP:{hp}/{mhp}',
        'msg_legendary':      '★{name}を入手！ATK+{atk}',
        'msg_buy':            '{name}を購入！ATK+{atk}',
        'msg_no_gold':        '所持金が足りない！あと{need}G必要',
        'msg_lower_rank':     'もっと強い武器を持っている！',
        # title
        'title_main':       'ALPHA ROGUE.ROYAL',
        'title_exit':       'ゲーム終了',
        'title_hint':       'Ｗ／↑・Ｓ／↓：選択　ＳＰＡＣＥ／Ｅｎｔｅｒ：決定',
        'title_cursor_on':  '＞',
        'title_cursor_off': '　',
        # hud
        'hud_hp':       'ＨＰ',
        'hud_enemies':  '残敵：',
        'hud_turn':     'ターン：{n}',
        'end_turn':     '経過ターン：{n}',
        'hud_controls':  'ＷＡＳＤ／矢印：移動　スペース：休憩',
        'hud_controls2': 'Ｉ：情報　Ｍ：ログ　Ｑ／ＥＳＣ：タイトルへ',
        # shop
        'shop_title':    '★　武器屋　★',
        'shop_gold':     '所持金：{gold}G',
        'shop_equipped': '　◀装備中',
        'shop_hint':     '1-4:購入　ＥＳＣ／Ｑ：閉じる',
        # info
        'info_title':        'ゲーム情報',
        'info_difficulty':   '難易度：{name}',
        'info_obj_header':   '■目的',
        'info_obj_1':        'Ｚを倒せばクリア！弱い敵で経験値を稼ぎ、',
        'info_obj_2':        '武器屋（＄）でパワーアップして撃破しよう。',
        'info_obj_3':        'ぐずぐずしてると毒の沼地が迫ってくるぞ！（{ivl}ターンごと）',
        'info_tiles_header': '■マスの意味',
        'info_tile_self':    '自分　　',
        'info_tile_potion':  'ポーション',
        'info_tile_shop':    '武器屋',
        'info_tile_poison':  '毒の沼地　',
        'info_tile_wall':    '壁　　　　',
        'info_tile_floor':   '床',
        'info_enemy_header': '■敵一覧　ＨＰ／ＡＴＫ／ＤＦＮ',
        'info_special_header': '■特別な敵',
        'info_fast_desc':      '：動きが速い',
        'info_chase_desc':     '：プレイヤーを追ってくる',
        'info_drop_desc':      '：倒すと{name}をドロップ！',
        'info_range_desc':     '：３マス先から攻撃してくる',
        'info_footer':       'ＥＳＣ／Ｑ／Ｉ：閉じる',
        # log overlay
        'log_header': '─ログ履歴　',
        'log_hint':   'Ｗ／↑：上　Ｓ／↓：下　ＥＳＣ／Ｑ／Ｍ：閉じる',
        # end screen
        'end_clear':     '★　ＧＡＭＥ　ＣＬＥＡＲ　★',
        'end_over':      '―　ＧＡＭＥ　ＯＶＥＲ　―',
        'end_clear_sub': 'おめでとう！Zを撃破！最終Lv：{lv}',
        'end_over_sub':  'あなたは倒れた…　到達Lv：{lv}',
        'end_hint_clear': 'Ｑ／ＥＳＣ：タイトルへ',
        'end_hint_over':  'Ｑ／ＥＳＣ：タイトルへ　　Ｒ：リトライ',
        # confirm quit
        'quit_msg':  'タイトルに戻りますか？',
        'quit_hint': 'Ｙ：はい　　Ｎ：いいえ',
    },
    'en': {
        # weapons
        'weapon_dagger':     'Dagger',
        'weapon_sword':      'Sword',
        'weapon_axe':        'Axe',
        'weapon_greatsword': 'Greatsword',
        'weapon_legendary':  'Legendary Sword',
        # game log
        'msg_start':          'Defeat Z to win! Level up on weak foes.',
        'msg_poison_spread':  'The poison swamp is spreading!',
        'msg_poison_dead':    'You perished in the poison swamp...',
        'msg_poison_dmg':     'Poison! -2HP  HP:{hp}/{mhp}',
        'msg_kill':           'Defeated {L}! +{xp}XP +{gold}G',
        'msg_levelup':        'Lv.{lv}! HP:{hp} ATK:{atk} DEF:{dfn}',
        'msg_potion':         'Drank potion! Full HP restored (+{healed})',
        'msg_attack_hit':     'Hit {L} for {dmg}! HP:{hp}/{mhp}',
        'msg_enemy_atk_dead': '{L} attacks! {dmg} dmg. HP:0/{mhp}',
        'msg_player_dead':    'You have fallen...',
        'msg_enemy_atk':      '{L} attacks! {dmg} dmg. HP:{hp}/{mhp}',
        'msg_legendary':      'Got {name}! ATK+{atk}',
        'msg_buy':            'Bought {name}! ATK+{atk}',
        'msg_no_gold':        'Not enough gold! Need {need}G more',
        'msg_lower_rank':     'You already have a better weapon!',
        # title
        'title_main':       'ALPHA ROGUE.ROYAL',
        'title_exit':       'Quit Game',
        'title_hint':       'W/Up S/Down:Select Space/Enter:OK',
        'title_cursor_on':  '>',
        'title_cursor_off': ' ',
        # hud
        'hud_hp':       'HP',
        'hud_enemies':  'Enemies: ',
        'hud_turn':     'Turn:{n}',
        'end_turn':     'Turns: {n}',
        'hud_controls':  'WASD/Arrows:Move  Space:Rest',
        'hud_controls2': 'I:Info M:Log Q/ESC:Title',
        # shop
        'shop_title':    '* Weapon Shop *',
        'shop_gold':     'Gold: {gold}G',
        'shop_equipped': ' <Equipped',
        'shop_hint':     '1-4:Buy ESC/Q:Close',
        # info
        'info_title':        'Game Info',
        'info_difficulty':   'Difficulty: {name}',
        'info_obj_header':   '[Objective]',
        'info_obj_1':        'Defeat Z to win! Grind XP on weak foes,',
        'info_obj_2':        'buy weapons at shop ($) to power up.',
        'info_obj_3':        'Poison swamp closes in every {ivl} turns!',
        'info_tiles_header': '[Tile Guide]',
        'info_tile_self':    'You     ',
        'info_tile_potion':  'Potion',
        'info_tile_shop':    'Shop',
        'info_tile_poison':  'Poison  ',
        'info_tile_wall':    'Wall    ',
        'info_tile_floor':   'Floor',
        'info_enemy_header': '[Enemy List]  HP/ATK/DFN',
        'info_special_header': '[Special Enemies]',
        'info_fast_desc':      ':Fast',
        'info_chase_desc':     ':Always chases you',
        'info_drop_desc':      ':Defeat X to get {name}!',
        'info_range_desc':     ':Ranged attack (3 tiles)',
        'info_footer':       'ESC/Q/I: Close',
        # log overlay
        'log_header': '-- Log  ',
        'log_hint':   'W/Up:Up S/Down:Down ESC/Q/M:Close',
        # end screen
        'end_clear':     '* GAME CLEAR *',
        'end_over':      '- GAME OVER -',
        'end_clear_sub': 'Congrats! Defeated Z! Final Lv: {lv}',
        'end_over_sub':  'You have fallen... Reached Lv: {lv}',
        'end_hint_clear': 'Q/ESC: Return to Title',
        'end_hint_over':  'Q/ESC: Return to Title   R: Retry',
        # confirm quit
        'quit_msg':  'Return to title?',
        'quit_hint': 'Y: Yes    N: No',
    },
}


def T(key: str, **kw) -> str:
    return STRINGS[_lang][key].format(**kw)


def FW(s: str) -> str:
    """Full-width conversion in Japanese mode; identity in English."""
    return fw(s)# if _lang == 'ja' else s


def _sw(s: str) -> int:
    """Pixel width: full-width chars (>U+007E) = 8px, half-width = 4px."""
    s = fw(s)
    return sum(8 if ord(c) > 0x7E else 4 for c in s)


def fw(s: str) -> str:
    """ASCII印刷可能文字を全角Unicodeに変換。日本語はそのまま。"""
    out = []
    for c in s:
        cp = ord(c)
        if 0x21 <= cp <= 0x7E:
            out.append(chr(cp + 0xFEE0))   # ！ … ～
        elif cp == 0x20:
            out.append('　')            # 全角スペース
        else:
            out.append(c)
    return ''.join(out)


def _font_path() -> Path:
    """misaki_gothic.bdf をプロジェクトフォルダから探す。"""
    p = Path(__file__).parent / 'misaki_gothic.bdf'
    if not p.exists():
        raise FileNotFoundError(
            "misaki_gothic.bdf が見つかりません。\n"
            "美咲フォント公式サイトから BDF 版をダウンロードして\n"
            f"{p} に配置してください。"
        )
    return p


def _ecolor(letter: str) -> int:
    i = ord(letter) - ord('A')
    if i <= 7:  return 3        # 暗緑 (弱)
    if i <= 15: return _YELLOW  # 黄   (中)
    if i <= 22: return pyxel.COLOR_PURPLE #  赤(強)
    return _RED                 # 紫  (XYZ ボス)




# ─── Stats ────────────────────────────────────────────────


def enemy_data(letter: str, table: dict) -> dict:
    hp, atk, dfn, xp, gold = table[letter]
    return {'hp': hp, 'atk': atk, 'dfn': dfn, 'xp': xp, 'gold': gold}

def player_data(level: int) -> dict:
    lv = level - 1
    return {'hp': 60 + lv * 8, 'atk': 20 + lv * 3, 'dfn': 2 + lv}

def xp_needed(level: int) -> int:
    return level * 10


# ─── Balance Simulation ───────────────────────────────────

_WEAPON_AFTER_KILL: dict[str, dict] = {
    'B': WEAPONS[0], 'H': WEAPONS[1], 'P': WEAPONS[2], 'W': WEAPONS[3],
    'X': LEGENDARY_SWORD,
}
_DIFF_LEVEL_PENALTY: dict[str, int] = {
    'EASY': 7, 'NORMAL': 5, 'HARD': 4, 'HELL': 3,
}
_XYZ_XP         = [250, 650, 0]
_XYZ_GOLD       = [250, 260, 0]
_XYZ_HP_MULT: dict[str, float] = {'X': 1.0, 'Y': 1.2, 'Z': 2.0}
_EARLY_LETTERS  = frozenset('ABCDE')
_ALL_LETTERS    = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')


def _sim_survives(player: dict, enemy: dict, letter: str) -> bool:
    p_dmg  = max(1, player['atk'] + player['weapon'] - enemy['dfn'])
    e_dmg  = max(1, enemy['atk'] - player['dfn'])
    rounds = -(-enemy['hp'] // p_dmg)
    mult   = _XYZ_HP_MULT.get(letter)
    eff_hp = int(player['max_hp'] * mult) if mult is not None else player['max_hp'] // 2
    return eff_hp - rounds * e_dmg > 0


def _sim_survives_lv1(enemy: dict) -> bool:
    pd    = player_data(1)
    p_dmg = max(1, pd['atk'] - enemy['dfn'])
    e_dmg = max(1, enemy['atk'] - pd['dfn'])
    return pd['hp'] - (-(-enemy['hp'] // p_dmg)) * e_dmg > 0


def _sim_weakened(player: dict, penalty: int) -> dict:
    lv = max(1, player['level'] - penalty)
    pd = player_data(lv)
    return {**player, 'level': lv, 'max_hp': pd['hp'], 'atk': pd['atk'], 'dfn': pd['dfn']}


def build_enemy_table(diff_idx: int) -> dict:
    """ゲーム開始時に難易度に応じた敵パラメータをシミュレーション生成する。"""
    penalty = _DIFF_LEVEL_PENALTY[DIFF_NAMES[diff_idx]]
    pd      = player_data(1)
    player  = {
        'level': 1, 'max_hp': pd['hp'], 'atk': pd['atk'],
        'dfn': pd['dfn'], 'xp': 0, 'gold': 0, 'weapon': 0,
    }
    table: dict = {}

    for i, letter in enumerate(_ALL_LETTERS):
        enemy      = {'hp': 5, 'atk': 5, 'dfn': 0}
        prev_enemy = None
        maxed: set = set()
        itr        = 0

        bp      = _sim_weakened(player, penalty)
        dfn_cap = max(0, bp['atk'] + bp['weapon'] - 1)

        can_win = _sim_survives(bp, enemy, letter)
        if letter in _EARLY_LETTERS:
            can_win = can_win and _sim_survives_lv1(enemy)
        if can_win:
            prev_enemy = enemy.copy()

        while itr < 100_000:
            itr += 1
            available = [s for s in ['hp', 'atk', 'dfn'] if s not in maxed]
            if not available:
                break

            weights = [{'hp': 9, 'atk': 3, 'dfn': 2}[s] for s in available]
            stat    = random.choices(available, weights=weights)[0]

            if stat == 'atk' and enemy['atk'] >= 99:
                maxed.add('atk'); continue
            if stat == 'dfn' and enemy['dfn'] >= dfn_cap:
                maxed.add('dfn'); continue

            backup = enemy.copy()
            hp_inc = 0
            if stat == 'hp':
                hp_inc = random.randint(1, 3)
                enemy['hp'] += hp_inc
            elif stat == 'atk':
                enemy['atk'] += 1
            else:
                enemy['dfn'] += 1

            can_win = _sim_survives(bp, enemy, letter)
            if letter in _EARLY_LETTERS:
                can_win = can_win and _sim_survives_lv1(enemy)

            if can_win:
                prev_enemy = enemy.copy()
            else:
                enemy = backup
                if stat == 'hp' and hp_inc > 1:
                    enemy['hp'] += 1
                    can_win2 = _sim_survives(bp, enemy, letter)
                    if letter in _EARLY_LETTERS:
                        can_win2 = can_win2 and _sim_survives_lv1(enemy)
                    if can_win2:
                        prev_enemy = enemy.copy()
                        continue
                    enemy = backup
                maxed.add(stat)

        final = prev_enemy if prev_enemy is not None else {'hp': 5, 'atk': 5, 'dfn': 0}
        xyz   = i - 23 if i >= 23 else None
        final['xp']   = _XYZ_XP[xyz]   if xyz is not None else 10 + i * 5
        final['gold'] = _XYZ_GOLD[xyz]  if xyz is not None else 20 + i * 10

        table[letter] = (final['hp'], final['atk'], final['dfn'], final['xp'], final['gold'])

        player['gold'] += final['gold']
        player['xp']   += final['xp']
        while player['xp'] >= xp_needed(player['level']):
            player['xp']    -= xp_needed(player['level'])
            player['level'] += 1
            new_pd           = player_data(player['level'])
            player['max_hp'] = new_pd['hp']
            player['atk']    = new_pd['atk']
            player['dfn']    = new_pd['dfn']

        if letter in _WEAPON_AFTER_KILL:
            w = _WEAPON_AFTER_KILL[letter]
            if w['atk'] > player['weapon']:
                player['weapon'] = w['atk']
                player['gold']  -= w.get('price', 0)

    return table


# ─── Map ──────────────────────────────────────────────────

class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.cx = x + w // 2
        self.cy = y + h // 2

    def inner_rand(self):
        return (random.randint(self.x + 1, self.x + self.w - 2),
                random.randint(self.y + 1, self.y + self.h - 2))

    def overlaps(self, o, pad=1):
        return not (self.x + self.w + pad <= o.x or o.x + o.w + pad <= self.x or
                    self.y + self.h + pad <= o.y or o.y + o.h + pad <= self.y)


def _edge_dist(tiles: list) -> list:
    """マップ端からの BFS 距離を計算（外側ほど小さい値）。"""
    dist = [[-1] * MAP_W for _ in range(MAP_H)]
    q = deque()
    for x in range(MAP_W):
        for y in [0, MAP_H - 1]:
            dist[y][x] = 0
            q.append((x, y))
    for y in range(1, MAP_H - 1):
        for x in [0, MAP_W - 1]:
            if dist[y][x] == -1:
                dist[y][x] = 0
                q.append((x, y))
    while q:
        x, y = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAP_W and 0 <= ny < MAP_H and dist[ny][nx] == -1:
                dist[ny][nx] = dist[y][x] + 1
                q.append((nx, ny))
    return dist


def _astar(tiles, start, goal):
    """FLOOR と POISON を通行可能として A* 経路探索。
    Returns: start を除くステップのリスト。経路なしは None。"""
    sx, sy = start
    gx, gy = goal
    if (sx, sy) == (gx, gy):
        return []

    def h(x, y):
        return abs(x - gx) + abs(y - gy)

    open_heap = [(h(sx, sy), 0, sx, sy)]
    came_from = {}
    g_score = {(sx, sy): 0}

    while open_heap:
        _, cost, x, y = heapq.heappop(open_heap)

        if (x, y) == (gx, gy):
            path = []
            cur = (x, y)
            while cur != (sx, sy):
                path.append(cur)
                cur = came_from[cur]
            path.reverse()
            return path

        if cost > g_score.get((x, y), float('inf')):
            continue

        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
                continue
            if tiles[ny][nx] == WALL:
                continue
            new_cost = cost + 1
            if new_cost < g_score.get((nx, ny), float('inf')):
                g_score[(nx, ny)] = new_cost
                came_from[(nx, ny)] = (x, y)
                heapq.heappush(open_heap, (new_cost + h(nx, ny), new_cost, nx, ny))

    return None


def gen_map():
    tiles = [[WALL] * MAP_W for _ in range(MAP_H)]
    rooms = []

    # 中央に大きな部屋を先に配置（ショップ用）
    cw = random.randint(16, 24)
    ch = random.randint(10, 16)
    cx_pos = MAP_W // 2 - cw // 2
    cy_pos = MAP_H // 2 - ch // 2
    center_room = Room(cx_pos, cy_pos, cw, ch)
    for ry in range(cy_pos, cy_pos + ch):
        for rx in range(cx_pos, cx_pos + cw):
            tiles[ry][rx] = FLOOR
    rooms.append(center_room)

    for _ in range(800):
        if len(rooms) >= MAX_ROOMS:
            break
        w, h = random.randint(5, 12), random.randint(4, 9)
        x = random.randint(1, MAP_W - w - 2)
        y = random.randint(1, MAP_H - h - 2)
        r = Room(x, y, w, h)
        if any(r.overlaps(e) for e in rooms):
            continue
        for ry in range(y, y + h):
            for rx in range(x, x + w):
                tiles[ry][rx] = FLOOR
        prev = rooms[-1]
        if random.random() < 0.5:
            for rx in range(min(r.cx, prev.cx), max(r.cx, prev.cx) + 1):
                tiles[prev.cy][rx] = FLOOR
            for ry in range(min(r.cy, prev.cy), max(r.cy, prev.cy) + 1):
                tiles[ry][r.cx] = FLOOR
        else:
            for ry in range(min(r.cy, prev.cy), max(r.cy, prev.cy) + 1):
                tiles[ry][prev.cx] = FLOOR
            for rx in range(min(r.cx, prev.cx), max(r.cx, prev.cx) + 1):
                tiles[r.cy][rx] = FLOOR
        rooms.append(r)

    # 追加通路：近い部屋どうしをランダムに接続してループを増やす
    for i in range(1, len(rooms)):
        if random.random() < 0.45:
            j = random.randint(max(0, i - 5), i - 1)
            a, b = rooms[i], rooms[j]
            if random.random() < 0.5:
                for rx in range(min(a.cx, b.cx), max(a.cx, b.cx) + 1):
                    tiles[a.cy][rx] = FLOOR
                for ry in range(min(a.cy, b.cy), max(a.cy, b.cy) + 1):
                    tiles[ry][b.cx] = FLOOR
            else:
                for ry in range(min(a.cy, b.cy), max(a.cy, b.cy) + 1):
                    tiles[ry][a.cx] = FLOOR
                for rx in range(min(a.cx, b.cx), max(a.cx, b.cx) + 1):
                    tiles[b.cy][rx] = FLOOR

    if len(rooms) < MIN_ROOMS:
        return gen_map()
    return tiles, rooms, _edge_dist(tiles)


# ─── Entities ─────────────────────────────────────────────

class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.level = 1
        self.xp = 0
        d = player_data(1)
        self.max_hp = d['hp']
        self.hp     = d['hp']
        self.atk    = d['atk']
        self.dfn    = d['dfn']
        self.gold       = 0
        self.weapon_atk = 0
        self.weapon_name: str | None = None  # stores weapon key, e.g. 'weapon_dagger'

    def xp_to_next(self):
        return xp_needed(self.level)

    def gain_xp(self, amount: int) -> list:
        self.xp += amount
        msgs = []
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            d = player_data(self.level)
            self.hp  = min(self.hp + d['hp'] - self.max_hp, d['hp'])
            self.max_hp, self.atk, self.dfn = d['hp'], d['atk'], d['dfn']
            msgs.append(FW(T('msg_levelup', lv=self.level,
                             hp=self.max_hp, atk=self.atk, dfn=self.dfn)))
        return msgs


class Enemy:
    def __init__(self, letter, x, y, table: dict):
        self.letter, self.x, self.y = letter, x, y
        d = enemy_data(letter, table)
        self.max_hp = d['hp']
        self.hp     = d['hp']
        self.atk    = d['atk']
        self.dfn    = d['dfn']
        self.xp     = d['xp']
        self.gold   = d['gold']
        self.tx, self.ty = x, y
        self.path: list = []
        self.move_interval = ENEMY_MOVE_INTERVALS.get(letter, 3)


# ─── Game ─────────────────────────────────────────────────

class Game:
    def __init__(self, diff_idx: int = 1):
        self.poison_interval = DIFF_INTERVALS[diff_idx]
        self.potion_count    = DIFF_POTIONS[diff_idx]
        self.enemy_table     = build_enemy_table(diff_idx)
        self.reset()

    def reset(self):
        self.tiles, self.rooms, self.edge_dist = gen_map()
        self.player = Player(self.rooms[0].cx, self.rooms[0].cy)
        self.enemies: dict = {}
        self.potions: dict = {}
        self.in_shop = False
        self._place_shop()
        self._place_enemies()
        self._place_potions()
        self.msgs = deque([FW(T('msg_start'))], maxlen=200)
        self.running = True
        self.won = False
        self.turn = 0
        self.poison_wave = 0
        self.levelup_sfx_queue: list[int] = []

    def _place_shop(self):
        cx, cy = MAP_W // 2, MAP_H // 2
        best_room = min(self.rooms, key=lambda r: abs(r.cx - cx) + abs(r.cy - cy))
        self.shop_pos = best_room.inner_rand()

    def _place_enemies(self):
        p = self.player
        # edge_dist が高いほど中央寄り、低いほど外縁寄り
        sorted_rooms = sorted(self.rooms,
                              key=lambda r: self.edge_dist[r.cy][r.cx],
                              reverse=True)
        n     = len(sorted_rooms)
        third = max(1, n // 3)
        center_pool = sorted_rooms[:third]         # 中央寄りの部屋（上位1/3）
        outer_pool  = sorted_rooms[n - third:]     # 外縁寄りの部屋（下位1/3）
        all_pool    = self.rooms

        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if letter <= 'H':
                pool = center_pool   # A-H: 中央寄り
            elif letter >= 'Q':
                pool = outer_pool    # Q-Z: 外縁寄り
            else:
                pool = all_pool      # I-P: 全体
            for _ in range(500):
                x, y = random.choice(pool).inner_rand()
                if ((x, y) not in self.enemies and (x != p.x or y != p.y)
                        and (x, y) != self.shop_pos):
                    self.enemies[(x, y)] = Enemy(letter, x, y, self.enemy_table)
                    break

    def _place_potions(self):
        pool = self.rooms
        p = self.player
        placed = 0
        for _ in range(500):
            if placed >= self.potion_count:
                break
            x, y = random.choice(pool).inner_rand()
            if ((x, y) not in self.enemies and (x, y) not in self.potions
                    and (x != p.x or y != p.y) and (x, y) != self.shop_pos):
                self.potions[(x, y)] = True
                placed += 1

    def _pick_enemy_target(self, e: Enemy) -> tuple:
        for _ in range(10):
            x, y = random.choice(self.rooms).inner_rand()
            if self.tiles[y][x] == FLOOR:
                return x, y
        return e.x, e.y

    def _spread_poison(self):
        wave = self.turn // self.poison_interval
        if wave <= self.poison_wave:
            return
        self.poison_wave = wave
        changed = False
        for y in range(MAP_H):
            for x in range(MAP_W):
                if (self.tiles[y][x] == FLOOR
                        and self.edge_dist[y][x] <= wave
                        and (x, y) != self.shop_pos):
                    self.tiles[y][x] = POISON
                    changed = True
        if changed:
            self.log(T('msg_poison_spread'))
            pyxel.play(SFX_CH, SND_POISON)

    def _apply_poison(self):
        p = self.player
        if self.tiles[p.y][p.x] == POISON:
            p.hp -= 2
            pyxel.play(SFX_CH, SND_HIT)
            if p.hp <= 0:
                p.hp = 0
                self.running = False
                pyxel.stop(BGM_CH)
                pyxel.play(MUSIC_CH, SND_GAMEOVER)
                self.log(T('msg_poison_dead'))
                return
            self.log(FW(T('msg_poison_dmg', hp=p.hp, mhp=p.max_hp)))

    def _enemies_attack(self):
        p = self.player
        self._attacked_this_turn = set()
        for e in list(self.enemies.values()):
            dist = abs(e.x - p.x) + abs(e.y - p.y)
            attack_range = 3 if e.letter in ('M', 'W') else 1
            if dist <= attack_range:
                self._enemy_attack(e)
                self._attacked_this_turn.add((e.x, e.y))
                if not self.running:
                    return

    def _move_enemies(self):
        p = self.player
        occupied = set(self.enemies.keys())
        new_enemies = {}
        for (ex, ey), e in self.enemies.items():
            if self.turn % e.move_interval != 0:
                new_enemies[(ex, ey)] = e
                continue

            if (ex, ey) in self._attacked_this_turn:
                new_enemies[(ex, ey)] = e
                continue

            # Vは常にプレイヤーの現在地を目的地にする
            if e.letter == 'V':
                e.tx, e.ty = p.x, p.y
                e.path = []
            # 目的地が毒沼になった、または到達済みなら再抽選
            elif self.tiles[e.ty][e.tx] == POISON or (e.x == e.tx and e.y == e.ty):
                e.tx, e.ty = self._pick_enemy_target(e)
                e.path = []

            # キャッシュ済み経路がなければ A* で計算
            if not e.path:
                result = _astar(self.tiles, (e.x, e.y), (e.tx, e.ty))
                e.path = result if result else []

            if not e.path:
                # 経路なし → 来ターンに再抽選
                e.tx, e.ty = e.x, e.y
                new_enemies[(e.x, e.y)] = e
                continue

            nx, ny = e.path[0]

            if (nx, ny) in occupied or (nx, ny) == (p.x, p.y):
                # 他の敵または主人公がいる → 目的地を再抽選（Vはプレイヤーに再設定）
                if e.letter == 'V':
                    e.tx, e.ty = p.x, p.y
                else:
                    e.tx, e.ty = self._pick_enemy_target(e)
                e.path = []
                new_enemies[(e.x, e.y)] = e
                continue

            occupied.discard((e.x, e.y))
            occupied.add((nx, ny))
            e.x, e.y = nx, ny
            e.path.pop(0)
            new_enemies[(e.x, e.y)] = e

        self.enemies = new_enemies

    def log(self, msg: str):
        self.msgs.append(msg)

    def _combat(self, e: Enemy):
        p = self.player
        p_dmg = max(1, round((p.atk + p.weapon_atk - e.dfn + random.randint(-2, 2)) * random.uniform(0.85, 1.15)))
        e.hp -= p_dmg
        if e.hp <= 0:
            del self.enemies[(e.x, e.y)]
            p.gold += e.gold
            self.log(FW(T('msg_kill', L=e.letter, xp=e.xp, gold=e.gold)))
            levelup_msgs = p.gain_xp(e.xp)
            for m in levelup_msgs:
                self.log(m)
            if levelup_msgs:
                for i in range(len(levelup_msgs)):
                    self.levelup_sfx_queue.append(i * 23)
            else:
                pyxel.play(SFX_CH, SND_KILL)
            if e.letter == 'Z':
                self.won = True
                self.running = False
                pyxel.stop(BGM_CH)
                pyxel.play(MUSIC_CH, SND_CLEAR)
            elif e.letter == 'X':
                if p.weapon_atk < LEGENDARY_SWORD['atk']:
                    p.weapon_atk  = LEGENDARY_SWORD['atk']
                    p.weapon_name = LEGENDARY_SWORD['key']
                    self.log(FW(T('msg_legendary',
                                  name=T(LEGENDARY_SWORD['key']),
                                  atk=LEGENDARY_SWORD['atk'])))
                    pyxel.play(MUSIC_CH, SND_LEGENDARY)
                    self.levelup_sfx_queue.clear()
            elif e.letter in ('C', 'H', 'L', 'R', 'P'):
                self.potions[(e.x, e.y)] = True
        else:
            self.log(FW(T('msg_attack_hit', L=e.letter, dmg=p_dmg,
                          hp=e.hp, mhp=e.max_hp)))

    def _enemy_attack(self, e: Enemy):
        pyxel.play(SFX_CH, SND_HIT)
        p = self.player
        e_dmg = max(1, round((e.atk - p.dfn + random.randint(-2, 2)) * random.uniform(0.85, 1.15)))
        p.hp -= e_dmg
        if p.hp <= 0:
            p.hp = 0
            self.running = False
            pyxel.stop(BGM_CH)
            pyxel.play(MUSIC_CH, SND_GAMEOVER)
            self.log(FW(T('msg_enemy_atk_dead', L=e.letter, dmg=e_dmg, mhp=p.max_hp)))
            self.log(T('msg_player_dead'))
        else:
            self.log(FW(T('msg_enemy_atk', L=e.letter, dmg=e_dmg,
                          hp=p.hp, mhp=p.max_hp)))

    def move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
            return
        if self.tiles[ny][nx] == WALL:
            return
        if (nx, ny) in self.enemies:
            self._combat(self.enemies[(nx, ny)])
        else:
            self.player.x, self.player.y = nx, ny
            if (nx, ny) in self.potions:
                del self.potions[(nx, ny)]
                healed = self.player.max_hp - self.player.hp
                self.player.hp = self.player.max_hp
                pyxel.play(SFX_CH, SND_POTION)
                self.log(FW(T('msg_potion', healed=healed)))
            elif (nx, ny) == self.shop_pos:
                self.in_shop = True
        self.turn += 1
        self._spread_poison()
        self._apply_poison()
        if not self.running:
            return
        self._enemies_attack()
        if self.running:
            self._move_enemies()

    def wait(self):
        p = self.player
        if p.hp < p.max_hp:
            p.hp += 1
        self.turn += 1
        self._spread_poison()
        self._apply_poison()
        if not self.running:
            return
        self._enemies_attack()
        if self.running:
            self._move_enemies()


# ─── App (Pyxel) ──────────────────────────────────────────

class App:

    def __init__(self):
        pyxel.init(SCR_W, SCR_H, title="ALPHA ROGUE ROYAL", fps=30, quit_key=pyxel.KEY_NONE)
        pyxel.sounds[SND_KILL].mml("T200 @0 O4 L16 G E C")
        pyxel.sounds[SND_POISON].mml("T90 @0 O3 L4 D C")
        pyxel.sounds[SND_TITLE].mml("T150 @0 O4 L8 C E G >C2 <G4 E4 C4 E4 G4 >C1")
        pyxel.sounds[SND_GAMEOVER].mml("T100 @0 O4 L4 A G F E D C2")
        pyxel.sounds[SND_CLEAR].mml("T180 @0 O4 L8 C E G >C E G >C4 <G4 E4 C4 R4 E4 G4 >C4 E4 G4 >C2 <G2 >C1")
        pyxel.sounds[SND_POTION].mml("T200 @0 O5 L16 C E G >C")
        pyxel.sounds[SND_LEGENDARY].mml("T180 @0 O5 L16 C E G >C E G >C4 <B4 G4 >C1")
        pyxel.sounds[SND_HIT].mml("T180 @0 O4 L16 F D C")
        pyxel.sounds[SND_LEVELUP].mml("T160 @0 O5 L8 C E G >C")
        pyxel.sounds[SND_BGM].mml("T45 @4 O2 L1 A2 F2 G2 E2 R1 D2 E2 F2 A2 R1")
        self.font        = pyxel.Font(str(_font_path()))
        self.diff_idx    = 1
        self.game        = None
        self.show_info   = False
        self.show_log    = False
        self.log_offset  = 0
        self.confirm_quit = False
        self._go_to_title()
        pyxel.run(self.update, self.draw)

    def _t(self, x: int, y: int, s: str, col: int):
        """フォント付き text ショートハンド。座標は8の倍数に切り捨て。"""
        pyxel.text((x // 8) * 8, (y // 8) * 8, fw(s), col, self.font)

    # ── Input ─────────────────────────────────────────────

    def _go_to_title(self):
        self.title_cursor = getattr(self, 'diff_idx', 1)
        self.scene = 'title'
        pyxel.stop(BGM_CH)
        pyxel.play(MUSIC_CH, SND_TITLE)

    def _start_game(self):
        self.game = Game(diff_idx=self.diff_idx)
        self.scene = 'game'
        self.show_info  = True
        self.show_log   = False
        self.log_offset = 0
        pyxel.play(BGM_CH, SND_BGM, loop=True)

    def update(self):
        global _lang
        esc = pyxel.btnp(pyxel.KEY_ESCAPE)
        q   = pyxel.btnp(pyxel.KEY_Q)

        if self.confirm_quit:
            if pyxel.btnp(pyxel.KEY_Y):
                self.confirm_quit = False
                self._go_to_title()
            elif pyxel.btnp(pyxel.KEY_N) or esc or q:
                self.confirm_quit = False
            return

        if self.scene == 'title':
            lang_i  = len(DIFF_NAMES)      # Language 項目のインデックス
            exit_i  = len(DIFF_NAMES) + 1  # Quit 項目のインデックス
            n_items = len(DIFF_NAMES) + 2  # 難易度4 + Language + ゲーム終了
            if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_K) or pyxel.btnp(pyxel.KEY_W):
                self.title_cursor = (self.title_cursor - 1) % n_items
            if pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_J) or pyxel.btnp(pyxel.KEY_S):
                self.title_cursor = (self.title_cursor + 1) % n_items
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                if self.title_cursor == exit_i:
                    pyxel.quit()
                elif self.title_cursor == lang_i:
                    _lang = 'en' if _lang == 'ja' else 'ja'
                else:
                    self.diff_idx = self.title_cursor
                    self._start_game()
            if q or esc:
                pyxel.quit()
            return

        g   = self.game

        if g.levelup_sfx_queue:
            remaining = []
            for frames in g.levelup_sfx_queue:
                if frames <= 0:
                    pyxel.play(SFX_CH, SND_LEVELUP)
                else:
                    remaining.append(frames - 1)
            g.levelup_sfx_queue = remaining

        if self.show_info:
            if esc or q or pyxel.btnp(pyxel.KEY_I):
                self.show_info = False
            return

        if self.show_log:
            total   = len(g.msgs)
            max_off = max(0, total - LOG_LINES)
            if pyxel.btnp(pyxel.KEY_UP, 12, 4) or pyxel.btnp(pyxel.KEY_W, 12, 4):
                self.log_offset = min(self.log_offset + 1, max_off)
            if pyxel.btnp(pyxel.KEY_DOWN, 12, 4) or pyxel.btnp(pyxel.KEY_S, 12, 4):
                self.log_offset = max(0, self.log_offset - 1)
            if esc or q or pyxel.btnp(pyxel.KEY_M):
                self.show_log   = False
                self.log_offset = 0
            return

        if g.in_shop:
            if esc or q:
                g.in_shop = False
                return
            for i, w in enumerate(WEAPONS):
                if pyxel.btnp(getattr(pyxel, f'KEY_{i + 1}')):
                    p = g.player
                    if p.weapon_atk >= w['atk']:
                        g.log(FW(T('msg_lower_rank')))
                    elif p.gold >= w['price']:
                        p.gold -= w['price']
                        p.weapon_atk = w['atk']
                        p.weapon_name = w['key']
                        pyxel.play(SFX_CH, SND_POTION)
                        g.log(FW(T('msg_buy', name=T(w['key']), atk=w['atk'])))
                    else:
                        g.log(FW(T('msg_no_gold', need=w['price'] - p.gold)))
                    g.in_shop = False
                    return

        elif g.running:
            if q or esc:
                self.confirm_quit = True
                return
            if pyxel.btnp(pyxel.KEY_I):
                self.show_info = True
                return
            if pyxel.btnp(pyxel.KEY_M):
                self.show_log   = True
                self.log_offset = 0
                return
            _DIRS = (
                (pyxel.KEY_UP,     0, -1), (pyxel.KEY_K,  0, -1), (pyxel.KEY_W,  0, -1),
                (pyxel.KEY_DOWN,   0,  1), (pyxel.KEY_J,  0,  1), (pyxel.KEY_S,  0,  1),
                (pyxel.KEY_LEFT,  -1,  0), (pyxel.KEY_H, -1,  0), (pyxel.KEY_A, -1,  0),
                (pyxel.KEY_RIGHT,  1,  0), (pyxel.KEY_L,  1,  0), (pyxel.KEY_D,  1,  0),
            )
            for key, dx, dy in _DIRS:
                if pyxel.btnp(key, 12, 4):
                    g.move(dx, dy)
                    break
            else:
                if pyxel.btnp(pyxel.KEY_SPACE, 12, 4):
                    g.wait()

        else:
            if q or esc:
                self._go_to_title()
            if pyxel.btnp(pyxel.KEY_R) and not g.won:
                self._start_game()

    # ── Rendering ─────────────────────────────────────────

    def draw(self):
        pyxel.cls(_BG)
        if self.scene == 'title':
            self._draw_title()
            return
        g = self.game
        if self.show_info:
            self._draw_info()
        elif self.show_log:
            self._draw_log()
        elif g.in_shop:
            self._draw_shop()
        elif g.running:
            self._draw_map()
            self._draw_hud()
        else:
            self._draw_end()
        if self.confirm_quit:
            self._draw_confirm_quit()

    def _draw_title(self):
        t  = self._t
        cx = SCR_W // 2
        cy = SCR_H // 2

        title_raw = T('title_main')
        title_fw  = fw(title_raw)
        title_w   = _sw(title_raw)

        title_x = ((cx - title_w // 2) // 8) * 8
        title_y = ((cy - 56) // 8) * 8
        tiles_w = title_w // 8

        # wall border (2 tiles out)
        for dr in range(-2, 3):
            for dc in range(-2, tiles_w + 2):
                if dr in (-2, 2) or dc in (-2, tiles_w + 1):
                    if dr == -2 and dc == tiles_w // 2:
                        pyxel.text(
                            title_x + (tiles_w // 2) * 8,
                            title_y + dr * 8,
                            fw('@'), _GREEN, self.font
                        )
                    elif dr == -2 and dc == tiles_w // 2 - 1:
                        pyxel.text(
                            title_x + dc * 8,
                            title_y + dr * 8,
                            fw('.'), _FLOOR, self.font
                        )
                    elif dr == -2 and dc == tiles_w // 2 + 1:
                        pyxel.text(
                            title_x + dc * 8,
                            title_y + dr * 8,
                            fw('.'), _FLOOR, self.font
                        )
                    else:
                        pyxel.text(
                            title_x + dc * 8,
                            title_y + dr * 8,
                            fw('#'), _WALL, self.font
                        )

        # floor border (1 tile out)
        for dr in range(-1, 2):
            for dc in range(-1, tiles_w + 1):
                if dr in (-1, 1) or dc in (-1, tiles_w):
                    pyxel.text(title_x + dc * 8, title_y + dr * 8,
                               fw('.'), _FLOOR, self.font)

        # title logo: each char colored like its matching enemy letter
        x = title_x
        for ch in title_fw:
            cw = 8 if ord(ch) > 0x7E else 4
            cp = ord(ch) - 0xFEE0
            ascii_eq = chr(cp) if 0x21 <= cp <= 0x7E else ' '
            if ascii_eq.upper().isalpha():
                char_col = _ecolor(ascii_eq.upper())
            elif ascii_eq == '.':
                char_col = _FLOOR
            else:
                char_col = _DIM
            pyxel.text(x, title_y, ch, char_col, self.font)
            x += cw

        cursor_prefix_w = _sw(T('title_cursor_on') + ' ')
        for i, (name, _interval) in enumerate(zip(DIFF_NAMES, DIFF_INTERVALS)):
            col    = DIFF_COLORS[i]
            cur_on  = T('title_cursor_on')
            cur_off = T('title_cursor_off')
            cursor  = cur_on if i == self.title_cursor else cur_off
            label   = cursor + ' ' + name
            row_y   = cy + i * CHAR_H * 2
            label_x = cx - _sw(name) // 2 - cursor_prefix_w
            t(label_x, row_y, label, col if i == self.title_cursor else _DIM)

        lang_i     = len(DIFF_NAMES)
        cur_on     = T('title_cursor_on')
        cur_off    = T('title_cursor_off')
        lang_val   = 'EN' if _lang == 'en' else 'JA'
        lang_text  = 'Language: ' + lang_val
        cursor     = cur_on if self.title_cursor == lang_i else cur_off
        label      = cursor + ' ' + lang_text
        row_y      = cy + 8 + lang_i * CHAR_H * 2
        label_x    = cx - _sw(lang_text) // 2 - cursor_prefix_w
        t(label_x, row_y, label, _CYAN if self.title_cursor == lang_i else _DIM)

        exit_i     = len(DIFF_NAMES) + 1
        cur_on     = T('title_cursor_on')
        cur_off    = T('title_cursor_off')
        cursor     = cur_on if self.title_cursor == exit_i else cur_off
        exit_text  = T('title_exit')
        label      = cursor + ' ' + exit_text
        row_y      = cy + 8 + exit_i * CHAR_H * 2
        label_x    = cx - _sw(exit_text) // 2 - cursor_prefix_w
        t(label_x, row_y, label, _RED if self.title_cursor == exit_i else _DIM)

        hint = T('title_hint')
        t(cx - _sw(hint) // 2, SCR_H - CHAR_H, hint, _DIM)

    def _draw_map(self):
        g = self.game
        p = g.player
        cam_x = max(0, min(p.x - VP_W // 2, MAP_W - VP_W))
        cam_y = max(0, min(p.y - VP_H // 2, MAP_H - VP_H))

        for sy in range(VP_H):
            my = cam_y + sy
            for sx in range(VP_W):
                mx = cam_x + sx
                px_x = sx * CHAR_W
                px_y = sy * CHAR_H
                if not (0 <= mx < MAP_W and 0 <= my < MAP_H):
                    continue
                if mx == p.x and my == p.y:
                    self._t(px_x, px_y, fw('@'), _GREEN)
                elif (mx, my) in g.enemies:
                    e = g.enemies[(mx, my)]
                    self._t(px_x, px_y, fw(e.letter), _ecolor(e.letter))
                elif (mx, my) in g.potions:
                    self._t(px_x, px_y, fw('!'), _PINK)
                elif (mx, my) == g.shop_pos:
                    self._t(px_x, px_y, fw('$'), _YELLOW)
                elif g.tiles[my][mx] == POISON:
                    self._t(px_x, px_y, fw('~'), _POISON)
                elif g.tiles[my][mx] == WALL:
                    self._t(px_x, px_y, fw('#'), _WALL)
                else:
                    self._t(px_x, px_y, fw('.'), _FLOOR)

    def _draw_hud(self):
        g = self.game
        p = g.player

        y = HUD_Y  # 160

        # ── 行1: Lv(黄) / XP(青) / Gold(黄) / Turn(右端) ──
        lv_text  = FW(f'Lv.{p.level}')
        xp_text  = FW(f'  XP:{p.xp}/{p.xp_to_next()}')
        g_text   = FW(f'  G:{p.gold}')
        row1 = [(lv_text, _YELLOW), (xp_text, _CYAN), (g_text, _YELLOW)]
        x = 0
        for text, col in row1:
            self._t(x, y, text, col)
            x += _sw(text)
        turn_text = FW(T('hud_turn', n=g.turn))
        self._t(SCR_W - _sw(turn_text), y, turn_text, _DIM)
        y += CHAR_H

        # ── 行2: HP + ATK + DEF（同行）──
        self._t(0, y, T('hud_hp'), _RED)
        hp_label_w = _sw(T('hud_hp'))
        n = 9
        filled = pyxel.floor(n * max(0, p.hp) / p.max_hp) if p.max_hp else 0
        bar_head = fw('[') + fw('|') * filled
        bar_dots = fw('.') * (n - filled)
        bar_close = fw(']')
        bar_x = hp_label_w + 2
        self._t(bar_x, y, bar_head, _RED)
        self._t(bar_x + _sw(bar_head), y, bar_dots, _DIM)
        self._t(bar_x + _sw(bar_head + bar_dots), y, bar_close, _RED if filled == n else _DIM)
        bar_w = _sw(bar_head + bar_dots + bar_close)
        hp_text = FW(f'{p.hp}/{p.max_hp}')
        self._t(bar_x + bar_w + 2, y, hp_text, _WHITE)
        x = bar_x + bar_w + 2 + _sw(hp_text) + CHAR_W // 2
        atk = p.atk + p.weapon_atk
        atk_text = FW(f'ATK:{atk}')
        self._t(x, y, atk_text, _WHITE)
        x += _sw(atk_text)
        if p.weapon_atk:
            bonus_text = FW(f'(+{p.weapon_atk})')
            self._t(x, y, bonus_text, _YELLOW)
            x += _sw(bonus_text)
        x += CHAR_W
        self._t(x, y, FW(f'DEF:{p.dfn}'), _WHITE)
        y += CHAR_H * 2

        # ── 行4: 残敵一覧（色分け） ──
        label = T('hud_enemies')
        self._t(0, y, label, _WHITE)
        x = _sw(label)
        for letter in sorted(e.letter for e in g.enemies.values()):
            ch = fw(letter)
            self._t(x, y, ch, _ecolor(letter))
            x += _sw(ch)
        y += CHAR_H * 2

        # ── ログメッセージ 3行 ──
        for msg in list(g.msgs)[-3:]:
            self._t(0, y, msg, _WHITE)
            y += CHAR_H

        # ── 操作説明（2行）──
        y = pyxel.height - 16
        self._t(0, y, T('hud_controls'), _DIM)
        y += CHAR_H
        self._t(0, y, T('hud_controls2'), _DIM)

    def _draw_shop(self):
        g = self.game
        p = g.player
        cx = SCR_W // 2
        y  = SCR_H // 4

        shop_title = T('shop_title')
        self._t(cx - _sw(shop_title) // 2, y, shop_title, _YELLOW)
        y += CHAR_H * 2
        gold_text = FW(T('shop_gold', gold=p.gold))
        self._t(cx - _sw(gold_text) // 2, y, gold_text, _YELLOW)
        y += CHAR_H * 2

        for i, w in enumerate(WEAPONS):
            if w['atk'] <= p.weapon_atk:
                col = _DIM
            elif p.gold >= w['price']:
                col = _WHITE
            else:
                col = _DIM
            tag = T('shop_equipped') if p.weapon_name == w['key'] else ''
            wname = T(w['key'])
            label = FW(f'[{i+1}]') + ' ' + wname + '  ' + FW(f'ATK+{w["atk"]:2}  {w["price"]}G') + tag
            self._t(cx - _sw(label) // 2, y, label, col)
            y += CHAR_H

        y += CHAR_H
        hint = T('shop_hint')
        self._t(cx - _sw(hint) // 2, y, hint, _DIM)

    def _draw_info(self):
        pyxel.cls(_BG)
        t = self._t
        y = 0

        # ── ヘッダー ──
        diff_name = DIFF_NAMES[self.diff_idx]
        diff_col  = DIFF_COLORS[self.diff_idx]
        t(0, y, T('info_title'), _YELLOW)
        diff_str = FW(T('info_difficulty', name=diff_name))
        t(SCR_W // 2 - _sw(diff_str) // 2, y, diff_str, diff_col)
        y += CHAR_H
        t(0, y, '─' * (SCR_W // CHAR_W), _DIM)
        y += CHAR_H

        # ── 目的 ──
        t(0, y, T('info_obj_header'), _CYAN)
        y += CHAR_H
        t(CHAR_W, y, T('info_obj_1'), _WHITE)
        y += CHAR_H
        t(CHAR_W, y, T('info_obj_2'), _WHITE)
        y += CHAR_H
        poison_ivl = DIFF_INTERVALS[self.diff_idx]
        t(CHAR_W, y, FW(T('info_obj_3', ivl=poison_ivl)), _POISON)
        y += CHAR_H * 2

        # ── マスの意味 ──
        t(0, y, T('info_tiles_header'), _CYAN)
        y += CHAR_H
        # row 1
        t(CHAR_W,      y, fw('@'), _GREEN);  t(CHAR_W * 2,  y, T('info_tile_self'),   _WHITE)
        t(CHAR_W * 11, y, fw('!'), _PINK);   t(CHAR_W * 12, y, T('info_tile_potion'), _WHITE)
        t(CHAR_W * 22, y, fw('$'), _YELLOW); t(CHAR_W * 23, y, T('info_tile_shop'),   _WHITE)
        y += CHAR_H
        # row 2
        t(CHAR_W,      y, fw('~'), _POISON); t(CHAR_W * 2,  y, T('info_tile_poison'), _WHITE)
        t(CHAR_W * 11, y, fw('#'), _WALL);   t(CHAR_W * 12, y, T('info_tile_wall'),   _WHITE)
        t(CHAR_W * 22, y, fw('.'), _FLOOR);  t(CHAR_W * 23, y, T('info_tile_floor'),  _WHITE)
        y += CHAR_H * 2

        # ── 敵一覧 ──
        t(0, y, T('info_enemy_header'), _CYAN)
        y += CHAR_H
        col_w = 13 * CHAR_W   # 3列：x=0, 104, 208
        tbl = self.game.enemy_table
        for i, (L, (hp, atk, dfn, *_)) in enumerate(tbl.items()):
            cx = (i % 3) * col_w
            cy = y + (i // 3) * CHAR_H
            t(cx,          cy, fw(L), _ecolor(L))
            t(cx + CHAR_W, cy, fw(f':{hp:3}/{atk:2}/{dfn}'), _WHITE)
        y += CHAR_H

        # ── 特別な敵 ──
        drop_y = y + ((len(tbl) + 2) // 3) * CHAR_H + 2
        t(0, drop_y, T('info_special_header'), _CYAN)
        drop_y += CHAR_H
        for li, ltr in enumerate(('F', 'Q', 'S')):
            t(CHAR_W * (1 + li), drop_y, fw(ltr), _ecolor(ltr))
        t(CHAR_W * 4, drop_y, T('info_fast_desc'), _WHITE)
        drop_y += CHAR_H
        t(CHAR_W, drop_y, fw('V'), _ecolor('V'))
        t(CHAR_W * 2, drop_y, T('info_chase_desc'), _WHITE)
        drop_y += CHAR_H
        t(CHAR_W,          drop_y, fw('M'), _ecolor('M'))
        t(CHAR_W * 2,      drop_y, fw('W'), _ecolor('W'))
        t(CHAR_W * 3,      drop_y, T('info_range_desc'), _WHITE)
        drop_y += CHAR_H
        t(CHAR_W, drop_y, fw('X'), _RED)
        t(CHAR_W * 2, drop_y,
          T('info_drop_desc', name=T(LEGENDARY_SWORD['key'])),
          _WHITE)
        drop_y += CHAR_H

        # ── フッター ──
        foot_y = pyxel.height - CHAR_H * 2
        t(0, foot_y, '─' * (SCR_W // CHAR_W), _DIM)
        t(0, foot_y + CHAR_H, T('info_footer'), _DIM)

    def _draw_log(self):
        g       = self.game
        msgs    = list(g.msgs)
        total   = len(msgs)
        max_off = max(0, total - LOG_LINES)
        offset  = min(self.log_offset, max_off)
        end_idx = total - offset
        start_idx = max(0, end_idx - LOG_LINES)
        visible = msgs[start_idx:end_idx]

        pos_str = FW(f'({total - offset - len(visible) + 1}-{total - offset}/{total})')
        title   = T('log_header') + pos_str
        self._t(0, 0, title, _CYAN)
        for i, msg in enumerate(visible):
            self._t(0, CHAR_H * (i + 1), msg, _WHITE)
        self._t(0, SCR_H - CHAR_H, T('log_hint'), _DIM)

    def _draw_end(self):
        g = self.game
        p = g.player
        cx = SCR_W // 2
        cy = SCR_H // 2

        if g.won:
            msg = T('end_clear')
            sub = FW(T('end_clear_sub', lv=p.level))
            col = _YELLOW
        else:
            msg = T('end_over')
            sub = FW(T('end_over_sub', lv=p.level))
            col = _RED

        self._t(cx - _sw(msg) // 2, cy - 16, msg, col)
        self._t(cx - _sw(sub) // 2, cy - 8,  sub, _WHITE)
        diff_name = DIFF_NAMES[self.diff_idx]
        diff_col  = DIFF_COLORS[self.diff_idx]
        diff_text = FW(T('info_difficulty', name=diff_name))
        self._t(cx - _sw(diff_text) // 2, cy + 4, diff_text, diff_col)
        turn_text = FW(T('end_turn', n=g.turn))
        self._t(cx - _sw(turn_text) // 2, cy + 16, turn_text, _DIM)
        hint = T('end_hint_clear' if g.won else 'end_hint_over')
        self._t(cx - _sw(hint) // 2, cy + 28, hint, _DIM)

    def _draw_confirm_quit(self):
        cx, cy = SCR_W // 2, SCR_H // 2
        msg  = T('quit_msg')
        hint = T('quit_hint')
        bw = max(_sw(msg), _sw(hint)) + CHAR_W * 4
        bh = CHAR_H * 4
        bx, by = cx - bw // 2, cy - bh // 2
        pyxel.rect(bx - 1, by - 1, bw + 2, bh + 2, _DIM)
        pyxel.rect(bx, by, bw, bh, _BG)
        self._t(cx - _sw(msg)  // 2, by + CHAR_H,         msg,  _WHITE)
        self._t(cx - _sw(hint) // 2, by + CHAR_H * 2 + 2, hint, _DIM)


# ─── Error logging ────────────────────────────────────────

def _append_error(exc: BaseException):
    errors_path = Path(__file__).parent / 'ERRORS.md'
    date = datetime.date.today().isoformat()
    tb = traceback.format_exc()
    entry = (
        f"\n### [UNRESOLVED] {type(exc).__name__}: {exc}\n"
        f"- Date: {date}\n"
        f"- Context: ゲーム実行中のランタイムエラー\n"
        f"- Error: {type(exc).__name__}: {exc}\n"
        f"- Notes:\n```\n{tb}```\n"
    )
    text = errors_path.read_text(encoding='utf-8') if errors_path.exists() else ''
    text = text.replace('\n*(No errors recorded yet)*', '')
    errors_path.write_text(text + entry, encoding='utf-8')


if __name__ == '__main__':
    try:
        App()
    except Exception as e:
        _append_error(e)
        raise
