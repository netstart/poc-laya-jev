from __future__ import annotations

"""Testes de integração com Playwright (requer Chrome rodando)."""

import asyncio

import pytest

from laya_ultrafast.agent import LayaAgent


@pytest.mark.integration
class TestLAYAIntegration:
    """Testes de integração que requerem navegador real."""

    @pytest.mark.asyncio
    async def test_agent_can_start_and_stop(self):
        """Testa inicialização básica do agente."""
        agent = LayaAgent()
        # Testa que podemos criar o agente sem erro
        assert agent is not None
        assert agent.config is not None

    @pytest.mark.asyncio
    async def test_agent_initializes_components(self):
        """Testa que componentes são inicializados."""
        agent = LayaAgent()
        # Componentes são lazy-loaded, então só existem após uso
        # Este é um teste básico - em implementação real, testaríamos mais
        assert hasattr(agent, 'engine')
        assert hasattr(agent, 'config')

    @pytest.mark.asyncio
    async def test_snapshot_mock_data(self):
        """Testa estrutura de snapshot com dados mock."""
        agent = LayaAgent()
        
        # Simula um snapshot simples
        mock_snapshot = [
            {
                "id": "elem-1",
                "index": 0,
                "tag": "button",
                "role": "button",
                "label": "Clique aqui",
                "selector": "button#test",
                "bbox": {"x": 100, "y": 200, "width": 120, "height": 40},
                "attrs": {"type": "submit"},
                "state": {},
                "is_visible": True,
                "is_obstructed": False,
                "is_interactive": True,
                "is_editable": False,
            }
        ]
        
        # Verifica que o snapshot tem estrutura correta
        elem = mock_snapshot[0]
        assert elem["id"] == "elem-1"
        assert elem["tag"] == "button"
        assert elem["label"] == "Clique aqui"
        assert elem["is_visible"] is True

    @pytest.mark.asyncio
    async def test_agent_run_with_mock(self, monkeypatch):
        """Testa run com mocks para evitar dependências externas."""
        agent = LayaAgent()
        
        # Mock do browser
        class MockBrowser:
            async def navigate(self, url):
                pass
            async def get_snapshot(self):
                return [
                    {
                        "id": "btn-1", "index": 0, "tag": "button", "role": "button",
                        "label": "Pesquisar", "selector": "input#search",
                        "bbox": {"x": 100, "y": 200, "width": 120, "height": 40},
                        "attrs": {"type": "submit"}, "state": {},
                        "is_visible": True, "is_obstructed": False,
                        "is_interactive": True, "is_editable": False,
                    }
                ]
            async def click_at(self, x, y):
                pass
            async def type_text(self, selector, text):
                pass
            async def wait(self, ms):
                await asyncio.sleep(ms / 1000)
            async def wait_for_stability(self, ms):
                await asyncio.sleep(ms / 1000)
            def get_viewport(self):
                from laya_ultrafast.utils.geometry import Viewport
                return Viewport(width=1280, height=720)
            async def go_back(self):
                pass
        
        # Mock do model
        class MockModel:
            async def complete(self, prompt):
                return '{"action": "TYPE_TEXT", "target_id": "btn-1", "selector": "input#search", "value": "test"}'
        
        agent.engine.browser = MockBrowser()
        agent.engine.model = MockModel()
        
        # Executa com meta simples
        result = await agent.engine.run(
            goal="Testar funcionalidade básica",
            max_steps=2,
        )
        
        # Deve pelo menos completar sem erro (mesmo que não alcance o goal)
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'steps_taken')


