"""
Texas Hold'em Poker — GUI
python3 texas_holdem_gui.py
Features: hand history, hand strength, win odds, all-in, bot difficulty,
          animated dealing, sound effects (beeps), SB/BB system
"""
import tkinter as tk
from tkinter import simpledialog
import random, threading, time, math
from itertools import combinations
from collections import Counter

# ── COLORS ──────────────────────────────────
BG        = "#0a2e1a"
FELT      = "#0f3d22"
FELT_DARK = "#092618"
GOLD      = "#d4a843"
GOLD_LT   = "#f0c96a"
WHITE     = "#f5f0e8"
GRAY      = "#8a9a88"
RED_C     = "#e8402a"
CHIP_BLU  = "#2255cc"
CHIP_RED  = "#cc2222"
CARD_FACE = "#faf6ee"
CARD_BACK = "#1a3a8c"
RED_SUITS = {'♥','♦'}

# ── SOUND (cross-platform beeps via tkinter bell) ────
def snd_deal(root):
    try: root.bell()
    except: pass

def snd_chip(root):
    try: root.bell()
    except: pass

def snd_win(root):
    try:
        for _ in range(3): root.bell(); time.sleep(0.08)
    except: pass

# ── CARD ENGINE ─────────────────────────────
SUITS    = ['♠','♥','♦','♣']
RANKS    = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
RANK_VAL = {r:i for i,r in enumerate(RANKS,2)}

def make_deck():
    return [(r,s) for s in SUITS for r in RANKS]

def score_five(cards):
    vals  = sorted([RANK_VAL[c[0]] for c in cards],reverse=True)
    suits = [c[1] for c in cards]
    flush = len(set(suits))==1
    st = (vals==list(range(vals[0],vals[0]-5,-1)) or vals==[14,5,4,3,2])
    if st and vals==[14,5,4,3,2]: vals=[5,4,3,2,1]
    counts=Counter(vals); freq=sorted(counts.values(),reverse=True)
    grp=sorted(counts.keys(),key=lambda v:(counts[v],v),reverse=True)
    if st and flush: return (8,vals)
    if freq==[4,1]:  return (7,grp)
    if freq==[3,2]:  return (6,grp)
    if flush:        return (5,vals)
    if st:           return (4,vals)
    if freq[0]==3:   return (3,grp)
    if freq[:2]==[2,2]: return (2,grp)
    if freq[0]==2:   return (1,grp)
    return (0,vals)

def hand_rank(hand):
    best=None
    for five in combinations(hand,5):
        s=score_five(five)
        if best is None or s>best: best=s
    return best

HNAMES={8:'Straight Flush',7:'Four of a Kind',6:'Full House',5:'Flush',
        4:'Straight',3:'Three of a Kind',2:'Two Pair',1:'Pair',0:'High Card'}
HSTRENGTH={8:'Unbeatable!',7:'Monster hand!',6:'Very strong!',5:'Strong hand',
           4:'Decent hand',3:'Decent hand',2:'Okay hand',1:'Weak — be careful',0:'Trash — consider folding'}

def best_hand_name(hole,comm):
    r=hand_rank(hole+comm)
    return HNAMES[r[0]]

def estimate_strength(hole,comm,trials=120):
    wins=0
    deck=[c for c in make_deck() if c not in hole and c not in comm]
    needed=5-len(comm)
    for _ in range(trials):
        random.shuffle(deck)
        board=comm+deck[:needed]; opp=deck[needed:needed+2]
        if hand_rank(hole+board)>=hand_rank(opp+board): wins+=1
    return wins/trials

# ── BOT AI ──────────────────────────────────
DIFFICULTY_ADJ = {
    'easy':   {'fold_bias':0.10, 'bluff':0.04, 'raise_cap':0.20, 'skill':-0.08},
    'medium': {'fold_bias':0.05, 'bluff':0.06, 'raise_cap':0.30, 'skill': 0.00},
    'hard':   {'fold_bias':0.00, 'bluff':0.10, 'raise_cap':0.45, 'skill': 0.08},
}

def bot_decision(player,comm,pot,call_amt,min_raise,difficulty='medium'):
    s=estimate_strength(player['hand'],comm)
    persona_adj={'aggressive':0.10,'tight':-0.12,'loose':0.04}
    d=DIFFICULTY_ADJ.get(difficulty,DIFFICULTY_ADJ['medium'])
    s=max(0.0,min(1.0,s+persona_adj.get(player.get('persona',''),0)+d['skill']))
    stack=player['stack']
    bluff=random.random()<d['bluff']
    eff=min(1.0,s+0.20) if bluff else s

    def safe_raise():
        pot_bet=int(pot*random.uniform(0.5,0.75))
        capped=min(pot_bet,int(stack*d['raise_cap']),stack)
        return max(min_raise,capped)

    if call_amt==0:
        if eff>0.72 and stack>=min_raise and random.random()<0.6:
            return('raise',safe_raise())
        return('check',0)
    else:
        pot_odds=call_amt/(pot+call_amt) if (pot+call_amt)>0 else 1
        if eff<pot_odds+d['fold_bias'] and not bluff:
            return('fold',0)
        elif eff<0.55:
            if call_amt<=int(stack*0.10): return('call',min(call_amt,stack))
            return('fold',0)
        elif eff<0.75:
            return('call',min(call_amt,stack))
        else:
            if stack>=min_raise and random.random()<0.55:
                return('raise',safe_raise())
            return('call',min(call_amt,stack))

# ── DRAWING HELPERS ─────────────────────────
def rrect(c,x1,y1,x2,y2,r=10,**kw):
    pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,
         x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
    return c.create_polygon(pts,smooth=True,**kw)

