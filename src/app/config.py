# src/app/config.py
import os
from typing import Dict, Any, Optional

class Settings:
    """Classe de configurações da aplicação."""
    
    def __init__(self):
        # Variáveis de ambiente básicas
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
        self.DEBUG = os.getenv("DEBUG", "True").lower() == "true"
        self.APP_NAME = "fruit-detection-api"
        self.APP_VERSION = "0.1.0"
        
        # Configurações da AWS
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        
        # Prefixos para recursos
        self.resource_prefix = f"{self.APP_NAME}-{self.ENVIRONMENT}"
        
        # DynamoDB
        self.DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", f"{self.resource_prefix}-results")
        
        # S3
        self.S3_IMAGES_BUCKET = os.getenv("S3_IMAGES_BUCKET", f"{self.resource_prefix}-images")
        self.S3_RESULTS_BUCKET = os.getenv("S3_RESULTS_BUCKET", f"{self.resource_prefix}-results")
        
        # Serviço de IA em EC2
        self.EC2_IA_ENDPOINT = os.getenv("EC2_IA_ENDPOINT", "http://localhost:8001")
        self.DETECTION_ENDPOINT = f"{self.EC2_IA_ENDPOINT}/detect"
        self.MATURATION_ENDPOINT = f"{self.EC2_IA_ENDPOINT}/maturation"
        self.MATURATION_WITH_BOXES_ENDPOINT = f"{self.EC2_IA_ENDPOINT}/maturation-with-boxes"
        
        # Timeout para requisições (em segundos)
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Configurações para upload de imagens
        self.MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
        self.ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
        self.PRESIGNED_URL_EXPIRY_MINUTES = int(os.getenv("PRESIGNED_URL_EXPIRY_MINUTES", "15"))
        
        # Configurações para processamento combinado
        self.ENABLE_AUTO_MATURATION = os.getenv("ENABLE_AUTO_MATURATION", "True").lower() == "true"
        self.MIN_DETECTION_CONFIDENCE = float(os.getenv("MIN_DETECTION_CONFIDENCE", "0.6"))
        self.MIN_MATURATION_CONFIDENCE = float(os.getenv("MIN_MATURATION_CONFIDENCE", "0.7"))
        
        # Configurações de cache (opcional para versões futuras)
        self.ENABLE_CACHE = os.getenv("ENABLE_CACHE", "False").lower() == "true"
        self.CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        
        # Configurações de CORS
        self.CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
        self.CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.CORS_HEADERS = ["*"]
        
        # Configurações de logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
    def load_dotenv(self, env_file: str = ".env") -> None:
        """
        Carrega variáveis de ambiente de um arquivo .env se disponível.
        
        Args:
            env_file: Caminho para o arquivo .env
        """
        try:
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key and not os.getenv(key):
                                os.environ[key] = value
                # Recarregar as configurações após carregar as variáveis de ambiente
                self.__init__()
                print(f"Variáveis de ambiente carregadas de {env_file}")
        except Exception as e:
            print(f"Erro ao carregar arquivo .env: {e}")
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Retorna todas as configurações como um dicionário.
        
        Returns:
            Dict[str, Any]: Dicionário com todas as configurações
        """
        return {
            key: value for key, value in self.__dict__.items() 
            if not key.startswith('_') and key != 'get_all_settings' and key != 'load_dotenv'
        }
    
    def get_s3_url(self, bucket_name: str, key: str) -> str:
        """
        Constrói uma URL S3 para um objeto.
        
        Args:
            bucket_name: Nome do bucket
            key: Chave do objeto
            
        Returns:
            str: URL do objeto
        """
        return f"https://{bucket_name}.s3.{self.AWS_REGION}.amazonaws.com/{key}"
    
    def get_processing_options(self) -> Dict[str, Any]:
        """
        Retorna as opções de processamento para os modelos de IA.
        
        Returns:
            Dict[str, Any]: Opções de processamento
        """
        return {
            "enable_auto_maturation": self.ENABLE_AUTO_MATURATION,
            "min_detection_confidence": self.MIN_DETECTION_CONFIDENCE,
            "min_maturation_confidence": self.MIN_MATURATION_CONFIDENCE
        }

settings = Settings()
settings.load_dotenv()