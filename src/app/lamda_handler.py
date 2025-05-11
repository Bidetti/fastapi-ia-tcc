import json
import logging
from mangum import Mangum
from .main import app

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    Função handler para AWS Lambda.
    Processa eventos da AWS e os converte para o formato esperado pela aplicação FastAPI.
    
    Args:
        event: Evento da AWS Lambda (normalmente do API Gateway)
        context: Contexto de execução do Lambda
        
    Returns:
        dict: Resposta processada pelo Mangum
    """
    logger.info(f"Evento recebido: {json.dumps(event)}")
    return handler(event, context)