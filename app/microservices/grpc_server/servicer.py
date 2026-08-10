import grpc
from app.core.config import settings
from app.core.logging import logger


class CoreGrpcServicer:
    """Implementation of gRPC Servicer matching proto definitions."""

    async def Ping(self, request, context):
        logger.info("gRPC Ping received")
        return {"message": "pong", "status": "ok"}


async def start_grpc_server():
    """Khởi chạy gRPC Async Server với grpc.aio."""
    server = grpc.aio.server()
    address = f"{settings.MICROSERVICE_GRPC_HOST}:{settings.MICROSERVICE_GRPC_PORT}"
    server.add_insecure_port(address)
    logger.info("Starting gRPC Async Server...", address=address)
    await server.start()
    return server
