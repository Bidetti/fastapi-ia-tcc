import os

class Settings:
    """Classe de configurações simplificada sem depender do Pydantic"""
    
    def __init__(self):
        # Variáveis de ambiente básicas
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
        self.DEBUG = os.getenv("DEBUG", "True").lower() == "true"
        
        # Configurações da AWS
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
        
        # DynamoDB
        self.DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "ia-results")
        
        # EC2
        self.EC2_IA_ENDPOINT = os.getenv("EC2_IA_ENDPOINT", "http://localhost:8001")
        self.DETECTION_ENDPOINT = f"{self.EC2_IA_ENDPOINT}/detect"
        self.MATURATION_ENDPOINT = f"{self.EC2_IA_ENDPOINT}/maturation"
        
        # Timeout para requisições (em segundos)
        self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
    def load_dotenv(self, env_file=".env"):
        """Carrega variáveis de ambiente de um arquivo .env se disponível"""
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
                self.__init__()
        except Exception as e:
            print(f"Erro ao carregar arquivo .env: {e}")

settings = Settings()
settings.load_dotenv()