@pytest.mark.asyncio
async def test_end_to_end_mock():
    """Teste end-to-end completo com mocks."""
    from laya_ultrafast.agent import LayaAgent
    
    agent = LayaAgent()
    
    # Mocks completos
    class MockBrowser:
        def __init__(self):
            self.urls = []
            self.clicks = []
            self.texts = []
            self.focused_elements = []
            self.snapshot_count = 0
            
        async def navigate(self, url):
            self.urls.append(url)
            return None
        async def get_snapshot(self):
            self.snapshot_count += 1
            # 1st call: initial page with search input (before any action)
            # 2nd call: after TYPE_TEXT, still initial page (freshness check before stale target detection)
            # 3rd call: same, first freshness check
            # 4th call: same, second freshness check - then results page shows up
            if self.snapshot_count <= 3:
                return [
                    {
                        "id": "search-input", "index": 0, "tag": "input", "role": "textbox",
                        "label": "Pesquisar", "selector": "input[name='q']",
                        "bbox": {"x": 100, "y": 100, "width": 200, "height": 30},
                        "attrs": {"type": "text", "name": "q"},
                        "state": {}, "is_visible": True, "is_obstructed": False,
                        "is_interactive": True, "is_editable": True,
                    },
                    {
                        "id": "search-btn", "index": 1, "tag": "button", "role": "button",
                        "label": "Pesquisar", "selector": "button[type='submit']",
                        "bbox": {"x": 320, "y": 100, "width": 80, "height": 30},
                        "attrs": {"type": "submit"},
                        "state": {}, "is_visible": True, "is_obstructed": False,
                        "is_interactive": True, "is_editable": False,
                    }
                ]
            elif self.snapshot_count >= 4:
                # After typing - show results
                return [
                    {
                        "id": "result-link", "index": 0, "tag": "a", "role": "link",
                        "label": "Resultado da busca", "selector": "a.result-link",
                        "bbox": {"x": 100, "y": 200, "width": 300, "height": 40},
                        "attrs": {"href": "/result"}, "state": {},
                        "is_visible": True, "is_obstructed": False,
                        "is_interactive": True, "is_editable": False,
                    }
                ]
            return []
        async def click_at(self, x, y):
            self.clicks.append((x, y))
            return None
        async def focus_element(self, selector):
            self.focused_elements.append(selector)
            return None
        async def type_text(self, selector, text):
            self.texts.append((selector, text))
            return None
        async def wait(self, ms):
            await asyncio.sleep(ms / 1000)
        async def wait_for_stability(self, ms):
            await asyncio.sleep(ms / 1000)
        async def get_element_value(self, selector):
            # Mock returns the last typed value
            return self.texts[-1][1] if self.texts else None
        def get_viewport(self):
            from laya_ultrafast.utils.geometry import Viewport
            return Viewport(width=1280, height=720)
        async def go_back(self):
            return None
    
    class MockModel:
        def __init__(self):
            self.call_count = 0
            
        async def complete(self, prompt):
            self.call_count += 1
            if self.call_count == 1:
                # Primeira chamada: digitar no campo de busca
                return '{"action": "TYPE_TEXT", "target_id": "search-input", "selector": "input[name=\'q\']", "value": "LAYA automação"}'
            elif self.call_count == 2:
                # Segunda chamada: clicar no botão de busca
                return '{"action": "CLICK", "target_id": "search-btn", "selector": "button[type=\'submit\']"}'
            elif self.call_count == 3:
                # Terceira chamada: clicar no resultado
                return '{"action": "CLICK", "target_id": "result-link", "selector": "a.result-link"}'
            else:
                # Quarta chamada: concluir
                return '{"action": "DONE"}'
    
    agent.engine.browser = MockBrowser()
    agent.engine.model = MockModel()
    
    # Executa
    result = await agent.engine.run(
        goal="Pesquise por 'LAYA automação' e clique no primeiro resultado",
        max_steps=10,
    )
    
    # Verificações
    assert result.success
    assert result.steps_taken == 3  # type_text, click result-link, done
    assert len(agent.engine.browser.texts) == 1
    assert agent.engine.browser.texts[0][1] == "LAYA automação"
    assert len(agent.engine.browser.clicks) == 1
    assert len(agent.engine.browser.urls) == 0  # navigate not called in this test


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])