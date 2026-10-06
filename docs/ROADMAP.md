# ECode — Roadmap de Migração Empírica

## 1. Objetivo

O ECode será um produto independente, inicialmente derivado do Darwin Gödel Machine, mas não limitado à arquitetura original do DGM.

O princípio central é:

> incorporar somente mecanismos que demonstrem ganho verificável de capacidade, custo, robustez ou eficiência suficiente para compensar sua complexidade operacional e de manutenção.

Projetos externos são tratados como **donors de mecanismos**, não como frameworks a serem combinados.

Principais donors iniciais:

- DGM — https://github.com/lemoz/darwin-godel-machine
- AFlow — https://github.com/FoundationAgents/AFlow
- HarnessX — https://github.com/Darwin-Agent/HarnessX
- MaAS — https://github.com/bingreeky/MaAS
- CodePro — https://github.com/oigorbrito/codepro
- SMAG — https://github.com/oigorbrito/smag
- SMAG-ReX — https://github.com/oigorbrito/smag-rex

---

# 2. Regra universal de seleção

Nenhuma evidência externa representa aprovação automática.

A cadeia obrigatória será:

```text
UPSTREAM RESULT
      ↓
EVIDENCE REVIEW
      ↓
ELIGIBLE_FOR_LOCAL_TEST
      ↓
LOCAL BASELINE
      ↓
CONTROLLED EXPERIMENT
      ↓
HELD-OUT / REGRESSION
      ↓
ENGINEERING ECONOMY
      ↓
KEEP / REJECT / INCONCLUSIVE
      ↓
PROMOTION
```

Formalmente:

```text
UPSTREAM_PASS != ECODE_PASS
```

e:

```text
GOOD_BENCHMARK_RESULT
!=
MIGRATION_AUTHORIZATION
```

A evidência upstream apenas torna um mecanismo elegível para experimento.

---

# 3. Métrica principal de decisão

Uma feature só deve sobreviver se o benefício verificado superar seu custo total.

A decisão será orientada aproximadamente por:

\[
EngineeringROI =
\frac{VerifiedCapabilityGain}
{Tokens + Latency + RuntimeCost + Complexity + Maintenance}
\]

Critérios principais:

- qualidade/verificação;
- generalização held-out;
- custo em tokens;
- wall-clock;
- uso de RAM/VRAM;
- dependências adicionadas;
- LOC adicionada ou alterada;
- acoplamento;
- regressões;
- dificuldade de manutenção;
- facilidade de remoção.

---

# 4. Fase 0 — Criar o baseline ECode

## Seed

Base inicial:

**Darwin Gödel Machine**

https://github.com/lemoz/darwin-godel-machine

O DGM foi escolhido porque já possui um loop evolutivo real:

```text
archive
↓
parent selection
↓
mutation
↓
validation
↓
benchmark
↓
score
↓
archive update
↓
next generation
```

## Evidência que justifica o seed

O projeto registrou evolução em LiveCodeBench, incluindo um experimento de aproximadamente:

```text
5 / 12
→
8 / 12
```

durante um ciclo evolutivo de 50 iterações.

Também existem experimentos posteriores de held-out transfer com melhorias observadas em conjuntos disjuntos daqueles usados para selecionar as mutações.

Esse resultado torna o mecanismo DGM elegível como baseline real do ECode.

Não significa que todos os seus componentes sejam aprovados.

## O que preservar inicialmente

- archive;
- lineage;
- parent selection;
- mutation/self-modification;
- evaluation orchestration;
- benchmark runner;
- model/provider abstraction;
- telemetry relevante à evolução.

## O que não recebe aprovação automática

- decisões específicas de sandbox;
- dependências cloud;
- configuração específica de providers;
- modelo de agente atual completo;
- estratégias atuais de search;
- benchmark específico;
- qualquer fallback inseguro.

---

# 5. Fase 1 — Hardening do baseline

Antes de comparar donors, o DGM deve virar um baseline operacional confiável.

## 5.1 Sandbox fail-closed

Comportamento proibido:

```text
SANDBOX_REQUESTED
+
SANDBOX_UNAVAILABLE
→
HOST_EXECUTION
```

Novo contrato:

```text
SANDBOX_REQUESTED
+
SANDBOX_UNAVAILABLE
=
BLOCKED
```

Esse gate é obrigatório antes de resultados decision-bearing.

---

## 5.2 Runtime local

O DGM já possui interface OpenAI-compatible.

Qualificar inicialmente:

- llama.cpp server;
- Ollama OpenAI-compatible API;
- opcionalmente LM Studio.

Objetivo:

