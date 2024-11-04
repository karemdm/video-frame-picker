# Aplicativo de Reprodução de Vídeo

Este é um reprodutor de vídeo em Python construído com Tkinter e OpenCV que permite carregar, visualizar e interagir com arquivos de vídeo. O player oferece navegação quadro a quadro, intervalos de pulo personalizados, salvamento de quadros como imagens e redimensionamento dinâmico da tela de vídeo com base nas dimensões da tela.

## Funcionalidades

- **Navegação por Quadro**: Avance ou retroceda pelos quadros com intervalos de pulo personalizáveis usando as setas do teclado.
- **Salvar Quadros**: Capture e salve o quadro atual como uma imagem.
- **Redimensionamento Dinâmico**: A tela do vídeo se redimensiona proporcionalmente de acordo com o tamanho da tela.
- **Navegação por Barra de Rolagem**: Navegue pelos quadros usando uma barra de rolagem com controles de clique, rolagem e arraste.
- **Controle por Mouse e Teclado**: Controle a navegação de quadros com atalhos de mouse e teclado.
- **Abrir Novo Vídeo**: Carregue um vídeo diferente diretamente pelo reprodutor.

## Instalação

### Pré-requisitos

- Python 3.x

### Criar um Ambiente Virtual

Para isolar as dependências do projeto, é recomendável criar um ambiente virtual. Execute os seguintes comandos no terminal:

```bash
# Navegue até o diretório do seu projeto
cd /caminho/para/seu/projeto

# Crie um ambiente virtual chamado 'venv'
python -m venv venv

# Ative o ambiente virtual (Windows)
venv\Scripts\activate

# Ative o ambiente virtual (macOS/Linux)
source venv/bin/activate

# Instalação das Dependências
# Após ativar o ambiente virtual, execute o seguinte comando para instalar as bibliotecas necessárias:
pip install -r requirements.txt
```

## Inicialização

Execute o script para abrir o reprodutor de vídeo. Você será solicitado a escolher um arquivo de vídeo para reprodução.

## Controles de Navegação

- **Seta Direita**: Avança 40 quadros para frente.
- **Seta Esquerda**: Retrocede 20 quadros.
- **Seta para Cima**: Avança 200 quadros.
- **Seta para Baixo**: Retrocede 100 quadros.
- **Espaço ou ‘S’**: Salva o quadro atual como uma imagem.
- **Navegação por Barra de Rolagem**: Use a barra de rolagem na parte inferior para avançar ou retroceder no vídeo.
- **Abrir Novo Vídeo**: Use o botão “Abrir Novo Vídeo” para carregar um arquivo de vídeo diferente.

## Salvando Quadros

Os quadros são salvos no mesmo diretório do vídeo com um nome baseado no nome do arquivo original, com o número do quadro adicionado ao final.

## Comandos de Teclado

- **Seta Direita**: Avança para o próximo quadro.
- **Seta Esquerda**: Retrocede para o quadro anterior.
- **Espaço ou ‘S’**: Salva o quadro atual.
- **‘Q’**: Encerra o reprodutor.

## Estrutura do Código

A seguir está uma visão geral das principais classes e métodos:

- **Classe VideoPlayer**: Classe principal que gerencia a reprodução do vídeo.
  - `__init__`: Inicializa o reprodutor, configura a interface e os eventos.
  - `next_frame` e `previous_frame`: Navegação de quadros para frente e para trás.
  - `save_current_frame`: Salva o quadro atual como uma imagem.
  - `update_display`: Atualiza a tela com o quadro atual.
  - `scroll_video`: Controla a barra de rolagem para a navegação de quadros.

## Exemplo de Uso

Para iniciar o reprodutor de vídeo, execute o código abaixo:

```python
if __name__ == "__main__":
    main()
