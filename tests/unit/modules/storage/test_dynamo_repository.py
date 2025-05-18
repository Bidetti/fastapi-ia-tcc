from unittest.mock import AsyncMock, patch

import pytest

from src.modules.storage.repo.dynamo_repository import DynamoRepository
from src.shared.domain.entities.combined_result import CombinedResult
from src.shared.domain.entities.image import Image
from src.shared.domain.entities.result import DetectionResult, ProcessingResult
from src.shared.domain.enums.ia_model_type_enum import ModelType


class TestDynamoRepository:
    @pytest.mark.asyncio
    async def test_save_image_metadata(self, mock_dynamo_client):
        image = Image(
            image_url="https://fruit-analysis.com/banana_metadata.jpg",
            user_id="banana_metadata_manager",
            metadata={"quality": "premium"},
            image_id="test-banana-metadata-id",
        )

        mock_dynamo_client.put_item.return_value = {
            "pk": f"IMG#{image.image_id}",
            "sk": f"META#{image.image_id}",
            "image_id": image.image_id,
            "user_id": image.user_id,
        }

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.save_image_metadata(image)

        assert result["pk"] == f"IMG#{image.image_id}"
        assert result["sk"] == f"META#{image.image_id}"
        assert result["image_id"] == image.image_id

        called_item = mock_dynamo_client.put_item.call_args[0][0]
        assert called_item["pk"] == f"IMG#{image.image_id}"
        assert called_item["sk"] == f"META#{image.image_id}"
        assert called_item["entity_type"] == "IMAGE"
        assert called_item["user_id"] == image.user_id

    @pytest.mark.asyncio
    async def test_save_processing_result(self, mock_dynamo_client):
        detection_result = DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])

        processing_result = ProcessingResult(
            image_id="test-banana-processing-id",
            model_type=ModelType.DETECTION,
            results=[detection_result],
            status="success",
            request_id="test-banana-request-id",
            summary={"total_objects": 1},
        )

        mock_dynamo_client.put_item.return_value = {
            "pk": f"IMG#{processing_result.image_id}",
            "sk": f"RESULT#{processing_result.request_id}",
            "image_id": processing_result.image_id,
            "request_id": processing_result.request_id,
        }

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.save_processing_result(processing_result)

        assert result["pk"] == f"IMG#{processing_result.image_id}"
        assert result["sk"] == f"RESULT#{processing_result.request_id}"
        assert result["image_id"] == processing_result.image_id
        assert result["request_id"] == processing_result.request_id

        called_item = mock_dynamo_client.put_item.call_args[0][0]
        assert called_item["pk"] == f"IMG#{processing_result.image_id}"
        assert called_item["sk"] == f"RESULT#{processing_result.request_id}"
        assert called_item["entity_type"] == "RESULT"
        assert called_item["model_type"] == processing_result.model_type.value

    @pytest.mark.asyncio
    async def test_get_image_by_id(self, mock_dynamo_client):
        image_id = "test-banana-query-id"
        expected_item = {
            "image_id": image_id,
            "image_url": "https://fruit-analysis.com/banana_query.jpg",
            "user_id": "banana_query_user",
            "metadata": {},
            "upload_timestamp": "2025-05-12T10:30:00",
        }

        mock_dynamo_client.get_item.return_value = expected_item

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.get_image_by_id(image_id)

        assert isinstance(result, Image)
        assert result.image_id == image_id
        assert result.image_url == expected_item["image_url"]
        assert result.user_id == expected_item["user_id"]

        called_key = mock_dynamo_client.get_item.call_args[0][0]
        assert called_key["pk"] == f"IMG#{image_id}"
        assert called_key["sk"] == f"META#{image_id}"

    @pytest.mark.asyncio
    async def test_get_image_by_id_not_found(self, mock_dynamo_client):
        image_id = "test-banana-notfound-id"
        mock_dynamo_client.get_item.return_value = None

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.get_image_by_id(image_id)

        assert result is None
        called_key = mock_dynamo_client.get_item.call_args[0][0]
        assert called_key["pk"] == f"IMG#{image_id}"

    @pytest.mark.asyncio
    async def test_get_result_by_request_id(self, mock_dynamo_client):
        request_id = "test-banana-result-req"

        mock_result = {
            "image_id": "test-banana-result-id",
            "request_id": request_id,
            "model_type": "detection",
            "results": [{"class_name": "banana", "confidence": 0.95, "bounding_box": [0.1, 0.1, 0.2, 0.2]}],
            "status": "success",
            "processing_timestamp": "2025-05-12T10:30:00",
            "summary": {"total_objects": 1},
        }

        mock_dynamo_client.query_items = AsyncMock(return_value=[mock_result])

        with patch("src.shared.domain.entities.result.ProcessingResult.from_dict") as mock_from_dict:
            mock_from_dict.return_value = ProcessingResult(
                image_id="test-banana-result-id",
                model_type=ModelType.DETECTION,
                results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
                status="success",
                request_id=request_id,
            )

            repo = DynamoRepository(dynamo_client=mock_dynamo_client)
            result = await repo.get_result_by_request_id(request_id)

            assert result.image_id == "test-banana-result-id"
            assert result.request_id == request_id
            assert result.status == "success"
            assert result.model_type == ModelType.DETECTION
            assert len(result.results) == 1
            assert result.results[0].class_name == "banana"
            assert result.results[0].confidence == 0.95
            assert result.results[0].bounding_box == [0.1, 0.1, 0.2, 0.2]
            assert result.results[0].maturation_level is None

            mock_dynamo_client.query_items.assert_called_once_with(
                key_name="request_id", key_value=request_id, index_name="RequestIdIndex"
            )

    @pytest.mark.asyncio
    async def test_get_results_by_image_id(self, mock_dynamo_client):
        image_id = "test-banana-results-id"

        mock_items = [
            {
                "entity_type": "RESULT",
                "image_id": image_id,
                "request_id": "detection-req-1",
                "model_type": "detection",
                "results": [{"class_name": "banana", "confidence": 0.95, "bounding_box": [0.1, 0.1, 0.2, 0.2]}],
                "status": "success",
                "processing_timestamp": "2025-05-12T10:30:00",
            },
            {
                "entity_type": "RESULT",
                "image_id": image_id,
                "request_id": "maturation-req-1",
                "model_type": "maturation",
                "results": [
                    {
                        "class_name": "banana",
                        "confidence": 0.95,
                        "bounding_box": [0.1, 0.1, 0.2, 0.2],
                        "maturation_level": {"score": 0.8, "category": "ripe"},
                    }
                ],
                "status": "success",
                "processing_timestamp": "2025-05-12T10:35:00",
            },
            {
                "entity_type": "IMAGE",
                "image_id": image_id,
                "user_id": "banana_user",
            },
        ]

        mock_dynamo_client.query_items.return_value = mock_items

        with patch("src.shared.domain.entities.result.ProcessingResult.from_dict") as mock_from_dict:
            mock_from_dict.side_effect = [
                ProcessingResult(
                    image_id=image_id,
                    model_type=ModelType.DETECTION,
                    results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
                    status="success",
                    request_id="detection-req-1",
                ),
                ProcessingResult(
                    image_id=image_id,
                    model_type=ModelType.MATURATION,
                    results=[
                        DetectionResult(
                            class_name="banana",
                            confidence=0.95,
                            bounding_box=[0.1, 0.1, 0.2, 0.2],
                            maturation_level={"score": 0.8, "category": "ripe"},
                        )
                    ],
                    status="success",
                    request_id="maturation-req-1",
                ),
            ]

            repo = DynamoRepository(dynamo_client=mock_dynamo_client)
            results = await repo.get_results_by_image_id(image_id)

            assert len(results) == 2
            assert all(r.image_id == image_id for r in results)
            assert results[0].model_type == ModelType.DETECTION
            assert results[1].model_type == ModelType.MATURATION

        mock_dynamo_client.query_items.assert_called_once_with(key_name="pk", key_value=f"IMG#{image_id}")

    @pytest.mark.asyncio
    async def test_save_combined_result(self, mock_dynamo_client):
        detection_result = ProcessingResult(
            image_id="test-banana-combined-id",
            model_type=ModelType.DETECTION,
            results=[DetectionResult(class_name="banana", confidence=0.95, bounding_box=[0.1, 0.1, 0.2, 0.2])],
            status="success",
            request_id="detection-req-id",
            summary={"total_objects": 1},
        )

        maturation_result = ProcessingResult(
            image_id="test-banana-combined-id",
            model_type=ModelType.MATURATION,
            results=[
                DetectionResult(
                    class_name="banana",
                    confidence=0.95,
                    bounding_box=[0.1, 0.1, 0.2, 0.2],
                    maturation_level={"score": 0.8, "category": "ripe"},
                )
            ],
            status="success",
            request_id="maturation-req-id",
            summary={"average_maturation_score": 0.8},
        )

        combined_result = CombinedResult(
            image_id="test-banana-combined-id",
            user_id="banana_combined_user",
            detection_result=detection_result,
            maturation_result=maturation_result,
            location="warehouse_C",
        )

        mock_dynamo_client.put_item.return_value = {
            "combined_id": combined_result.combined_id,
            "image_id": combined_result.image_id,
        }

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.save_combined_result(combined_result)

        assert result["combined_id"] == combined_result.combined_id
        assert result["image_id"] == combined_result.image_id

        called_item = mock_dynamo_client.put_item.call_args[0][0]
        assert called_item["combined_id"] == combined_result.combined_id
        assert called_item["image_id"] == combined_result.image_id
        assert called_item["user_id"] == combined_result.user_id
        assert called_item["location"] == combined_result.location

    @pytest.mark.asyncio
    async def test_get_combined_result(self, mock_dynamo_client):
        image_id = "test-banana-get-combined-id"

        mock_item = {
            "pk": f"IMG#{image_id}",
            "sk": "RESULT#COMBINED",
            "entity_type": "COMBINED_RESULT",
            "combined_id": "combined-test-id",
            "image_id": image_id,
            "user_id": "banana_combined_getter",
            "processing_timestamp": "2025-05-12T10:30:00",
            "detection": {
                "request_id": "detection-req-id",
                "status": "success",
                "processing_timestamp": "2025-05-12T10:25:00",
                "summary": {"total_objects": 1},
                "image_result_url": "https://fruit-analysis.com/results/banana_detection.jpg",
            },
            "results": [
                {
                    "class_name": "banana",
                    "confidence": 0.95,
                    "bounding_box": [0.1, 0.1, 0.2, 0.2],
                    "maturation_level": {"score": 0.8, "category": "ripe"},
                }
            ],
            "total_processing_time_ms": 800,
            "status": "completed",
            "created_at": "2025-05-12T10:20:00",
            "updated_at": "2025-05-12T10:35:00",
            "location": "warehouse_D",
            "maturation": {
                "request_id": "maturation-req-id",
                "status": "success",
                "processing_timestamp": "2025-05-12T10:30:00",
                "summary": {"average_maturation_score": 0.8},
                "image_result_url": "https://fruit-analysis.com/results/banana_maturation.jpg",
            },
        }

        mock_dynamo_client.get_item.return_value = mock_item
        mock_dynamo_client.convert_from_dynamo_item.return_value = mock_item

        repo = DynamoRepository(dynamo_client=mock_dynamo_client)
        result = await repo.get_combined_result(image_id)

        assert isinstance(result, CombinedResult)
        assert result.image_id == image_id
        assert result.combined_id == "combined-test-id"
        assert result.user_id == "banana_combined_getter"
        assert result.location == "warehouse_D"
        assert result.status == "completed"
        assert isinstance(result.detection_result, ProcessingResult)
        assert isinstance(result.maturation_result, ProcessingResult)

        called_key = mock_dynamo_client.get_item.call_args[0][0]
        assert called_key["pk"] == f"IMG#{image_id}"
        assert called_key["sk"] == "RESULT#COMBINED"
