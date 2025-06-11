from .. import env

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {"url": env("BROKER_URL")},
    "MIDDLEWARE": [],
}
DRAMATIQ_IGNORED_MODULES = ("adminactions.tasks",)
DRAMATIQ_CRONTAB = {
    "REDIS_URL": env("BROKER_URL"),
}
