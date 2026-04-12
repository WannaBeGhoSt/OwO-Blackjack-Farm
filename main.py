"""
This code is only made for educational and practice purposes. 
Author and Async Development are not responsible for misuse.

GhoSty OwO BlackJack V1 Stable Build
Stable Alpha Build Version: 060426.1.0.0

GitHub: https://github.com/WannaBeGhoSt
Discord: https://discord.gg/SyMJymrV8x
"""

import discord
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init
import asyncio, json, re, os, time, unicodedata, sys
from datetime import datetime
import random

colorama_init()

if sys.version_info >= (3, 10):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

ghostyop = discord.Intents.all()
GhoStyyy = "."
ghosty = commands.Bot(
    command_prefix=GhoStyyy, case_insensitive=True, self_bot=True, intents=ghostyop, loop=loop
)
ghosty.remove_command("help")

@ghosty.event
async def on_ready():
    print(
        f"{Fore.LIGHTRED_EX} > GhoSty OwO BlackJack Farm v1 Connected To:{Style.RESET_ALL}",
        f"{Fore.LIGHTGREEN_EX}{ghosty.user}{Style.BRIGHT}{Style.RESET_ALL}",
    )
    print(f"{Fore.LIGHTRED_EX} > Released - 6 April 2026 [Join Async Development For Further Updates]{Style.RESET_ALL}")
    print(f"{Fore.CYAN} > https://discord.gg/SyMJymrV8x {Style.RESET_ALL}")

farming_active = False
farm_task = None
DATA_FILE = "data.json"
OWO_BOT_ID = 408785106942164992

def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    return {"TOKEN": "", "BET_SEQUENCE": "Low"}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "start_timestamp": None,
        "starting_balance": 0,
        "current_balance": 0,
        "wins": 0,
        "losses": 0,
        "ties": 0,
        "commands_used": 0,
        "seq_index": 0
    }

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()
config = load_config()

BET_SEQUENCES = {
    "Low": [2000, 3011, 7000, 15777, 29000, 58000, 115123],
    "High": [10000, 25000, 50000, 100000, 180000, 240000] # not recommended due to higher risk of hitting max bet limit, but included for variety
}