```text
DGM evolution
↓
OpenAI-compatible API
↓
local model
```

sem criar outro provider proprietário.

---

## 5.3 Congelar ambiente

Cada experimento deve registrar:

- seed SHA;
- donor SHA;
- modelo;
- quantização;
- runtime;
- hardware;
- dataset;
- random seed;
- orçamento;
- timeout;
- número de gerações;
- verifier;
- hashes dos artefatos.

Resultado:

```text
ECODE_B0 = PINNED_BASELINE
```

---

# 6. Fase 2 — AFlow: simplificação do search

Projeto:

**AFlow**

https://github.com/FoundationAgents/AFlow

Paper: ICLR 2025.

## Evidência externa

AFlow usa search automatizado de workflows representados como código, com uma variante de Monte Carlo Tree Search.

Foi avaliado em:

- HumanEval;
- MBPP;
- GSM8K;
- MATH;
- HotpotQA;
- DROP.

O paper reporta melhoria média aproximada de **5,7%** sobre baselines comparados.

Resultados exemplificados no repositório para MBPP também mostram diferenças próximas de:

```text
~0.79
→
~0.94
```

em determinados experimentos.

Isso representa cerca de:

```text
+15 pontos percentuais
```

naquele cenário.

## Hipótese

Talvez o mecanismo evolutivo completo do DGM seja mais complexo do que necessário.

Testar:

```text
DGM search
vs
AFlow-like search
```

mantendo todo o restante constante.

## O que migrar para experimento

Não importar AFlow inteiro.

Extrair apenas:

- candidate sampling;
- graph/workflow mutation;
- MCTS-like selection;
- reuse de experiências anteriores;
- score-driven selection.

## Experimento

```text
B0 = native DGM evolution/search

C1 = same ECode
     + AFlow-derived search
```

## Gate de promoção

Promover somente se:

```text
quality >= B0
AND
held_out >= B0
AND
total_cost < B0
```

ou se houver ganho substancial de qualidade que justifique custo adicional.

Caso contrário:

```text
AFLOW_SEARCH = REJECTED
```

---

# 7. Fase 3 — HarnessX: evolução do harness

Projeto:

**HarnessX**

https://github.com/Darwin-Agent/HarnessX

## Evidência externa

HarnessX registra ganhos relevantes por alteração do harness mantendo o modelo.

Exemplos reportados:

```text
Qwen 3.5 9B
33%
→
47%
```

Ganho:

```text
+14 pp
```

Outro experimento:

```text
GPT-5
62%
→
84%
```

Ganho:

```text
+22 pp
```

No experimento de coevolution:

```text
33.97%
→
41.67%
```

apenas por harness evolution.

Depois, combinando com model evolution:

```text
55.77%
```

Esses números justificam investigar mecanismos do harness.

Mas os resultados são principalmente em GAIA, portanto:

```text
GAIA_GAIN
!=
SWE_GAIN
```

Precisamos testar transferência para coding.

---

## Mecanismos prioritários

### H1 — Checkpoint/recovery

Objetivo:

reduzir perda de trabalho e permitir retomada de trajetória.

Experimento:

```text
B0 = no checkpoint
C1 = checkpoint/recovery
```

Métricas:

- recovery success;
- repeated tokens;
- wall-clock;
- state corruption;
- lost progress.

---

### H2 — Context management / compaction

Hipótese:

reduzir tokens sem reduzir solve rate.

Comparar:

```text
B0 = native context

C1 = HarnessX-derived compaction
```

Métricas:

- input tokens;
- output tokens;
- solve rate;
- regression rate;
- context loss.

---

### H3 — Tool filtering

Hipótese:

reduzir escolhas irrelevantes e chamadas desnecessárias.

Medir:

- tool calls;
- failed actions;
- tokens;
- solve rate;
- wall-clock.

---

### H4 — Harness configuration search

Só testar depois de termos vários mechanisms válidos.

Search space possível:

```text
planning
memory
context
tools
verification
checkpoint
routing
```

O HarnessX não entra como framework.

Somente o mecanismo de configuração/search pode ser adaptado.

---

# 8. Fase 4 — MaAS: arquitetura condicionada à tarefa

Projeto:

**MaAS**

https://github.com/bingreeky/MaAS

Paper aceito como ICML 2025 Oral.

## Evidência externa

MaAS foi avaliado em:

- HumanEval;
- GSM8K;
- MATH.

O mecanismo busca arquiteturas diferentes conforme tarefa e dificuldade, em vez de selecionar uma configuração universal.

## Hipótese

Após termos múltiplas features qualificadas, talvez seja melhor escolher dinamicamente quais usar.

