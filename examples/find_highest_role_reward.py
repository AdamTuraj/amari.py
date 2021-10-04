# Imports a package used to run the asyncronous function. This library is not required for the wrapper.
import asyncio

# Importing the package
from amari import AmariClient


# Creating the function to get the rewards
async def fetch_amari_rewards(guild_id):
    # Initialize the package and
    # Make sure to put your api token here
    amari = AmariClient("authorization_token")

    # Here we are closing the connection. This is required once your done using the client
    await amari.close()

    # Gets the reward and returns it
    # I set the limit to 100 to make sure it will return all of the possible rewards
    return await amari.fetch_rewards(guild_id, limit=100)


async def get_max_reward(guild_id):
    # Gets the rewards
    rewards = await fetch_amari_rewards(guild_id)

    # Here it returns the last key of the rewards.
    # This is doing that by turning the rewards into a list of all the keys,
    # then getting the last value with the -1.
    final_key = list(rewards.roles)[-1]

    # Here we get the role from that key we just got
    return rewards.get_role(final_key)


# Runs the function using asyncio due to trying to run an async function in a non-async enviroment.
print(asyncio.run(get_max_reward(guild_id)))