def parse_balance(text):
    match = re.search(r'__([\d,]+)__\s*cowoncy', text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    match = re.search(r'([\d,]+)\s*cowoncy', text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None

def extract_rank(card_str):
    rank_part = re.match(r"(\d+|a|j|q|k)", card_str, re.I)
    if not rank_part:
        return None
    rank = rank_part.group(1).lower()
    if rank == 'a':
        return 'A'
    elif rank in ['j', 'q', 'k']:
        return 10
    return int(rank)

def hand_value(cards):
    values = []
    aces = 0
    for c in cards:
        if c == 'A':
            aces += 1
            values.append(11)
        else:
            values.append(c)
    total = sum(values)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    soft = (aces > 0 and total <= 21)
    return total, soft

def basic_strategy(player_total, dealer_upcard, soft):
    dealer_val = dealer_upcard if isinstance(dealer_upcard, int) else (11 if dealer_upcard == 'A' else 10)
    if soft:
        if player_total >= 19:
            return 'stand'
        elif player_total == 18:
            return 'stand' if dealer_val <= 8 else 'hit'
        else:
            return 'hit'
    else:
        if player_total >= 17:
            return 'stand'
        elif player_total >= 13:
            return 'stand' if dealer_val <= 6 else 'hit'
        elif player_total == 12:
            return 'stand' if dealer_val in [4, 5, 6] else 'hit'
        else:
            return 'hit'

def decide(text):
    try:
        clean = text.replace("`", "")
        
        dealer_rank, player_values, soft = parse_game_state(clean)
        total, soft = hand_value(player_values)
        action = basic_strategy(total, dealer_rank, soft)
        print(f"{Fore.YELLOW}[DECIDE] Cards={player_values} total={total} soft={soft} dealer={dealer_rank} → {action}{Style.RESET_ALL}")
        return action
    except Exception as e:
        print(f"{Fore.RED}[DECIDE ERROR] {e}{Style.RESET_ALL}")
        return 'stand'

def parse_game_state(text):
    card_pattern = r":([^:]+):"
    dealer_match = re.search(r"Dealer \[([^+?]+)\+?\?\]", text)
    if not dealer_match:
        raise ValueError("Could not find dealer upcard")
    dealer_rank_str = dealer_match.group(1).strip()
    dealer_rank = extract_rank(dealer_rank_str)

    lines = text.splitlines()
    player_cards = []
    for i, line in enumerate(lines):
        if re.search(r"\[\d+\*?\]", line) and not re.search(r"[Dd]ealer", line):
            for j in range(i + 1, len(lines)):
                current_line = lines[j]
                if re.search(r"[Dd]ealer", current_line):
                    break
                if current_line.strip().startswith("```") or "game in progress" in current_line.lower():
                    break

                card_matches = re.findall(card_pattern, current_line)
                if card_matches:
                    player_cards.extend(card_matches)
                    continue

                if player_cards and current_line.strip():
                    break
            break

    if not player_cards:
        all_cards = re.findall(card_pattern, text)
        player_cards = [c for c in all_cards if c not in ["cardback", dealer_rank_str] and "?" not in c]

    values = []
    for card in player_cards:
        try:
            rank = extract_rank(card)
            values.append(rank)
        except Exception:
            continue

    total, soft = hand_value(values)
    return dealer_rank, values, soft

def get_owo_text(msg):
    parts = []
    if msg.content:
        parts.append(msg.content)
    if msg.embeds:
        embed = msg.embeds[0]
        if embed.author and embed.author.name:
            parts.append(embed.author.name)
        if embed.description:
            parts.append(embed.description)
        for field in embed.fields:
            if field.name:
                parts.append(field.name)
            if field.value:
                parts.append(field.value)
        if embed.footer and embed.footer.text:
            parts.append(embed.footer.text)
    return "\n".join(parts)

async def fetch_owo_balance(ctx):
    last_owo_id = None
    try:
        pre_history = await ctx.channel.history(limit=10).flatten()
        for m in pre_history:
            if m.author.id == OWO_BOT_ID:
                last_owo_id = m.id
                break
    except Exception as e:
        print(f"{Fore.RED}[snapshot error] {e}{Style.RESET_ALL}")

    await ctx.send("owo cash")

    for attempt in range(10):
        await asyncio.sleep(1.5)
        try:
            messages = await ctx.channel.history(limit=10).flatten()
            for msg in messages:
                if msg.author.id != OWO_BOT_ID:
                    continue
                if last_owo_id and msg.id <= last_owo_id:
                    continue
                text = get_owo_text(msg)
                if "cowoncy" in text.lower():
                    balance = parse_balance(text)
                    if balance is not None:
                        print(f"{Fore.GREEN}[BALANCE] Fetched: {balance:,}{Style.RESET_ALL}")
                        return balance
        except Exception as e:
            print(f"{Fore.RED}[fetch error] {e}{Style.RESET_ALL}")

    print(f"{Fore.RED}[BALANCE] No fresh cowoncy response found.{Style.RESET_ALL}")
    return None

async def check_warning(ctx):
    if not farming_active:
        return True
    try:
        messages = await ctx.channel.history(limit=15).flatten()
        for msg in messages:
            if msg.author.id != OWO_BOT_ID:
                continue
            msg_content = str(msg.content)
            if not msg_content:
                continue
            clean = unicodedata.normalize("NFKC", msg_content)
            clean = re.sub(r'[\u200B-\u200D\uFEFF]', '', clean).lower()
            if "captcha" in clean and "verify" in clean:
                match = re.search(r'[\(\[\{]?\s*(\d+)\s*[\/／]\s*5\s*[\)\]\}]?', clean)
                if match:
                    count = int(match.group(1))
                    print(f"{Fore.YELLOW}⚠️ CAPTCHA WARNING DETECTED: ({count}/5){Style.RESET_ALL}")
                    if count == 1:
                        return True
        return False
    except Exception as e:
        print(f"{Fore.RED}Warning check error: {e}{Style.RESET_ALL}")
        return False

async def run_farm(ctx):
    global farming_active, data
    
    farming_active = True
    print(f"{Fore.GREEN}[FARM] Started.{Style.RESET_ALL}")
    
    seq_idx = data.get("seq_index", 0)
    
    while farming_active:
        try:
            if await check_warning(ctx):
                farming_active = False
                print(f"{Fore.RED}[FARM] Stopped: CAPTCHA WARNING.{Style.RESET_ALL}")
                await ctx.send("⚠️ **__WARNING DETECTED!__** 🛑 Stopping | **SOLVE YOUR CAPTCHA FIRST** | Type `.start` again to restart.")
                return

            cfg = load_config()
            seq_name = cfg.get("BET_SEQUENCE", "Low")
            sequence = BET_SEQUENCES.get(seq_name, BET_SEQUENCES["Low"])
            
            if seq_idx >= len(sequence):
                seq_idx = 0
                
            bet = sequence[seq_idx]
            data["commands_used"] += 1
            save_data(data)
            
            await asyncio.sleep(random.uniform(4.1, 16.9))
            print(f"{Fore.CYAN}[ROUND] Betting {bet:,} | idx={seq_idx} | seq={seq_name}{Style.RESET_ALL}")
            
            last_owo_id = None
            try:
                pre_history = await ctx.channel.history(limit=10).flatten()
                for m in pre_history:
                    if m.author.id == OWO_BOT_ID:
                        last_owo_id = m.id
                        break
            except Exception as e:
                print(f"{Fore.RED}[snapshot error] {e}{Style.RESET_ALL}")
            
            await ctx.send(f"owo bj {bet}")
            
            msg = None
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    history = await ctx.channel.history(limit=10).flatten()
                    for m in history:
                        if m.author.id != OWO_BOT_ID:
                            continue
                        if last_owo_id and m.id <= last_owo_id:
                            continue
                        if not m.embeds:
                            continue
                        msg = m
                        break
                    if msg:
                        break
                except Exception as e:
                    print(f"{Fore.RED}[wait error] {e}{Style.RESET_ALL}")
                await asyncio.sleep(1.5)
            
            if not msg:
                print(f"{Fore.YELLOW}[FARM] No OwO embed found, retrying round...{Style.RESET_ALL}")
                await asyncio.sleep(5)
                continue
            last_reaction = None

            while farming_active:
                if await check_warning(ctx):
                    farming_active = False
                    await ctx.send("⚠️ **__CAPTCHA WARNING!__** Stopped. Solve & restart.")
                    return
                

                try:
                    await asyncio.sleep(2)
                    history = await ctx.channel.history(limit=10).flatten()
                    for m in history:
                        if m.id == msg.id:
                            msg = m
                            break
                except Exception as e:
                    print(f"{Fore.RED}[refetch error] {e}{Style.RESET_ALL}")
                
                full_text = get_owo_text(msg)
                
                footer = ""
                if msg.embeds and msg.embeds[0].footer:
                    footer = msg.embeds[0].footer.text or ""
                footer_lower = footer.lower().strip()
                
                
                if "game in progress" not in footer_lower:
                    if "won" in footer_lower and "lost" not in footer_lower:
                        data["wins"] += 1
                        seq_idx = 0
                        print(f"{Fore.GREEN}[WIN] +{bet:,} → reset to idx 0{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    elif "tied" in footer_lower or "both bust" in footer_lower:
                        data["ties"] += 1
                        print(f"{Fore.YELLOW}[TIE] {bet:,} → same idx {seq_idx}{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    elif "lost" in footer_lower or ("bust" in footer_lower and "both" not in footer_lower):
                        data["losses"] += 1
                        seq_idx += 1
                        print(f"{Fore.RED}[LOSS] -{bet:,} → next idx {seq_idx}{Style.RESET_ALL}")
                        data["seq_index"] = seq_idx
                        save_data(data)
                        break
                    else:
                        await asyncio.sleep(2)
                        continue
                

                action = decide(full_text)

                emoji = "👊" if action == "hit" else "🛑"

                if last_reaction:
                    try:
                        await msg.remove_reaction(last_reaction, ghosty.user)
                    except Exception as e:
                        print(f"{Fore.RED}[remove reaction error] {e}{Style.RESET_ALL}")

                try:
                    await msg.add_reaction(emoji)
                    last_reaction = emoji
                except Exception as e:
                    print(f"{Fore.RED}[react error] {e}{Style.RESET_ALL}")
                
                data["commands_used"] += 1
                save_data(data)
                await asyncio.sleep(3)
            
            await asyncio.sleep(4)          
        except Exception as e:
            print(f"{Fore.RED}[FARM ERROR] {e}{Style.RESET_ALL}")
            await asyncio.sleep(5)     
    print(f"{Fore.YELLOW}[FARM] Stopped.{Style.RESET_ALL}")

@ghosty.command()
async def start(ctx):
    global farming_active, farm_task, data
    if farming_active:
        return await ctx.send("⚠️ **GhoSty OwO BlackJack Worker is already running!**\n\n🛑 Please use `.stop` first, then `.start` to restart/force fix the worker.\nJoin the support server for better guidance.")
    print(f"{Fore.CYAN}[START] Initializing...{Style.RESET_ALL}")
    
    balance = await fetch_owo_balance(ctx)
    if balance is None:
        return await ctx.send("❌ Failed to fetch owo cash balance. Join the support server Async Development for troubleshooting.")
    data["starting_balance"] = balance
    data["current_balance"] = balance
    data["start_timestamp"] = datetime.now().isoformat()
    data["wins"] = 0
    data["losses"] = 0
    data["ties"] = 0
    data["commands_used"] = 0
    data["seq_index"] = 0
    save_data(data)
    
    print(f"{Fore.GREEN}[START] Balance saved: {balance:,}{Style.RESET_ALL}")
    await ctx.send(f"✅ GhoSty OwO BlackJack Farm Running. Starting balance: **__{balance:,}__** cowoncy.")
    
    farm_task = ghosty.loop.create_task(run_farm(ctx))

@ghosty.command()
async def stop(ctx):
    global farming_active
    if not farming_active:
        return await ctx.send("⏹ GhoSty OwO BlackJack Worker is not running.")
    farming_active = False
    await ctx.send("🛑 **__Stopped__** successfully.")
    print(f"{Fore.YELLOW}[STOP] User halted farm.{Style.RESET_ALL}")

@ghosty.command(aliases=["h"])
async def help(ctx):
    ghosty_help = """
    # 🤑 GhoSty OwO BlackJack Farm V1 🤑 
Prefix: `.`

**__Main__**
 🌟 Start: *Starts The AutoBot*
 🛑 Stop: *Stops The AutoBot*
 🔍 Status: *Shows Bot Status*
 ⚡ Bets: *Change bet sequence (Low/High)*

**__Features__**
 ⚠ Ban Bypass
 🚨 Auto Detects OwO Warnings
 ⏱ Auto Cut After 1 Warning
 💎 Auto Determine Hit/Stand
 👓 Tracking & Profit Calculator
 🏹 Fast And Secure
 🧠 Smart Dynamic
 🎯 Integrated Data with Advanced Decisions

**__Made with 💖 and 🧠 by GhoSty | [Async Development]__** 
"""
    await ctx.send(ghosty_help)  

@ghosty.command()
async def bets(ctx, seq_name=None):
    cfg = load_config()
    if not seq_name:
        current = cfg.get("BET_SEQUENCE", "Low")
        return await ctx.send(f"⚙️ Usage: `.bets Low` or `.bets High` (High sequence not recommended)\nCurrent: {current}")
    target = seq_name.capitalize()
    if target not in BET_SEQUENCES:
        return await ctx.send("❌ Invalid sequence. Use `Low` or `High`.")
    cfg["BET_SEQUENCE"] = target
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    await ctx.send(f"✅ Sequence updated to **__{target}__**. Applies on win/restart.")

@ghosty.command()
async def status(ctx):
    global data
    balance = await fetch_owo_balance(ctx)
    if balance is not None:
        data["current_balance"] = balance
        save_data(data)
        print(f"{Fore.GREEN}[STATUS] Current balance updated: {balance:,}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}[STATUS] Could not fetch balance, using saved value{Style.RESET_ALL}")
        
        
    profit = data["current_balance"] - data["starting_balance"]
    profit_str = f"+{profit:,}" if profit >= 0 else f"{profit:,}"
    status_icon = "🟢" if profit >= 0 else "🔴"
    total_games = data["wins"] + data["losses"] + data["ties"]
    win_pct = (data["wins"] / total_games * 100) if total_games > 0 else 0.0
    loss_pct = (data["losses"] / total_games * 100) if total_games > 0 else 0.0
    start_dt = datetime.fromisoformat(data["start_timestamp"]) if data["start_timestamp"] else datetime.now()
    elapsed = datetime.now() - start_dt
    h, rem = divmod(int(elapsed.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    
    
    cfg = load_config()
    text = (
        f"📊 **__GHOSTY OwO BLACKJACK FARM STATUS__**\n\n"
        f"{status_icon} Balance: Started **__{data['starting_balance']:,}__** | Current **__{data['current_balance']:,}__**\n"
        f"💸 Profit/Loss: **__{profit_str}__**\n\n"
        f"🎲 Results: Wins **__{data['wins']}__** ({win_pct:.1f}%) | Losses **__{data['losses']}__** ({loss_pct:.1f}%) | Ties **__{data['ties']}__**\n\n"
        f"⏱️ Runtime: Started **__{start_dt.strftime('%H:%M %m/%d')}__** | Elapsed **__{h}h {m}m {s}s__**\n\n"
        f"⚙️ Config: Sequence **__{cfg.get('BET_SEQUENCE', 'Low')}__** | Index **__{data.get('seq_index', 0)}__** | Commands **__{data['commands_used']}__**"
    )
    await ctx.send(text)

if __name__ == "__main__":
    config = load_config()
    if not os.path.exists("config.json") or not config.get("TOKEN"):
        print(f"{Fore.RED}❌ Missing config.json or TOKEN.{Style.RESET_ALL}")
        exit(1)
    print(
    f"""{Fore.BLUE}
    
           ▒▒                    ▒▒            ░░░░░░░░░░░  ░░░░░░░░░░░░░░░
        ▒▒▒▒▒▒▒   ▒▒▒     ▒▒▒▒ ▒▒▒▒▒▒▒▒      ░░░█████████░░░░█████████████░░ 
      ▒▒▒▒████▒▒ ▒▒█▒▒  ▒▒▒█▒▒▒▒░█████▒    ░░░████░░░░░░██░░░░░░░░░██░░░░░░   
     ▒▒▒▒██░░██▒▒▒██▒▒ ▒▒░██▒░▒██░░░░█▒     ░░░░░█░░░░░░░██░░░░░░░░██░░░  
     ▒▒██░░░░██▒▒██▒▒▒ ▒░██▒▒██░░░░░░█▒        ░░█░░░░░░░██░░░░░░░░██░░░ 
    ▒▒██░░█░░█▒▒▒█▒▒▒▒▒▒░█▒▒▒█░░░█░░██▒       ░░░█░░░░░░██░░░░░░░░░██░░░
    ▒▒█░░░░░░█▒▒█░░██░▒░█▒▒ ▒█░░░░░█▒▒▒       ░░██░░█████░░░░░░░░░░██░░░
    ▒▒█░░░░██▒▒▒████████▒▒  ▒██░░███▒▒        ░░█████████░░░░░░░░░███░░░
     ▒██████▒▒▒███▒▒▒██▒▒   ▒▒████▒▒▒         ░░█░░░░░░░██░░░░░░░░██░░░
    ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒     ▒▒▒▒▒▒          ░░██░░░░░░░██░░░█░░░░██░░░  
     ▒▒▒▒▒    ▒▒▒▒▒▒▒▒▒      ▒▒▒▒▒        ░░░░░█░░░░░░░███░░░█░░░██░░░     
               ▒▒   ▒▒        ▒▒         ░░███░█░░░░░███░░░░░█████░░░
                                          ░░░█████████░░░   ░░███░░░
                                          
               
                                                 Async Development Stable Build Version: 060426.1.0.0{Style.RESET_ALL}"""
    ) 
    print(f"{Fore.LIGHTRED_EX}\n\n > Made By GhoSty [Async Development]{Style.RESET_ALL}")
    ghosty.run(config["TOKEN"], bot=False)
