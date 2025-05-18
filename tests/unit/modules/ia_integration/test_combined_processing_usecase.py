import uuid
from unittest.mock import AsyncMock, patch

import pytest

from src.modules.ia_integration.usecase.combined_processing_usecase import CombinedProcessingUseCase
from src.shared.domain.entities.combined_result import CombinedResult
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType
from src.shared.domain.models.http_models import ProcessingStatusResponse


class TestCombinedProcessingUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_combined.jpg"
        user_id = "banana_combined_analyst"
        metadata = {"batch": "banana_weekly_45"}
        location = "warehouse_A"

        detection_result = ProcessingResult(
            image_id="test-banana-id",
            model_type=ModelType.DETECTION,
            results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
            status="success",
            request_id="test-banana-detection-req",
            summary={"total_objects": 1, "detection_time_ms": 350},
            image_result_url="https://fruit-analysis.com/results/banana_detection_result.jpg",
        )

        maturation_result = ProcessingResult(
            image_id="test-banana-id",
            model_type=ModelType.MATURATION,
            results=[
                DetectionResult(
                    class_name="banana",
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
            request_id="test-banana-maturation-req",
            summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
            image_result_url="https://fruit-analysis.com/results/banana_maturation_result.jpg",
        )

        expected_result = CombinedResult(
            image_id="test-banana-id",
            user_id=user_id,
            detection_result=detection_result,
            maturation_result=maturation_result,
            location=location,
        )
        expected_result.summary = {"total_objects": 1, "average_maturation_score": 0.8, "total_processing_time_ms": 800}

        with patch.object(CombinedProcessingUseCase, "execute", new_callable=AsyncMock, return_value=expected_result):
            usecase = CombinedProcessingUseCase(
                ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository
            )
            result = await usecase.execute(image_url=image_url, user_id=user_id, metadata=metadata, location=location)

            assert isinstance(result, CombinedResult)
            assert result.user_id == user_id
            assert result.status == "completed"
            assert result.detection_result == detection_result
            assert result.maturation_result == maturation_result

    @pytest.mark.asyncio
    async def test_execute_with_detection_error(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_detection_error.jpg"
        user_id = "banana_detection_error_handler"
        location = "warehouse_B"

        error_result = ProcessingResult(
            image_id="test-banana-error-id",
            model_type=ModelType.DETECTION,
            results=[],
            status="error",
            error_message="Failed to detect bananas",
            request_id="test-banana-error-req",
        )

        combined_error_result = CombinedResult(
            image_id="test-banana-error-id",
            user_id=user_id,
            detection_result=error_result,
            maturation_result=None,
            location=location,
        )

        with patch.object(
            CombinedProcessingUseCase, "execute", new_callable=AsyncMock, return_value=combined_error_result
        ):
            usecase = CombinedProcessingUseCase(
                ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository
            )
            result = await usecase.execute(image_url=image_url, user_id=user_id, location=location)

            assert isinstance(result, CombinedResult)
            assert result.status == "error"
            assert result.detection_result.status == "error"
            assert result.maturation_result is None

    @pytest.mark.asyncio
    async def test_start_processing_background(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_background.jpg"
        user_id = "banana_background_processor"

        uuid_hex = "04005e861cfb445fa3b1904a3d49e70c"
        uuid_obj = uuid.UUID(uuid_hex)
        request_id = f"combined-{uuid_hex}"

        mock_dynamo_repository.save_item = AsyncMock()

        with patch.object(uuid, "uuid4", return_value=uuid_obj):
            usecase = CombinedProcessingUseCase(
                ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository
            )

            result = await usecase.start_processing(image_url=image_url, user_id=user_id)

            result_uuid = result.replace("combined-", "").replace("-", "")
            expected_uuid = request_id.replace("combined-", "")

            assert result_uuid == expected_uuid

            mock_dynamo_repository.save_item.assert_called_once()
            call_args = mock_dynamo_repository.save_item.call_args[0]
            assert call_args[0] == "processing_status"
            status_data = call_args[1]
            assert status_data["request_id"] == result
            assert status_data["status"] == "queued"
            assert status_data["image_url"] == image_url
            assert status_data["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_get_processing_status(self, mock_ia_repository, mock_dynamo_repository):
        usecase = CombinedProcessingUseCase(ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository)

        mock_status_data = {
            "pk": "PROCESSING#test-request-id",
            "sk": "STATUS",
            "request_id": "test-request-id",
            "status": "processing",
            "progress": 0.5,
            "updated_at": "2025-05-12T10:30:00+00:00",
        }

        mock_dynamo_repository.get_item = AsyncMock(return_value=mock_status_data)

        status = await usecase.get_processing_status("test-request-id")

        assert isinstance(status, ProcessingStatusResponse)
        assert status.request_id == "test-request-id"
        assert status.status == "processing"
        assert status.progress == 0.5

        mock_dynamo_repository.get_item.assert_called_once_with(
            "processing_status", {"pk": "PROCESSING#test-request-id", "sk": "STATUS"}
        )

    @pytest.mark.asyncio
    async def test_get_processing_status_not_found(self, mock_ia_repository, mock_dynamo_repository):
        usecase = CombinedProcessingUseCase(ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository)

        mock_dynamo_repository.get_item = AsyncMock(return_value=None)

        status = await usecase.get_processing_status("non-existent-id")

        assert status is None

        mock_dynamo_repository.get_item.assert_called_once_with(
            "processing_status", {"pk": "PROCESSING#non-existent-id", "sk": "STATUS"}
        )

    @pytest.mark.asyncio
    async def test_get_combined_result(self, mock_ia_repository, mock_dynamo_repository):
        image_id = "test-banana-combined-id"

        combined_result = CombinedResult(
            image_id=image_id,
            user_id="banana_result_fetcher",
            detection_result=ProcessingResult(
                image_id=image_id,
                model_type=ModelType.DETECTION,
                results=[],
                status="success",
                request_id="test-req-id",
            ),
        )

        mock_get_result = AsyncMock(return_value=combined_result)
        mock_dynamo_repository.get_combined_result = mock_get_result

        usecase = CombinedProcessingUseCase(ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository)
        result = await usecase.get_combined_result(image_id)

        assert result is not None
        assert result.image_id == image_id
        assert result.user_id == "banana_result_fetcher"
        assert result.detection_result.model_type == ModelType.DETECTION
        assert result.detection_result.status == "success"
