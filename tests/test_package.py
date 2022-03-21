from amari import AmariClient as Amari
import pytest

token = "a8a7a409096e7d9d9daee709.50964a.72fdcc24868e6f1c0f8ae2e2b02"


@pytest.mark.asyncio
async def test_users():
    """Tests the fetching users function"""
    client = Amari(token)

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

    client = Amari(token)

    try:
        assert await client.fetch_leaderboard(346474194394939393, page=3, limit=100)
        assert await client.fetch_full_leaderboard(346474194394939393, weekly=True)
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_rewards():
    """Tests the fetching rewards function"""

    client = Amari(token)

    try:
        assert await client.fetch_rewards(346474194394939393, page=1, limit=20)
    finally:
        await client.close()
