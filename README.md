# Trabalho Prático de Testes: Buscador de notícias web sobre notícias da BBC

Repositório do trabalho prático de **Teste de Software**, contendo uma máquina de busca web sobre o corpus de notícias da BBC e sua suíte de testes de unidade e End-to-End (E2E).

## Integrantes
- Beatriz Camilly Gulart Pereira
- Clarice Oliveira Minobolli Teixeira
- Maria Eduarda Nunes e Carvalho de Vasconcelos Costa

## Sobre o sistema
Protótipo funcional de **máquina de busca web** desenvolvido para indexar e consultar 2.225 notícias da BBC (base de Greene e Cunningham, 2006).

**Principais funcionalidades:**
- **Indexação e persistência:** constrói um índice invertido baseado em **Trie Compacta** e salva a estrutura e as estatísticas dos termos em arquivo `.dat` para reutilização em disco.
- **Consultas booleanas:** processa expressões com os operadores `AND`, `OR`, `NOT` e parênteses por meio de um *parser* recursivo definido por gramática EBNF.
- **Ranqueamento e paginação:** ordena os documentos com *mergesort* pela média dos *z-scores* dos termos da consulta e exibe os resultados em páginas de 10 itens com *snippets* destacados.
- **Navegação web:** permite abrir o conteúdo completo de cada documento, consultar o histórico das 10 buscas mais recentes da sessão e acessar a página de ajuda com exemplos de sintaxe.

## Tecnologias
- **Aplicação:** Python, Flask, Jinja2, HTML e CSS.
- **Testes de unidade e cobertura:** `pytest` e `pytest-cov`.
- **Testes End-to-End (E2E):** Cypress.
- **Integração Contínua (CI/CD):** GitHub Actions (execução automatizada em Linux, macOS e Windows e publicação do relatório de cobertura).

## Como executar
Abaixo, estão listados os comandos para executar a aplicação, os testes de unidade e de integração, a cobertura dos testes e os testes E2E.

### Aplicação
```bash
pip install -r requirements.txt
python app.py
```
Ou utilizando o comando make:
```bash
make run
```

### Testes de unidade e de integração
```bash
python -m pytest tests/unit/            # apenas unidade
python -m pytest tests/integration/     # apenas integração
python -m pytest tests/                 # unidade e integração 
```
Ou utilizando o comando make:
```bash
make test-unit          # apenas unidade
make test-integration   # apenas integração
make test               # unidade e integração
```

### Teste de cobertura
```bash
pytest --cov=modules --cov-report=term-missing
```
Ou utilizando o comando make:
```bash
make coverage
```

### Testes E2E (Cypress)
Com o servidor Flask em execução (python app.py):
```bash
npx cypress open   # modo interativo
npx cypress run    # modo headless
```
Ou utilizando o comando make (com modo interativo):
```bash
make test-e2e
```

## Uso de IA
Ferramentas de IA generativa (como **Gemini** *[adicione outras, se houver]*) foram utilizadas como apoio durante o desenvolvimento para:
- revisar os testes de unidade e End-to-End (E2E) de acordo com as recomendações e boas práticas da disciplina;
- auxiliar na nomeação clara e descritiva de commits e funções de teste;
- apoiar na identificação e correção de erros durante a implementação e execução das suítes;
- verificar pontos do código não cobertos pela suíte de testes e acrescentar testes para esses casos.

Todas as sugestões foram revisadas, adaptadas ao código do projeto e validadas pela equipe.

## TO-DO
- Trocar o nome do repositório para um mais significativo
- Mínimo 50 testes de unidades com boas práticas
- 5 testes e2e 
- Mensurar cobertura de testes (>= 80%)
- Usar CD/CI: testes para Linux, MacOS e Windowns antes do commit
- Publicar relatório de cobertura através do GitHub Actions
- Commits pequenos, frequentes e mensagem descritiva
- Colocar sistema em produção
- Criar vídeo (máximo de 5 minutos): o vídeo deve apresentar brevemente: (1) o sistema desenvolvido, (2) as tecnologias utilizadas, (3) como as ferramentas de IA foram empregadas e (4) os testes implementados. O vídeo deve ser publicado no YouTube.
