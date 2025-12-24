"""
LLM Integration Module
=======================

Provides LLM integration for GraphRAG query processing.
Supports OpenAI, Anthropic Claude, and local models.

Author: Rajesh Kumar Gupta
"""

import os
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    NONE = "none"


@dataclass
class LLMResponse:
    """Response from LLM"""
    content: str
    model: str
    tokens_used: int = 0
    finish_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from prompt"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if client is available"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
                logger.info(f"OpenAI client initialized (model: {model})")
            except ImportError:
                logger.warning("openai package not installed")
    
    def is_available(self) -> bool:
        return self._client is not None
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        if not self._client:
            return LLMResponse(content="OpenAI client not available", model=self.model)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                finish_reason=response.choices[0].finish_reason,
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return LLMResponse(content=f"Error: {e}", model=self.model)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None
        
        if self.api_key:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"Anthropic client initialized (model: {model})")
            except ImportError:
                logger.warning("anthropic package not installed")
    
    def is_available(self) -> bool:
        return self._client is not None
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
        **kwargs
    ) -> LLMResponse:
        if not self._client:
            return LLMResponse(content="Anthropic client not available", model=self.model)
        
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}],
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens if response.usage else 0,
                finish_reason=response.stop_reason,
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return LLMResponse(content=f"Error: {e}", model=self.model)


class LocalLLMClient(BaseLLMClient):
    """Local LLM client (placeholder for ollama, llama.cpp, etc.)"""
    
    def __init__(self, model: str = "llama2", endpoint: str = "http://localhost:11434"):
        self.model = model
        self.endpoint = endpoint
        self._available = False
        
        # Try to connect
        try:
            import requests
            response = requests.get(f"{endpoint}/api/tags", timeout=2)
            self._available = response.status_code == 200
            if self._available:
                logger.info(f"Local LLM client connected to {endpoint}")
        except:
            pass
    
    def is_available(self) -> bool:
        return self._available
    
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        if not self._available:
            return LLMResponse(content="Local LLM not available", model=self.model)
        
        try:
            import requests
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=120,
            )
            data = response.json()
            return LLMResponse(
                content=data.get("response", ""),
                model=self.model,
            )
        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            return LLMResponse(content=f"Error: {e}", model=self.model)


# =============================================================================
# GRAPHRAG PROMPT TEMPLATES
# =============================================================================

GRAPHRAG_SYSTEM_PROMPT = """You are a financial analyst assistant with access to a knowledge graph containing information about companies, financial metrics, risks, and economic indicators.

Your role is to:
1. Analyze the provided knowledge graph context
2. Answer questions accurately based on the available data
3. Cite specific entities and relationships from the graph
4. Acknowledge when information is not available in the graph

When answering:
- Be specific and cite evidence from the graph
- Use financial terminology appropriately
- If the graph doesn't contain enough information, say so
- Format numerical values with appropriate units (millions, billions)
"""

CYPHER_GENERATION_PROMPT = """Given the following question, generate a Cypher query to retrieve relevant information from a Neo4j knowledge graph.

The graph has these node types:
- Company (properties: name, ticker, cik, sector)
- FinancialMetric (properties: name, value, currency, fiscalYear)
- Risk (properties: name, entity_type, severity)
- Person (properties: name, title)
- Product (properties: name)
- EconomicIndicator (properties: name, value, date)

The graph has these relationship types:
- FACES_RISK (Company -> Risk)
- COMPETES_WITH (Company -> Company)
- REPORTED (Company -> FinancialMetric)
- CEO_OF (Person -> Company)
- MANUFACTURES (Company -> Product)
- IMPACTED_BY (Company -> EconomicIndicator)

Question: {question}

Generate a Cypher query that would retrieve the relevant information. Only output the Cypher query, nothing else.
"""

CONTEXT_ANSWER_PROMPT = """Based on the following knowledge graph context, answer the question.

KNOWLEDGE GRAPH CONTEXT:
{context}

QUESTION: {question}

Provide a comprehensive answer based on the graph data. If the information is not available in the graph, acknowledge this limitation.

ANSWER:"""

ENTITY_EXTRACTION_PROMPT = """Extract financial entities from the following text. For each entity, identify:
1. The entity text
2. The entity type (Company, Person, FinancialMetric, Risk, Product, Date, MonetaryAmount)
3. Any associated values or properties

TEXT:
{text}

Output the entities in JSON format:
{{"entities": [
  {{"text": "...", "type": "...", "properties": {{...}}}}
]}}
"""

RELATION_EXTRACTION_PROMPT = """Given the following text and entities, extract relationships between them.

TEXT:
{text}

ENTITIES:
{entities}

For each relationship, identify:
1. Subject entity
2. Predicate/relationship type (COMPETES_WITH, FACES_RISK, REPORTED, CEO_OF, MANUFACTURES, ACQUIRED, PARTNERS_WITH)
3. Object entity
4. Evidence text

Output relationships in JSON format:
{{"relations": [
  {{"subject": "...", "predicate": "...", "object": "...", "evidence": "..."}}
]}}
"""


