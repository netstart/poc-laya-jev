/**
 * LAYA Snapshot - Extração Atômica de Elementos Interativos
 *
 * Injetado na página via CDP para extrair estado estruturado do DOM
 * sem depender de screenshots. Retorna array de ElementSnapshot.
 *
 * Requisitos:
 * - ES2020+
 * - Execução < 50ms em páginas típicas
 * - Sem dependências externas
 * - Output: JSON serializável
 */

(() => {
  'use strict';

  /**
   * Configuração da extração
   */
  const CONFIG = {
    // Seletores de elementos interativos (prioridade)
    interactiveSelectors: [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled]):not([type="hidden"])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[role="button"]:not([disabled])',
      '[role="link"]:not([disabled])',
      '[role="checkbox"]:not([disabled])',
      '[role="radio"]:not([disabled])',
      '[role="tab"]:not([disabled])',
      '[role="menuitem"]:not([disabled])',
      '[role="option"]:not([disabled])',
      '[role="slider"]:not([disabled])',
      '[role="spinbutton"]:not([disabled])',
      '[role="textbox"]:not([disabled])',
      '[role="searchbox"]:not([disabled])',
      '[role="combobox"]:not([disabled])',
      '[role="listbox"]:not([disabled])',
      '[role="treeitem"]:not([disabled])',
      '[role="gridcell"]:not([disabled])',
      '[role="rowheader"]:not([disabled])',
      '[role="columnheader"]:not([disabled])',
      '[tabindex]:not([tabindex="-1"]):not([disabled])',
      '[onclick]',
      '[ondblclick]',
      '[onmousedown]',
      '[onmouseup]',
      '[contenteditable="true"]',
    ].join(', '),

    // Atributos ARIA para rótulos
    ariaLabelAttributes: [
      'aria-label',
      'aria-labelledby',
      'aria-describedby',
      'title',
      'alt',
      'placeholder',
      'name',
      'value',
      'data-testid',
      'data-test-id',
      'data-cy',
      'id',
    ],

    // Tags que são inherentemente interativas
    interactiveTags: new Set([
      'A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA',
      'OPTION', 'OPTGROUP', 'LABEL', 'FIELDSET', 'LEGEND',
      'DETAILS', 'SUMMARY', 'DIALOG',
    ]),

    // Atributos para extrair
    extractAttributes: [
      'id', 'class', 'name', 'type', 'value', 'placeholder',
      'href', 'role', 'aria-label', 'aria-labelledby', 'aria-describedby',
      'aria-expanded', 'aria-selected', 'aria-checked', 'aria-disabled',
      'aria-hidden', 'aria-controls', 'aria-owns', 'aria-activedescendant',
      'tabindex', 'contenteditable', 'disabled', 'readonly', 'required',
      'data-testid', 'data-test-id', 'data-cy', 'data-action',
    ],

    // Thresholds de visibilidade
    minVisibleArea: 1, // pixels
    minOpacity: 0.01,
    maxDepth: 50,

    // Filtros
    ignoreHidden: true,
    ignoreZeroSize: true,
    ignoreObstructed: true,
  };

  /**
   * Utilitários
   */
  const utils = {
    /**
     * Gera ID único para elemento
     */
    generateId(): string {
      return `laya_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    },

    /**
     * Obtém bounding box normalizado relativo ao viewport
     */
    getBoundingBox(element): DOMRect | null {
      try {
        const rect = element.getBoundingClientRect();
        if (!rect || rect.width === 0 && rect.height === 0) {
          return null;
        }
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
          left: rect.left,
        };
      } catch {
        return null;
      }
    },

    /**
     * Verifica se elemento está no viewport
     */
    isInViewport(rect): boolean {
      if (!rect) return false;
      return (
        rect.width > 0 &&
        rect.height > 0 &&
        rect.right > 0 &&
        rect.bottom > 0 &&
        rect.left < window.innerWidth &&
        rect.top < window.innerHeight
      );
    },

    /**
     * Verifica se elemento tem área visível mínima
     */
    hasMinVisibleArea(rect): boolean {
      return rect && rect.width * rect.height >= CONFIG.minVisibleArea;
    },

    /**
     * Obtém computed style de forma segura
     */
    getComputedStyle(element): CSSStyleDeclaration | null {
      try {
        return window.getComputedStyle(element);
      } catch {
        return null;
      }
    },

    /**
     * Verifica visibilidade via computed style
     */
    isVisibleByStyle(element): boolean {
      const style = utils.getComputedStyle(element);
      if (!style) return false;

      if (style.display === 'none') return false;
      if (style.visibility === 'hidden') return false;
      if (style.opacity < CONFIG.minOpacity) return false;
      if (style.pointerEvents === 'none') return false;

      return true;
    },

    /**
     * Extrai atributos relevantes do elemento
     */
    extractAttributes(element): Record<string, string> {
      const attrs: Record<string, string> = {};
      for (const attr of CONFIG.extractAttributes) {
        const value = element.getAttribute(attr);
        if (value !== null && value !== '') {
          attrs[attr] = value;
        }
      }
      return attrs;
    },

    /**
     * Gera seletor CSS único para o elemento
     */
    generateSelector(element): string {
      // Prioridade: id > data-testid > role+name > xpath
      if (element.id) {
        return `#${element.id}`;
      }
      const testId = element.getAttribute('data-testid') || element.getAttribute('data-test-id');
      if (testId) {
        return `[data-testid="${testId}"]`;
      }
      const cy = element.getAttribute('data-cy');
      if (cy) {
        return `[data-cy="${cy}"]`;
      }
      const role = element.getAttribute('role');
      const label = utils.getAccessibleName(element);
      if (role && label) {
        return `[role="${role}"][aria-label="${label.replace(/"/g, '\\"')}"]`;
      }
      if (role) {
        return `[role="${role}"]`;
      }
      // Fallback: caminho CSS simplificado
      return utils.generateCssPath(element);
    },

    /**
     * Gera caminho CSS simplificado
     */
    generateCssPath(element): string {
      const parts = [];
      let current = element;
      while (current && current !== document.body) {
        let part = current.tagName.toLowerCase();
        if (current.id) {
          part += `#${current.id}`;
          parts.unshift(part);
          break;
        }
        const classNames = Array.from(current.classList)
          .filter(c => !c.startsWith('laya-') && c.length > 1)
          .slice(0, 2)
          .join('.');
        if (classNames) {
          part += `.${classNames}`;
        }
        const siblings = Array.from(current.parentElement?.children || [])
          .filter(el => el.tagName === current.tagName);
        if (siblings.length > 1) {
          const index = siblings.indexOf(current) + 1;
          part += `:nth-of-type(${index})`;
        }
        parts.unshift(part);
        current = current.parentElement;
      }
      return parts.join(' > ');
    },

    /**
     * Obtém nome acessível do elemento (ARIA)
     */
    getAccessibleName(element): string {
      // 1. aria-labelledby
      const labelledBy = element.getAttribute('aria-labelledby');
      if (labelledBy) {
        const labelEl = document.getElementById(labelledBy);
        if (labelEl) return labelEl.textContent?.trim() || '';
      }

      // 2. aria-label
      const ariaLabel = element.getAttribute('aria-label');
      if (ariaLabel) return ariaLabel.trim();

      // 3. label associado (para inputs)
      if (element.tagName === 'INPUT' || element.tagName === 'SELECT' || element.tagName === 'TEXTAREA') {
        const id = element.id;
        if (id) {
          const label = document.querySelector(`label[for="${id}"]`);
          if (label) return label.textContent?.trim() || '';
        }
        const parentLabel = element.closest('label');
        if (parentLabel) return parentLabel.textContent?.trim() || '';
      }

      // 4. title
      const title = element.getAttribute('title');
      if (title) return title.trim();

      // 5. alt (para imagens)
      const alt = element.getAttribute('alt');
      if (alt) return alt.trim();

      // 6. placeholder
      const placeholder = element.getAttribute('placeholder');
      if (placeholder) return placeholder.trim();

      // 7. textContent (truncado)
      const text = element.textContent?.trim();
      if (text && text.length > 0) {
        return text.length > 100 ? text.slice(0, 100) + '…' : text;
      }

      // 8. value (para inputs)
      const value = element.getAttribute('value');
      if (value) return value.trim();

      return '';
    },

    /**
     * Determina o role ARIA do elemento
     */
    getRole(element): string {
      const explicitRole = element.getAttribute('role');
      if (explicitRole) return explicitRole;

      const tag = element.tagName;
      switch (tag) {
        case 'A': return 'link';
        case 'BUTTON': return 'button';
        case 'INPUT': return 'textbox';
        case 'SELECT': return 'combobox';
        case 'TEXTAREA': return 'textbox';
        case 'OPTION': return 'option';
        case 'LABEL': return 'label';
        case 'FIELDSET': return 'group';
        case 'LEGEND': return 'group';
        case 'DETAILS': return 'group';
        case 'SUMMARY': return 'button';
        case 'DIALOG': return 'dialog';
        case 'IMG': return 'img';
        case 'NAV': return 'navigation';
        case 'MAIN': return 'main';
        case 'HEADER': return 'banner';
        case 'FOOTER': return 'contentinfo';
        case 'ASIDE': return 'complementary';
        case 'SECTION': return 'region';
        case 'ARTICLE': return 'article';
        default: return 'generic';
      }
    },

    /**
     * Verifica se elemento está obstruído por outros elementos
     */
    isObstructed(element, rect): boolean {
      if (!rect) return true;

      // Verifica elementos sobrepostos no centro do elemento
      const centerX = rect.x + rect.width / 2;
      const centerY = rect.y + rect.height / 2;

      const topElement = document.elementFromPoint(centerX, centerY);
      if (!topElement) return false;

      // Se o elemento no topo é o próprio elemento ou ancestral, não está obstruído
      if (topElement === element || element.contains(topElement)) {
        return false;
      }

      // Verifica se o elemento no topo é transparente/pointer-events: none
      const topStyle = utils.getComputedStyle(topElement);
      if (topStyle && (topStyle.pointerEvents === 'none' || topStyle.opacity < 0.01)) {
        return false;
      }

      return true;
    },

    /**
     * Verifica se elemento é editável
     */
    isEditable(element): boolean {
      if (element.contentEditable === 'true') return true;
      if (element.tagName === 'INPUT' && !['hidden', 'button', 'submit', 'reset', 'checkbox', 'radio', 'file'].includes(element.type)) return true;
      if (element.tagName === 'TEXTAREA') return true;
      if (element.tagName === 'SELECT') return true;
      return false;
    },

    /**
     * Obtém estado do elemento (checked, selected, expanded, etc.)
     */
    getState(element): Record<string, boolean | string> {
      const state: Record<string, boolean | string> = {};

      // Checked
      if (element.type === 'checkbox' || element.type === 'radio') {
        state.checked = element.checked;
      } else if (element.getAttribute('aria-checked') !== null) {
        state.checked = element.getAttribute('aria-checked') === 'true';
      }

      // Selected
      if (element.tagName === 'OPTION') {
        state.selected = element.selected;
      } else if (element.getAttribute('aria-selected') !== null) {
        state.selected = element.getAttribute('aria-selected') === 'true';
      }

      // Expanded
      if (element.getAttribute('aria-expanded') !== null) {
        state.expanded = element.getAttribute('aria-expanded') === 'true';
      }

      // Disabled
      if (element.disabled || element.getAttribute('aria-disabled') === 'true') {
        state.disabled = true;
      }

      // Readonly
      if (element.readOnly || element.getAttribute('readonly') !== null) {
        state.readonly = true;
      }

      // Required
      if (element.required || element.getAttribute('aria-required') === 'true') {
        state.required = true;
      }

      return state;
    },
  };

  /**
   * Extrai um único elemento para ElementSnapshot
   */
  function extractElement(element, index): ElementSnapshot | null {
    try {
      // Filtro básico
      if (!element || element.nodeType !== Node.ELEMENT_NODE) return null;

      // Verifica visibilidade
      if (!utils.isVisibleByStyle(element)) return null;

      const rect = utils.getBoundingBox(element);
      if (!rect) return null;

      if (CONFIG.ignoreZeroSize && !utils.hasMinVisibleArea(rect)) return null;
      if (CONFIG.ignoreHidden && !utils.isInViewport(rect)) return null;

      // Verifica obstrução
      const isObstructed = CONFIG.ignoreObstructed ? utils.isObstructed(element, rect) : false;

      // Extrai dados
      const tag = element.tagName;
      const role = utils.getRole(element);
      const label = utils.getAccessibleName(element);
      const selector = utils.generateSelector(element);
      const attrs = utils.extractAttributes(element);
      const state = utils.getState(element);
      const isEditable = utils.isEditable(element);

      // Verifica se é interativo
      const isInteractive = CONFIG.interactiveTags.has(tag) ||
        element.matches(CONFIG.interactiveSelectors) ||
        element.getAttribute('role') !== null ||
        element.hasAttribute('tabindex') ||
        element.hasAttribute('onclick');

      // Se não for interativo e não tiver label, pula
      if (!isInteractive && !label) return null;

      return {
        id: utils.generateId(),
        index,
        tag: tag.toLowerCase(),
        role,
        label,
        selector,
        bbox: rect,
        attrs,
        state,
        is_visible: true,
        is_obstructed: isObstructed,
        is_interactive: isInteractive,
        is_editable: isEditable,
      };
    } catch (e) {
      // Ignora erros em elementos individuais
      return null;
    }
  }

  /**
   * Função principal de extração
   */
  function runSnapshot(config?: Partial<typeof CONFIG>): ElementSnapshot[] {
    // Mescla config personalizada
    if (config) {
      Object.assign(CONFIG, config);
    }

    const snapshots: ElementSnapshot[] = [];
    let index = 0;

    // Query all candidates
    const candidates = document.querySelectorAll(CONFIG.interactiveSelectors);

    for (const candidate of candidates) {
      const snapshot = extractElement(candidate, index++);
      if (snapshot) {
        snapshots.push(snapshot);
      }
    }

    // Ordena por posição visual (top-to-bottom, left-to-right)
    snapshots.sort((a, b) => {
      const ay = a.bbox.top;
      const by = b.bbox.top;
      if (Math.abs(ay - by) > 10) return ay - by;
      return a.bbox.left - b.bbox.left;
    });

    // Reindexa após ordenação
    snapshots.forEach((s, i) => { s.index = i; });

    return snapshots;
  }

  // Tipos para TypeScript (referência)
  /**
   * @typedef {Object} ElementSnapshot
   * @property {string} id
   * @property {number} index
   * @property {string} tag
   * @property {string} role
   * @property {string} label
   * @property {string} selector
   * @property {DOMRect} bbox
   * @property {Record<string, string>} attrs
   * @property {Record<string, boolean|string>} state
   * @property {boolean} is_visible
   * @property {boolean} is_obstructed
   * @property {boolean} is_interactive
   * @property {boolean} is_editable
   */

  // Exporta para uso via CDP
  if (typeof window !== 'undefined') {
    window.__LAYA_SNAPSHOT__ = {
      run: runSnapshot,
      config: CONFIG,
      utils,
    };
  }

  // Auto-executa se chamado diretamente
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runSnapshot, CONFIG, utils };
  }
})();