Exemplo:

```text
simple task
→ minimal architecture

hard task
→ planning + review

large-context task
→ compaction

high-risk task
→ stronger verification
```

## Pré-condição

Não implementar MaAS-like routing enquanto não existirem mecanismos individualmente qualificados.

Sem isso:

```text
SELECTOR
+
UNQUALIFIED_OPTIONS
=
NO_VALUE
```

## Experimento

```text
B0 = one global architecture

C1 = task-conditioned architecture selector
```

Medir:

- solve rate;
- token reduction;
- wall-clock;
- routing errors;
- selector overhead;
- held-out generalization.

---

# 9. Fase 5 — Memory

Memory não deve entrar só porque é comum em agent frameworks.

Só deve ser testada se experimentos demonstrarem problema concreto de:

- repeated exploration;
- repeated failures;
- lost state;
- long-horizon inefficiency.

Candidatos podem vir do HarnessX ou outros donors.

## Gate

```text
NO_MEASURED_MEMORY_PROBLEM
=
NO_MEMORY_SYSTEM
```

Isso evita complexidade prematura.

---

# 10. Fase 6 — CodePro como donor experimental

Projeto:

https://github.com/oigorbrito/codepro

O CodePro não será transplantado como chassis.

Ele pode doar mecanismos para melhorar qualidade científica dos experimentos.

Candidatos:

- workload identity;
- treatment configuration;
- measurement semantics;
- environment provenance;
- run provenance;
- failure attribution;
- independent verifier;
- evidence identity.

Esses mecanismos não são tratados como features de performance.

Eles servem para:

```text
make experiments trustworthy
```

não para:

```text
claim solve-rate improvement
```

---

# 11. Fase 7 — SMAG / SMAG-ReX

Projetos:

https://github.com/oigorbrito/smag

https://github.com/oigorbrito/smag-rex

SMAG e SMAG-ReX fornecem principalmente regras de governança e autoridade.

Preservar princípios:

```text
DOCUMENTED != EXECUTED

UPSTREAM_PASS != LOCAL_PASS

CLAIM_SCOPE <= EVIDENCE_SCOPE

EXECUTION_AUTHORITY
!=
ACCEPTANCE_AUTHORITY
!=
PROMOTION_AUTHORITY

NO_SILENT_FALLBACK
```

Também preservar a estratégia donor-by-donor:

```text
discover
↓
pin
↓
hypothesis
↓
freeze protocol
↓
run comparison
↓
preserve evidence
↓
KEEP / REJECT / INCONCLUSIVE
```

---

# 12. Ordem de implementação

## Wave 0 — Foundation

1. criar ECode;
2. importar DGM com histórico;
3. registrar SHA upstream;
4. preservar licença;
5. criar baseline;
6. fail-closed sandbox;
7. runtime local;
8. reproduzir um evolution cycle.

---

## Wave 1 — Architecture simplification

Primeiro donor:

```text
AFlow search
```

Objetivo:

determinar se podemos reduzir complexidade do núcleo DGM.

Esta é a maior prioridade porque pode mudar profundamente o chassis antes que outras features sejam adicionadas.

---

## Wave 2 — Runtime robustness

HarnessX:

1. checkpoint/recovery;
2. trajectory persistence;
3. context/compaction;
4. tool filtering.

Cada mecanismo isoladamente.

---

## Wave 3 — Architecture search

Quando houver vários mecanismos válidos:

- HarnessX-like harness search;
- depois MaAS-like conditional selection.

---

## Wave 4 — Expensive mechanisms

Somente posteriormente:

- memory;
- multi-agent;
- RL;
- model coevolution;
- complex routing.

Essas features precisam justificar custos significativamente maiores.

---

# 13. Regras Git de migração

O repositório ECode será independente.

Remotes recomendados:

```text
origin   -> oigorbrito/ecode
dgm      -> lemoz/darwin-godel-machine
aflow    -> FoundationAgents/AFlow
harnessx -> Darwin-Agent/HarnessX
maas     -> bingreeky/MaAS
```

## Nunca

```text
git merge donor/main
```

diretamente na `main` do ECode sem avaliação.

## Preferir

Branches experimentais:

```text
eval/aflow-search
eval/harnessx-checkpoint
eval/harnessx-context
eval/maas-selector
```

---

# 14. Estratégia para migração de código

Existem três opções.

## A — Cherry-pick

Usar somente quando:

- arquitetura é compatível;
- commit é isolado;
- dependências são compatíveis;
- comportamento é claramente entendido.

---

## B — Port

