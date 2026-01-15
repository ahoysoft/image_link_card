"""Bot detection utility for social media crawlers."""

# User-agent strings for common social media and search crawlers
BOT_USER_AGENTS = [
    'twitterbot',
    'facebookexternalhit',
    'linkedinbot',
    'slackbot',
    'telegrambot',
    'whatsapp',
    'discordbot',
    'pinterest',
    'tumblr',
    'redditbot',
    'embedly',
    'quora link preview',
    'outbrain',
    'rogerbot',
    'showyoubot',
    'slurp',
    'baiduspider',
    'bingbot',
    'googlebot',
    'applebot',
    'yandexbot',
    'duckduckbot',
]


def is_bot(user_agent: str) -> bool:
    """Check if the request is from a social media crawler or bot.

    Args:
        user_agent: The User-Agent header value

    Returns:
        True if the user agent matches a known bot pattern
    """
    if not user_agent:
        return False

    ua_lower = user_agent.lower()
    return any(bot in ua_lower for bot in BOT_USER_AGENTS)
