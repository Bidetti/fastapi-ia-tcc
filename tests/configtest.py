import pytest
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import uuid
import json
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv(".env.test")

from src.app.main import app
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import ProcessingResult, DetectionResult
from src.shared.domain.enums.ia_model_type_enum import ModelType

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_s3_client():
    with patch("src.shared.infra.external.s3.s3_client.S3Client") as mock:
        s3_client_instance = mock.return_value
        
        # Mock para generate_presigned_url
        s3_client_instance.generate_presigned_url = AsyncMock(return_value={
            "upload_url": "https://test-bucket.s3.amazonaws.com/test-key?AWSSignature",
            "key": "test-key",
            "expires_in_seconds": 900
        })
        
        # Mock para upload_file
        s3_client_instance.upload_file = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
        
        # Mock para get_file_url
        s3_client_instance.get_file_url = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
        
        # Mock para delete_file
        s3_client_instance.delete_file = AsyncMock(return_value=True)
        
        yield s3_client_instance

@pytest.fixture
def mock_dynamo_client():
    with patch("src.shared.infra.external.dynamo.dynamo_client.DynamoClient") as mock:
        dynamo_client_instance = mock.return_value
        
        # Mock para put_item
        dynamo_client_instance.put_item = AsyncMock(return_value={"pk": "IMG#test-id", "sk": "META#test-id"})
        
        # Mock para get_item
        dynamo_client_instance.get_item = AsyncMock(return_value={
            "image_id": "test-id",
            "image_url": "https://test-bucket.s3.amazonaws.com/test-key",
            "user_id": "test-user",
            "metadata": {},
            "upload_timestamp": datetime.utcnow().isoformat()
        })
        
        # Mock para query_items
        dynamo_client_instance.query_items = AsyncMock(return_value=[{
            "image_id": "test-id",
            "request_id": "test-request-id",
            "model_type": "detection",
            "results": json.dumps([{
                "class": "apple",
                "confidence": 0.95,
                "bounding_box": [0.1, 0.1, 0.2, 0.2]
            }]),
            "status": "success",
            "processing_timestamp": datetime.utcnow().isoformat(),
            "summary": json.dumps({"total_objects": 1}),
            "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key"
        }])
        
        yield dynamo_client_instance

@pytest.fixture
def mock_ec2_client():
    with patch("src.shared.infra.external.ec2.ec2_client.EC2Client") as mock:
        ec2_client_instance = mock.return_value
        
        # Mock para detect_objects
        ec2_client_instance.detect_objects = AsyncMock(return_value={
            "status": "success",
            "request_id": "test-request-id",
            "results": [{
                "class": "apple",
                "confidence": 0.95,
                "bounding_box": [0.1, 0.1, 0.2, 0.2]
            }],
            "summary": {"total_objects": 1, "detection_time_ms": 350},
            "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key"
        })
        
        # Mock para analyze_maturation
        ec2_client_instance.analyze_maturation = AsyncMock(return_value={
            "status": "success",
            "request_id": "test-request-id",
            "results": [{
                "class": "apple",
                "confidence": 0.95,
                "bounding_box": [0.1, 0.1, 0.2, 0.2],
                "maturation_level": {
                    "score": 0.8,
                    "category": "ripe",
                    "estimated_days_until_spoilage": 3
                }
            }],
            "summary": {"average_maturation_score": 0.8, "detection_time_ms": 450},
            "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key"
        })
        
        # Mock para _make_request
        ec2_client_instance._make_request = AsyncMock(return_value={
            "status": "success",
            "request_id": "test-request-id"
        })
        
        yield ec2_client_instance

@pytest.fixture
def sample_image():
    return Image(
        image_url="https://test-bucket.s3.amazonaws.com/test-key",
        user_id="test-user",
        metadata={"original_filename": "test.jpg", "content_type": "image/jpeg"},
        image_id="test-image-id"
    )

@pytest.fixture
def sample_detection_result():
    detection_result = DetectionResult(
        class_name="apple",
        confidence=0.95,
        bounding_box=[0.1, 0.1, 0.2, 0.2]
    )
    
    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.DETECTION,
        results=[detection_result],
        status="success",
        request_id="test-request-id",
        summary={"total_objects": 1, "detection_time_ms": 350},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key"
    )

@pytest.fixture
def sample_maturation_result():
    detection_result = DetectionResult(
        class_name="apple",
        confidence=0.95,
        bounding_box=[0.1, 0.1, 0.2, 0.2],
        maturation_level={
            "score": 0.8,
            "category": "ripe",
            "estimated_days_until_spoilage": 3
        }
    )
    
    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.MATURATION,
        results=[detection_result],
        status="success",
        request_id="test-maturation-id",
        summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key"
    )