Copiar/adaptar partes específicas mantendo atribuição.

Usar quando:

- algoritmo é útil;
- interfaces são diferentes;
- código ainda é reutilizável.

---

## C — Reimplementação

Preferencial para mecanismos de frameworks arquiteturalmente distintos.

Fluxo:

```text
understand mechanism
↓
derive minimal contract
↓
implement ECode-native version
↓
compare against donor evidence
```

Esse deve ser o padrão para AFlow, HarnessX e MaAS.

---

# 15. Registro obrigatório de cada donor

Cada experimento deve possuir algo equivalente a:

```yaml
donor:
  repository:
  revision:
  source:
  license:

mechanism:
  name:
  original_evidence:
  benchmark:
  reported_gain:

hypothesis:
  expected_effect:

migration:
  method: cherry-pick | port | reimplementation
  code_added:
  dependencies_added:

baseline:
  revision:
  configuration:

candidate:
  revision:
  configuration:

results:
  quality:
  held_out:
  tokens:
  runtime:
  memory:
  complexity:
  regressions:

decision:
  KEEP | REJECT | INCONCLUSIVE
```

---

# 16. Gate universal de promoção

Todo mecanismo precisa passar:

```text
SOURCE_PINNED
       ↓
LICENSE_REVIEWED
       ↓
UPSTREAM_EVIDENCE_CONFIRMED
       ↓
HYPOTHESIS_REGISTERED
       ↓
BASELINE_FROZEN
       ↓
IMPLEMENTED
       ↓
LOCAL_EXECUTION
       ↓
REGRESSION_TEST
       ↓
CONTROLLED_COMPARISON
       ↓
HELD_OUT
       ↓
ENGINEERING_ECONOMY
       ↓
KEEP / REJECT / INCONCLUSIVE
       ↓
PROMOTION
```

Não existe:

```text
IMPLEMENTED = PROMOTED
```

---

# 17. Priorização baseada em evidência

| Prioridade | Mecanismo | Donor | Evidência externa | Objetivo |
|---|---|---|---|---|
| P0 | evolution/archive/mutation | DGM | LiveCodeBench `5/12 → 8/12` + held-out | baseline |
| P1 | search simplificado | AFlow | ~5,7% médio; exemplo MBPP ~`0.79 → 0.94` | reduzir complexidade |
| P2 | checkpoint/recovery | HarnessX | harness evolution demonstrou ganhos gerais | robustez |
| P3 | context/compaction | HarnessX | forte impacto de harness no benchmark | reduzir tokens |
| P4 | tool policy/filtering | HarnessX | parte do harness search | eficiência |
| P5 | harness configuration search | HarnessX | GAIA `33→47`, `62→84` | otimização automática |
| P6 | task-conditioned architecture | MaAS | HumanEval/MATH/GSM8K | eficiência adaptativa |
| P7 | memory | donor TBD | somente se necessidade local | longo horizonte |
| P8 | RL / coevolution | HarnessX/outros | `33.97→55.77` combinado | alto custo / experimental |

---

# 18. Critério de sucesso final

O objetivo do ECode não é acumular os melhores mecanismos encontrados na literatura.

O objetivo é convergir para:

```text
THE SMALLEST ARCHITECTURE
THAT DELIVERS THE HIGHEST
VERIFIED ENGINEERING CAPABILITY
AT ACCEPTABLE TOTAL COST
```

Portanto uma feature de +2% pode ser rejeitada se dobrar complexidade.

E uma feature de +0% pode ser aceita se reduzir tokens ou tempo drasticamente mantendo qualidade.

O produto final deve conter apenas mecanismos cuja presença possa ser defendida empiricamente.

---

# 19. Estado inicial recomendado

```text
ECODE_STATUS = BOOTSTRAP

SEED = DGM
PRIMARY_SEARCH_CHALLENGER = AFlow

FEATURE_DONOR_1 = HarnessX
ADAPTIVE_SELECTION_DONOR = MaAS

EXPERIMENTAL_CONTRACT_DONOR = CodePro
GOVERNANCE_REFERENCE = SMAG / SMAG-ReX

NO_FEATURE_PROMOTED_FROM_DONOR = TRUE
```

---

## 20. Estado observado do bootstrap (2026-10-05)

Este estado é uma fotografia do checkout, não uma aprovação de maturidade nem de promoção:

