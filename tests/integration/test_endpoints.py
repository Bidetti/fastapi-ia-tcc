import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock, MagicMock

from src.app.main import app
from src.shared.domain.entities.result import ProcessingResult, DetectionResult
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestIAEndpoints:
    @pytest.mark.asyncio
    async def test_process_image_detection(self, client):
        request_data = {
            "image_url": "https://banana-analysis-bucket.s3.amazonaws.com/banana_detection_batch47.jpg",
            "user_id": "banana_farm_supervisor",
            "model_type": "detection",
            "metadata": {
                "device_info": "plantation_camera_unit5",
                "location": "warehouse_section_A",
                "batch_id": "banana_shipment_042",
            },
        }

        with patch(
            "src.modules.ia_integration.usecase.detect_usecase.DetectUseCase.execute",
            new_callable=AsyncMock,
        ) as mock_detect, patch(
            "src.modules.ia_integration.usecase.detect_usecase.IARepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.usecase.detect_usecase.DynamoRepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.repo.ia_repository.EC2Client",
            new_callable=MagicMock,
        ), patch(
            "src.modules.storage.repo.dynamo_repository.DynamoClient",
            new_callable=MagicMock,
        ):

            detection_result = DetectionResult(
                class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2]
            )

            mock_detect.return_value = ProcessingResult(
                image_id="banana-img-47d23",
                model_type=ModelType.DETECTION,
                results=[detection_result],
                status="success",
                request_id="banana-detection-req-5732",
                summary={"total_objects": 1, "detection_time_ms": 350},
                image_result_url="https://banana-analysis-bucket.s3.amazonaws.com/results/banana_detection_result_47d23.jpg",
            )

            response = client.post("/ia/process", json=request_data)
            print(f"Response body: {response.text}")

            assert response.status_code == 200
            response_json = response.json()
            assert response_json["status"] == "success"
            assert response_json["model_type"] == "detection"
            assert response_json["request_id"] == "banana-detection-req-5732"
            assert len(response_json["results"]) == 1
            assert response_json["results"][0]["class_name"] == "banana"
            assert response_json["results"][0]["confidence"] == 0.95

            mock_detect.assert_called_once()

            call_args = mock_detect.call_args
            kwargs = call_args[1] if not call_args[0] else {}

            if "image_url" in kwargs:
                assert kwargs.get("image_url") == request_data["image_url"]
            if "user_id" in kwargs:
                assert kwargs.get("user_id") == request_data["user_id"]

            metadata = kwargs.get("metadata", {})
            assert (
                metadata.get("device_info") == request_data["metadata"]["device_info"]
            )
            assert metadata.get("location") == request_data["metadata"]["location"]

    @pytest.mark.asyncio
    async def test_process_image_maturation(self, client):
        request_data = {
            "image_url": "https://banana-analysis-bucket.s3.amazonaws.com/banana_maturation_sample36.jpg",
            "user_id": "banana_ripeness_analyst",
            "model_type": "maturation",
            "metadata": {
                "device_info": "ripeness_scanner_v2",
                "location": "distribution_center_B",
                "banana_variety": "prata",
            },
        }

        with patch(
            "src.modules.ia_integration.usecase.maturation_usecase.MaturationUseCase.execute",
            new_callable=AsyncMock,
        ) as mock_maturation, patch(
            "src.modules.ia_integration.usecase.maturation_usecase.IARepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.usecase.maturation_usecase.DynamoRepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.repo.ia_repository.EC2Client",
            new_callable=MagicMock,
        ), patch(
            "src.modules.storage.repo.dynamo_repository.DynamoClient",
            new_callable=MagicMock,
        ):

            detection_result = DetectionResult(
                class_name="banana",
                confidence=0.95,
                bounding_box=[0.1, 0.1, 0.2, 0.2],
                maturation_level={
                    "score": 0.8,
                    "category": "ripe",
                    "estimated_days_until_spoilage": 3,
                },
            )

            mock_maturation.return_value = ProcessingResult(
                image_id="banana-ripeness-img-89f41",
                model_type=ModelType.MATURATION,
                results=[detection_result],
                status="success",
                request_id="banana-maturation-req-8732",
                summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
                image_result_url="https://banana-analysis-bucket.s3.amazonaws.com/results/banana_maturation_result_89f41.jpg",
            )

            response = client.post("/ia/process", json=request_data)

            assert response.status_code == 200
            response_json = response.json()
            assert response_json["status"] == "success"
            assert response_json["model_type"] == "maturation"
            assert response_json["request_id"] == "banana-maturation-req-8732"
            assert len(response_json["results"]) == 1
            assert response_json["results"][0]["class_name"] == "banana"
            assert response_json["results"][0]["maturation_level"]["category"] == "ripe"

            mock_maturation.assert_called_once()

            call_args = mock_maturation.call_args
            kwargs = call_args[1] if not call_args[0] else {}

            if "image_url" in kwargs:
                assert kwargs.get("image_url") == request_data["image_url"]
            if "user_id" in kwargs:
                assert kwargs.get("user_id") == request_data["user_id"]

            metadata = kwargs.get("metadata", {})
            assert (
                metadata.get("device_info") == request_data["metadata"]["device_info"]
            )
            assert metadata.get("location") == request_data["metadata"]["location"]

    def test_process_image_invalid_model(self, client):
        request_data = {
            "image_url": "https://banana-analysis-bucket.s3.amazonaws.com/banana_batch_assessment.jpg",
            "user_id": "banana_quality_manager",
            "model_type": "invalid_model",
            "metadata": {
                "device_info": "handheld_scanner_unit3",
                "banana_origin": "colombia",
            },
        }

        response = client.post("/ia/process", json=request_data)

        assert response.status_code == 422
        response_json = response.json()
        assert "detail" in response_json

    
    def test_process_image_error_handling(self, client):
        request_data = {
            "image_url": "https://banana-analysis-bucket.s3.amazonaws.com/banana_ripeness_batch_damaged.jpg",
            "user_id": "banana_quality_inspector",
            "model_type": "detection",
            "metadata": {
                "device_info": "quality_scanner_unit7",
                "batch_id": "banana_shipment_corrupted_158",
            },
        }

        with patch(
            "src.modules.ia_integration.usecase.detect_usecase.DetectUseCase.execute",
            new_callable=AsyncMock,
        ) as mock_detect, patch(
            "src.modules.ia_integration.usecase.detect_usecase.IARepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.usecase.detect_usecase.DynamoRepository",
            new_callable=MagicMock,
        ), patch(
            "src.modules.ia_integration.repo.ia_repository.EC2Client",
            new_callable=MagicMock,
        ), patch(
            "src.modules.storage.repo.dynamo_repository.DynamoClient",
            new_callable=MagicMock,
        ):

            mock_detect.side_effect = Exception(
                "Erro na análise de maturação da imagem"
            )
            response = client.post("/ia/process", json=request_data)

            assert response.status_code == 500
            response_json = response.json()
            assert "detail" in response_json
            assert "Erro ao processar imagem" in response_json["detail"]
