import asyncio

# Importing the package
from amari import AmariClient


# Creating the function to get the rewards
async def fetch_amari_rewards(guild_id):
    # Initialize the package and
    # Make sure to put your api token here
    amari = AmariClient("authorization_token")
    # Gets the reward and returns it
    # I set the limit to 100 to make sure it will return all of the possible rewards
    return await amari.fetch_rewards(guild_id, limit=100)


async def get_max_reward(guild_id):
    # Gets the rewards
    rewards = await fetch_amari_rewards(guild_id)

    # Here it returns the final reward. The -1 does that for you!
    return rewards.roles[-1]


# Runs the function using asyncio due to trying to run an async function in a non-async enviroment.
print(asyncio.run(get_max_reward("your_guild_id")))