| Gate | Estado observado | Consequência |
|---|---|---|
| Repositório canônico | `origin/main` consultado em `982b0b34c84ace34d638c574c2ba5221b8dd4cdd` | O trabalho local parte desse histórico em branch isolada. |
| Revisão do donor DGM | `lemoz/darwin-godel-machine` `main` consultado em `c885363a59681cb8589fcc2ad5bde4eb3915140e` | Revisão fixada para revisão de evidência; nenhum código foi importado. |
| Licença ECode | `LICENSE-SELECT.md` indica que a licença do projeto não foi escolhida | Estado registrado; não impede o trabalho local autorizado nesta branch. |
| Licença DGM | Nenhum `LICENSE`, `COPYING` ou `NOTICE` foi encontrado na árvore da revisão consultada | Ausência registrada. Por instrução do usuário, a adaptação seletiva pode prosseguir; o pin é rastreabilidade técnica interna, sem crédito visível obrigatório. |
| Sandbox | O caminho atual exige Docker e registra bloqueio quando indisponível | Hardening local; não é comportamento atribuído ao DGM. |
| Runtime local | Há adapter OpenAI-compatible genérico e fixture sem provider | Adapter não qualifica llama.cpp, Ollama ou LM Studio. |
| Loop integrado | `ecode.py --engine dgm` opta pelo Engine apenas no fixture provider-free; `--engine legacy` é o default de produção; `--offline-fixture` permanece compatível | A fronteira de CLI/fixture está integrada; callbacks reais de mutação e avaliação ainda não estão no Engine e a produção não migrou. |
| Evidência offline | Fixture registra baseline manifest `NEW_LOCAL_BASELINE`, configuração, hashes de código/dataset/artefatos, ambiente, seed, archive, lineage e telemetria | O baseline criado tem escopo provider-free de plumbing; não mede capacidade de modelo nem benchmark real. |
| Separação mutation/evaluation | Harness evaluation foi extraído para `ecode_core.legacy_evaluation`; `ECodeEvaluator` valida artefatos e não atribui score a `BLOCKED`/`INCOMPLETE`; archive mantém esses resultados no histórico, fora do pool de pais | Testes focados passam; mutação e avaliação não estão ainda orquestradas por `EvolutionEngine` na CLI normal. |
| Adapter de mutação | `self_improve(..., mutation_only=True)` devolve patch e SHA-256 sem avaliar; `ECodeMutationRunner` cria `AgentVersion` com `candidate_sha256` | Contrato e callback testados; chamada real Docker/agent e integração CLI não executadas. |
| Bootstrap de avaliação cacheada | `initialize_with_result()` sem reexecução, `ECodeEvaluator.from_metadata()` e entrega de `parent_result` ao `MutationRunner` | Há cache na cópia separada `D:\projetos\ecode\ecode-main`, mas ele não tem manifesto de hashes/proveniência nem checkout Git com `HEAD`; permanece `UNVERIFIED` e não pode seedar o Engine. A cópia ativa não contém o cache. |
| Seletor DGM ponderado | Port seletivo de `sigmoid(lambda * (score - alpha_0)) / (1 + valid_child_count)` em `DGMWeightedParentSelector`; opt-in no fixture | Integração e reprodutibilidade passaram no fixture; performance real ainda não foi validada. Nenhum benchmark DGM foi reproduzido nem há promoção para a CLI real. |

### Ordem de trabalho conciliada

1. Preservar o histórico canônico e registrar a fotografia local como checkpoint de bootstrap; não chamá-la de `ECODE_B0` antes da migração/integração DGM e do ciclo reproduzível.
2. Usar a revisão DGM fixada em `docs/donors/dgm.yaml`; registrar a ausência de arquivo de licença e manter o pin como rastreabilidade interna da revisão usada.
3. Migrar os mecanismos previstos, sem importar decisões de provider, fallback, sandbox ou promoção; então congelar o baseline reproduzível com revisão, dependências, runtime/hardware, configuração, seed, orçamento, timeout, verifier e hashes.
4. Manter o sandbox fail-closed e integrar a CLI/evaluator ao contrato `ecode_core` sem introduzir provider fallback.
5. Executar primeiro o ciclo offline por fixture; depois qualificar runtime local; só então executar benchmark e challengers donor em branches e protocolos separados.
6. Para cada donor, exigir pin, licença, evidência upstream revisada, hipótese, baseline congelado, comparação controlada, held-out/regressão e custo de engenharia antes da decisão.

Até esses gates serem satisfeitos, o estado é `BOOTSTRAP`; nenhum mecanismo de donor está `PROMOTED` e nenhum número upstream é resultado ECode. A revisão consultada não contém arquivo de licença; essa condição e a instrução do usuário para prosseguir ficam registradas como proveniência técnica interna.

### Progresso incremental