# =============================================================================
# LLM MANAGER
# =============================================================================

class LLMManager:
    """
    Manages LLM clients and provides unified interface.
    
    Features:
    - Multi-provider support (OpenAI, Anthropic, Local)
    - Automatic fallback between providers
    - Prompt template management
    - Response caching (optional)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.clients: Dict[LLMProvider, BaseLLMClient] = {}
        self.primary_provider: Optional[LLMProvider] = None
        
        self._init_clients()
    
    def _init_clients(self) -> None:
        """Initialize LLM clients based on config"""
        
        # Try OpenAI
        openai_config = self.config.get("openai", {})
        openai_client = OpenAIClient(
            api_key=openai_config.get("api_key"),
            model=openai_config.get("model", "gpt-4"),
        )
        if openai_client.is_available():
            self.clients[LLMProvider.OPENAI] = openai_client
            if not self.primary_provider:
                self.primary_provider = LLMProvider.OPENAI
        
        # Try Anthropic
        anthropic_config = self.config.get("anthropic", {})
        anthropic_client = AnthropicClient(
            api_key=anthropic_config.get("api_key"),
            model=anthropic_config.get("model", "claude-3-sonnet-20240229"),
        )
        if anthropic_client.is_available():
            self.clients[LLMProvider.ANTHROPIC] = anthropic_client
            if not self.primary_provider:
                self.primary_provider = LLMProvider.ANTHROPIC
        
        # Try Local
        local_config = self.config.get("local", {})
        if local_config.get("enabled", False):
            local_client = LocalLLMClient(
                model=local_config.get("model", "llama2"),
                endpoint=local_config.get("endpoint", "http://localhost:11434"),
            )
            if local_client.is_available():
                self.clients[LLMProvider.LOCAL] = local_client
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.LOCAL
        
        if self.primary_provider:
            logger.info(f"LLMManager initialized with primary provider: {self.primary_provider.value}")
        else:
            logger.warning("No LLM provider available")
    
    def is_available(self) -> bool:
        """Check if any LLM is available"""
        return self.primary_provider is not None
    
    def generate(
        self, 
        prompt: str,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using specified or primary provider"""
        provider = provider or self.primary_provider
        
        if not provider or provider not in self.clients:
            return LLMResponse(
                content="No LLM provider available",
                model="none",
            )
        
        return self.clients[provider].generate(prompt, **kwargs)
    
    def generate_with_fallback(self, prompt: str, **kwargs) -> LLMResponse:
        """Try all available providers until one succeeds"""
        for provider, client in self.clients.items():
            try:
                response = client.generate(prompt, **kwargs)
                if response.content and not response.content.startswith("Error:"):
                    return response
            except Exception as e:
                logger.warning(f"Provider {provider.value} failed: {e}")
                continue
        
        return LLMResponse(content="All LLM providers failed", model="none")
    
    def generate_cypher(self, question: str) -> str:
        """Generate Cypher query from natural language question"""
        prompt = CYPHER_GENERATION_PROMPT.format(question=question)
        response = self.generate(prompt, temperature=0.0)
        
        # Clean up the response
        cypher = response.content.strip()
        cypher = re.sub(r'^```(?:cypher)?\n?', '', cypher)
        cypher = re.sub(r'\n?```$', '', cypher)
        
        return cypher
    
    def answer_with_context(self, question: str, context: str) -> str:
        """Answer question using knowledge graph context"""
        prompt = CONTEXT_ANSWER_PROMPT.format(
            context=context,
            question=question,
        )
        response = self.generate(
            prompt,
            system_prompt=GRAPHRAG_SYSTEM_PROMPT,
            temperature=0.1,
        )
        return response.content
    
    def extract_entities_llm(self, text: str) -> List[Dict]:
        """Use LLM to extract entities from text"""
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text[:4000])
        response = self.generate(prompt, temperature=0.0)
        
        try:
            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("entities", [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse entity extraction response")
        
        return []
    
    def extract_relations_llm(self, text: str, entities: List[Dict]) -> List[Dict]:
        """Use LLM to extract relations from text"""
        entities_str = json.dumps(entities, indent=2)
        prompt = RELATION_EXTRACTION_PROMPT.format(
            text=text[:4000],
            entities=entities_str,
        )
        response = self.generate(prompt, temperature=0.0)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response.content)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("relations", [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse relation extraction response")
        
        return []


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

_llm_manager_instance: Optional[LLMManager] = None


def get_llm_manager(config: Optional[Dict] = None) -> LLMManager:
    """Get or create LLM manager singleton"""
    global _llm_manager_instance
    if _llm_manager_instance is None:
        _llm_manager_instance = LLMManager(config)
    return _llm_manager_instance
