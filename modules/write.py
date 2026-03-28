from pathlib import Path
import logging
import re
from .utils import run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)


def escape_drawtext(text: str) -> str:
	"""
	Escapa caracteres especiais para FFmpeg drawtext filter.
	Refs: https://ffmpeg.org/ffmpeg-filters.html#drawtext-1
	"""
	# Escapa caracteres especiais
	text = text.replace('\\', '\\\\')  # Barra invertida primeiro
	text = text.replace("'", "\\'")     # Aspas simples
	text = text.replace(':', '\\:')     # Dois-pontos
	text = text.replace('\n', ' ')      # Quebras de linha → espaço
	return text


@log_function
def add_text(
	video_path: str,
	text: str,
	x: str = "(w-text_w)/2",
	y: str = "(h-text_h)/2",
	output_dir: str = "write_output",
	font_size: int = 30,
	font_color: str = "white",
	font: str = "Calibri",
	font_dir: str = None,
	text_align: str = "center",
	start_time: float = None,
	end_time: float = None,
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Escreve texto em um vídeo usando FFmpeg drawtext.

	Args:
		video_path (str): Caminho do vídeo de entrada.
		text (str): Texto a escrever.
		x (str): Posição horizontal - valor ou expressão passada direto pro ffmpeg.
		y (str): Posição vertical - valor ou expressão passada direto pro ffmpeg.
		output_dir (str): Diretório de saída (padrão: "write_output").
		font_size (int): Tamanho da fonte (padrão: 30).
		font_color (str): Cor da fonte em nome ou hex (padrão: white).
		font (str): Nome da fonte (padrão: Calibri).
		font_dir (str): Diretório de fontes (opcional). Se fornecido, espera-se arquivo .ttf.
		text_align (str): Alinhamento do texto (padrão: "center"). Opções: "left", "center", "right".
		start_time (float): Tempo de início em segundos (opcional).
		end_time (float): Tempo de fim em segundos (opcional).
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False)

	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho de saída e comando FFmpeg como lista.
	"""
	video_path = Path(video_path)
	output_dir = Path(output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)

	# Define nome do arquivo de saída
	output_filename = f"{video_path.stem}_write{video_path.suffix}"
	output_path = str(output_dir / output_filename)

	# Define condição de enable (quando mostrar o texto)
	if start_time is not None and end_time is not None:
		# Mostrar entre start_time e end_time
		enable_cond = f"between(t,{start_time},{end_time})"
	elif start_time is not None:
		# Mostrar a partir de start_time até o final
		enable_cond = f"gte(t,{start_time})"
	elif end_time is not None:
		# Mostrar do início até end_time
		enable_cond = f"lte(t,{end_time})"
	else:
		# Mostrar o tempo todo
		enable_cond = "1"

	# Escapa o texto para FFmpeg
	text_escaped = escape_drawtext(text)

	# Constrói o filtro drawtext
	drawtext_filter = f"drawtext=text='{text_escaped}':x={x}:y={y}:fontsize={font_size}:fontcolor={font_color}:text_align={text_align}"
	
	# Adiciona fontfile ou fonte padrão
	if font_dir:
		# Se fornecido um diretório, constrói o caminho completo da fonte
		font_dir_path = Path(font_dir)
		font_file = font_dir_path / f"{font}"
		
		# Se o arquivo não tiver extensão, tenta adicionar .ttf
		if not font_file.suffix:
			# Tenta encontrar o arquivo .ttf
			ttf_files = list(font_dir_path.glob(f"{font}*.ttf"))
			if ttf_files:
				font_file = ttf_files[0]  # Pega o primeiro match
				logger.debug(f"Found font file: {font_file}")
			else:
				logger.warning(f"No .ttf file found for font '{font}' in {font_dir_path}, using system font")
				drawtext_filter += f":font='{font}'"
		else:
			# Arquivo completo fornecido
			pass
		
		if font_file.exists():
			# Usa caminho absoluto convertido para formato POSIX
			fontfile_path = font_file.as_posix()
			drawtext_filter += f":fontfile='{fontfile_path}'"
		else:
			logger.warning(f"Font file not found: {font_file}, trying system font")
			drawtext_filter += f":font='{font}'"
	else:
		# Se nenhum diretório, assume que a fonte está no diretório padrão do sistema
		drawtext_filter += f":font='{font}'"
	
	# Adiciona condição de enable
	drawtext_filter += f":enable='{enable_cond}'"

	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_path),
		"-vf", drawtext_filter,
		"-c:a", "copy",
		output_path,
	]

	logger.info(f"Writing text '{text}' on video...")
	
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)
	
	return output_path, cmd_result