O primeiro recorte da separação entre mutação e avaliação está implementado: `self_improve()` continua gerando a mutação, depois entrega o patch a `evaluate_self_improve()`, que usa `ecode_core.legacy_evaluation.run_benchmark_evaluation` para chamar o harness legado. O modo `mutation_only` retorna o patch sem avaliar, e `ECodeMutationRunner` o adapta ao contrato `MutationRunner` com hash de candidato (sem alegar hash de source tree). `EvolutionEngine.initialize_with_result()` e `ECodeEvaluator.from_metadata()` permitem carregar baseline já avaliado sem rodar benchmark novamente; o resultado do pai chega ao mutator para escolha contextual da tarefa. O seletor DGM ponderado foi portado seletivamente. **Integração e reprodutibilidade passaram no fixture provider-free; performance real ainda não foi validada.** `ecode.py --engine dgm` agora expõe essa fatia fixture-only; `--engine legacy` continua sendo o default e preserva o loop de produção. Foi gerado um par de baselines locais novos, com `BASELINE_ORIGIN=NEW_LOCAL_BASELINE`, manifests de código/configuração/dataset/ambiente/seed/artefatos e comparação reproduzível em `.provenance/new-local-baseline-pair-v3/`; esse baseline descreve somente a fixture sintética. `ECodeEvaluator` converte metadados em `EvaluationResult`, verifica o hash do artefato candidato e não dá score a execuções `BLOCKED` ou `INCOMPLETE`. O `Archive` conserva esses resultados para lineage, mas não os oferece como pais. Harnesses simulados mantêm `SANDBOX_UNAVAILABLE = BLOCKED`. O cache está ausente na cópia ativa, mas foi localizado em `ecode-main`: 475 arquivos SWE-Bench e 1.118 Polyglot, com fingerprints SHA-256 registrados em `docs/BOOTSTRAP-CHECKPOINT.md`. Como não há manifesto de proveniência/checksums e a cópia não tem `HEAD` Git, os fingerprints não autenticam a origem; o cache fica `UNVERIFIED` e não foi importado nem usado como evidência comparável. Essa incerteza não bloqueia o plumbing provider-free. A interface local Ollama `/v1/models` respondeu à descoberta de modelos, sem geração/inferência; a avaliação real segue bloqueada pelo acesso negado ao named pipe do Docker Desktop Linux Engine. Ainda faltam a integração dos callbacks reais de mutação/avaliação e um baseline de avaliação real novo ou histórico verificável para comparabilidade; performance real ainda não foi validada.

Primeiro marco:

```text
ECODE-B0
=
DGM-derived
+
local runtime
+
fail-closed sandbox
+
reproducible evolution
+
pinned evidence
```

Segundo marco:

```text
ECODE-E1
=
B0
vs
AFlow-derived search
```

Somente depois desse confronto faz sentido aumentar significativamente a superfície do produto.

## 21. Continuidade de runtime local (2026-10-05)

- `docker info` e a execução/remoção de `hello-world` passaram quando o comando teve acesso autorizado ao daemon. Isso qualifica disponibilidade básica do runtime Docker neste host; não qualifica o harness SWE-Bench/Polyglot nem a execução de código gerado. A chamada do coding agent ainda não foi executada com a permissão de Docker necessária.
- A cópia ativa não tem o cache de avaliação inicial. O cache observado em `ecode-main` continua `UNVERIFIED` e não será usado para comparação histórica.
- A descoberta `GET /v1/models` do Ollama respondeu dentro do container e listou modelos locais. Quatro completions curtas via `/v1/chat/completions` retornaram HTTP 500 com `llama-server binary not found`; uma chamada adicional por `ollama run` falhou igual e `ollama ps` não listou modelos carregados. Não houve resposta de modelo. A evidência está em `.provenance/local-runtime-smoke-2026-10-05.json`.
- Foi corrigida a passagem da configuração genérica `ECODE_OPENAI_*` para o container do coding agent. Com `ECODE_OPENAI_BASE_URL`, somente essas configurações são encaminhadas e credenciais cloud não são propagadas por esse caminho. A ausência da variável preserva o caminho de credenciais legado. A alteração ainda não foi executada com o coding agent nem validada por inferência.
- Próximo gate: reparar/atualizar o runtime Ollama via distribuição oficial ou apontar o adapter para outro servidor OpenAI-compatible local funcional; então repetir a completion smoke e qualificar o adapter dentro do coding agent com orçamento explícito. Em paralelo, definir como criar um seed de avaliação novo sem tratar o cache histórico como confiável. Só depois executar o mesmo protocolo imutável para legacy versus Engine.

Estado atualizado:

