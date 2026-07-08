"""
This code is only made for educational and practice purposes. 
Author and Async Development are not responsible for misuse.

GhoSty OwO BlackJack V2.1 Stable Build
Stable Alpha Build Version: 080726.2.1.0

GitHub: https://github.com/WannaBeGhoSt
Discord: https://discord.gg/mSasJWY8Gw
"""

import discord
from discord import emoji
from discord.ext import commands
from colorama import Fore, Style, init as colorama_init
import asyncio, json, re, os, time, unicodedata, sys
from datetime import datetime, timedelta
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
        f"{Fore.LIGHTRED_EX} > GhoSty OwO BlackJack Farm v2.1 Connected To:{Style.RESET_ALL}",
        f"{Fore.LIGHTGREEN_EX}{ghosty.user}{Style.BRIGHT}{Style.RESET_ALL}",
    )
    print(f"{Fore.LIGHTRED_EX} > Released - 8 July 2026 [Join Async Development For Further Updates]{Style.RESET_ALL}")
    print(f"{Fore.CYAN} > https://discord.gg/mSasJWY8Gw {Style.RESET_ALL}")

farming_active = False
farm_task = None
DATA_FILE = "data.json"
OWO_BOT_ID = 408785106942164992

GHOSTY_LIFETIME_MODULE = {
    "action_delay_min": 7.0,
    "action_delay_max": 22.0,
    "random_long_delay_min": 250,
    "random_long_delay_max": 550,
    "reaction_delay_min": 1.2,
    "reaction_delay_max": 2.8,
    "work_duration_min": 3 * 3600,  
    "work_duration_max": 5 * 3600,  
    "break_duration_min": 9 * 3600, 
    "break_duration_max": 14 * 3600,
    "day_skip_threshold": 3,
    "day_skip_duration": 24 * 3600,
}
_sleep_mode = False
_farming_start_time = None
_lifetime_cycle_start_time = None
_lifetime_work_cycles = 0
_lifetime_day_skip_active = False

def parse_time_to_seconds(time_str):
    seconds = 0
    time_str = time_str.lower()
    hours = re.search(r'(\d+)h', time_str)
    mins = re.search(r'(\d+)m', time_str)
    secs = re.search(r'(\d+)s', time_str)
    if hours: seconds += int(hours.group(1)) * 3600
    if mins: seconds += int(mins.group(1)) * 60
    if secs: seconds += int(secs.group(1))
    return seconds

def parse_amount(amt_str):
    amt_str = amt_str.lower().replace(",", "")
    if amt_str.endswith('k'):
        return int(float(amt_str[:-1]) * 1000)
    elif amt_str.endswith('m'):
        return int(float(amt_str[:-1]) * 1000000)
    else:
        return int(amt_str)

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
        "seq_index": 0,
        "timer_end": None,
        "stop_on_loss_limit": None,
        "internal_profit": 0
    }

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load_data()
data["timer_end"] = None 
save_data(data)
config = load_config()