def draw_card(c,x,y,rank=None,suit=None,face_up=True,w=58,h=82,tag=None):
    tg=(tag,) if tag else ()
    c.create_rectangle(x+3,y+3,x+w+3,y+h+3,fill="#222222",outline="",tags=tg)
    rrect(c,x,y,x+w,y+h,r=7,fill=CARD_FACE if face_up else CARD_BACK,
          outline=GOLD if face_up else "#0a1a5a",width=1.5,tags=tg)
    if face_up and rank and suit:
        col=RED_C if suit in RED_SUITS else "#111"
        c.create_text(x+9, y+13,text=rank,fill=col,font=("Georgia",12,"bold"),anchor="center",tags=tg)
        c.create_text(x+9, y+26,text=suit,fill=col,font=("Georgia",10),      anchor="center",tags=tg)
        c.create_text(x+w//2,y+h//2,text=suit,fill=col,font=("Georgia",28),  anchor="center",tags=tg)
        c.create_text(x+w-9,y+h-13,text=rank,fill=col,font=("Georgia",12,"bold"),anchor="center",tags=tg)
    elif not face_up:
        for i in range(3,w-6,7):
            c.create_line(x+i,y+4,x+4,y+i,   fill="#2244aa",width=1,tags=tg)
            c.create_line(x+w-4,y+i,x+i,y+h-4,fill="#2244aa",width=1,tags=tg)

def draw_chip(c,x,y,amt,color=CHIP_BLU,r=20,tag=None):
    tg=(tag,) if tag else ()
    c.create_oval(x-r,y-r+2,x+r,y+r+2,fill="#1a1a1a",outline="",tags=tg)
    c.create_oval(x-r,y-r,x+r,y+r,fill=color,outline=GOLD,width=2,tags=tg)
    c.create_oval(x-r+5,y-r+5,x+r-5,y+r-5,fill="",outline="#aaaaaa",width=1,tags=tg)
    c.create_text(x,y,text=f"${amt}",fill=WHITE,font=("Georgia",9,"bold"),tags=tg)

# ── SETUP DIALOG ────────────────────────────
def setup_dialog():
    root=tk.Tk(); root.withdraw()
    dlg=tk.Toplevel(root)
    dlg.title("Texas Hold'em — Setup")
    dlg.configure(bg=BG)
    dlg.resizable(False,False)
    sw,sh=420,340
    dlg.geometry(f"{sw}x{sh}+{(dlg.winfo_screenwidth()-sw)//2}+{(dlg.winfo_screenheight()-sh)//2}")
    dlg.grab_set()

    c=tk.Canvas(dlg,width=sw,height=sh,bg=BG,highlightthickness=0); c.pack(fill="both",expand=True)
    rrect(c,12,12,sw-12,sh-12,r=16,fill=FELT,outline=GOLD,width=2)
    c.create_text(sw//2,48,text="♠  TEXAS HOLD'EM  ♠",fill=GOLD,font=("Georgia",20,"bold"))
    c.create_text(sw//2,76,text="You vs Bot 1 • Bot 2 • Bot 3",fill=WHITE,font=("Georgia",11))

    lbl_cfg=[("Your name:",110),("Starting stack ($):",158),("Small blind ($):",200),("Difficulty:",242)]
    for txt,y in lbl_cfg:
        c.create_text(sw//2-90,y,text=txt,fill=GOLD_LT,font=("Georgia",10),anchor="e")

    name_var  =tk.StringVar(value="Player")
    stack_var =tk.StringVar(value="1000")
    sb_var    =tk.StringVar(value="25")
    diff_var  =tk.StringVar(value="medium")

    def entry(y,var,w=160):
        e=tk.Entry(dlg,textvariable=var,font=("Georgia",12),bg=FELT_DARK,fg=WHITE,
                   insertbackground=GOLD,relief="flat",bd=4,justify="center",width=14)
        e.place(x=sw//2-76,y=y-14,width=w,height=28)
        return e
    e_name =entry(110,name_var)
    e_stack=entry(158,stack_var)
    e_sb   =entry(200,sb_var)
    e_name.select_range(0,'end'); e_name.focus_set()

    # Difficulty radio buttons
    for i,(val,lbl) in enumerate([('easy','Easy'),('medium','Medium'),('hard','Hard')]):
        rb=tk.Radiobutton(dlg,text=lbl,variable=diff_var,value=val,
                          bg=FELT,fg=WHITE,selectcolor=FELT_DARK,
                          activebackground=FELT,activeforeground=GOLD,
                          font=("Georgia",10))
        rb.place(x=sw//2-60+i*80,y=228)

    result={}
    def start(_=None):
        try:
            stk=int(stack_var.get()); sb=int(sb_var.get())
            assert stk>0 and sb>0
        except:
            c.create_text(sw//2,290,text="Invalid numbers!",fill=RED_C,font=("Georgia",10))
            return
        result.update({'name':name_var.get().strip() or 'Player',
                       'stack':stk,'sb':sb,'bb':sb*2,'diff':diff_var.get()})
        dlg.destroy(); root.destroy()

    btn=tk.Button(dlg,text="SIT DOWN  ▶",font=("Georgia",13,"bold"),
                  bg="#1a5c2a",fg=WHITE,activebackground="#2a7a3a",
                  activeforeground=WHITE,relief="flat",bd=0,cursor="hand2",command=start)
    btn.place(x=sw//2-85,y=274,width=170,height=42)
    for e in (e_name,e_stack,e_sb): e.bind("<Return>",start)
    dlg.protocol("WM_DELETE_WINDOW",lambda:None)
    root.wait_window(dlg)
    return result

# ── MAIN APP ────────────────────────────────
class App:
    W,H=1160,780
    SEATS=[(580,600),(115,420),(580,100),(1045,420)]
    # card deal start (center of table)
    DEAL_SRC=(580,390)

    def __init__(self,root,cfg):
        self.root=root
        self.cfg=cfg
        self.diff=cfg['diff']
        self.start_stack=cfg['stack']
        self.SB=cfg['sb']; self.BB=cfg['bb']

        self.cv=tk.Canvas(root,width=self.W,height=self.H,bg=BG,highlightthickness=0)
        self.cv.pack(side="left",fill="both")

        # ── RIGHT PANEL (history + info) ──
        self.panel=tk.Frame(root,bg=FELT_DARK,width=220)
        self.panel.pack(side="right",fill="y")
        self.panel.pack_propagate(False)

        tk.Label(self.panel,text="HAND HISTORY",bg=FELT_DARK,fg=GOLD,
                 font=("Georgia",10,"bold"),pady=6).pack(fill="x")
        self.hist_box=tk.Text(self.panel,bg="#061a0e",fg=WHITE,font=("Georgia",9),
                              wrap="word",state="disabled",relief="flat",
                              height=28,width=26,padx=6,pady=4)
        self.hist_box.pack(fill="both",expand=True,padx=4,pady=(0,4))

        # Hand strength + odds panel
        tk.Label(self.panel,text="YOUR HAND",bg=FELT_DARK,fg=GOLD,
                 font=("Georgia",10,"bold"),pady=4).pack(fill="x")
        self.strength_var=tk.StringVar(value="—")
        self.odds_var    =tk.StringVar(value="—")
        tk.Label(self.panel,textvariable=self.strength_var,bg=FELT_DARK,fg=WHITE,
                 font=("Georgia",10,"bold"),wraplength=200,pady=2).pack(fill="x",padx=6)
        tk.Label(self.panel,textvariable=self.odds_var,bg=FELT_DARK,fg="#66dd66",
                 font=("Georgia",10),pady=2).pack(fill="x",padx=6)

        # Difficulty label
        tk.Label(self.panel,text=f"Difficulty: {self.diff.upper()}",
                 bg=FELT_DARK,fg=GRAY,font=("Georgia",8),pady=4).pack(fill="x",padx=6)

        self.logv=tk.StringVar(value="♠  Welcome!")
        tk.Label(root,textvariable=self.logv,bg=FELT_DARK,fg=GOLD,
                 font=("Georgia",12,"italic"),pady=5,padx=10,anchor="w").pack(
                 side="bottom",fill="x")

        self.NAME_POOL=[
            "James","Oliver","Liam","Noah","Ethan","Mason","Logan","Lucas",
            "Aiden","Jackson","Sophia","Emma","Olivia","Ava","Isabella",
            "Mia","Charlotte","Amelia","Harper","Evelyn","William","Henry",
            "Sebastian","Alexander","Daniel","Matthew","David","Joseph",
            "Carter","Owen","Wyatt","Luke","Dylan","Ryan","Nathan",
            "Zoe","Lily","Grace","Chloe","Victoria","Hannah","Nora",
            "Riley","Layla","Eleanor","Scarlett","Penelope","Aurora","Stella"
        ]
        bot_names=self._pick_bot_names(cfg['name'])
        self.players=[
            {'name':cfg['name'],   'stack':cfg['stack'],'human':True, 'hand':[],'folded':False,'bet':0,'persona':''},
            {'name':bot_names[0],  'stack':cfg['stack'],'human':False,'hand':[],'folded':False,'bet':0,'persona':'aggressive'},
            {'name':bot_names[1],  'stack':cfg['stack'],'human':False,'hand':[],'folded':False,'bet':0,'persona':'tight'},
            {'name':bot_names[2],  'stack':cfg['stack'],'human':False,'hand':[],'folded':False,'bet':0,'persona':'loose'},
        ]
        self.comm=[];self.pot=0;self.dealer=random.randint(0,3)
        self.hnum=0;self.hbet=0;self.aq=[];self.btns=[]
        self.rv=tk.IntVar(value=100)
        self.active_idx=None
        self.last_action={}
        self.animating=False
        # ── Stats ──
        me=self.players[0]
        self.stats={
            'hands_played':0,'hands_won':0,'total_won':0,'total_lost':0,
            'biggest_pot':0,'biggest_pot_hand':0,'folds':0,'raises':0,
            'calls':0,'checks':0,'showdowns':0,'showdowns_won':0,
            'all_ins':0,'start_stack':cfg['stack'],
        }

        self.redraw()
        root.update_idletasks(); root.update()
        root.after(300,self.start_hand)

    def _pick_bot_names(self,exclude=''):
        pool=[n for n in self.NAME_POOL if n.lower()!=exclude.lower()]
        return random.sample(pool,3)

    def _rename_bots(self):
        exclude_names={self.players[0]['name']}
        pool=[n for n in self.NAME_POOL if n not in exclude_names]
        new_names=random.sample(pool,3)
        for i,name in enumerate(new_names):
            self.players[i+1]['name']=name

    # ── LOGGING ─────────────────────────────
    def log(self,msg):
        self.logv.set(f"♠  {msg}")

    def hist(self,msg):
        self.hist_box.config(state="normal")
        self.hist_box.insert("end",msg+"\n")
        self.hist_box.see("end")
        self.hist_box.config(state="disabled")

    def hist_divider(self,txt=""):
        line=f"── {txt} ──" if txt else "─"*22
        self.hist(line)

    def update_hand_info(self):
        me=next(p for p in self.players if p['human'])
        if not me['hand']:
            self.strength_var.set("—"); self.odds_var.set("—"); return
        if len(self.comm)>=3:
            hn=best_hand_name(me['hand'],self.comm)
            rank=hand_rank(me['hand']+self.comm)
            tip=HSTRENGTH.get(rank[0],'')
            self.strength_var.set(f"{hn}\n{tip}")
        else:
            # Pre-flop: just show hole cards description
            r1,r2=me['hand'][0][0],me['hand'][1][0]
            s1,s2=me['hand'][0][1],me['hand'][1][1]
            suited=" suited" if s1==s2 else ""
            pair=" (Pocket Pair!)" if r1==r2 else ""
            self.strength_var.set(f"{r1}{s1} {r2}{s2}{suited}{pair}")
        # Odds (run in background)
        hand_snap=list(me['hand']); comm_snap=list(self.comm)
        def calc():
            pct=estimate_strength(hand_snap,comm_snap,trials=150)
            self.root.after(0,lambda:self.odds_var.set(f"Win odds: {pct*100:.0f}%"))
        if len(self.comm)>=3:
            threading.Thread(target=calc,daemon=True).start()
        else:
            self.odds_var.set("Odds shown after flop")

    # ── DRAWING ─────────────────────────────
    def redraw(self,reveal=False):
        c=self.cv; c.delete("all")
        c.create_oval(50,70,self.W-50,self.H-70,fill="#061a0e",outline="")
        c.create_oval(65,85,self.W-65,self.H-85,fill=FELT,outline=GOLD,width=4)
        c.create_oval(80,100,self.W-80,self.H-100,fill="",outline="#b8902e",width=1)
        c.create_text(self.W//2,self.H//2-8,text="♠  TEXAS HOLD'EM  ♠",
                      fill="#a07828",font=("Georgia",18,"bold"))
        # SB / BB labels
        c.create_text(self.W//2,self.H//2+130,
                      text=f"SB ${self.SB}  /  BB ${self.BB}",
                      fill="#8a7030",font=("Georgia",9))
        # Community
        n=len(self.comm); sx=self.W//2-(n*68)//2+4
        for i,card in enumerate(self.comm):
            draw_card(c,sx+i*68,self.H//2-44,rank=card[0],suit=card[1],face_up=True,tag="x")
        # Pot
        if self.pot>0:
            draw_chip(c,self.W//2,self.H//2+78,self.pot,color=CHIP_RED,r=26,tag="x")
            c.create_text(self.W//2,self.H//2+112,text="POT",fill=GOLD,font=("Georgia",9,"bold"))
        # Seats
        # Chip bet offsets toward table center per seat
        off=[(0,-86),(92,0),(0,86),(-92,0)]
        for i,p in enumerate(self.players):
            cx,cy=self.SEATS[i]
            fold=p['folded']
            is_active=(i==self.active_idx) and not fold

            # ── Cards ──
            # Only draw cards if dealt (hand is non-empty) AND animation done
            if p.get('hand') and not self.animating:
                show=p['human'] or (reveal and not fold)
                for j,card in enumerate(p['hand']):
                    ox2=-34 if j==0 else 6
                    draw_card(c,cx+ox2-28,cy-62,rank=card[0],suit=card[1],face_up=show,tag="x")

            # ── Nameplate: positioned beside cards ──
            # Seat 0 (bottom): cards left of center, nameplate to the right
            # Seat 1 (left):   cards above, nameplate to the right of cards
            # Seat 2 (top):    cards below nameplate (nameplate to the right)
            # Seat 3 (right):  nameplate to the LEFT of cards
            bw,bh=148,56
            # card area center is cx-14, cy-20 (approx). nameplate offsets per seat:
            np_offsets=[
                ( 68, -20),   # 0 bottom: nameplate right of cards
                ( 68, -20),   # 1 left:   nameplate right of cards
                ( 68, -20),   # 2 top:    nameplate right of cards
                (-68-bw, -20),# 3 right:  nameplate LEFT of cards
            ]
            npx = cx + np_offsets[i][0] - 28
            npy = cy + np_offsets[i][1] - 62

            x1,y1=npx,npy
            box_fill=FELT_DARK if not fold else "#0a1a0a"
            box_out="#ffee44" if is_active else (GOLD if p['human'] else (GRAY if not fold else "#333"))
            rrect(c,x1,y1,x1+bw,y1+bh,r=10,fill=box_fill,outline=box_out,
                  width=3 if is_active else 2)
            if is_active:
                rrect(c,x1+4,y1+4,x1+bw-4,y1+26,r=6,fill="#3a5a20",outline="")
            nc="#ffee44" if is_active else (GOLD if p['human'] else (WHITE if not fold else GRAY))
            c.create_text(x1+bw//2,y1+16,text=p['name'],fill=nc,font=("Georgia",11,"bold"))
            sc_col=GOLD_LT if not fold else GRAY
            status=""
            if fold and p['stack']==0: status="ELIMINATED"
            elif fold: status="FOLDED"
            if status:
                c.create_text(x1+bw//2,y1+36,text=status,fill="#aa1111",font=("Georgia",9,"bold"))
            else:
                c.create_text(x1+bw//2,y1+36,text=f"${p['stack']}",fill=sc_col,font=("Georgia",10))

            # Last action bubble — show below/above the card+nameplate cluster
            if i in self.last_action:
                la=self.last_action[i]
                la_col={"fold":"#dd4444","check":"#aaaaaa","call":"#66aaff",
                        "raise":"#ffcc00","blind":"#ffaa44","all-in":"#ff6600"
                        }.get(la.split()[0].lower(),"#cccccc")
                lox,loy=[(0,36),(0,-42),(0,36),(0,-42)][i]
                c.create_text(cx+lox,cy+loy,text=la,fill=la_col,font=("Georgia",10,"bold"))

            # Dealer button
            if i==self.dealer:
                c.create_oval(x1+bw-6,y1-12,x1+bw+11,y1+5,fill=GOLD,outline=WHITE,width=1.5)
                c.create_text(x1+bw+2,y1-4,text="D",fill="#111",font=("Georgia",8,"bold"))

            # Bet chip toward table center
            if p['bet']>0:
                ox,oy=off[i]; draw_chip(c,cx+ox,cy+oy,p['bet'],color=CHIP_BLU,r=18,tag="x")
        self._draw_scoreboard()
        c.update()

    def _draw_scoreboard(self):
        c=self.cv; c.delete("scoreboard")
        x,y=12,12; w,h=178,22+len(self.players)*23
        rrect(c,x,y,x+w,y+h,r=8,fill=FELT_DARK,outline=GOLD,width=1.5,tags="scoreboard")
        c.create_text(x+w//2,y+12,text="SCOREBOARD",fill=GOLD,
                      font=("Georgia",9,"bold"),tags="scoreboard")
        leader=max(self.players,key=lambda p:p['stack'])
        for i,p in enumerate(self.players):
            ty=y+28+i*23; is_me=p['human']
            if p is leader and p['stack']>0:
                rrect(c,x+5,ty-10,x+w-5,ty+11,r=4,fill="#1a4a28",outline="",tags="scoreboard")
            sym="★ " if p is leader and p['stack']>0 else "  "
            c.create_text(x+10,ty,text=f"{sym}{p['name']}",
                          fill=GOLD if is_me else WHITE,
                          font=("Georgia",10,"bold" if is_me else "normal"),
                          anchor="w",tags="scoreboard")
            sc=p['stack']
            scol="#66dd66" if sc>self.start_stack else ("#dd4444" if sc<self.start_stack else WHITE)
            if sc==0: scol=GRAY
            c.create_text(x+w-10,ty,text=f"${sc}",fill=scol,
                          font=("Georgia",10,"bold"),anchor="e",tags="scoreboard")

    # ── DEAL ANIMATION ──────────────────────
    def animate_deal(self,callback):
        """Slide cards from center to each player one by one."""
        me=next(p for p in self.players if p['human'])
        targets=[(i,p) for i,p in enumerate(self.players) if p['stack']>0]
        steps=10; delay=18
        card_items=[]

        def deal_one(ti):
            if ti>=len(targets)*2:
                for cid in card_items: self.cv.delete(cid)
                callback(); return
            pi=ti//2; ji=ti%2
            idx,p=targets[pi]
            cx,cy=self.SEATS[idx]
            tx=cx+(-34 if ji==0 else 6)-28; ty=cy-62
            sx,sy=self.DEAL_SRC
            cid=self.cv.create_rectangle(sx,sy,sx+58,sy+82,fill=CARD_BACK,outline=GOLD,width=1)
            card_items.append(cid)
            snd_deal(self.root)
            step=[0]
            def move():
                step[0]+=1
                t=step[0]/steps
                nx=sx+(tx-sx)*t; ny=sy+(ty-sy)*t
                self.cv.coords(cid,nx,ny,nx+58,ny+82)
                if step[0]<steps: self.root.after(delay,move)
                else: self.root.after(40,lambda:deal_one(ti+1))
            move()
        deal_one(0)

    # ── HAND FLOW ───────────────────────────
    def start_hand(self):
        me=next(p for p in self.players if p['human'])
        if me['stack']==0: self.game_over(); return
        alive=[p for p in self.players if p['stack']>0]
        if len(alive)==1 and alive[0]['human']: self.game_over(); return
        self.hnum+=1; self.comm=[]; self.pot=0
        self.last_action={}; self.active_idx=None
        self.stats['hands_played']+=1
        deck=make_deck(); random.shuffle(deck)
        for p in self.players:
            if p['stack']>0:
                p['hand']=[deck.pop(),deck.pop()]; p['folded']=False; p['bet']=0
            else:
                p['hand']=[]; p['folded']=True; p['bet']=0
        self.deck=deck
        self.hist_divider(f"Hand #{self.hnum}")
        alive_names=[p['name'] for p in self.players if p['stack']>0]
        self.hist(f"Players: {', '.join(alive_names)}")
        self.log(f"Hand #{self.hnum} — dealing cards...")
        self.strength_var.set("—"); self.odds_var.set("—")
        self.redraw()
        self.animating=True
        self.animate_deal(lambda: (setattr(self,'animating',False), self.redraw(), self.root.after(300,self.preflop)))

    def preflop(self):
        self.hbet=0
        alive_idxs=[i for i in range(4) if self.players[i]['stack']>0]
        if len(alive_idxs)<2: self.end_hand(); return
        def next_alive(after):
            for off in range(1,5):
                i=(after+off)%4
                if self.players[i]['stack']>0: return i
        sbi=next_alive(self.dealer); bbi=next_alive(sbi)
        sb,bb=self.players[sbi],self.players[bbi]
        for p,a,lbl in [(sb,self.SB,'SB'),(bb,self.BB,'BB')]:
            pd=min(a,p['stack']); p['stack']-=pd; p['bet']+=pd; self.pot+=pd
            pidx=self.players.index(p)
            self.last_action[pidx]=f"blind ${pd}"
            self.hist(f"{p['name']}: posts {lbl} ${pd}")
        self.hbet=bb['bet']
        self.log(f"Blinds — {sb['name']}: ${self.SB} (SB)   {bb['name']}: ${self.BB} (BB)")
        self.update_hand_info()
        self.redraw()
        start=next_alive(bbi); seen=set(); order=[]
        i=start
        for _ in range(4):
            if self.players[i]['stack']>0 and not self.players[i]['folded'] and i not in seen:
                order.append(i); seen.add(i)
            i=(i+1)%4
        self.aq=order
        self.root.after(500,self.next_action)

    def street(self,name,cards):
        self.comm+=cards
        for p in self.players: p['bet']=0
        self.hbet=0; self.last_action={}; self.active_idx=None
        self.hist_divider(name)
        comm_str=" ".join(f"{r}{s}" for r,s in self.comm)
        self.hist(f"Board: {comm_str}")
        self.log(f"— {name} —")
        self.update_hand_info()
        self.redraw()
        start=(self.dealer+1)%4
        self.aq=[(start+i)%4 for i in range(4)
                 if not self.players[(start+i)%4]['folded']
                 and self.players[(start+i)%4]['stack']>0]
        self.root.after(400,self.next_action)

    def next_action(self):
        active=[p for p in self.players if not p['folded']]
        if len(active)<=1: self.end_hand(); return
        if not self.aq: self.advance(); return
        idx=self.aq.pop(0); p=self.players[idx]
        if p['folded'] or p['stack']==0: self.root.after(50,self.next_action); return
        self.active_idx=idx; self.redraw()
        call=max(0,self.hbet-p['bet']); mr=max(self.BB,self.hbet*2)-p['bet']
        if p['human']:
            self.human_turn(p,call,mr)
        else:
            self.log(f"{p['name']} is thinking...")
            comm_snap=list(self.comm)
            p_snap=dict(p); p_snap['hand']=list(p['hand'])
            diff=self.diff
            def think(idx=idx,p=p,p_snap=p_snap,comm_snap=comm_snap,call=call,mr=mr):
                act,amt=bot_decision(p_snap,comm_snap,self.pot,call,mr,diff)
                delay=random.randint(600,1400)
                self.root.after(delay,lambda:self.apply(idx,p,act,amt,call,mr))
            threading.Thread(target=think,daemon=True).start()

    def advance(self):
        active=[p for p in self.players if not p['folded']]
        if len(active)<=1: self.end_hand(); return
        n=len(self.comm)
        if   n==0: self.root.after(700,lambda:self.street("Flop",[self.deck.pop(),self.deck.pop(),self.deck.pop()]))
        elif n==3: self.root.after(700,lambda:self.street("Turn",[self.deck.pop()]))
        elif n==4: self.root.after(700,lambda:self.street("River",[self.deck.pop()]))
        else: self.end_hand()

    def apply(self,idx,p,act,amt,call,mr):
        self.clear_btns(); self.active_idx=None; nm=p['name']
        if act=='fold':
            p['folded']=True; self.last_action[idx]="fold"
            self.log(f"❌ {nm} folds."); self.hist(f"{nm}: fold")
            if p['human']: self.stats['folds']+=1
        elif act=='check':
            self.last_action[idx]="check"
            self.log(f"✋ {nm} checks."); self.hist(f"{nm}: check")
            if p['human']: self.stats['checks']+=1
        elif act=='call':
            pd=min(call,p['stack']); p['stack']-=pd; p['bet']+=pd; self.pot+=pd
            self.last_action[idx]=f"call ${pd}"
            self.log(f"📞 {nm} calls ${pd}."); self.hist(f"{nm}: call ${pd}")
            snd_chip(self.root)
            if p['human']: self.stats['calls']+=1
        elif act=='raise':
            pd=min(call+amt,p['stack']); p['stack']-=pd; p['bet']+=pd; self.pot+=pd
            if p['bet']>self.hbet:
                self.hbet=p['bet']
                for i,q in enumerate(self.players):
                    if not q['folded'] and q!=p and q['stack']>0 and q['bet']<self.hbet and i not in self.aq:
                        self.aq.append(i)
            allin=" (ALL-IN!)" if p['stack']==0 else ""
            self.last_action[idx]=f"raise ${p['bet']}{allin}"
            self.log(f"💰 {nm} raises to ${p['bet']}!{allin}"); self.hist(f"{nm}: raise ${p['bet']}{allin}")
            snd_chip(self.root)
            if p['human']:
                self.stats['raises']+=1
                if p['stack']==0: self.stats['all_ins']+=1
        self.redraw(); self.root.after(350,self.next_action)

    # ── HUMAN BUTTONS ───────────────────────
    def human_turn(self,p,call,mr):
        self.clear_btns()
        bx,by=310,self.H-92; bw,bh=112,46
        pidx=self.players.index(p)

        def btn(x,y,txt,col,cmd,w=bw):
            r=rrect(self.cv,x,y,x+w,y+bh,r=8,fill=col,outline=GOLD,width=1.5)
            t=self.cv.create_text(x+w//2,y+bh//2,text=txt,fill=WHITE,font=("Georgia",12,"bold"))
            for item in (r,t):
                self.cv.tag_bind(item,"<Button-1>",lambda e,c=cmd:c())
            self.btns+=[r,t]

        btn(bx,by,"FOLD","#8b1a1a",lambda:self.apply(pidx,p,'fold',0,call,mr))
        lbl="CHECK" if call==0 else f"CALL ${call}"
        act='check' if call==0 else 'call'
        btn(bx+120,by,lbl,"#1a5c2a",lambda a=act,ca=call:self.apply(pidx,p,a,0,ca,mr))

        # ALL-IN button
        btn(bx+240,by,"ALL IN","#8b4a00",
            lambda:self.apply(pidx,p,'raise',p['stack']-call,call,mr),w=90)

        # Raise text entry
        rmin=max(mr,1); rmax=p['stack']
        self.rv.set(min(rmin,p['stack']))
        fr=tk.Frame(self.root,bg="#0d3520",bd=0)
        fr.place(x=bx+344,y=by-4,width=216,height=56)
        tk.Label(fr,text=f"Raise  (min ${rmin}, max ${rmax})",
                 bg="#0d3520",fg=GOLD,font=("Georgia",8)).pack(anchor="w",padx=6)
        entry=tk.Entry(fr,textvariable=self.rv,font=("Georgia",14,"bold"),
                       bg=FELT_DARK,fg=WHITE,insertbackground=GOLD,
                       relief="flat",justify="center",width=8)
        entry.pack(padx=6,pady=2)
        entry.select_range(0,'end')
        self.btns.append(fr)

        def do_raise():
            try: amt=int(self.rv.get())
            except: self.log("Enter a valid number!"); return
            if amt<rmin: self.log(f"Minimum raise is ${rmin}!"); return
            if amt>rmax: self.log(f"You only have ${rmax}!"); return
            self.apply(pidx,p,'raise',amt,call,mr)

        btn(bx+574,by,"RAISE","#7a5c1a",do_raise)
        entry.bind("<Return>",lambda e:do_raise())
        self.log(f"YOUR TURN   To call: ${call}   Stack: ${p['stack']}   [F]old [C]all/Check [R]aise [A]ll-in")
        # Keyboard shortcuts
        def kb_fold(e):  self.root.unbind('<f>'); self.root.unbind('<F>'); self.apply(pidx,p,'fold',0,call,mr)
        def kb_call(e):  self.root.unbind('<c>'); self.root.unbind('<C>'); self.apply(pidx,p,act,0,call,mr)
        def kb_allin(e): self.root.unbind('<a>'); self.root.unbind('<A>'); self.apply(pidx,p,'raise',p['stack']-call,call,mr)
        def kb_raise(e): entry.focus_set(); entry.select_range(0,'end')
        self.root.bind('<f>',kb_fold); self.root.bind('<F>',kb_fold)
        self.root.bind('<c>',kb_call); self.root.bind('<C>',kb_call)
        self.root.bind('<a>',kb_allin);self.root.bind('<A>',kb_allin)
        self.root.bind('<r>',kb_raise); self.root.bind('<R>',kb_raise)

    def clear_btns(self):
        for b in self.btns:
            if isinstance(b,tk.Frame): b.destroy()
            else: self.cv.delete(b)
        self.btns=[]
        for key in ('<f>','<F>','<c>','<C>','<a>','<A>','<r>','<R>'):
            try: self.root.unbind(key)
            except: pass

    # ── END HAND ────────────────────────────
    def end_hand(self):
        self.clear_btns(); self.active_idx=None
        active=[p for p in self.players if not p['folded']]
        if len(active)==1:
            w=active[0]; w['stack']+=self.pot
            self.log(f"🏆 {w['name']} wins ${self.pot} — everyone folded!")
            self.hist(f"→ {w['name']} wins ${self.pot} (uncontested)")
            if w['human']:
                self.stats['hands_won']+=1
                self.stats['total_won']+=self.pot
                if self.pot>self.stats['biggest_pot']:
                    self.stats['biggest_pot']=self.pot
                    self.stats['biggest_pot_hand']=self.hnum
            self.redraw()
        else:
            self.redraw(reveal=True)
            ranked=sorted([(hand_rank(p['hand']+self.comm),p) for p in active],
                          reverse=True,key=lambda x:x[0])
            best=ranked[0][0]; winners=[p for r,p in ranked if r==best]
            split=self.pot//len(winners)
            for w in winners: w['stack']+=split
            self.stats['showdowns']+=1
            self.hist_divider("Showdown")
            for r,p in ranked:
                hn=best_hand_name(p['hand'],self.comm)
                cs=" ".join(f"{c[0]}{c[1]}" for c in p['hand'])
                self.hist(f"{p['name']}: {cs} → {hn}")
            names=" & ".join(w['name'] for w in winners)
            hn=best_hand_name(winners[0]['hand'],self.comm)
            self.hist(f"→ {names} wins ${self.pot} with {hn}")
            self.log(f"🏆 {names} wins ${self.pot} with {hn}!")
            self.redraw(reveal=True)
            snd_win(self.root)
            me=next(p for p in self.players if p['human'])
            if me in winners:
                self.stats['hands_won']+=1; self.stats['showdowns_won']+=1
                self.stats['total_won']+=split
                if self.pot>self.stats['biggest_pot']:
                    self.stats['biggest_pot']=self.pot
                    self.stats['biggest_pot_hand']=self.hnum
        self.update_hand_info()
        for off in range(1,5):
            nxt=(self.dealer+off)%4
            if self.players[nxt]['stack']>0: self.dealer=nxt; break
        self.root.after(2800,self.deal_btn)

    def deal_btn(self):
        self.clear_btns()
        me=next(p for p in self.players if p['human'])
        if me['stack']==0: self.game_over(); return
        alive=[p for p in self.players if p['stack']>0]
        if len(alive)==1: self.game_over(); return
        x,y,w,h=self.W//2-95,self.H//2+118,190,50
        r=rrect(self.cv,x,y,x+w,y+h,r=10,fill="#1a5040",outline=GOLD,width=2)
        t=self.cv.create_text(x+w//2,y+h//2,text="▶  DEAL NEXT HAND",fill=WHITE,font=("Georgia",13,"bold"))
        for item in (r,t):
            self.cv.tag_bind(item,"<Button-1>",lambda e:self.start_hand())
        self.btns+=[r,t]

    def game_over(self):
        self.clear_btns()
        standings=sorted(self.players,key=lambda p:p['stack'],reverse=True)
        winner=standings[0]
        me=next(p for p in self.players if p['human'])
        headline="🏆 YOU WIN!" if winner['human'] else f"💸 {winner['name']} wins!"
        self.log(f"{headline}  Finished with ${winner['stack']}")
        self.hist_divider("GAME OVER")
        for p in standings: self.hist(f"{p['name']}: ${p['stack']}")
        self.redraw()

        # Build fun stats lines
        s=self.stats
        net=me['stack']-s['start_stack']
        net_str=f"+${net}" if net>=0 else f"-${abs(net)}"
        net_col="#66dd66" if net>=0 else "#dd4444"
        win_rate=f"{s['hands_won']/max(s['hands_played'],1)*100:.0f}%"
        sd_rate=f"{s['showdowns_won']}/{max(s['showdowns'],1)}" if s['showdowns']>0 else "0"
        aggr=s['raises']+s['calls']+s['checks']+s['folds']
        aggr_pct=f"{s['raises']/max(aggr,1)*100:.0f}%" if aggr>0 else "0%"
        fun_facts=[]
        if s['all_ins']>0: fun_facts.append(f"💀 Went all-in {s['all_ins']}x")
        if s['folds']>s['hands_played']*0.5: fun_facts.append("🐔 Bit of a folder...")
        elif s['raises']>s['hands_played']*0.4: fun_facts.append("🔥 Aggressive player!")
        if s['biggest_pot']>0: fun_facts.append(f"🏅 Biggest pot: ${s['biggest_pot']} (Hand #{s['biggest_pot_hand']})")
        if winner['human'] and net>500: fun_facts.append("💰 Crushed it!")
        elif not winner['human']: fun_facts.append("😬 The bots got you this time!")

        # Overlay — wider to fit stats
        bx,by,bw,bh=self.W//2-310,self.H//2-200,620,420
        rrect(self.cv,bx,by,bx+bw,by+bh,r=14,fill=FELT_DARK,outline=GOLD,width=3)
        self.cv.create_text(self.W//2,by+30,text="GAME OVER",fill=GOLD,font=("Georgia",26,"bold"))
        self.cv.create_text(self.W//2,by+60,text=headline,fill=WHITE,font=("Georgia",15,"bold"))

        # Standings (left column)
        self.cv.create_text(bx+80,by+90,text="── Standings ──",fill=GRAY,font=("Georgia",9),anchor="center")
        medals=["🥇","🥈","🥉","   "]
        for i,p in enumerate(standings):
            ty=by+112+i*28
            col=GOLD if p['human'] else WHITE
            self.cv.create_text(bx+20,ty,text=f"{medals[min(i,3)]} {p['name']}",
                                fill=col,font=("Georgia",11,"bold" if p['human'] else "normal"),anchor="w")
            sc=p['stack']
            scol="#66dd66" if sc==max(q['stack'] for q in self.players) else WHITE
            self.cv.create_text(bx+158,ty,text=f"${sc}",fill=scol,font=("Georgia",11,"bold"),anchor="e")

        # Divider
        self.cv.create_line(bx+175,by+85,bx+175,by+230,fill=GOLD+"88",width=1)

        # Your stats (right column)
        self.cv.create_text(bx+390,by+90,text="── Your Stats ──",fill=GRAY,font=("Georgia",9),anchor="center")
        stat_lines=[
            (f"Hands played:",     f"{s['hands_played']}",        WHITE),
            (f"Hands won:",        f"{s['hands_won']} ({win_rate})", "#66dd66" if s['hands_won']>0 else WHITE),
            (f"Showdowns won:",    sd_rate,                        "#66aaff"),
            (f"Net profit/loss:",  net_str,                        net_col),
            (f"Times raised:",     f"{s['raises']} ({aggr_pct})",  "#ffcc00"),
            (f"Times folded:",     f"{s['folds']}",                "#dd8888"),
        ]
        for j,(lbl,val,vc) in enumerate(stat_lines):
            ty=by+112+j*24
            self.cv.create_text(bx+188,ty,text=lbl,fill=GRAY,font=("Georgia",10),anchor="w")
            self.cv.create_text(bx+610-12,ty,text=val,fill=vc,font=("Georgia",10,"bold"),anchor="e")

        # Fun facts
        for k,fact in enumerate(fun_facts[:2]):
            self.cv.create_text(self.W//2,by+240+k*22,text=fact,fill=GOLD_LT,
                                font=("Georgia",10,"italic"),anchor="center")

        # Play again button
        x,y,w,h=self.W//2-85,by+bh-52,170,42
        r=rrect(self.cv,x,y,x+w,y+h,r=8,fill="#1a5c2a",outline=GOLD,width=1.5)
        t=self.cv.create_text(x+w//2,y+h//2,text="PLAY AGAIN",fill=WHITE,font=("Georgia",13,"bold"))
        for item in (r,t):
            self.cv.tag_bind(item,"<Button-1>",lambda e:self.reset())
        self.btns+=[r,t]
        snd_win(self.root)

    def reset(self):
        for p in self.players:
            p['stack']=self.start_stack;p['hand']=[];p['folded']=False;p['bet']=0
        self.comm=[];self.pot=0;self.hnum=0;self.dealer=random.randint(0,3)
        self.last_action={}; self.active_idx=None
        self.stats={k:0 for k in self.stats}; self.stats['start_stack']=self.start_stack
        bot_names=self._pick_bot_names(self.players[0]['name'])
        for i,nm in enumerate(bot_names): self.players[i+1]['name']=nm
        self.hist_box.config(state="normal"); self.hist_box.delete("1.0","end")
        self.hist_box.config(state="disabled")
        self.clear_btns(); self.redraw()
        self.root.after(300,self.start_hand)

# ── LAUNCH ──────────────────────────────────
if __name__=="__main__":
    cfg=setup_dialog()
    if not cfg: exit()
    root=tk.Tk()
    root.title(f"♠ Texas Hold'em — {cfg['name']} ♥")
    root.configure(bg=BG)
    root.resizable(False,False)
    ww,wh=1380,840
    root.geometry(f"{ww}x{wh}+{(root.winfo_screenwidth()-ww)//2}+{(root.winfo_screenheight()-wh)//2}")
    App(root,cfg)
    root.mainloop()