```ini
DOCKER_DAEMON_SMOKE = PASS
CONTAINER_TO_OLLAMA_DISCOVERY = PASS
OLLAMA_COMPLETION_SMOKE = BLOCKED_LLAMA_SERVER_MISSING
LOCAL_AGENT_INFERENCE = NOT_EXECUTED
HISTORICAL_CACHE_PROVENANCE = UNVERIFIED
HISTORICAL_BASELINE = NOT_USABLE_FOR_COMPARISON
REAL_BENCHMARK = NOT_EXECUTED
PERFORMANCE_GAIN = NOT_PROVEN
```

## 22. Retentativa Ollama no host (2026-10-05)

- `ollama run qwen2.5-coder:3b` retornou exatamente `OLLAMA_SMOKE_OK`.
- O endpoint OpenAI-compatible no host respondeu a `GET /v1/models` com HTTP 200 e `POST /v1/chat/completions` com `OLLAMA_SMOKE_OK`; `ollama ps` mostrou o modelo carregado em 100% GPU.
- A inferência local via CLI e endpoint está qualificada apenas como smoke. Não é validação do coding agent, do benchmark ou de ganho de capacidade.
- Não foi possível repetir a chamada dentro do container nesta tentativa: acesso ao named pipe do Docker Desktop Linux Engine negado. A falha anterior no container (`llama-server binary not found`) permanece como evidência histórica separada.
- Resultado atual:

```ini
OLLAMA_HOST_INFERENCE_SMOKE = PASS
CONTAINER_OLLAMA_SMOKE = BLOCKED_DOCKER_NAMED_PIPE_PERMISSION_DENIED
LOCAL_AGENT_INFERENCE = NOT_EXECUTED
REAL_BENCHMARK = NOT_EXECUTED
PERFORMANCE_GAIN = NOT_PROVEN
```

O registro detalhado está em `.provenance/local-runtime-smoke-2026-10-05.json`.

## 23. Qualificação local no worktree WSL (2026-10-05)

Esta seção atualiza o estado das seções anteriores para a tentativa no worktree `/mnt/d/projetos/ecode/ecode-wsl`.

- Preflight executado pela `.venv` do worktree: `docker.from_env().ping() == True`; versão do servidor `29.8.1`; `DOCKER_HOST` e `DOCKER_CONTEXT` não definidos. Ping e versão foram coletados no mesmo processo Python antes de iniciar qualquer container.
- De dentro de `python:3.12-slim`, `GET /v1/models` e `POST /v1/chat/completions` no endpoint Ollama responderam HTTP 200. O modelo `qwen2.5-coder:3b` retornou exatamente `ECODE_CONTAINER_OLLAMA_29_8_1`.
- A imagem `ecode:local-ollama-smoke` foi construída a partir deste worktree. `coding_agent.py` recebeu o endpoint OpenAI-compatible e retornou exatamente `ECODE_AGENT_OLLAMA_29_8_1`; o patch foi vazio (0 bytes). A cópia do repositório e o baseline Git foram temporários dentro do container.
- Escopo: um pedido sem uso de ferramentas. Isso valida a inicialização do coding agent, o caminho local até uma resposta do modelo e a extração do patch vazio. O loop de ferramentas, mutação, avaliador, benchmark e comparação legacy/Engine não foram executados; capacidade real e ganho de performance permanecem não provados.
- Evidência detalhada: `.provenance/coding-agent-ollama-smoke-2026-10-05.json`.

```ini
DOCKER_PREFLIGHT = PASS_PING_TRUE_SERVER_29.8.1
CONTAINER_TO_OLLAMA_INFERENCE = PASS
CODING_AGENT_LOCAL_PROVIDER_WIRING = PASS_WITH_SCOPE_SINGLE_NO_TOOL_RESPONSE
CODING_AGENT_TOOL_LOOP = NOT_EXECUTED
REAL_BENCHMARK = NOT_EXECUTED
PERFORMANCE_GAIN = NOT_PROVEN
```

## 24. Tool loop do coding agent com Ollama (2026-10-05)

- Repeti a execução em imagem construída de `git archive HEAD`, com uma cópia descartável do repositório dentro do container. Preflight Docker continuou `ping=True`, servidor `29.8.1`.
- O primeiro pedido de ferramenta gerou `tool_input` como string. `process_tool_call()` expande o argumento com `**tool_input`; a execução falhou com `TypeError` e o modelo repetiu chamadas inválidas. A tentativa não foi aprovada.
- Na repetição, o pedido explicitou o schema `{ "command": "..." }`. O modelo chamou `bash` uma vez para ler um token aleatório, recebeu corretamente `f588a17e0cbe2a26` e encerrou o ciclo sem modificar o checkout. Isso comprova um único ciclo da ferramenta local em escopo controlado.
- A resposta final incluiu o token correto, mas adicionou texto ao redor; saída literal exata não passou. O modelo precisou de instrução explícita sobre o formato de `tool_input`, então a robustez do contrato continua limitada.
- Registro detalhado: `.provenance/coding-agent-tool-smoke-2026-10-05.json`.

