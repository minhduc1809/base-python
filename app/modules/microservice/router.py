from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/microservice", tags=["microservice"])


@router.get("/status")
async def get_microservice_status():
    return {
        "grpc": {"host": settings.MICROSERVICE_GRPC_HOST, "port": settings.MICROSERVICE_GRPC_PORT},
        "rabbitmq": {"status": "configured", "url": settings.MICROSERVICE_RABBITMQ_URL},
    }


@router.get("/client/hello-world")
async def client_hello_world():
    """Gọi gRPC Client Hello World (khớp MicroserviceClientController.clientHelloWorld)."""
    return {"message": "Hello World from gRPC Client!"}
