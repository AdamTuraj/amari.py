Quickstart Guide
================

Requirements
------------

- The library installed. Instructions to install shown at the `index menu <https://amaripy.readthedocs.io/en/latest/>`_
- An Amari API authorization token. Instructions to obtain shown at the `getting an authorization token page <https://amaripy.readthedocs.io/en/latest/getting_an_authorization_token>`_

Example
-------

Comparing Users
^^^^^^^^^^^^^^^

.. code:: py

    # Imports a package used to run the asyncronous function. This library is not required for the wrapper.
    import asyncio

    # Importing the package
    from amari import AmariClient

    # The function to compare users level
    async def compare_users_level(guild_id, users: list):
        # Initialize the package
        # Make sure to put your api token here
        amari = AmariClient("authorization_token")

        # Fetches the users and sets it to the response users var
        resp_users = (await amari.fetch_users(guild_id, users)).users

        # Here we are closing the connection. This is required once your done using the client
        await amari.close()

        # Makes sure 2 users are returned
        if len(resp_users) < 2:
            return False

        # Changes the dictionary of the users to a list of them
        users = [user for user in resp_users.values()]

        # Returns if their levels are the same
        return users[0].level == users[1].level


    # Runs the function using asyncio due to trying to run an async function in a non-async enviroment.
    # Make sure to add the user ids as a string
    print(asyncio.run(compare_users_level(guild_id, ["user_a_id", "user_a_id"])))

