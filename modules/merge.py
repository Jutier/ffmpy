from pathlib import Path
import logging
from .utils import run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)


@log_function
def merge_write(cmds, video_path=None, output_dir="text_output", dry_run=False):
	"""
	Mescla múltiplos comandos drawtext em um único comando FFmpeg.
	Extrai todos os filtros drawtext dos comandos e os combina com vírgulas,
	evitando recodificação múltipla do vídeo.
	
	Args:
		cmds (list): Lista de comandos (cada um é uma lista como retornado por dry_run).
				   Exemplo: [cmd1, cmd2, cmd3] onde cada cmd é uma lista tipo
				   ["ffmpeg", "-y", "-i", "video.mp4", "-vf", "drawtext=...", "-c:a", "copy", "output.mp4"]
		video_path (str): Caminho do vídeo de entrada original. Se None, extrai do primeiro comando.
		output_dir (str): Diretório de saída (padrão: "text_output").
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False).
	
	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho de saída e comando FFmpeg unificado.
	"""
	
	# Extrai o vídeo de entrada do primeiro comando se não for fornecido
	if video_path is None:
		first_cmd = cmds[0]
		try:
			i_index = first_cmd.index("-i")
			video_path = first_cmd[i_index + 1]
		except (ValueError, IndexError):
			raise ValueError("Could not extract video path from first command")
	
	# Cria diretório de saída
	output_dir_path = Path(output_dir)
	output_dir_path.mkdir(parents=True, exist_ok=True)

	video_path_obj = Path(video_path)

	# Define nome do arquivo de saída (com sufixo _merged_written)
	output_filename = f"{video_path_obj.stem}_write{video_path_obj.suffix}"
	output_path = str(output_dir_path / output_filename)
	
	# Extrai todos os filtros drawtext dos comandos
	filters = []
	for cmd in cmds:
		try:
			# Procura por "-vf" no comando
			vf_index = cmd.index("-vf")
			filters.append(cmd[vf_index + 1])
		except (ValueError, IndexError):
			raise ValueError(f"Could not extract filter from command: {cmd}")
	
	# Combina todos os filtros com vírgula
	combined_filter = ",".join(filters)
	
	# Constrói o comando unificado
	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_path),
		"-vf", combined_filter,
		"-c:a", "copy",
		output_path,
	]
	
	logger.info(f"Merged {len(cmds)} write commands into one")
	
	return output_path, cmd


@log_function
def merge_mark(cmds, video_path=None, output_dir="mark_output", dry_run=False):
	"""
	Mescla múltiplos comandos overlay (mark) em um único comando FFmpeg.
	Extrai todas as imagens e os filtros overlay dos comandos e os combina,
	evitando recodificação múltipla do vídeo.
	
	Args:
		cmds (list): Lista de comandos mark (cada um é uma lista como retornado por dry_run).
				   Exemplo: [cmd1, cmd2] onde cada cmd é uma lista tipo
				   ["ffmpeg", "-y", "-i", "video.mp4", "-i", "mark.png", "-filter_complex", "overlay=10:10", "-c:a", "copy", "output.mp4"]
		video_path (str): Caminho do vídeo de entrada original. Se None, extrai do primeiro comando.
		output_dir (str): Diretório de saída (padrão: "mark_output").
		dry_run (bool): Se True, retorna o comando sem executar (padrão: False).
	
	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho de saída e comando FFmpeg unificado.
	"""
	
	# Extrai o vídeo de entrada do primeiro comando se não for fornecido
	if video_path is None:
		first_cmd = cmds[0]
		try:
			i_index = first_cmd.index("-i")
			video_path = first_cmd[i_index + 1]
		except (ValueError, IndexError):
			raise ValueError("Could not extract video path from first command")
	
	# Cria diretório de saída
	output_dir_path = Path(output_dir)
	output_dir_path.mkdir(parents=True, exist_ok=True)

	video_path_obj = Path(video_path)

	# Define nome do arquivo de saída (com sufixo _merged_marked)
	output_filename = f"{video_path_obj.stem}_mark{video_path_obj.suffix}"
	output_path = str(output_dir_path / output_filename)
	
	# Extrai todas as imagens e filtros dos comandos
	mark_paths = []
	filters = []
	
	for cmd in cmds:
		try:
			# Procura pelas imagens (-i que não é o vídeo)
			i_indices = [i for i, x in enumerate(cmd) if x == "-i"]
			for idx in i_indices[1:]:
				mark_paths.append(cmd[idx + 1])
			
			# Procura pelo filtro overlay
			fc_index = cmd.index("-filter_complex")
			filters.append(cmd[fc_index + 1])
		except (ValueError, IndexError):
			raise ValueError(f"Invalid mark command: {cmd}")
	
	# Constrói o comando unificado com labels interligados
	# Estrutura: [0][1]overlay=...,[tmp0][2]overlay=...[tmp1]
	filter_parts = []
	current_input = "[0]"  # Começamos com o vídeo
	mark_index = 1  # Índice da primeira marca (0 é o vídeo)
	
	for i, filter_str in enumerate(filters):
		filter_parts.append(f"{current_input}[{mark_index}]{filter_str}[tmp{i}]")
		current_input = f"[tmp{i}]"
		mark_index += 1
	
	combined_filter = ";".join(filter_parts)
	last_filter_index = len(filters) - 1
	
	# Constrói o comando unificado
	cmd = [
		"ffmpeg",
		"-y",
		"-i", str(video_path),
	]
	
	# Adiciona todas as imagens
	for mark_path in mark_paths:
		cmd.extend(["-i", str(mark_path)])
	
	# Mapeia a saída do último filtro + áudio
	cmd.extend([
		"-filter_complex", combined_filter,
		"-map", f"[tmp{last_filter_index}]",
		"-map", "0:a",
		"-c:a", "copy",
		output_path,
	])
	
	logger.info(f"Merged {len(cmds)} mark commands into one")
	
	return output_path, cmd
