import logging
import os

import django
from celery import Celery, signals
from django.conf import settings
from kombu import Exchange, Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


logger = logging.getLogger(__name__)


app = Celery(
    "config",
    include=["enrollments.tasks"],
)
django.setup()  # enables us to import app modules in tasks modules

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)

# variable names values

# exchange declaration
mainx_name = "main"
dlx_name = f"{mainx_name}-dlx"
retryx_name = f"{mainx_name}-retry"
main_exchange = Exchange(
    name=mainx_name,
    type="direct",
    durable=True,
    delivery_mode="persistent",
)
main_dlx = Exchange(
    name=dlx_name,
    type="direct",
    durable=True,
    delivery_mode="persistent",
)
main_retry = Exchange(
    name=retryx_name,
    type="direct",
    durable=True,
    delivery_mode="persistent",
)

# queues declaration
main_queue_name = "main"
main_routing_key = "main"
dlq_routing_key = f"{main_routing_key}-dlq"
dlq_queue_name = f"{main_queue_name}-dlq"
retry_queue_name = f"{main_queue_name}-retry"
retry_routing_key = f"{main_routing_key}-retry"

dlq_queue = Queue(
    name=dlq_queue_name,
    # only binding to dlx exchange when declared this way
    exchange=dlx_name,
    routing_key=dlq_routing_key,
    durable=True,
    queue_arguments={
        "x-message-ttl": 30 * 24 * 60 * 60 * 1000,  # 30 days
        "x-expires": 30 * 24 * 60 * 60 * 1000,  # 30 days
    },
)

main_queue = Queue(
    name=main_queue_name,
    exchange=main_exchange,
    routing_key=main_routing_key,
    durable=True,
    queue_arguments={
        "x-dead-letter-exchange": main_dlx.name,
        "x-dead-letter-routing-key": dlq_queue.routing_key,
    },
)

retry_queue = Queue(
    retry_queue_name,
    exchange=retryx_name,
    routing_key=retry_routing_key,
    durable=True,
    queue_arguments={
        "x-message-ttl": 60000,  # 60 seconds delay
        "x-dead-letter-exchange": main_exchange.name,
        "x-dead-letter-routing-key": main_queue.routing_key,
    },
)


app.conf.task_default_queue = main_queue_name
app.conf.task_queues = (main_queue, retry_queue, dlq_queue)
app.conf.task_default_exchange = mainx_name
app.conf.task_default_routing_key = main_routing_key
# create queues on the fly in case celery don't initialize at start time
app.conf.task_create_missing_queues = True
# consumes one message at a time
app.conf.worker_prefetch_multiplier = 1


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    logger.info(f"Request: {self.request!r}")


@signals.worker_ready.connect
def declare_dlq(sender=None, **kwargs):  # force initializing dlq
    with sender.app.connection_for_write() as conn:
        dlq_queue(conn.default_channel).declare()
