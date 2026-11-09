# Guia de estilo do portfólio

Para agentes que fazem figura, tabela, relatório ou README em qualquer projeto do portfólio. O visual vem do projeto de gestão hospitalar do SUS-SP. Siga este guia e use os arquivos do kit; não invente paleta, fonte ou tema por projeto.

## O kit

| Arquivo | Para quê |
|---|---|
| `estilo_portfolio.py` | tema matplotlib, paleta, auxiliares de desenho, validador (`--validar`) |
| `theme_portfolio.R` | o mesmo visual em ggplot2 |
| `modelo_relatorio.tex` | preâmbulo, capa e caixa de destaque do relatório em LaTeX |
| `README_modelo.md` | estrutura do README de cada projeto |
| `exemplos/` | figura, PDF e registro de números de exemplo, sobre dados fictícios |

## Regras de gráfico

1. **O título afirma o achado.** "A Unidade C reduziu a espera em 31%", e não "Espera por unidade". O número do título sai da conta, por f-string ou `paste0`, e nunca é digitado. Período, unidade e definição da métrica vão no subtítulo: `titulo(ax, achado, subtitulo)`.
2. **Use rótulo direto, e não legenda.** O nome da série vai na ponta da linha (`rotular_ponta`). A legenda é a saída quando o rótulo não cabe, e só então.
3. **Uma cor de destaque, o resto neutro.** A série que a figura aponta sai em `DESTAQUE` (vermelho). As demais saem em `NEUTRO` (cinza), sem rótulo individual. A distribuição de uma variável só sai em `COR_BARRA` (azul). Use `destacar(categorias, foco)`.
4. **A barra começa no zero.** Use `eixo_no_zero(ax)` ou `expand = c(0, 0)` com `limits = c(0, ...)`. A linha pode ter eixo truncado, desde que o corte esteja marcado e dito no subtítulo.
5. **Não use eixo duplo.** Dois indicadores com unidades diferentes vão em dois painéis com o mesmo eixo x, ou num índice com base 100.
6. **A fonte vai no rodapé.** Use `fonte(ax, "Fonte: ...")` ou `labs(caption = ...)`. Caminho de arquivo não entra: o rastro fica no script e em `NUMEROS_CANONICOS.md`.

Detalhes que o kit já resolve. Não refaça à mão:

- **Cor por entidade.** Quando a categoria tem identidade (grupo, rede, região), escreva o mapa de cores uma vez (modelo: `CORES_EXEMPLO`) e reutilize-o em todas as figuras. Use no máximo quatro cores próprias. Azul e roxo ficam perto sob protanopia: se os dois forem linha ou ponto no mesmo quadro, use também `MARCADORES`.
- **Sem transparência.** Para uma zona que recua, use `misturar(cor, 0.82)`, que dá um tom sólido, e não `alpha`.
- **Texto colorido.** Texto na cor de uma série passa por `cor_de_texto(cor)`, que escurece até 4,5:1 contra o branco. `rotular_ponta` já faz isso.
- **Gradiente só para magnitude.** Use `mapa_sequencial()` para magnitude e `mapa_divergente()` para desvio em torno de um ponto com significado. Nunca use gradiente para identidade.
- **Números no eixo.** O eixo sai com vírgula decimal. Eixo de ano chama `eixo_ano(ax)`; sem isso, a locale escreve "2.015".
- **Texto.** A fonte é Lato. O título vai em negrito e todo o resto em regular, nos tamanhos `TAM_*`. Não escreva `fontsize=` nem `fontweight=` soltos.
- **Distribuição.** Distribuição se mostra em boxplot, e não em violino.

## A regra dos números

**Todo número impresso sai de um script e fica registrado em `NUMEROS_CANONICOS.md`.** Isso vale para o README, o relatório, o título e os rótulos de figura, as tabelas e os slides.

