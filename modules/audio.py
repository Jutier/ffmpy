from pathlib import Path
import logging
from .utils import run_ffmpeg
from .logs import log_function

logger = logging.getLogger(__name__)



@log_function
def enhance_audio(
	video_path: str,
	output_dir: str = "audio_output",
	# denoise
	anlmdn_strength: float = 5e-2,
	afftdn_nf: int = -70,
	afftdn_type: str = "v",  # v=voice, w=white
	# filters
	highpass_freq: int = 250,
	lowpass_freq: int = 4000,
	# equalizer bands [(freq, width, gain)]
	eq_bands: list = None,
	# compressor
	comp_threshold: str = "-24dB",
	comp_ratio: float = 1.5,
	comp_attack: int = 15,
	comp_release: int = 100,
	# declick
	declick_threshold: int = 40,
	# encoding
	audio_bitrate: str = "192k",
	audio_codec: str = "aac",
	overwrite: bool = True,
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Aplica processamento de áudio em um vídeo usando FFmpeg.

	Args:
		video_path (str): Caminho do vídeo original.
		output_dir (str, optional): Diretório de saída.
		
		anlmdn_strength (float): Força do denoise (Non-Local Means).
		afftdn_nf (int): Noise floor do afftdn (-20 a -80).
		afftdn_type (str): Tipo de ruído ('v'=voice, 'w'=white).

		highpass_freq (int): Frequência do high-pass.
		lowpass_freq (int): Frequência do low-pass.

		eq_bands (list): Lista de tuplas (freq, width, gain).

		comp_threshold (str): Threshold do compressor (ex: "-24dB").
		comp_ratio (float): Ratio do compressor.
		comp_attack (int): Attack em ms.
		comp_release (int): Release em ms.

		declick_threshold (int): Threshold do declick (1 a 100).

		audio_bitrate (str): Bitrate do áudio.
		audio_codec (str): Codec de áudio.

		overwrite (bool): Sobrescrever saída.

	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho do arquivo e comando FFmpeg como lista.
	"""

	video_path = Path(video_path)
	output_dir = Path(output_dir)

	output_path = output_dir / f"{video_path.stem}_audio{video_path.suffix}"

	video_ffmpeg = video_path.as_posix()
	output_ffmpeg = output_path.as_posix()

	output_dir.mkdir(exist_ok=True, parents=True)

	# Default EQ (se não for passado)
	if eq_bands is None:
		eq_bands = [
			(400, 1, -5),
			(2500, 1, -3),
		]

	# Monta cadeia de filtros
	filters = []

	# denoise
	filters.append(f"anlmdn=s={anlmdn_strength}")
	filters.append(f"afftdn=nf={afftdn_nf}:nt={afftdn_type}")

	# pass filters
	filters.append(f"highpass=f={highpass_freq}")
	filters.append(f"lowpass=f={lowpass_freq}")

	# equalizer
	for freq, width, gain in eq_bands:
		filters.append(f"equalizer=f={freq}:t=q:w={width}:g={gain}")

	# compressor
	filters.append(
		f"acompressor=threshold={comp_threshold}:ratio={comp_ratio}:attack={comp_attack}:release={comp_release}"
	)

	# declick
	filters.append(f"adeclick=threshold={declick_threshold}")

	filter_chain = ",".join(filters)

	# Monta comando FFmpeg com filtros de áudio
	# Exemplo: ffmpeg -y -i input.mp4 -af "lowpass=4000,highpass=80,acompressor=...,adeclick=..." -c:v copy -c:a aac -b:a 128k output.mp4
	cmd = [
		"ffmpeg",
		"-y" if overwrite else "-n",
		"-i", str(video_ffmpeg),
		"-af", filter_chain,
		"-c:v", "copy",
		"-c:a", audio_codec,
		"-b:a", audio_bitrate,
		str(output_ffmpeg),
	]

	logger.info("Enhancing audio...")
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)

	return str(output_path), cmd_result


@log_function
def generate_spectrum(
	video_path: str,
	output_dir: str = "spectrum_output",
	width: int = 1280,
	height: int = 720,
	scale: str = "log",  # "log" ou "lin"
	gain: int = 10,
	start_freq: int = None,
	stop_freq: int = None,
	overwrite: bool = True,
	dry_run: bool = False,
) -> tuple[str, list]:
	"""
	Gera uma imagem do espectro de áudio de um vídeo usando FFmpeg.

	Args:
		video_path (str): Caminho do vídeo de entrada.
		output_dir (str, optional): Diretório de saída.
		width (int): Largura da imagem.
		height (int): Altura da imagem.
		scale (str): Escala do espectro ("log" ou "lin").
		gain (int): Ganho visual do espectro.
		start_freq (int, optional): Frequência mínima (zoom inferior).
		stop_freq (int, optional): Frequência máxima (zoom superior).
		overwrite (bool): Sobrescrever arquivo existente.
		dry_run (bool): Se True, retorna comando sem executar.

	Returns:
		tuple[str, list]: (output_path, cmd) - Caminho da imagem e comando FFmpeg como lista.
	"""

	video_path = Path(video_path)
	output_dir = Path(output_dir)

	output_path = output_dir / f"{video_path.stem}_spectrum.png"

	video_ffmpeg = video_path.as_posix()
	output_ffmpeg = output_path.as_posix()

	output_dir.mkdir(exist_ok=True, parents=True)

	# Monta filtro base
	filter_parts = [
		f"s={width}x{height}",
		f"scale={scale}",
		f"gain={gain}",
	]

	if start_freq is not None:
		filter_parts.append(f"start={start_freq}")

	if stop_freq is not None:
		filter_parts.append(f"stop={stop_freq}")

	filter_str = "showspectrumpic=" + ":".join(filter_parts)

	# Monta comando FFmpeg para gerar espectro de áudio
	# Exemplo: ffmpeg -y -i input.mp4 -lavfi "showspectrumpic=s=1280x720:gain=1" output.png
	cmd = [
		"ffmpeg",
		"-y" if overwrite else "-n",
		"-i", str(video_ffmpeg),
		"-lavfi", filter_str,
		str(output_ffmpeg),
	]

	logger.info("Generating spectrum...")
	cmd_result = run_ffmpeg(cmd, dry_run=dry_run)

	return str(output_path), cmd_result
