from unittest.mock import AsyncMock

import pytest

from src.modules.ia_integration.usecase.detect_usecase import DetectUseCase
from src.shared.domain.entities.image import Image
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestDetectUseCase:
    @pytest.mark.asyncio
    async def test_execute_success(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_detection_raw.jpg"
        user_id = "banana_farm_inspector"
        metadata = {"original_filename": "banana_plantation_batch42.jpg"}

        detect_usecase = DetectUseCase(ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository)
        result = await detect_usecase.execute(image_url, user_id, metadata)

        assert result.model_type == ModelType.DETECTION
        assert result.status == "success"
        assert len(result.results) == 1
        assert result.results[0].class_name == "banana"
        assert result.results[0].confidence == 0.95
        assert result.image_result_url == "https://fruit-analysis.com/results/banana_detection_result.jpg"

        mock_dynamo_repository.save_image_metadata.assert_called_once()
        mock_ia_repository.detect_objects.assert_called_once()
        mock_dynamo_repository.save_processing_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_error(self, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_ripeness_analysis.jpg"
        user_id = "ripeness_quality_inspector"
        metadata = {"original_filename": "banana_maturacao_lote35.jpg"}

        mock_failing_ia_repository = AsyncMock()
        mock_failing_ia_repository.detect_objects = AsyncMock(side_effect=Exception("Falha na detecção de maturação"))

        detect_usecase = DetectUseCase(
            ia_repository=mock_failing_ia_repository,
            dynamo_repository=mock_dynamo_repository,
        )
        result = await detect_usecase.execute(image_url, user_id, metadata)

        assert result.model_type == ModelType.DETECTION
        assert result.status == "error"
        assert len(result.results) == 0
        assert "Erro interno" in result.error_message

        mock_dynamo_repository.save_image_metadata.assert_called_once()
        mock_failing_ia_repository.detect_objects.assert_called_once()
        mock_dynamo_repository.save_processing_result.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_empty_metadata(self, mock_ia_repository, mock_dynamo_repository):
        image_url = "https://fruit-analysis.com/banana_shipment_inspection.jpg"
        user_id = "distribution_center_analyst"

        detect_usecase = DetectUseCase(ia_repository=mock_ia_repository, dynamo_repository=mock_dynamo_repository)
        result = await detect_usecase.execute(image_url, user_id)

        assert result.model_type == ModelType.DETECTION
        assert result.status == "success"

        called_args = mock_ia_repository.detect_objects.call_args[0][0]
        assert isinstance(called_args, Image)
        assert called_args.image_url == image_url
        assert called_args.user_id == user_id
        assert called_args.metadata == {}

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_ia_repository):
        image_url = "https://fruit-analysis.com/banana_maturation_study.jpg"
        user_id = "banana_ripeness_researcher"

        mock_failing_dynamo_repository = AsyncMock()
        mock_failing_dynamo_repository.save_image_metadata = AsyncMock(side_effect=Exception("Erro de acesso ao banco"))

        detect_usecase = DetectUseCase(
            ia_repository=mock_ia_repository,
            dynamo_repository=mock_failing_dynamo_repository,
        )
        result = await detect_usecase.execute(image_url, user_id)

        assert result.model_type == ModelType.DETECTION
        assert result.status == "error"
        assert "Erro interno" in result.error_message
        assert mock_failing_dynamo_repository.save_image_metadata.call_count == 1
        assert mock_ia_repository.detect_objects.call_count == 0
