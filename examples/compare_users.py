import asyncio

# Importing the package
from amari import AmariBot


# Creating the function to get the user
async def get_amari_user(guild_id, user_id):
    # Initialize the package
    # Make sure to put your api token here
    amari = AmariBot("authorization_token")
    # Gets the user and returns it
    return await amari.get_user(guild_id, user_id)


# Function to compare users level
async def compare_users_level(guild_id, user_a, user_b):
    # Gets user a
    amari_user_a = await get_amari_user(guild_id, user_a)
    # Gets user b
    amari_user_b = await get_amari_user(guild_id, user_b)

    # Returns if their levels are the same
    return amari_user_a.level == amari_user_b.level


# Runs the function using asyncio due to trying to run an async function in a non-async enviroment.
print(asyncio.run(compare_users_level("your_guild_id", "your_user_a_id", "your_user_b_id")))
