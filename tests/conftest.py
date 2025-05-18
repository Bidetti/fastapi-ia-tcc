import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from src.app.main import app
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv(".env.test")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_s3_client():
    with patch("src.shared.infra.external.s3.s3_client.S3Client") as mock:
        s3_client_instance = mock.return_value

        # Mock para generate_presigned_url
        s3_client_instance.generate_presigned_url = AsyncMock(
            return_value={
                "upload_url": "https://test-bucket.s3.amazonaws.com/test-key?AWSSignature",
                "key": "test-key",
                "expires_in_seconds": 900,
            }
        )

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
        dynamo_client_instance.get_item = AsyncMock(
            return_value={
                "image_id": "test-id",
                "image_url": "https://test-bucket.s3.amazonaws.com/test-key",
                "user_id": "test-user",
                "metadata": {},
                "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Mock para query_items
        dynamo_client_instance.query_items = AsyncMock(
            return_value=[
                {
                    "image_id": "test-id",
                    "request_id": "test-request-id",
                    "model_type": "detection",
                    "results": [
                        {
                            "class_name": "apple",
                            "confidence": 0.95,
                            "bounding_box": [0.1, 0.1, 0.2, 0.2],
                        }
                    ],
                    "status": "success",
                    "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "summary": {"total_objects": 1},
                    "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key",
                }
            ]
        )

        dynamo_client_instance.convert_from_dynamo_item = MagicMock(side_effect=lambda x: x)

        yield dynamo_client_instance


@pytest.fixture
def mock_ec2_client():
    with patch("src.shared.infra.external.ec2.ec2_client.EC2Client") as mock:
        ec2_client_instance = mock.return_value

        # Mock para detect_objects
        ec2_client_instance.detect_objects = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "test-request-id",
                "results": [
                    {
                        "class_name": "apple",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    }
                ],
                "summary": {"total_objects": 1, "detection_time_ms": 350},
                "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key",
            }
        )

        # Mock para analyze_maturation
        ec2_client_instance.analyze_maturation = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "test-request-id",
                "results": [
                    {
                        "class_name": "apple",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                        "maturation_level": {
                            "score": 0.8,
                            "category": "ripe",
                            "estimated_days_until_spoilage": 3,
                        },
                    }
                ],
                "summary": {"average_maturation_score": 0.8, "detection_time_ms": 450},
                "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key",
            }
        )

        # Mock para analyze_maturation_with_boxes
        ec2_client_instance.analyze_maturation_with_boxes = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "test-maturation-with-boxes-id",
                "results": [
                    {
                        "class_name": "apple",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                        "maturation_level": {"score": 0.8, "category": "ripe", "estimated_days_until_spoilage": 3},
                    }
                ],
                "summary": {"average_maturation_score": 0.8, "detection_time_ms": 450},
                "image_result_url": "https://test-bucket.s3.amazonaws.com/results/test-key",
            }
        )

        # Mock para _make_request
        ec2_client_instance._make_request = AsyncMock(
            return_value={"status": "success", "request_id": "test-request-id"}
        )

        yield ec2_client_instance


@pytest.fixture
def sample_image():
    return Image(
        image_url="https://test-bucket.s3.amazonaws.com/test-key",
        user_id="test-user",
        metadata={"original_filename": "test.jpg", "content_type": "image/jpeg"},
        image_id="test-image-id",
    )


@pytest.fixture
def sample_detection_result():
    detection_result = DetectionResult(class_name="apple", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])

    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.DETECTION,
        results=[detection_result],
        status="success",
        request_id="test-request-id",
        summary={"total_objects": 1, "detection_time_ms": 350},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
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
            "estimated_days_until_spoilage": 3,
        },
    )

    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.MATURATION,
        results=[detection_result],
        status="success",
        request_id="test-maturation-id",
        summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
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
        s3_repo_instance.generate_presigned_url = AsyncMock(
            return_value={
                "upload_url": "https://test-bucket.s3.amazonaws.com/test-key?AWSSignature",
                "key": "test-key",
                "expires_in_seconds": 900,
            }
        )

        # Mock para generate_image_key
        s3_repo_instance.generate_image_key = AsyncMock(return_value="test-user/2025/05/12/test-uuid.jpg")

        # Mock para upload_file
        s3_repo_instance.upload_file = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")

        # Mock para upload_result_image
        s3_repo_instance.upload_result_image = AsyncMock(
            return_value="https://test-bucket.s3.amazonaws.com/results/test-key"
        )

        # Mock para get_file_url
        s3_repo_instance.get_file_url = AsyncMock(return_value="https://test-bucket.s3.amazonaws.com/test-key")

        # Mock para get_result_url
        s3_repo_instance.get_result_url = AsyncMock(
            return_value="https://test-bucket.s3.amazonaws.com/results/test-key"
        )

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
        dynamo_repo_instance.save_image_metadata = AsyncMock(
            return_value={
                "image_id": "test-image-id",
                "pk": "IMG#test-image-id",
                "sk": "META#test-image-id",
            }
        )

        # Mock para save_processing_result
        dynamo_repo_instance.save_processing_result = AsyncMock(
            return_value={
                "image_id": "test-image-id",
                "request_id": "test-request-id",
                "pk": "IMG#test-image-id",
                "sk": "RESULT#test-request-id",
            }
        )

        # Mock para get_image_by_id
        dynamo_repo_instance.get_image_by_id = AsyncMock(
            return_value=Image(
                image_url="https://test-bucket.s3.amazonaws.com/test-key",
                user_id="test-user",
                metadata={
                    "original_filename": "test.jpg",
                    "content_type": "image/jpeg",
                },
                image_id="test-image-id",
            )
        )

        async def get_result_by_request_id_side_effect(request_id):
            if request_id == "test-request-id":
                return create_sample_detection_result()
            elif request_id == "test-maturation-id":
                return create_sample_maturation_result()
            else:
                return None

        dynamo_repo_instance.get_result_by_request_id = AsyncMock(side_effect=get_result_by_request_id_side_effect)

        async def get_results_by_image_id_effect(image_id):
            return [
                create_sample_detection_result(),
                create_sample_maturation_result(),
            ]

        dynamo_repo_instance.get_results_by_image_id = AsyncMock(side_effect=get_results_by_image_id_effect)

        async def get_results_by_user_id_effect(user_id):
            return [
                create_sample_detection_result(),
                create_sample_maturation_result(),
            ]

        dynamo_repo_instance.get_results_by_user_id = AsyncMock(side_effect=get_results_by_user_id_effect)

        async def get_combined_result_effect(image_id):
            return create_sample_combined_result()

        dynamo_repo_instance.get_combined_result = AsyncMock(side_effect=get_combined_result_effect)

        dynamo_repo_instance.save_combined_result = AsyncMock(
            return_value={"combined_id": "test-combined-id", "image_id": "test-image-id"}
        )

        yield dynamo_repo_instance