@pytest.fixture
def sample_upload_file():
    class MockFile:
        def __init__(self):
            self.file = MagicMock()
            self.file.read = MagicMock(return_value=b"test file content")
            self.filename = "test.jpg"
            self.content_type = "image/jpeg"
            
    return MockFile()

@pytest.fixture
def mock_s3_repository():
    with patch("src.modules.storage.repo.s3_repository.S3Repository") as mock:
        s3_repo_instance = mock.return_value
        
        # Mock para generate_presigned_url
        s3_repo_instance.generate_presigned_url = AsyncMock(return_value={
            "upload_url": "https://test-bucket.s3.amazonaws.com/test-key?AWSSignature",
            "key": "test-key",
            "expires_in_seconds": 900
        })
        
        # Mock para generate_image_key
        s3_repo_instance.generate_image_key = AsyncMock(return_value="test-user/2025/05/12/test-uuid.jpg")
        
        # Mock para upload_file
        s3_repo_instance.upload_file = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
        
        # Mock para upload_result_image
        s3_repo_instance.upload_result_image = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/results/test-key")
        
        # Mock para get_file_url
        s3_repo_instance.get_file_url = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
        
        # Mock para get_result_url
        s3_repo_instance.get_result_url = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/results/test-key")
        
        # Mock para delete_file
        s3_repo_instance.delete_file = AsyncMock(return_value=True)
        
        # Mock para delete_result
        s3_repo_instance.delete_result = AsyncMock(return_value=True)
        
        yield s3_repo_instance

@pytest.fixture
def mock_dynamo_repository():
    with patch("src.modules.storage.repo.dynamo_repository.DynamoRepository") as mock:
        dynamo_repo_instance = mock.return_value
        
        # Mock para save_image_metadata
        dynamo_repo_instance.save_image_metadata = AsyncMock(return_value={
            "image_id": "test-image-id",
            "pk": "IMG#test-image-id",
            "sk": "META#test-image-id"
        })
        
        # Mock para save_processing_result
        dynamo_repo_instance.save_processing_result = AsyncMock(return_value={
            "image_id": "test-image-id",
            "request_id": "test-request-id",
            "pk": "IMG#test-image-id",
            "sk": "RESULT#test-request-id"
        })
        
        # Mock para get_image_by_id
        dynamo_repo_instance.get_image_by_id = AsyncMock(return_value=Image(
            image_url="https://test-bucket.s3.amazonaws.com/test-key",
            user_id="test-user",
            metadata={"original_filename": "test.jpg", "content_type": "image/jpeg"},
            image_id="test-image-id"
        ))
        
        # Mock para get_result_by_request_id
        dynamo_repo_instance.get_result_by_request_id = AsyncMock(side_effect=lambda request_id: 
            sample_detection_result() if request_id == "test-request-id" else 
            sample_maturation_result() if request_id == "test-maturation-id" else None
        )
        
        # Mock para get_results_by_image_id
        dynamo_repo_instance.get_results_by_image_id = AsyncMock(return_value=[
            sample_detection_result(),
            sample_maturation_result()
        ])
        
        # Mock para get_results_by_user_id
        dynamo_repo_instance.get_results_by_user_id = AsyncMock(return_value=[
            sample_detection_result(),
            sample_maturation_result()
        ])
        
        yield dynamo_repo_instance

@pytest.fixture
def mock_ia_repository():
    with patch("src.modules.ia_integration.repo.ia_repository.IARepository") as mock:
        ia_repo_instance = mock.return_value
        
        # Mock para detect_objects
        ia_repo_instance.detect_objects = AsyncMock(side_effect=lambda image: 
            ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.DETECTION,
                results=[
                    DetectionResult(
                        class_name="apple",
                        confidence=0.95,
                        bounding_box=[0.1, 0.1, 0.2, 0.2]
                    )
                ],
                status="success",
                request_id="test-request-id",
                summary={"total_objects": 1, "detection_time_ms": 350},
                image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key"
            )
        )
        
        # Mock para analyze_maturation
        ia_repo_instance.analyze_maturation = AsyncMock(side_effect=lambda image: 
            ProcessingResult(
                image_id=image.image_id,
                model_type=ModelType.MATURATION,
                results=[
                    DetectionResult(
                        class_name="apple",
                        confidence=0.95,
                        bounding_box=[0.1, 0.1, 0.2, 0.2],
                        maturation_level={
                            "score": 0.8,
                            "category": "ripe",
                            "estimated_days_until_spoilage": 3
                        }
                    )
                ],
                status="success",
                request_id="test-maturation-id",
                summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
                image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key"
            )
        )
        
        yield ia_repo_instance