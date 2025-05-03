import json
from mangum import Mangum
from .main import app

handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    Função handler para AWS Lambda
    """
    print(f"Evento recebido: {json.dumps(event)}")
    return handler(event, context)