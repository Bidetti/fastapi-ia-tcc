import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from src.shared.infra.external.ec2.ec2_client import EC2Client


class TestEC2Client:
    @pytest.mark.asyncio
    async def test_detect_objects_success(self):
        image_url = "https://fruit-analysis-bucket.s3.amazonaws.com/banana_batch_47.jpg"
        metadata = {"user_id": "banana_quality_inspector"}
        
        mock_response = {
            "status": "success",
            "request_id": "banana-detection-req-45871",
            "results": [
                {
                    "class": "banana",
                    "confidence": 0.95,
                    "bounding_box": [0.1, 0.2, 0.3, 0.4]
                }
            ],
            "summary": {"total_objects": 1, "detection_time_ms": 350},
            "image_result_url": "https://fruit-analysis-bucket.s3.amazonaws.com/results/banana_detection_result.jpg"
        }
        
        with patch.object(EC2Client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            ec2_client = EC2Client(base_url="http://banana-analysis-api.com")
            result = await ec2_client.detect_objects(image_url, metadata)
            
            assert result == mock_response
            expected_payload = {
                "image_url": image_url,
                "metadata": metadata
            }
            mock_make_request.assert_called_once_with(
                "http://banana-analysis-api.com/detect", 
                expected_payload
            )
    
    @pytest.mark.asyncio
    async def test_analyze_maturation_success(self):
        image_url = "https://fruit-analysis-bucket.s3.amazonaws.com/banana_maturation_sample.jpg"
        metadata = {"user_id": "banana_ripeness_expert"}
        
        mock_response = {
            "status": "success",
            "request_id": "banana-maturation-req-7832",
            "results": [
                {
                    "class": "banana",
                    "confidence": 0.95,
                    "bounding_box": [0.1, 0.2, 0.3, 0.4],
                    "maturation_level": {
                        "score": 0.8,
                        "category": "ripe",
                        "estimated_days_until_spoilage": 3
                    }
                }
            ],
            "summary": {"average_maturation_score": 0.8, "detection_time_ms": 450},
            "image_result_url": "https://fruit-analysis-bucket.s3.amazonaws.com/results/banana_maturation_result.jpg"
        }
        
        with patch.object(EC2Client, '_make_request', new_callable=AsyncMock) as mock_make_request:
            mock_make_request.return_value = mock_response
            
            ec2_client = EC2Client(base_url="http://banana-analysis-api.com")
            result = await ec2_client.analyze_maturation(image_url, metadata)
            
            assert result == mock_response
            expected_payload = {
                "image_url": image_url,
                "metadata": metadata
            }
            mock_make_request.assert_called_once_with(
                "http://banana-analysis-api.com/maturation", 
                expected_payload
            )
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        url = "http://banana-analysis-api.com/detect"
        payload = {"image_url": "https://fruit-analysis-bucket.s3.amazonaws.com/banana_ripeness_check.jpg"}
        mock_response = {"status": "success"}
        
        # Configure o mock para retornar corretamente
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value.status = 200
        mock_context.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
        
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.post.return_value = mock_context
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            ec2_client = EC2Client()
            result = await ec2_client._make_request(url, payload)
            
            assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        url = "http://banana-analysis-api.com/detect"
        payload = {"image_url": "https://fruit-analysis-bucket.s3.amazonaws.com/banana_maturation_batch56.jpg"}
        
        mock_resp = AsyncMock()
        mock_resp.status = 404
        mock_resp.text = AsyncMock(return_value="Análise de maturação não disponível")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock()
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            ec2_client = EC2Client()
            result = await ec2_client._make_request(url, payload)
            
            assert result["status"] == "error"
            assert "Erro 404" in result["error_message"]
            mock_session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self):
        url = "http://banana-analysis-api.com/detect"
        payload = {"image_url": "https://fruit-analysis-bucket.s3.amazonaws.com/banana_ripeness_timeline.jpg"}
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=aiohttp.ClientError("Erro ao conectar ao serviço de análise de maturação"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            ec2_client = EC2Client()
            result = await ec2_client._make_request(url, payload)
            
            assert result["status"] == "error"
            assert "Erro de conexão" in result["error_message"]
            mock_session.post.assert_called_once()