@pytest.fixture
def mock_ia_repository():
    with patch("src.modules.ia_integration.repo.ia_repository.IARepository") as mock:
        ia_repo_instance = mock.return_value

        async def detect_objects_effect(image):
            return ProcessingResult(
                image_id="test-image-id",
                model_type=ModelType.DETECTION,
                results=[
                    DetectionResult(
                        class_name="banana",
                        confidence=0.95,
                        bounding_box=[0.1, 0.1, 0.2, 0.2],
                    )
                ],
                status="success",
                request_id="test-request-id",
                summary={"total_objects": 1, "detection_time_ms": 350},
                image_result_url="https://fruit-analysis.com/results/banana_detection_result.jpg",
            )

        ia_repo_instance.detect_objects = AsyncMock(side_effect=detect_objects_effect)

        async def analyze_maturation_effect(image):
            return ProcessingResult(
                image_id="test-image-id",
                model_type=ModelType.MATURATION,
                results=[
                    DetectionResult(
                        class_name="apple",
                        confidence=0.95,
                        bounding_box=[0.1, 0.1, 0.2, 0.2],
                        maturation_level={
                            "score": 0.8,
                            "category": "ripe",
                            "estimated_days_until_spoilage": 3,
                        },
                    )
                ],
                status="success",
                request_id="test-maturation-id",
                summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
                image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
            )

        ia_repo_instance.analyze_maturation = AsyncMock(side_effect=analyze_maturation_effect)

        async def analyze_maturation_with_boxes_effect(image, bounding_boxes, parent_request_id=None):
            return ProcessingResult(
                image_id="test-image-id",
                model_type=ModelType.MATURATION,
                results=[
                    DetectionResult(
                        class_name="apple",
                        confidence=0.95,
                        bounding_box=[0.1, 0.1, 0.2, 0.2],
                        maturation_level={
                            "score": 0.8,
                            "category": "ripe",
                            "estimated_days_until_spoilage": 3,
                        },
                    )
                ],
                status="success",
                request_id="test-maturation-boxes-id",
                summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
                image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
            )

        ia_repo_instance.analyze_maturation_with_boxes = AsyncMock(side_effect=analyze_maturation_with_boxes_effect)

        yield ia_repo_instance


def create_sample_detection_result():
    detection_result = DetectionResult(class_name="apple", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])

    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.DETECTION,
        results=[detection_result],
        status="success",
        request_id="test-request-id",
        summary={"total_objects": 1, "detection_time_ms": 350},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
    )


def create_sample_maturation_result():
    detection_result = DetectionResult(
        class_name="apple",
        confidence=0.95,
        bounding_box=[0.1, 0.1, 0.2, 0.2],
        maturation_level={
            "score": 0.8,
            "category": "ripe",
            "estimated_days_until_spoilage": 3,
        },
    )

    return ProcessingResult(
        image_id="test-image-id",
        model_type=ModelType.MATURATION,
        results=[detection_result],
        status="success",
        request_id="test-maturation-id",
        summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
        image_result_url="https://test-bucket.s3.amazonaws.com/results/test-key",
    )


def create_sample_combined_result():
    from src.shared.domain.entities.combined_result import CombinedResult

    detection_result = create_sample_detection_result()
    maturation_result = create_sample_maturation_result()

    combined = CombinedResult(
        image_id="test-image-id",
        user_id="test-user",
        detection_result=detection_result,
        maturation_result=maturation_result,
        location="test-warehouse",
    )

    combined.summary = {
        "total_objects": 1,
        "average_maturation_score": 0.8,
        "total_processing_time_ms": combined.total_processing_time_ms,
    }

    return combined
