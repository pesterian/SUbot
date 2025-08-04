import discord
from discord.ext import commands
import os
import json
import asyncio
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='*', intents=intents, help_command=None)

# User IDs
COMPLAINER_ID = 555429232877240341
REPLIER_ID = 336106546847023104

def load_complaints():
    try:
        with open('complaints.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_complaints(complaints):
    with open('complaints.json', 'w') as f:
        json.dump(complaints, f, indent=2)

def load_replies():
    try:
        with open('replies.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_replies(replies):
    with open('replies.json', 'w') as f:
        json.dump(replies, f, indent=2)

def load_crashouts():
    try:
        with open('crashouts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"counter": 0, "messages": []}

def save_crashouts(crashouts):
    with open('crashouts.json', 'w') as f:
        json.dump(crashouts, f, indent=2)

def generate_id():
    return str(uuid.uuid4())[:8]

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='complain')
async def complain(ctx):
    if ctx.author.id != COMPLAINER_ID:
        await ctx.send("Only SU can complain I don't care about anybody else")
        return
    
    # Ask for title
    await ctx.send("What would you like to complain about sweetie?")
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    try:
        title_msg = await bot.wait_for('message', check=check, timeout=60.0)
        title = title_msg.content
        
        # Ask for description
        await ctx.send("Alright, now tell me all about it! What's bothering you?")
        
        desc_msg = await bot.wait_for('message', check=check, timeout=300.0)
        description = desc_msg.content
        
        # Save to complaints.json with ID
        complaints = load_complaints()
        complaint_id = generate_id()
        complaints[complaint_id] = {
            "title": title,
            "description": description,
            "status": "pending"
        }
        save_complaints(complaints)
        
        # Ping the replier
        replier = bot.get_user(REPLIER_ID)
        if replier is None:
            try:
                replier = await bot.fetch_user(REPLIER_ID)
            except discord.NotFound:
                await ctx.send(f"Got it! Your complaint has been noted with ID: `{complaint_id}`")
                return
        
        await ctx.send(f"Got it! Your complaint has been noted with ID: `{complaint_id}` \n{replier.mention} - Get yo ass in here")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

@bot.command(name='crashout')
async def crashout(ctx, *, message=None):
    if ctx.author.id != COMPLAINER_ID:
        await ctx.send("Only SU can crash out")
        return
    
    if not message:
        await ctx.send("You need to provide a crash out message!")
        return
    
    crashouts = load_crashouts()
    crashouts["counter"] += 1
    crashouts["messages"].append({
        "id": crashouts["counter"],
        "message": message,
        "timestamp": ctx.message.created_at.isoformat()
    })
    save_crashouts(crashouts)
    
    await ctx.send(f"Crash out #{crashouts['counter']} recorded: {message}")

@bot.command(name='crashcounter')
async def crash_counter(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    crashouts = load_crashouts()
    await ctx.send(f"Current crash out counter: **{crashouts['counter']}**")

@bot.command(name='crashlist')
async def crash_list(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    crashouts = load_crashouts()
    
    if crashouts["counter"] == 0:
        await ctx.send("No crash outs recorded yet!")
        return
    
    embed = discord.Embed(
        title=f"All Crash Outs (Total: {crashouts['counter']})", 
        color=0xFF6B6B
    )
    
    for crash in crashouts["messages"]:
        embed.add_field(
            name=f"Crash Out #{crash['id']}",
            value=crash["message"][:100] + ("..." if len(crash["message"]) > 100 else ""),
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='listcomplaints')
async def list_complaints(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    complaints = load_complaints()
    
    if not complaints:
        await ctx.send("No complaints found!")
        return
    
    embed = discord.Embed(title="All Complaints", color=0xFFB6C1)
    
    for complaint_id, data in complaints.items():
        status = data.get("status", "pending").title()
        embed.add_field(
            name=f"ID: {complaint_id} - {data['title']} [{status}]",
            value=data['description'][:100] + ("..." if len(data['description']) > 100 else ""),
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='listreplies')
async def list_replies(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    replies = load_replies()
    
    if not replies:
        await ctx.send("No replies found!")
        return
    
    complaints = load_complaints()
    embed = discord.Embed(title="All Replies", color=0x98FB98)
    
    for reply_id, data in replies.items():
        complaint_title = complaints.get(data['complaint_id'], {}).get('title', 'Unknown')
        embed.add_field(
            name=f"Reply ID: {reply_id} - To: {complaint_title}",
            value=f"**Complaint:** {data['complaint_id']}\n**Reply:** {data['content'][:100] + ('...' if len(data['content']) > 100 else '')}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='edit')
async def edit_complaint(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    complaints = load_complaints()
    
    if not complaints:
        await ctx.send("No complaints to edit!")
        return
    
    # Show complaints with IDs
    complaint_list = "\n".join([f"• `{cid}` - {data['title']}" for cid, data in complaints.items()])
    await ctx.send(f"Which complaint would you like to edit? (Enter the ID)\n{complaint_list}")
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    try:
        id_msg = await bot.wait_for('message', check=check, timeout=60.0)
        complaint_id = id_msg.content.strip()
        
        if complaint_id not in complaints:
            await ctx.send("That complaint ID doesn't exist!")
            return
        
        await ctx.send("What would you like to edit?\n1. Title\n2. Description\n3. Both\nType 1, 2, or 3:")
        
        choice_msg = await bot.wait_for('message', check=check, timeout=60.0)
        choice = choice_msg.content.strip()
        
        if choice == "1" or choice == "3":
            await ctx.send("Enter the new title:")
            title_msg = await bot.wait_for('message', check=check, timeout=300.0)
            complaints[complaint_id]["title"] = title_msg.content
        
        if choice == "2" or choice == "3":
            await ctx.send("Enter the new description:")
            desc_msg = await bot.wait_for('message', check=check, timeout=300.0)
            complaints[complaint_id]["description"] = desc_msg.content
        
        save_complaints(complaints)
        await ctx.send(f"Complaint `{complaint_id}` has been updated!")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

@bot.command(name='delete')
async def delete_complaint(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    complaints = load_complaints()
    
    if not complaints:
        await ctx.send("No complaints to delete!")
        return
    
    # Show complaints with IDs
    complaint_list = "\n".join([f"• `{cid}` - {data['title']}" for cid, data in complaints.items()])
    await ctx.send(f"Which complaint would you like to delete? (Enter the ID)\n{complaint_list}")
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    try:
        id_msg = await bot.wait_for('message', check=check, timeout=60.0)
        complaint_id = id_msg.content.strip()
        
        if complaint_id not in complaints:
            await ctx.send("That complaint ID doesn't exist!")
            return
        
        title = complaints[complaint_id]["title"]
        del complaints[complaint_id]
        save_complaints(complaints)
        
        # Also delete related replies
        replies = load_replies()
        replies = {rid: data for rid, data in replies.items() if data['complaint_id'] != complaint_id}
        save_replies(replies)
        
        await ctx.send(f"Complaint `{complaint_id}` - '{title}' has been deleted!")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

@bot.command(name='reply')
async def reply_to_complaint(ctx):
    if ctx.author.id != REPLIER_ID:
        await ctx.send("This isn't your command, sweetie")
        return
    
    complaints = load_complaints()
    
    if not complaints:
        await ctx.send("No complaints to reply to right now!")
        return
    
    # Show available complaints with IDs
    pending_complaints = {cid: data for cid, data in complaints.items() if data.get("status") == "pending"}
    
    if not pending_complaints:
        await ctx.send("All complaints have been addressed!")
        return
    
    complaint_list = "\n".join([f"• `{cid}` - {data['title']}" for cid, data in pending_complaints.items()])
    await ctx.send(f"Which complaint would you like to reply to? (Enter the ID)\n{complaint_list}")
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel
    
    try:
        id_msg = await bot.wait_for('message', check=check, timeout=60.0)
        complaint_id = id_msg.content.strip()
        
        if complaint_id not in complaints:
            await ctx.send("That complaint ID doesn't exist!")
            return
        
        await ctx.send("What's your response?")
        
        reply_msg = await bot.wait_for('message', check=check, timeout=300.0)
        reply_content = reply_msg.content
        
        # Save reply to replies.json
        replies = load_replies()
        reply_id = generate_id()
        replies[reply_id] = {
            "complaint_id": complaint_id,
            "content": reply_content
        }
        save_replies(replies)
        
        # Update complaint status
        complaints[complaint_id]["status"] = "replied"
        save_complaints(complaints)
        
        # Show complaint and notify
        complainer = bot.get_user(COMPLAINER_ID)
        if complainer is None:
            try:
                complainer = await bot.fetch_user(COMPLAINER_ID)
            except discord.NotFound:
                await ctx.send("Reply saved but couldn't notify the complainer.")
                return
        
        embed = discord.Embed(
            title=f"Complaint: {complaints[complaint_id]['title']}",
            description=complaints[complaint_id]["description"],
            color=0xFFB6C1
        )
        embed.add_field(name="Reply", value=reply_content, inline=False)
        embed.set_footer(text=f"Complaint ID: {complaint_id} | Reply ID: {reply_id}")
        
        await ctx.send(embed=embed)
        await ctx.send(f"{complainer.mention} Your complaint has been addressed!")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

@bot.command(name='help')
async def help_command(ctx):
    if ctx.author.id not in [COMPLAINER_ID, REPLIER_ID]:
        await ctx.send("This command isn't for you, sweetie")
        return
    
    embed = discord.Embed(title="Bot Commands", color=0xFFB6C1)
    
    if ctx.author.id == COMPLAINER_ID:
        embed.add_field(
            name="Complainer Commands",
            value="`*complain` - Create new complaint\n"
                  "`*crashout [message]` - Record a crash out\n"
                  "`*listcomplaints` - View all complaints\n"
                  "`*listreplies` - View all replies\n"
                  "`*crashcounter` - View crash out counter\n"
                  "`*crashlist` - View all crash outs\n"
                  "`*edit` - Edit complaints by ID\n"
                  "`*delete` - Delete complaints by ID",
            inline=False
        )
    
    if ctx.author.id == REPLIER_ID:
        embed.add_field(
            name="Replier Commands",
            value="`*reply` - Reply to pending complaints\n"
                  "`*listcomplaints` - View all complaints\n"
                  "`*listreplies` - View all replies\n"
                  "`*crashcounter` - View crash out counter\n"
                  "`*crashlist` - View all crash outs\n"
                  "`*edit` - Edit complaints by ID\n"
                  "`*delete` - Delete complaints by ID",
            inline=False
        )
    
    embed.add_field(
        name="Note",
        value="Use the 8-character IDs shown in list commands for all operations.",
        inline=False
    )
    
    await ctx.send(embed=embed)

def main():
    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    bot.run(token)

if __name__ == '__main__':
    main()