BET_SEQUENCES = {
    # "Low": [2000, 3011, 7000, 15777, 29000, 58000, 115123], old low sequence not in use
    "Low": [488, 976, 1952, 3904, 7808, 15616, 31232, 62464, 124928, 249856],
    "High": [10000, 25000, 50000, 100000, 180000, 240000] # not recommended due to higher risk of losing, but included for variety
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
            for j in range(i + 1, min(i + 3, len(lines))):
                card_matches = re.findall(card_pattern, lines[j])
                for cm in card_matches:
                    player_cards.append(cm)
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
    for attempt in range(3):
        try:
            pre_history = await ctx.channel.history(limit=10).flatten()
            for m in pre_history:
                if m.author.id == OWO_BOT_ID:
                    last_owo_id = m.id
                    break
            break
        except Exception as e:
            print(f"{Fore.RED}[balance snapshot error] {e}. Retrying {attempt + 1}/3...{Style.RESET_ALL}")
            await asyncio.sleep(2)

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
    global _sleep_mode, _farming_start_time, _lifetime_cycle_start_time
    global _lifetime_work_cycles, _lifetime_day_skip_active

    farming_active = True
    _sleep_mode = False
    _farming_start_time = datetime.now()
    _lifetime_cycle_start_time = datetime.now()
    _lifetime_work_cycles = 0
    _lifetime_day_skip_active = False
    print(f"{Fore.GREEN}[FARM] Started.{Style.RESET_ALL}")
    
    seq_idx = data.get("seq_index", 0)
    
    while farming_active:
        try:
            if not _sleep_mode:
                current_time = datetime.now()
                if not _lifetime_day_skip_active:
                    if _lifetime_work_cycles >= GHOSTY_LIFETIME_MODULE["day_skip_threshold"] and random.random() < 0.5:
                        _lifetime_day_skip_active = True
                        day_skip_duration = GHOSTY_LIFETIME_MODULE["day_skip_duration"]
                        skip_end_time = current_time + timedelta(seconds=day_skip_duration)
                        await ctx.send(
                            f"😴 **SMART SLEEP: DAY SKIP ACTIVATED** 🌙\n"
                            f"Full 24-hour rest for detection bypass. Will resume at **{skip_end_time.strftime('%d-%b-%Y %I:%M:%S %p')}**"
                        )
                        print(f"{Fore.YELLOW}[SMART SLEEP] DAY SKIP started — 24h rest{Style.RESET_ALL}")
                        await asyncio.sleep(day_skip_duration)
                        _lifetime_day_skip_active = False
                        _lifetime_work_cycles = 0
                        _lifetime_cycle_start_time = datetime.now()
                        await ctx.send("⏰ **SMART SLEEP: RESUMING AFTER DAY SKIP** 🚀")
                        print(f"{Fore.GREEN}[SMART SLEEP] DAY SKIP ENDED — resuming{Style.RESET_ALL}")
                        continue



                if _lifetime_cycle_start_time is not None:
                    work_duration = random.uniform(
                        GHOSTY_LIFETIME_MODULE["work_duration_min"],
                        GHOSTY_LIFETIME_MODULE["work_duration_max"],
                    )
                    elapsed_cycle_time = (current_time - _lifetime_cycle_start_time).total_seconds()

                    if elapsed_cycle_time >= work_duration:
                        _sleep_mode = True
                        break_duration = random.uniform(
                            GHOSTY_LIFETIME_MODULE["break_duration_min"],
                            GHOSTY_LIFETIME_MODULE["break_duration_max"],
                        )
                        sleep_end_time = current_time + timedelta(seconds=break_duration)
                        _lifetime_work_cycles += 1
                        hours, remainder = divmod(int(break_duration), 3600)
                        mins = remainder // 60
                        await ctx.send(
                            f"😴 **SMART SLEEP: BREAK TIME** 🌙\n"
                            f"Work cycle #{_lifetime_work_cycles} complete. Breaking for {hours}h {mins}m. "
                            f"Resume at **{sleep_end_time.strftime('%d-%b-%Y %I:%M:%S %p')}**"
                        )
                        print(f"{Fore.YELLOW}[SMART SLEEP] BREAK #{_lifetime_work_cycles}: {hours}h {mins}m{Style.RESET_ALL}")
                        await asyncio.sleep(break_duration)
                        _sleep_mode = False
                        _lifetime_cycle_start_time = datetime.now()
                        await ctx.send(
                            f"⏰ **SMART SLEEP: BACK TO WORK** 🚀\n"
                            f"Starting work cycle #{_lifetime_work_cycles + 1}"
                        )
                        print(f"{Fore.GREEN}[SMART SLEEP] WORK CYCLE #{_lifetime_work_cycles + 1} started{Style.RESET_ALL}")
                        continue

            if _sleep_mode:
                await asyncio.sleep(10)
                continue


            if data.get("timer_end") and time.time() >= data["timer_end"]:
                if seq_idx == 0:
                    farming_active = False
                    data["timer_end"] = None
                    save_data(data)
                    await ctx.send("⏳ **Timer ended!** Farm stopped safely after a win.")
                    print(f"{Fore.YELLOW}[TIMER] Farm stopped naturally.{Style.RESET_ALL}")
                    return
                else:
                    print(f"{Fore.YELLOW}[TIMER] Time is up, but currently in a losing streak. Playing until next win to stop.{Style.RESET_ALL}")
            cfg = load_config()
            seq_name = cfg.get("BET_SEQUENCE", "Low")
            sol_limit = data.get("stop_on_loss_limit")
            if not sol_limit:
                sol_limit = 499224 if seq_name == "Low" else 605000
                
            if data.get("internal_profit", 0) < 0 and abs(data["internal_profit"]) >= sol_limit:
                farming_active = False
                await ctx.send(f"🛑 **Stop-on-Loss Triggered!** Net loss reached **__{abs(data['internal_profit']):,}__**. Farm stopped.")
                print(f"{Fore.RED}[STOP ON LOSS] Farm stopped due to max loss limit.{Style.RESET_ALL}")
                return

            if await check_warning(ctx):
                farming_active = False
                print(f"{Fore.RED}[FARM] Stopped: CAPTCHA WARNING.{Style.RESET_ALL}")
                await ctx.send("⚠️ **__WARNING DETECTED!__** 🛑 Stopping | **SOLVE YOUR CAPTCHA FIRST** | Type `.start` again to restart.")
                return

            sequence = BET_SEQUENCES.get(seq_name, BET_SEQUENCES["Low"])
            
            if seq_idx >= len(sequence):
                seq_idx = 0
                
            bet = sequence[seq_idx]
            data["commands_used"] += 1
            save_data(data)
            gap = random.uniform(
                GHOSTY_LIFETIME_MODULE["action_delay_min"],
                GHOSTY_LIFETIME_MODULE["action_delay_max"],
            )
            if random.random() < 0.05:
                gap += random.uniform(
                    GHOSTY_LIFETIME_MODULE["random_long_delay_min"],
                    GHOSTY_LIFETIME_MODULE["random_long_delay_max"],
                )
            await asyncio.sleep(gap)
            print(f"{Fore.CYAN}[ROUND] Betting {bet:,} | idx={seq_idx} | seq={seq_name}{Style.RESET_ALL}")
            
            last_owo_id = None
            for attempt in range(3):
                try:
                    pre_history = await ctx.channel.history(limit=10).flatten()
                    for m in pre_history:
                        if m.author.id == OWO_BOT_ID:
                            last_owo_id = m.id
                            break
                    break 
                except Exception as e:
                    print(f"{Fore.RED}[farm snapshot error] {e}. Retrying {attempt + 1}/3...{Style.RESET_ALL}")
                    await asyncio.sleep(2)
            
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
            stuck_counter = 0

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
                    print(f"{Fore.RED}[Network Drop] {e}. Waiting 10s to force resume...{Style.RESET_ALL}")
                    await asyncio.sleep(10)
                    break
                
                full_text = get_owo_text(msg)
                
                footer = ""
                if msg.embeds and msg.embeds[0].footer:
                    footer = msg.embeds[0].footer.text or ""
                footer_lower = footer.lower().strip()
                
                if "game in progress" not in footer_lower and "resuming" not in footer_lower:
                    if "won" in footer_lower and "lost" not in footer_lower:
                        data["wins"] += 1
                        data["internal_profit"] = data.get("internal_profit", 0) + bet
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
                        data["internal_profit"] = data.get("internal_profit", 0) - bet
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
                await asyncio.sleep(random.uniform(
                    GHOSTY_LIFETIME_MODULE["reaction_delay_min"],
                    GHOSTY_LIFETIME_MODULE["reaction_delay_max"],
                ))

                if last_reaction and last_reaction == emoji:
                    try:
                        await msg.remove_reaction(emoji, ghosty.user)
                        last_reaction = None  
                    except Exception as e:
                        print(f"{Fore.RED}[remove reaction error] {e}{Style.RESET_ALL}")
                elif last_reaction and last_reaction != emoji:
                    try:
                        await msg.add_reaction(emoji)
                        last_reaction = emoji
                    except Exception as e:
                        print(f"{Fore.RED}[react error] {e}{Style.RESET_ALL}")
                else:
                    try:
                        await msg.add_reaction(emoji)
                        last_reaction = emoji
                    except Exception as e:
                        print(f"{Fore.RED}[react error] {e}{Style.RESET_ALL}")
                
                stuck_counter += 1
                if stuck_counter >= 5:
                    print(f"{Fore.YELLOW}[STUCK] Game unresponsive after 5 attempts. Waiting 10s to force resume...{Style.RESET_ALL}")
                    await asyncio.sleep(10)
                    break

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
    data["internal_profit"] = 0
    save_data(data)
    
    print(f"{Fore.GREEN}[START] Balance saved: {balance:,}{Style.RESET_ALL}")
    await ctx.send(f"✅ GhoSty OwO BlackJack Farm Running. Starting balance: **__{balance:,}__** cowoncy.")
    
    farm_task = ghosty.loop.create_task(run_farm(ctx))

@ghosty.command()
async def stop(ctx):
    global farming_active, data
    if not farming_active:
        return await ctx.send("⏹ GhoSty OwO BlackJack Worker is not running.")
    farming_active = False
    data["timer_end"] = None
    save_data(data)
    await ctx.send("🛑 **__Stopped__** successfully. Timer also cleared if active.")
    print(f"{Fore.YELLOW}[STOP] User halted farm.{Style.RESET_ALL}")

@ghosty.command()
async def timer(ctx, *, time_input=None):
    global data
    if not time_input:
        return await ctx.send("⚙️ Usage: `.timer 1h 30m 20s`, `.timer 45m`, etc.")
    
    seconds = parse_time_to_seconds(time_input)
    if seconds < 300:
        return await ctx.send("❌ Error: Minimum timer duration allowed is 5 minutes.")
        
    data["timer_end"] = time.time() + seconds
    save_data(data)
    await ctx.send(f"✅ Timer set for **{time_input}**. Farm will naturally stop after this time (and after winning the active sequence streak).")

@ghosty.command()
async def stoponloss(ctx, amount_str=None):
    global data
    if not amount_str:
        return await ctx.send("⚙️ Usage: `.stoponloss 100k`, `.stoponloss 1m`, `.stoponloss 500k`")
        
    try:
        limit = parse_amount(amount_str)
        if limit < 100000:
            return await ctx.send("❌ Error: Minimum stop on loss amount allowed is 100k.")
            
        data["stop_on_loss_limit"] = limit
        save_data(data)
        await ctx.send(f"✅ Stop on Loss limit set successfully to **__{limit:,}__** cowoncy.")
    except Exception:
        await ctx.send("❌ Invalid format! Please use formats like `500k`, `1m`, `100k`, etc.")

@ghosty.command(aliases=["h"])
async def help(ctx):
    ghosty_help = """
    # 🤑 GhoSty OwO BlackJack Farm V2.1 🤑 
Prefix: `.`

**__Main__**
 🌟 Start: *Starts The AutoBot*
 🛑 Stop: *Stops The AutoBot*
 🔍 Status: *Shows Bot Status*
 ⚡ Bets: *Change bet sequence (Low/High)*
 ⏳ Timer: *Set duration to auto-stop (.timer 45m)*
 📉 StopOnLoss: *Set max loss limit (.stoponloss 1m)*

**__Features__**
 ⚠ Ban Bypass
 🚨 Auto Detects OwO Warnings
 ⏱ Auto Cut After 1 Warning
 💎 Auto Determine Hit/Stand
 👓 Tracking & Profit Calculator
 🏹 Fast And Secure
 🧠 Smart Dynamic
 🎯 Integrated Data with Advanced Decisions
 😴 Smart Sleep
 ✨ Smart Betting Strategy

**__Made with 💖 and 🧠 by GhoSty | [Async Development]__** """
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
                                          
               
                                                  Async Development Stable Build Version: 080726.2.1.0{Style.RESET_ALL}"""
    ) 
    print(f"{Fore.LIGHTRED_EX}\n\n > Made By GhoSty [Async Development]{Style.RESET_ALL}")
    ghosty.run(config["TOKEN"], bot=False)
