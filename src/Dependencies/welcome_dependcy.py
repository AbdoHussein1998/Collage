
# dependencies/welcome_dependencies.py

from Services.welcome_service import WelcomeService


async def get_welcome_service() -> WelcomeService:
    return await WelcomeService.init_service()