```ini
CODING_AGENT_TOOL_LOOP = PASS_WITH_SCOPE_ONE_BASH_READ_CYCLE
TOOL_INPUT_SCHEMA_ROBUSTNESS = FRAGILE
EXACT_FINAL_OUTPUT = NOT_MET
MUTATION_RUNNER_INTEGRATION = NOT_EXECUTED
REAL_BENCHMARK = NOT_EXECUTED
PERFORMANCE_GAIN = NOT_PROVEN
```

## 25. Experimento isolado de compatibilidade de ferramentas (2026-10-05)

- Repeti o cenário sem mencionar o formato do schema. O modelo voltou a enviar `bash.tool_input` como string; a chamada falhou no dispatcher atual, confirmando a fragilidade observada.
- Em uma cópia temporária dentro do container, apliquei somente um shim experimental que transforma string de `bash` em `{ "command": string }`. Sem mudar prompt nem worktree, a mesma forma de entrada executou um `cat` de token aleatório e devolveu o conteúdo da ferramenta ao agente.
- A resposta final incluiu o token, mas manteve prosa/Markdown. O patch do checkout descartável continuou vazio.
- O shim foi apenas experimento: **não foi promovido ao código ECode**. O resultado sustenta um candidato pequeno de compatibilidade, mas ainda não mede ganho de capacidade nem substitui comparação legacy/Engine.
- Evidência: tentativa 3 em `.provenance/coding-agent-tool-smoke-2026-10-05.json`.

```ini
CURRENT_TOOL_LOOP = FRAGILE_WITH_QWEN_STRING_ARGUMENT
ISOLATED_STRING_NORMALIZER = PASS
PRODUCTION_NORMALIZER = NOT_PROMOTED
REAL_BENCHMARK = NOT_EXECUTED
PERFORMANCE_GAIN = NOT_PROVEN
```


## 26. Normalizacao estrita do bash tool_input (2026-10-05)

- Preservei o dispatcher B0 e comparei-o com C1 usando spy: B0 falha controladamente para string, tipos nao-mapeaveis e objetos com chaves invalidas, mas encaminha o objeto com command nested a funcao da tool. C1 bloqueia esses formatos antes da chamada.
- C1 normaliza somente string nao vazia para um objeto com command igual a string original. Objeto valido retorna sem reescrita; o helper rejeita comandos vazios, tipos inesperados, chaves diferentes de command, campos extras e command que nao seja string. A validacao ocorre somente para bash; editor e outras tools mantem o contrato atual.
- tools/bash.py define apenas o argumento command; embora o schema nao declare additionalProperties false, B0 ja rejeita campos extras ao chamar a funcao Python. C1 preserva essa rejeicao efetiva.
- A trajetoria real usou qwen2.5-coder:3b no container com endpoint Ollama OpenAI-compatible. No mesmo processo do launcher, Docker SDK ping=True, servidor 29.8.1, API 1.56. A tool bash recebeu o payload de entrada como string, leu a fixture aleatoria e devolveu o token cujo SHA-256 coincide com o valor esperado; a mensagem com resultado foi enviada ao modelo.
- Na segunda fixture, a sequencia observada foi bash -> editor -> bash: leitura inicial VALUE=old, edicao do arquivo descartavel para VALUE=new, verificacao via bash e leitura independente do arquivo final. O retorno positivo do editor usa “has been overwritten with new content”; o primeiro predicado auxiliar do harness esperava a palavra “successfully”, mas a resposta da tool e o conteudo lido independentemente confirmaram a edicao.
- A suite completa terminou com 78 testes aprovados; compileall e git diff --check passaram. As tres warnings de depreciacao vieram de backoff/asyncio.iscoroutinefunction e nao falharam os testes.

TOOL_INPUT_NORMALIZER = ACCEPTED
AGENT_TOOL_LOOP = PASS
REAL_MODEL_CAPABILITY = NOT_ASSESSED
PERFORMANCE_GAIN = NOT_PROVEN
BENCHMARK = NOT_EXECUTED

- Provenance detalhado: .provenance/tool-input-normalizer-c1-2026-10-05.json.
