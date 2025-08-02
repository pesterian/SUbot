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
bot = commands.Bot(command_prefix='*', intents=intents)

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
            "replies": []
        }
        save_complaints(complaints)
        
        # Ping the replier
        replier = bot.get_user(REPLIER_ID)
        await ctx.send(f"Got it! Your complaint has been noted with ID: `{complaint_id}` \n{replier.mention} - Get yo ass in here")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

@bot.command(name='list')
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
        status = "Replied" if data.get("replies") else "Pending"
        embed.add_field(
            name=f"ID: {complaint_id} - {data['title']} [{status}]",
            value=data['description'][:100] + ("..." if len(data['description']) > 100 else ""),
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
    pending_complaints = {cid: data for cid, data in complaints.items() if not data.get("replies")}
    
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
        
        # Save reply
        complaints[complaint_id]["replies"].append(reply_content)
        save_complaints(complaints)
        
        # Show complaint and notify
        complainer = bot.get_user(COMPLAINER_ID)
        embed = discord.Embed(
            title=f"Complaint: {complaints[complaint_id]['title']}",
            description=complaints[complaint_id]["description"],
            color=0xFFB6C1
        )
        embed.add_field(name="Reply", value=reply_content, inline=False)
        embed.set_footer(text=f"Complaint ID: {complaint_id}")
        
        await ctx.send(embed=embed)
        await ctx.send(f"{complainer.mention} Your complaint has been addressed!")
        
    except asyncio.TimeoutError:
        await ctx.send("Took too long to respond! Try again when you're ready")

def main():
    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        return
    
    bot.run(token)

if __name__ == '__main__':
    main()