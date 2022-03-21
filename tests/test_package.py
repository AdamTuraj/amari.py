from amari import AmariClient as Amari
import pytest

import os

TOKEN = os.getenv("AMARI_TOKEN")


@pytest.mark.asyncio
async def test_users():
    """Tests the fetching users function"""
    client = Amari(TOKEN)

    try:
        assert await client.fetch_user(346474194394939393, 374147012599218176)
        assert await client.fetch_users(
            346474194394939393, ["374147012599218176", "107510319315697664"]
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_leaderboards():
    """Tests the fetching leaderboards function"""

    client = Amari(TOKEN)

    try:
        assert await client.fetch_leaderboard(346474194394939393, page=3, limit=100)
        assert await client.fetch_full_leaderboard(346474194394939393, weekly=True)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_rewards():
    """Tests the fetching rewards function"""

    client = Amari(TOKEN)

    try:
        assert await client.fetch_rewards(346474194394939393, page=1, limit=20)
    finally:
        await client.close()
