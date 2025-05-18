import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

from src.modules.ia_integration.usecase.combined_processing_usecase import (
    CombinedProcessingUseCase,
)
from src.shared.domain.entities.combined_result import CombinedResult
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestCombinedEndpoints:
    @pytest.mark.asyncio
    async def test_process_image_combined(self, client, mock_dynamo_repository, mock_ia_repository):
        with patch.object(
            CombinedProcessingUseCase,
            "start_processing",
            new_callable=AsyncMock,
            return_value="combined-req-123",
        ) as mock_start_processing:
            response = client.post(
                "/combined/process",
                json={
                    "image_url": "https://fruit-analysis.com/banana.jpg",
                    "user_id": "banana_analyst",
                    "location": "warehouse_A",
                },
            )

            assert response.status_code == 200
            assert response.json()["request_id"] == "combined-req-123"
            assert response.json()["status"] == "processing"

            mock_start_processing.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_processing_status(self, client):
        request_id = "combined-req-456"
        status_data = {"status": "completed", "message": "Processamento concluído", "request_id": request_id}

        with patch.object(
            CombinedProcessingUseCase,
            "get_processing_status",
            new_callable=AsyncMock,
            return_value=status_data,
        ) as mock_get_status:
            response = client.get(f"/combined/status/{request_id}")

            assert response.status_code == 200
            assert response.json()["status"] == "completed"

            mock_get_status.assert_called_once_with(request_id)

    @pytest.mark.asyncio
    async def test_get_processing_status_not_found(self, client):
        request_id = "combined-req-not-exists"

        with patch.object(
            CombinedProcessingUseCase,
            "get_processing_status",
            new_callable=AsyncMock,
            return_value=None,
        ) as mock_get_status:
            response = client.get(f"/combined/status/{request_id}")

            assert response.status_code == 404
            assert f"Processamento {request_id} não encontrado" in response.json()["detail"]

            mock_get_status.assert_called_once_with(request_id)

    @pytest.mark.asyncio
    async def test_get_combined_results(self, client):
        image_id = "banana-image-combined-123"

        detection_result = ProcessingResult(
            image_id=image_id,
            model_type=ModelType.DETECTION,
            results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
            status="success",
            request_id="detection-req-id",
            summary={"total_objects": 1, "detection_time_ms": 350},
            image_result_url="https://result-url.com/detection",
        )

        maturation_result = ProcessingResult(
            image_id=image_id,
            model_type=ModelType.MATURATION,
            results=[
                DetectionResult(
                    class_name="banana",
                    confidence=0.95,
                    bounding_box=[0.1, 0.1, 0.2, 0.2],
                    maturation_level={"score": 0.8, "category": "ripe", "estimated_days_until_spoilage": 3},
                )
            ],
            status="success",
            request_id="maturation-req-id",
            summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
            image_result_url="https://result-url.com/maturation",
        )

        combined_result = CombinedResult(
            image_id=image_id,
            user_id="banana_combined_user",
            detection_result=detection_result,
            maturation_result=maturation_result,
            location="warehouse_B",
        )

        combined_result.summary = {"total_objects": 1, "average_maturation_score": 0.8, "total_processing_time_ms": 800}

        combined_result.to_dict = MagicMock(
            return_value={
                "image_id": image_id,
                "user_id": "banana_combined_user",
                "detection_result": detection_result.to_dict(),
                "maturation_result": maturation_result.to_dict(),
                "location": "warehouse_B",
                "status": "completed",
                "summary": {"total_objects": 1, "average_maturation_score": 0.8, "total_processing_time_ms": 800},
                "combined_id": combined_result.combined_id,
            }
        )

        with patch.object(
            CombinedProcessingUseCase, "get_combined_result", new_callable=AsyncMock, return_value=combined_result
        ) as mock_get_result:
            response = client.get(f"/combined/results/{image_id}")

            assert response.status_code == 200
            assert response.json()["image_id"] == image_id
            assert response.json()["user_id"] == "banana_combined_user"
            assert response.json()["location"] == "warehouse_B"
            assert "summary" in response.json()
            assert response.json()["summary"]["total_objects"] == 1

            mock_get_result.assert_called_once_with(image_id)

    async def test_get_results_by_request_id(self, client):
        request_id = "combined-banana-req-789"
        image_id = "banana-by-request-123"

        detection_result = ProcessingResult(
            image_id=image_id,
            model_type=ModelType.DETECTION,
            results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
            status="success",
            request_id="detection-req-id",
            summary={"total_objects": 1, "detection_time_ms": 350},
            image_result_url="https://result-url.com/detection",
        )

        combined_result = CombinedResult(
            image_id=image_id,
            user_id="banana_request_user",
            detection_result=detection_result,
            location="warehouse_C",
        )

        combined_result.summary = {"total_objects": 1, "total_processing_time_ms": 350}

        combined_result.to_dict = MagicMock(
            return_value={
                "image_id": image_id,
                "user_id": "banana_request_user",
                "detection_result": detection_result.to_dict(),
                "maturation_result": None,
                "location": "warehouse_C",
                "status": "completed",
                "summary": {"total_objects": 1, "total_processing_time_ms": 350},
                "combined_id": combined_result.combined_id,
            }
        )

        with patch.object(
            CombinedProcessingUseCase, "get_result_by_request_id", new_callable=AsyncMock, return_value=combined_result
        ) as mock_get_result:
            response = client.get(f"/combined/results/request/{request_id}")

            assert response.status_code == 200
            assert response.json()["image_id"] == image_id
            assert response.json()["user_id"] == "banana_request_user"
            assert response.json()["location"] == "warehouse_C"

            mock_get_result.assert_called_once_with(request_id)