- O script que calcula o número também o escreve: na figura, por f-string; no LaTeX, como macro num `.tex` gerado (`\newcommand{\NumQueda}{31}`), lido com `\input`; nas linhas de tabela, num `.tex` lido com `\linhasde{...}`. Ver `exemplos/exemplo_figura.py`.
- Nenhum número é digitado no `.tex` nem no `.md`. Isso inclui anos de recorte e metas.
- `NUMEROS_CANONICOS.md` tem uma linha por número, com estas colunas: número, valor, o que é, de que script sai e onde aparece. Modelo: `exemplos/NUMEROS_CANONICOS.md`.
- Para mudar um número: mude o script, rode-o de novo e confira cada lugar da coluna "Onde aparece". Nunca corrija só o texto.
- Todo valor monetário declara a sua base: corrente, ou real com o mês de referência.
- No texto em português, use vírgula decimal e ponto de milhar.

## Como importar o kit

O repositório publicado de cada projeto precisa ser autossuficiente. Por isso, **copie** os arquivos do kit para uma pasta `estilo/` do projeto, em vez de apontar para `Desktop/portfolio-estilo`. O kit é a fonte: quando ele mudar, recopie os arquivos e regenere as figuras. Não edite a cópia dentro do projeto.

**Python**

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "estilo"))  # ajuste ao nível do script

from estilo_portfolio import (set_sus_style, titulo, fonte, rotular_ponta,
                              eixo_ano, eixo_no_zero, DESTAQUE, NEUTRO)
set_sus_style()          # antes de criar a primeira figura
```

Para conferir a fonte e a paleta, rode `python estilo/estilo_portfolio.py --validar` (sai com código 1 se alguma checagem de portão reprovar). Se o projeto tiver um mapa de cores próprio, meça esse mapa com `validar_paleta({"Grupo A": AZUL, ...})`.

**R**

```r
source("estilo/theme_portfolio.R")   # registra a Lato e define o tema
p <- ggplot(...) + ... + theme_portfolio()
salvar_figura(p, "figuras/minha_figura.png")   # ragg, fundo branco, 150 dpi
```

O R precisa de `ggplot2`, `scales`, `systemfonts` e `ragg`. Para formatar números, use `rotulo_virgula()`, `rotulo_pct()`, `rotulo_ano` e `num()`. Os rótulos diretos (`rotular_ponta()`) precisam de `coord_cartesian(clip = "off")` e de margem direita.

**LaTeX**

1. Copie `modelo_relatorio.tex` para `relatorio/relatorio.tex` no projeto.
2. Não edite o bloco entre `PREÂMBULO DO KIT` e `FIM DO PREÂMBULO DO KIT`.
3. Preencha "DADOS DA CAPA" e troque a seção de exemplo pelo conteúdo do projeto.
4. Ajuste `\graphicspath` para a pasta de figuras e troque o `\input` dos números pelo arquivo que o script do projeto gera.

Para compor:

- figura na medida larga: `\imagemplena[0.86]{arquivo}`;
- tabela com booktabs (a zebra e a Lato entram sozinhas);
- coluna sim/não: `\marcasim` e `\marcanao`;
- achado principal da seção: `\begin{destaque}[Título] ... \end{destaque}`, no máximo um por seção.

O motor é o pdfLaTeX, com duas passadas.

## Antes de entregar

- [ ] O título afirma o achado e o número dele sai do script.
- [ ] Há uma cor de destaque, o resto está neutro, e não há legenda onde cabe rótulo direto.
- [ ] O eixo de barra está no zero, não há eixo duplo e a fonte está no rodapé.
- [ ] Os números têm vírgula decimal, o ano não tem separador e as casas decimais são as mesmas dentro da figura.
- [ ] Todo número impresso está em `NUMEROS_CANONICOS.md` e foi regenerado pelo script depois da última mudança.
- [ ] O `--validar` passa (ou passa com as ressalvas declaradas) e o PDF compila sem erro.
