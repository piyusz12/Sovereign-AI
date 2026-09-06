import pytest
from unittest.mock import AsyncMock, patch

from backend.model_gateway.router import ModelGateway
from backend.model_gateway.schemas import (
    GatewayInferenceRequest,
    GatewayEmbeddingRequest,
    GatewayRerankRequest
)

@pytest.fixture
def gateway():
    return ModelGateway()

@pytest.mark.asyncio
async def test_gateway_get_provider_ollama():
    """Test ModelGateway routes to Ollama provider for reasoning-local."""
    gateway = ModelGateway()
    
    with patch("backend.model_gateway.router.get_model") as mock_get_model:
        # Mock registry response
        mock_model = type("obj", (object,), {"backend": "ollama"})
        mock_get_model.return_value = mock_model
        
        provider = gateway._get_provider("reasoning-local")
        from backend.model_gateway.client import OllamaGatewayProvider
        assert isinstance(provider, OllamaGatewayProvider)

@pytest.mark.asyncio
async def test_gateway_get_provider_vllm():
    """Test ModelGateway routes to vLLM provider when backend is vllm."""
    gateway = ModelGateway()
    
    with patch("backend.model_gateway.router.get_model") as mock_get_model:
        mock_model = type("obj", (object,), {"backend": "vllm"})
        mock_get_model.return_value = mock_model
        
        provider = gateway._get_provider("heavy-reasoning")
        from backend.model_gateway.client import VLLMGatewayProvider
        assert isinstance(provider, VLLMGatewayProvider)

@pytest.mark.asyncio
async def test_gateway_get_provider_infinity():
    """Test ModelGateway routes to Infinity provider for embeddings."""
    gateway = ModelGateway()
    
    with patch("backend.model_gateway.router.get_model") as mock_get_model:
        mock_model = type("obj", (object,), {"backend": "infinity"})
        mock_get_model.return_value = mock_model
        
        provider = gateway._get_provider("embedding-local")
        from backend.model_gateway.client import InfinityGatewayProvider
        assert isinstance(provider, InfinityGatewayProvider)

@pytest.mark.asyncio
async def test_gateway_embed_uses_cache():
    """Test that embedding request checks cache and avoids backend if found."""
    gateway = ModelGateway()
    req = GatewayEmbeddingRequest(
        model="embedding-local",
        input=["hello world"]
    )
    
    with patch("backend.model_gateway.router.embedding_cache") as mock_cache:
        # Cache hits
        mock_cache.get.return_value = [[0.1, 0.2, 0.3]]
        
        with patch.object(gateway, "_get_provider") as mock_get_provider:
            # We don't even need to mock the provider since it shouldn't be called
            res = await gateway.embed(req)
            
            assert res.embeddings == [[0.1, 0.2, 0.3]]
            mock_cache.get.assert_called_once_with("embedding-local", "hello world", None)
            mock_get_provider.assert_not_called()
