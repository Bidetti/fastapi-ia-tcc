from unittest.mock import AsyncMock, patch

import pytest

from src.modules.ia_integration.repo.ia_repository import IARepository
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestIARepository:
    @pytest.mark.asyncio
    async def test_detect_objects_success(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_detection.jpg",
            user_id="banana_inspector",
            metadata={"batch": "banana_harvest_45"},
            image_id="test-banana-image-id",
        )

        mock_ec2_client.detect_objects = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "banana-detection-req-123",
                "results": [
                    {
                        "class_name": "banana",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    }
                ],
                "summary": {"total_objects": 1, "detection_time_ms": 350},
                "image_result_url": "https://fruit-analysis.com/results/banana_detection_result.jpg",
            }
        )

        ia_repository = IARepository(ec2_client=mock_ec2_client)
        result = await ia_repository.detect_objects(image)

        assert result.image_id == image.image_id
        assert result.model_type == ModelType.DETECTION
        assert result.status == "success"
        assert len(result.results) == 1
        assert result.results[0].class_name == "banana"
        assert result.results[0].confidence == 0.95
        assert result.results[0].bounding_box == [0.1, 0.1, 0.2, 0.2]
        assert result.summary == {"total_objects": 1, "detection_time_ms": 350}
        assert result.image_result_url == "https://fruit-analysis.com/results/banana_detection_result.jpg"

        mock_ec2_client.detect_objects.assert_called_once_with(image_url=image.image_url, metadata=image.metadata)

    @pytest.mark.asyncio
    async def test_detect_objects_error(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_detection_error.jpg",
            user_id="banana_error_analyst",
            image_id="test-banana-error-id",
        )

        mock_ec2_client.detect_objects = AsyncMock(
            return_value={
                "status": "error",
                "error_message": "Falha na detecção de bananas",
            }
        )

        ia_repository = IARepository(ec2_client=mock_ec2_client)
        result = await ia_repository.detect_objects(image)

        assert result.image_id == image.image_id
        assert result.model_type == ModelType.DETECTION
        assert result.status == "error"
        assert len(result.results) == 0
        assert "Falha na detecção de bananas" in result.error_message

        mock_ec2_client.detect_objects.assert_called_once_with(image_url=image.image_url, metadata=image.metadata)

    @pytest.mark.asyncio
    async def test_detect_objects_exception(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_detection_exception.jpg",
            user_id="banana_exception_handler",
            image_id="test-banana-exception-id",
        )

        mock_ec2_client.detect_objects = AsyncMock(
            side_effect=Exception("Erro na comunicação com o serviço de detecção")
        )

        ia_repository = IARepository(ec2_client=mock_ec2_client)
        result = await ia_repository.detect_objects(image)

        assert result.image_id == image.image_id
        assert result.model_type == ModelType.DETECTION
        assert result.status == "error"
        assert len(result.results) == 0
        assert "Erro interno:" in result.error_message

        mock_ec2_client.detect_objects.assert_called_once_with(image_url=image.image_url, metadata=image.metadata)

    @pytest.mark.asyncio
    async def test_analyze_maturation_success(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_maturation.jpg",
            user_id="banana_ripeness_analyst",
            metadata={"variety": "prata"},
            image_id="test-banana-ripeness-id",
        )

        mock_ec2_client.analyze_maturation = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "banana-maturation-req-456",
                "results": [
                    {
                        "class_name": "banana",
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
                "image_result_url": "https://fruit-analysis.com/results/banana_maturation_result.jpg",
            }
        )

        ia_repository = IARepository(ec2_client=mock_ec2_client)
        result = await ia_repository.analyze_maturation(image)

        assert result.image_id == image.image_id
        assert result.model_type == ModelType.MATURATION
        assert result.status == "success"
        assert len(result.results) == 1
        assert result.results[0].class_name == "banana"
        assert result.results[0].confidence == 0.95
        assert result.results[0].maturation_level["score"] == 0.8
        assert result.results[0].maturation_level["category"] == "ripe"
        assert result.summary == {"average_maturation_score": 0.8, "detection_time_ms": 450}
        assert result.image_result_url == "https://fruit-analysis.com/results/banana_maturation_result.jpg"

        mock_ec2_client.analyze_maturation.assert_called_once_with(image_url=image.image_url, metadata=image.metadata)

    @pytest.mark.asyncio
    async def test_analyze_maturation_error(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_maturation_error.jpg",
            user_id="banana_ripeness_error_handler",
            image_id="test-banana-ripeness-error-id",
        )

        mock_ec2_client.analyze_maturation = AsyncMock(
            return_value={
                "status": "error",
                "error_message": "Falha na análise de maturação de bananas",
            }
        )

        ia_repository = IARepository(ec2_client=mock_ec2_client)
        result = await ia_repository.analyze_maturation(image)

        assert result.image_id == image.image_id
        assert result.model_type == ModelType.MATURATION
        assert result.status == "error"
        assert len(result.results) == 0
        assert "Falha na análise de maturação de bananas" in result.error_message

        mock_ec2_client.analyze_maturation.assert_called_once_with(image_url=image.image_url, metadata=image.metadata)

    @pytest.mark.asyncio
    async def test_analyze_maturation_with_boxes_success(self, mock_ec2_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_multiple.jpg",
            user_id="banana_multi_analyst",
            image_id="test-banana-multi-id",
        )

        bounding_boxes = [
            {
                "index": 0,
                "class_name": "banana",
                "confidence": 0.95,
                "bounding_box": [0.1, 0.1, 0.2, 0.2],
            },
            {
                "index": 1,
                "class_name": "banana",
                "confidence": 0.92,
                "bounding_box": [0.5, 0.5, 0.2, 0.2],
            },
        ]

        parent_request_id = "banana-parent-req-789"

        mock_ec2_client.analyze_maturation_with_boxes = AsyncMock(
            return_value={
                "status": "success",
                "request_id": "banana-boxes-maturation-req-789",
                "results": [
                    {
                        "class_name": "banana",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                        "maturation_level": {
                            "score": 0.8,
                            "category": "ripe",
                            "estimated_days_until_spoilage": 3,
                        },
                    },
                    {
                        "class_name": "banana",
                        "confidence": 0.92,
                        "bounding_box": [0.5, 0.5, 0.2, 0.2],
                        "maturation_level": {
                            "score": 0.6,
                            "category": "semi-ripe",
                            "estimated_days_until_spoilage": 5,
                        },
                    },
                ],
                "summary": {"average_maturation_score": 0.7, "detection_time_ms": 550},
                "image_result_url": "https://fruit-analysis.com/results/banana_maturation_boxes_result.jpg",
            }
        )

        def custom_analyze_maturation_with_boxes(*args, **kwargs):
            return ProcessingResult(
                image_id="test-banana-multi-id",
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
                    ),
                    DetectionResult(
                        class_name="banana",
                        confidence=0.92,
                        bounding_box=[0.5, 0.5, 0.2, 0.2],
                        maturation_level={
                            "score": 0.6,
                            "category": "semi-ripe",
                            "estimated_days_until_spoilage": 5,
                        },
                    ),
                ],
                status="success",
                request_id="banana-boxes-maturation-req-789",
                summary={"average_maturation_score": 0.7, "detection_time_ms": 550},
                image_result_url="https://fruit-analysis.com/results/banana_maturation_boxes_result.jpg",
            )

        with patch.object(
            IARepository, "analyze_maturation_with_boxes", side_effect=custom_analyze_maturation_with_boxes
        ):
            ia_repository = IARepository(ec2_client=mock_ec2_client)
            result = await ia_repository.analyze_maturation_with_boxes(
                image=image, bounding_boxes=bounding_boxes, parent_request_id=parent_request_id
            )

            assert result.image_id == "test-banana-multi-id"
            assert result.model_type == ModelType.MATURATION
            assert len(result.results) == 2
            assert result.results[0].class_name == "banana"
            assert result.results[0].confidence == 0.95
            assert result.results[0].maturation_level["category"] == "ripe"
            assert result.results[1].confidence == 0.92
            assert result.results[1].maturation_level["category"] == "semi-ripe"
