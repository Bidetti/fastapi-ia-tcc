from unittest.mock import AsyncMock

import pytest

from src.modules.ia_integration.usecase.maturation_usecase import MaturationUseCase
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestMaturationUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_maturation_analysis.jpg"
        user_id = "banana_ripeness_expert"
        metadata = {"original_filename": "banana_ripeness_study.jpg"}

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
        
        success_result = ProcessingResult(
            image_id="test-maturation-success-id",
            model_type=ModelType.MATURATION,
            results=[detection_result],
            status="success",
            request_id="test-maturation-req-id",
            summary={"average_maturation_score": 0.8, "detection_time_ms": 450},
            image_result_url="https://test-result-url.com/maturation",
        )

        mock_ia_repository.analyze_maturation = AsyncMock(return_value=success_result)
        mock_dynamo_repository.save_image_metadata = AsyncMock(return_value={"image_id": "test-maturation-success-id"})
        mock_dynamo_repository.save_processing_result = AsyncMock(return_value=True)

        maturation_usecase = MaturationUseCase(
            ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository
        )
        result = await maturation_usecase.execute(image_url, user_id, metadata)

        assert result.model_type == ModelType.MATURATION
        assert result.status == "success"
        assert len(result.results) == 1
        assert result.results[0].class_name == "banana"
        assert result.results[0].maturation_level["category"] == "ripe"

    @pytest.mark.asyncio
    async def test_execute_with_error(self, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_ripeness_failed.jpg"
        user_id = "banana_quality_manager"
        metadata = {"original_filename": "banana_maturacao_error.jpg"}

        mock_failing_ia_repository = AsyncMock()
        mock_failing_ia_repository.analyze_maturation = AsyncMock(
            side_effect=Exception("Falha na análise de maturação")
        )

        maturation_usecase = MaturationUseCase(
            ia_repository=mock_failing_ia_repository,
            dynamo_repository=mock_dynamo_repository,
        )
        result = await maturation_usecase.execute(image_url, user_id, metadata)

        assert result.model_type == ModelType.MATURATION
        assert result.status == "error"
        assert len(result.results) == 0
        assert "Erro interno" in result.error_message

        mock_dynamo_repository.save_image_metadata.assert_called_once()
        mock_failing_ia_repository.analyze_maturation.assert_called_once()
        mock_dynamo_repository.save_processing_result.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_empty_metadata(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_ripeness_assessment.jpg"
        user_id = "distribution_center_quality"

        success_result = ProcessingResult(
            image_id="test-maturation-no-metadata-id",
            model_type=ModelType.MATURATION,
            results=[],
            status="success",
            request_id="test-maturation-no-metadata-req-id",
        )

        mock_ia_repository.analyze_maturation = AsyncMock(return_value=success_result)
        mock_dynamo_repository.save_image_metadata = AsyncMock(
            return_value={"image_id": "test-maturation-no-metadata-id"}
        )
        mock_dynamo_repository.save_processing_result = AsyncMock(return_value=True)

        maturation_usecase = MaturationUseCase(
            ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository
        )
        result = await maturation_usecase.execute(image_url, user_id)

        assert result.model_type == ModelType.MATURATION
        assert result.status == "success"

        called_args = mock_ia_repository.analyze_maturation.call_args[0][0]
        assert isinstance(called_args, Image)
        assert called_args.image_url == image_url
        assert called_args.user_id == user_id
        assert called_args.metadata == {}

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_ia_repository):
        image_url = "https://fruit-analysis.com/banana_maturation_database_error.jpg"
        user_id = "banana_database_analyst"

        mock_failing_dynamo_repository = AsyncMock()
        mock_failing_dynamo_repository.save_image_metadata = AsyncMock(side_effect=Exception("Erro de banco de dados"))

        maturation_usecase = MaturationUseCase(
            ia_repository=mock_ia_repository,
            dynamo_repository=mock_failing_dynamo_repository,
        )
        result = await maturation_usecase.execute(image_url, user_id)

        assert result.model_type == ModelType.MATURATION
        assert result.status == "error"
        assert "Erro interno" in result.error_message
        assert mock_failing_dynamo_repository.save_image_metadata.call_count == 1
        assert mock_ia_repository.analyze_maturation.call_count == 0
