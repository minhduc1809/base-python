import aio_pika
from app.core.config import settings
from app.core.logging import logger


async def start_rabbitmq_consumer():
    """Khởi chạy RabbitMQ Consumer bất đồng bộ sử dụng aio-pika."""
    try:
        connection = await aio_pika.connect_robust(settings.MICROSERVICE_RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue("aisoft_events_queue", durable=True)

        logger.info("Connected to RabbitMQ, listening on 'aisoft_events_queue'...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logger.info("Received RabbitMQ message", body=message.body.decode())
    except Exception as e:
        logger.warn("RabbitMQ Consumer connection deferred", error=str(e))
